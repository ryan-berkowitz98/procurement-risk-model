# src/07_aggregate_risk_score.py
#
# This script aggregates bidder-level risk across all flags and produces a single
# composite risk score plus supporting context. It merges summaries from:
#   - Non-competitive tenders
#   - Spending concentration
#   - Short bidding windows
#   - Contract splitting
#
# Rationale:
#   A unified, comparable score helps triage and prioritize bidders for review.
#   Rolling up per-flag metrics preserves interpretability while enabling ranking.
#
# Key operations:
#   - Build base bidder summary (tenders, payments, buyer diversity)
#   - Compute top-buyer context per bidder
#   - Merge risk summaries from prior steps (03–06)
#   - Normalize/scale risk scores (when needed) and compute an average total score
#   - Output a tidy bidder-level table for export and dashboards
#
# Output:
#   1. {country_code}_aggregate_bidder_risk_scores.parquet
#      - One row per bidder with composite score, dollars at risk, per-flag scores,
#        and contextual fields (top buyer, payments, etc.).
#
# Notes:
#   - Ensure 02–06 have been run for the target country before executing this script.
#   - Missing flags are treated as 0; the composite score is the average of four components (03–06).
#   - Scores are averaged across the four fixed components; missing flags result in lower avg risk scores.


import os
import numpy as np
import pandas as pd
from config import DEFAULT_COUNTRY


# === Lightweight loader: return empty DataFrame if file absent ===
def load_summary(path):
    """Read parquet if it exists; otherwise return empty DataFrame."""
    return pd.read_parquet(path) if os.path.exists(path) else pd.DataFrame()


# === Load cleaned dataset (produced by 02_cleaning_and_prep.py) ===
def load_cleaned_data(country_code):
    """Load the cleaned parquet for the given country code, or raise a helpful error."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    path = os.path.join(base_dir, "output\\ancillary", f"{country_code}_cleaned.parquet")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing cleaned file: {path}")
    return pd.read_parquet(path)


# === Aggregate bidder-level risk across all flags ===
def aggregate_bidder_risk(country_code):
    """
    Build a bidder-level table combining base stats with per-flag scores and dollars-at-risk,
    then compute a composite (average) risk score.

    Returns:
      DataFrame with one row per bidder and the following groups:
        - Core context: totals, top buyer, buyers count
        - Per-flag: *_risk_score, *_dollars_at_risk
        - Rollups: total_risk_score, total_dollars_at_risk, num_flags
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    output_dir = os.path.join(base_dir, "output\\ancillary")

    # --- Load cleaned data to build the base bidder summary ---
    df_cleaned = load_cleaned_data(country_code)

    # Base: bidder totals + buyer diversity
    df_base = df_cleaned.groupby(['bidder_name', 'bidder_country']).agg(
        total_tenders_won=('tender_id', 'count'),
        total_payments=('cleaned_bid_price_usd', 'sum'),
        total_buyers=('buyer_name', pd.Series.nunique)
    ).reset_index()

    # Top-buyer context per bidder
    buyer_stats = df_cleaned.groupby(['bidder_name', 'bidder_country', 'buyer_name']).agg(
        total_paid_by_buyer=('cleaned_bid_price_usd', 'sum'),
        total_tenders_from_buyer=('tender_id', 'count')
    ).reset_index()

    idx = buyer_stats.groupby(['bidder_name', 'bidder_country'])['total_paid_by_buyer'].idxmax()
    top_buyers = buyer_stats.loc[idx].rename(columns={
        'buyer_name': 'top_buyer',
        'total_paid_by_buyer': 'total_paid_by_top_buyer',
        'total_tenders_from_buyer': 'total_tenders_from_top_buyer'
    })
    df_base = df_base.merge(top_buyers, on=['bidder_name', 'bidder_country'], how='left')

    # --- Load each risk summary (03–06). Missing files yield empty merges (handled below) ---
    df_non_comp = load_summary(os.path.join(output_dir, f"{country_code}_non_competitive_tenders_summary.parquet"))
    df_spending = load_summary(os.path.join(output_dir, f"{country_code}_spending_concentration_summary.parquet"))
    df_short = load_summary(os.path.join(output_dir, f"{country_code}_short_bid_window_summary.parquet"))
    df_split = load_summary(os.path.join(output_dir, f"{country_code}_contract_split_summary.parquet"))

    # Merge whatever is available
    risk_tables = [df_non_comp, df_spending, df_short, df_split]
    for risk_df in risk_tables:
        if not risk_df.empty:
            df_base = df_base.merge(risk_df, on=['bidder_name', 'bidder_country'], how='left')

    # --- Ensure expected risk/dollars-at-risk columns exist even if a table was missing ---
    expected_cols = [
        'non_competitive_tenders_risk_score', 'non_competitive_dollars_at_risk',
        'spending_concentration_risk_score', 'spending_concentration_dollars_at_risk',
        'short_bid_window_risk_score', 'short_bid_window_dollars_at_risk',
        'contract_splitting_risk_score', 'contract_splitting_dollars_at_risk'
    ]
    for col in expected_cols:
        if col not in df_base.columns:
            df_base[col] = 0.0

    # Null-safe fill
    risk_score_cols = [c for c in df_base.columns if c.endswith('_risk_score')]
    dollars_at_risk_cols = [c for c in df_base.columns if c.endswith('_dollars_at_risk')]
    df_base[risk_score_cols] = df_base[risk_score_cols].fillna(0)
    df_base[dollars_at_risk_cols] = df_base[dollars_at_risk_cols].fillna(0)

    # --- Scale risk scores if they appear to be proportions (0–1). Avoid double-scaling. ---
    for c in risk_score_cols:
        col_max = df_base[c].max()
        if pd.notnull(col_max) and col_max <= 1.0:
            df_base[c] = (df_base[c] * 100).round(1)

    # --- Rollups: composite risk score (average), dollars at risk (sum), active flags (count > 0) ---
    num_components = max(1, len(risk_score_cols))  # avoid divide-by-zero
    df_base['total_risk_score'] = (df_base[risk_score_cols].sum(axis=1) / num_components).round(1)
    df_base['total_dollars_at_risk'] = df_base[dollars_at_risk_cols].sum(axis=1)
    df_base['num_flags'] = (df_base[risk_score_cols] > 0).sum(axis=1)

    # --- Sort and rank bidders by composite score ---
    df_base = df_base.sort_values(by='total_risk_score', ascending=False).reset_index(drop=True)
    df_base['rank'] = df_base['total_risk_score'].rank(method='min', ascending=False).astype(int)
    
    # Standardize base column names (from summary table)
    df_base.rename(columns={
        'total_tenders_won_x': 'total_tenders_won',
        'total_payments_x': 'total_payments',
        'top_buyer_x': 'top_buyer',
        'total_paid_by_top_buyer_x': 'total_paid_by_top_buyer'
    }, inplace=True)

    # --- Final selection and light formatting ---
    selected_cols = [
        'rank', 'bidder_name', 'bidder_country', 'total_risk_score', 'total_dollars_at_risk', 'num_flags',
        'total_tenders_won', 'total_payments', 'total_buyers',
        'top_buyer', 'total_paid_by_top_buyer', 'total_tenders_from_top_buyer',
        'non_competitive_tenders_risk_score', 'non_competitive_dollars_at_risk',
        'spending_concentration_risk_score', 'spending_concentration_dollars_at_risk',
        'short_bid_window_risk_score', 'short_bid_window_dollars_at_risk',
        'contract_splitting_risk_score', 'contract_splitting_dollars_at_risk'
    ]
    df_out = df_base[selected_cols].copy()

    # Round all *_risk_score columns to 1 decimal for readability
    risk_score_cols_out = [c for c in df_out.columns if c.endswith('_risk_score')]
    df_out[risk_score_cols_out] = df_out[risk_score_cols_out].round(1)

    return df_out


# === Save output parquet ===
def save_aggregate_risk_score(df, country_code):
    """Persist aggregate bidder risk scores to /output/ancillary."""
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output\\ancillary"))
    out_path = os.path.join(output_dir, f"{country_code}_aggregate_bidder_risk_scores.parquet")
    df.to_parquet(out_path, index=False)
    print(f"✅ Saved aggregate bidder risk scores to {out_path}")


if __name__ == "__main__":
    # === CLI: allow `--country MX` or default to config ===
    import sys
    if len(sys.argv) > 1:
        import argparse
        parser = argparse.ArgumentParser(description="Aggregate bidder-level risk scores")
        parser.add_argument("--country", type=str, required=True, help="2-letter country code (e.g., MX)")
        args = parser.parse_args()
        country_code = args.country.upper()
    else:
        country_code = DEFAULT_COUNTRY
        print(f"No --country argument passed. Defaulting to {DEFAULT_COUNTRY}.")

    # === Run aggregation and save ===
    df_agg_risk_scores = aggregate_bidder_risk(country_code)
    if not df_agg_risk_scores.empty:
        save_aggregate_risk_score(df_agg_risk_scores, country_code)
