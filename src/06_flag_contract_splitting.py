# src/06_analyze_contract_splitting.py
#
# This script detects potential contract splitting by clustering multiple
# sub‑threshold awards that are similar in description and close in time for
# the same bidder. The goal is to surface patterns where several smaller
# contracts could have been split to avoid a higher approval threshold.
#
# Rationale:
#   Splitting a large procurement into several smaller awards within a short
#   window can bypass oversight/approval gates. Clustering tenders by text
#   similarity and award-date proximity helps flag bidders with suspicious
#   sequences of awards that merit review.
#
# Key operations:
#   - Normalize text (title) for fuzzy matching
#   - Impute/standardize award date for temporal proximity checks
#   - For bidders over an annual approval threshold, cluster sub‑threshold tenders
#     using (a) title similarity and (b) award-date proximity
#   - Build row‑level cluster output and bidder‑level summary with risk score
#
# Output:
#   1. {country_code}_contract_split_all.parquet
#      - Cluster‑level details (cluster_id, tender_ids, titles, dates, totals, buyers).
#
#   2. {country_code}_contract_split_summary.parquet
#      - Bidder‑level summary: number of clusters, average/max contracts per cluster,
#        dollars at risk, and a percentile‑based risk score.
#
# Notes:
#   - Ensure 02_cleaning_and_prep.py has been run prior to this script.
#   - Parameters (approval_threshold, time_window_days, similarity_threshold) can be
#     tuned via function args depending on procurement norms in a country.
#   - The clustering step uses pairwise comparisons within bidder groups and is O(n²)
#     per group; consider blocking or approximate similarity for very large datasets.


import os
import numpy as np
import pandas as pd
from difflib import SequenceMatcher
import networkx as nx
from tqdm import tqdm
from config import DEFAULT_COUNTRY


# === Load cleaned dataset (produced by 02_cleaning_and_prep.py) ===
def load_cleaned_data(country_code):
    """Load the cleaned parquet for the given country code, or raise a helpful error."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    path = os.path.join(base_dir, "output\\ancillary", f"{country_code}_cleaned.parquet")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing cleaned file: {path}")
    return pd.read_parquet(path)


# === Text normalization for fuzzy matching ===
def normalize_text(text):
    """
    Lowercase, trim, and strip non‑alphanumeric characters (keep spaces).
    Returns empty string for NaN to avoid downstream errors.
    """
    if pd.isnull(text):
        return ''
    text = str(text).lower().strip()
    return ''.join(c for c in text if c.isalnum() or c.isspace())


# === Main analyzer: find potential contract splitting clusters ===
def analyze_contract_splitting(df, approval_threshold=10_000_000, time_window_days=7, similarity_threshold=0.5):
    """
    Identify clusters of sub‑threshold awards for the same bidder that are similar in title
    and occur within a short time window.

    Parameters:
      approval_threshold (float): Threshold above which oversight/approval would trigger.
      time_window_days (int): Max days between earliest and latest award within a cluster.
      similarity_threshold (float): Minimum SequenceMatcher ratio to connect two tenders.

    Returns:
      - df_split_all (DataFrame): Cluster‑level details (one row per detected cluster)
      - df_split_summary (DataFrame): Bidder‑level summary and risk scores
    """

    # --- Ensure key datetime fields are parsable; coerce invalids to NaT ---
    date_columns = [
        'tender_publications_firstcallfortenderdate',
        'tender_biddeadline',
        'tender_awarddecisiondate',
        'tender_publications_firstdcontractawarddate',
        'tender_contractsignaturedate'
    ]
    for col in date_columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    # --- Impute award decision date using other available milestones when missing ---
    df['tender_award_date_filled'] = df['tender_awarddecisiondate']
    for col in ['tender_biddeadline', 'tender_publications_firstdcontractawarddate', 'tender_contractsignaturedate']:
        df['tender_award_date_filled'] = df['tender_award_date_filled'].fillna(df[col])

    # --- Prepare numeric and normalized text fields for clustering ---
    df['cleaned_bid_price_usd'] = pd.to_numeric(df['cleaned_bid_price_usd'], errors='coerce')
    df['normalized_title'] = df['tender_title'].apply(normalize_text)
    time_window = pd.Timedelta(days=time_window_days)

    # --- Step 2.1: Find bidders whose total payments exceed the oversight threshold ---
    bidders_over_threshold = df.groupby(['bidder_name', 'bidder_country']).agg(
        total_payments=('cleaned_bid_price_usd', 'sum')
    ).reset_index()
    bidders_over_threshold = bidders_over_threshold[bidders_over_threshold['total_payments'] >= approval_threshold]

    # --- Step 2.2: Keep only those bidders' contracts ---
    df_in_scope = df.merge(
        bidders_over_threshold[['bidder_name', 'bidder_country']],
        on=['bidder_name', 'bidder_country'],
        how='inner'
    )

    # --- Step 2.3: Focus on individual tenders below the approval threshold ---
    df_below_threshold = df_in_scope[df_in_scope['cleaned_bid_price_usd'] < approval_threshold].copy()
    df_below_threshold = df_below_threshold.sort_values(
        by=['bidder_name', 'bidder_country', 'tender_award_date_filled']
    ).reset_index(drop=True)

    # --- Step 3: Graph-based clustering per bidder using title similarity + date proximity ---
    contract_clusters = []
    grouped = df_below_threshold.groupby(['bidder_name', 'bidder_country'])
    print("Processing bidders:")
    for (bidder_name, bidder_country), group in tqdm(grouped, total=len(grouped)):
        group = group.reset_index(drop=True)
        G = nx.Graph()

        # Add nodes with row metadata
        for idx, row in group.iterrows():
            G.add_node(idx, **row.to_dict())

        # Pairwise connections within time window & similarity threshold (O(n²) per group)
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                date_i, date_j = group.loc[i, 'tender_award_date_filled'], group.loc[j, 'tender_award_date_filled']
                if pd.isnull(date_i) or pd.isnull(date_j):
                    continue
                if abs(date_j - date_i) > time_window:
                    # group is date-sorted; once out of window, break inner loop
                    break
                desc_i, desc_j = group.loc[i, 'normalized_title'], group.loc[j, 'normalized_title']
                if SequenceMatcher(None, desc_i, desc_j).ratio() >= similarity_threshold:
                    G.add_edge(i, j)

        # --- Step 4: Connected components → candidate clusters; enforce time-window sub-clusters ---
        clusters = list(nx.connected_components(G))
        for cluster in clusters:
            if len(cluster) <= 1:
                continue

            cluster_data = group.loc[list(cluster)].sort_values('tender_award_date_filled')

            # Split components further if their internal span exceeds time_window
            sub_clusters = []
            current_sub_cluster = []
            earliest = None
            for idx in cluster_data.index:
                date = cluster_data.loc[idx, 'tender_award_date_filled']
                if not current_sub_cluster:
                    current_sub_cluster = [idx]
                    earliest = date
                elif date - earliest <= time_window:
                    current_sub_cluster.append(idx)
                else:
                    sub_clusters.append(current_sub_cluster)
                    current_sub_cluster = [idx]
                    earliest = date
            if current_sub_cluster:
                sub_clusters.append(current_sub_cluster)

            # Keep meaningful sub-clusters: ≥ 2 contracts and material value (≥ $1M)
            for sub_cluster in sub_clusters:
                if len(sub_cluster) <= 1:
                    continue
                sub_data = cluster_data.loc[sub_cluster]
                total_value = sub_data['cleaned_bid_price_usd'].sum()
                if total_value < 1_000_000:
                    continue

                contract_clusters.append({
                    'bidder_name': bidder_name,
                    'bidder_country': bidder_country,
                    'number_of_contracts': len(sub_cluster),
                    'total_value_usd': total_value,
                    'tender_ids': sub_data['tender_id'].tolist(),
                    'award_dates': sub_data['tender_award_date_filled'].tolist(),
                    'tender_titles': sub_data['tender_title'].tolist(),
                    'values_usd': sub_data['cleaned_bid_price_usd'].tolist(),
                    'buyers': sub_data['buyer_name'].unique().tolist(),
                    'buyer_count': len(sub_data['buyer_name'].unique()),
                    'earliest_award_date': sub_data['tender_award_date_filled'].min(),
                    'latest_award_date': sub_data['tender_award_date_filled'].max(),
                    'date_range_days': (sub_data['tender_award_date_filled'].max() - sub_data['tender_award_date_filled'].min()).days
                })

    # --- Step 5: Format cluster-level output ---
    df_split_all = pd.DataFrame(contract_clusters)
    if df_split_all.empty:
        # No clusters detected → return empty summary as well
        return df_split_all, pd.DataFrame()

    df_split_all['avg_contract_value'] = df_split_all['total_value_usd'] / df_split_all['number_of_contracts']
    df_split_all['cluster_id'] = df_split_all.index + 1
    df_split_all = df_split_all[[
        'cluster_id', 'bidder_name', 'bidder_country',
        'earliest_award_date', 'latest_award_date', 'date_range_days',
        'number_of_contracts', 'total_value_usd', 'avg_contract_value',
        'buyer_count', 'buyers', 'tender_titles', 'tender_ids'
    ]]

    # --- Step 6: Bidder-level summary and risk scoring ---
    df_split_summary = df_split_all.groupby(['bidder_name', 'bidder_country']).agg(
        contract_split_clusters_count=('cluster_id', 'count'),
        avg_contracts_per_cluster=('number_of_contracts', 'mean'),
        max_contract_cluster_count=('number_of_contracts', 'max'),
        contract_splitting_avg_payment_per_cluster=('total_value_usd', 'mean'),
        contract_splitting_max_cluster_payment=('total_value_usd', 'max'),
        contract_splitting_dollars_at_risk=('total_value_usd', 'sum')
    ).reset_index()

    df_split_summary['contract_clusters_count_rank'] = df_split_summary['contract_split_clusters_count'].rank(pct=True)
    df_split_summary['avg_contracts_per_cluster_rank'] = df_split_summary['avg_contracts_per_cluster'].rank(pct=True)
    df_split_summary['contract_splitting_risk_score'] = 100 * (
        df_split_summary['contract_clusters_count_rank'] * df_split_summary['avg_contracts_per_cluster_rank']
    )

    df_split_summary = df_split_summary[[
        'bidder_name', 'bidder_country', 'contract_split_clusters_count', 'avg_contracts_per_cluster',
        'max_contract_cluster_count', 'contract_splitting_avg_payment_per_cluster',
        'contract_splitting_max_cluster_payment', 'contract_splitting_dollars_at_risk',
        'contract_splitting_risk_score'
    ]].sort_values(by='contract_splitting_risk_score', ascending=False)

    return df_split_all, df_split_summary


# === Save outputs to /output/ancillary ===
def save_outputs(df_split_all, df_split_summary, country_code):
    """Persist contract splitting cluster details and bidder summary to /output/ancillary."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    output_dir = os.path.join(base_dir, "output\\ancillary")
    df_split_all.to_parquet(os.path.join(output_dir, f"{country_code}_contract_split_all.parquet"), index=False)
    df_split_summary.to_parquet(os.path.join(output_dir, f"{country_code}_contract_split_summary.parquet"), index=False)
    print(f"Saved contract splitting outputs for {country_code} to /output/ancillary")


if __name__ == "__main__":
    # === CLI: allow `--country MX` or default to config ===
    import sys
    if len(sys.argv) > 1:
        import argparse
        parser = argparse.ArgumentParser(description="Flag contract splitting")
        parser.add_argument("--country", type=str, required=True, help="2-letter country code (e.g., MX)")
        args = parser.parse_args()
        country_code = args.country.upper()
    else:
        country_code = DEFAULT_COUNTRY
        print(f"No --country argument passed. Defaulting to {DEFAULT_COUNTRY}.")

    # === Run analysis and persist outputs ===
    df_cleaned = load_cleaned_data(country_code)
    df_contract_splitting_all, df_contract_splitting_summary = analyze_contract_splitting(df_cleaned)
    save_outputs(df_contract_splitting_all, df_contract_splitting_summary, country_code)
