# src/03_flag_non_competitive_tenders.py
#
# This script implements the logic to flag non-competitive tenders and identify
# bidders with a recurring pattern of winning such tenders, as opposed to open
# and competitive ones. 
#
# Rationale:
#   Non-competitive tenders are more prone to corruption and fraud, as they bypass 
#   open market competition. Detecting entities with repeated success in these tenders 
#   can help highlight potentially high-risk bidders for further investigation.
#
# Key operations:
#   - Aggregate wins by bidder and calculate percentage of non-competitive wins
#   - Flag bidders that exceed a defined threshold of non-competitive wins
#   - Prepare summary outputs for integration into the aggregate risk scoring process
#
# Output:
#   1. non_competitive_tenders_summary.parquet  
#      - Bidder-level summary with non-competitive win statistics and flags.
#
#   2. {country_code}_non_competitive_tenders_all.parquet  
#      - Full list of all identified non-competitive tenders, for optional closer review.
#
# Notes:
#   - Ensure 02_cleaning_and_prep.py has been run prior to executing this script.
#   - Thresholds for flagging can be adjusted in config.py.
#   - Output integrates with aggregate risk scoring in later scripts.



import os
import numpy as np
import pandas as pd
from config import DEFAULT_COUNTRY, NON_COMP_DOLLAR_THRESHOLD, NON_COMP_MAX_TENDER_THRESHOLD


# === Load cleaned dataset (produced by 02_cleaning_and_prep.py) ===
def load_cleaned_data(country_code):
    """Load the cleaned parquet for the given country code, or raise a helpful error."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    path = os.path.join(base_dir, "output\\ancillary", f"{country_code}_cleaned.parquet")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing cleaned file: {path}")
    return pd.read_parquet(path)


# === Analyze non-competitive tenders: bidder totals, top buyers, risk scoring ===
def analyze_non_comp_tenders(df):
    """
    Build bidder-level non-competitive tender metrics and risk scores.
    Returns:
      - df_flag_non_comp: bidder summary with flags/scores
      - df_filtered_non_comp: row-level non-competitive tenders for review
    """
    # --- Focus view for row-level output (non-competitive only) ---
    df_filtered_non_comp = df[df['flag_non_competitive'] == True].copy()

    # --- Step 1: Totals by bidder (all tenders: competitive + non-competitive) ---
    totals = df.groupby(['bidder_name', 'bidder_country']).agg(
        total_tenders_won=('tender_title', 'count'),
        total_payments=('cleaned_bid_price_usd', 'sum')
    ).reset_index()

    # --- Step 2: Non-competitive summary by bidder ---
    non_comp = df_filtered_non_comp.groupby(['bidder_name', 'bidder_country']).agg(
        non_competitive_dollars_at_risk=('cleaned_bid_price_usd', 'sum'),
        non_competitive_tenders_won=('tender_title', 'count'),
        avg_price_non_competitive_tenders=('cleaned_bid_price_usd', 'mean'),
        most_expensive_non_competitive_tender=('cleaned_bid_price_usd', 'max')
    ).reset_index()

    # --- Step 3: Identify top buyer (by non-competitive spend) for each bidder ---
    top_buyers_non_comp_df = (
        df_filtered_non_comp
        .groupby(['bidder_name', 'bidder_country', 'buyer_name'])['cleaned_bid_price_usd']
        .sum()
        .reset_index()
    )
    top_buyers_non_comp = (
        top_buyers_non_comp_df
        .sort_values(['bidder_name', 'bidder_country', 'cleaned_bid_price_usd'],
                     ascending=[True, True, False])
        .groupby(['bidder_name', 'bidder_country'])
        .first()
        .reset_index()
        .rename(columns={
            'buyer_name': 'top_buyer_non_comp_tenders',
            'cleaned_bid_price_usd': 'total_paid_by_top_buyer_non_comp_tenders'
        })
    )

    # --- Step 4: Merge components together ---
    merged = (
        totals
        .merge(non_comp, on=['bidder_name', 'bidder_country'], how='left')
        .merge(top_buyers_non_comp, on=['bidder_name', 'bidder_country'], how='left')
    )

    # Fill numeric nulls with 0 (no non-competitive tenders) and string with ""
    numeric_fill_cols = [
        'non_competitive_dollars_at_risk', 'non_competitive_tenders_won',
        'avg_price_non_competitive_tenders', 'most_expensive_non_competitive_tender',
        'total_paid_by_top_buyer_non_comp_tenders'
    ]
    merged[numeric_fill_cols] = merged[numeric_fill_cols].fillna(0)
    merged['top_buyer_non_comp_tenders'] = merged['top_buyer_non_comp_tenders'].fillna("")

    # --- Step 5: Percentage metrics (guard against divide-by-zero) ---
    merged['pct_payments_non_comp_tenders'] = (
        merged['non_competitive_dollars_at_risk'] / merged['total_payments'].replace(0, np.nan)
    )
    merged['pct_tenders_non_competitive'] = (
        merged['non_competitive_tenders_won'] / merged['total_tenders_won'].replace(0, np.nan)
    )
    merged[['pct_payments_non_comp_tenders', 'pct_tenders_non_competitive']] = (
        merged[['pct_payments_non_comp_tenders', 'pct_tenders_non_competitive']]
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0)
    )

    # --- Step 6: Apply thresholds from config for initial flagging ---
    df_flag_non_comp = merged[
        (merged['non_competitive_tenders_won'] >= 1) &
        (merged['non_competitive_dollars_at_risk'] >= NON_COMP_DOLLAR_THRESHOLD) &
        (merged['most_expensive_non_competitive_tender'] >= NON_COMP_MAX_TENDER_THRESHOLD)
    ].copy()

    # --- Step 7: Risk score (percentile of count * pct of tenders) ---
    df_flag_non_comp['non_competitive_tenders_pct_rank'] = df_flag_non_comp['non_competitive_tenders_won'].rank(pct=True)
    df_flag_non_comp['non_competitive_tenders_risk_score'] = (
        df_flag_non_comp['non_competitive_tenders_pct_rank'] *
        df_flag_non_comp['pct_tenders_non_competitive'] * 100
    )

    # --- Step 8: Finalize columns/order ---
    df_flag_non_comp = df_flag_non_comp[[
        'bidder_name', 'bidder_country',
        'non_competitive_tenders_won', 'total_tenders_won',
        'pct_tenders_non_competitive',
        'non_competitive_dollars_at_risk', 'total_payments',
        'pct_payments_non_comp_tenders',
        'avg_price_non_competitive_tenders',
        'most_expensive_non_competitive_tender',
        'top_buyer_non_comp_tenders', 'total_paid_by_top_buyer_non_comp_tenders',
        'non_competitive_tenders_risk_score'
    ]].reset_index(drop=True)

    # --- Step 9: Sort for readability (highest risk first) ---
    df_flag_non_comp = df_flag_non_comp.sort_values(
        by='non_competitive_tenders_risk_score', ascending=False
    )

    print(
        f"ℹ️  Flagging bidders with non-competitive tender totals ≥ ${NON_COMP_DOLLAR_THRESHOLD:,} "
        f"and at least one tender ≥ ${NON_COMP_MAX_TENDER_THRESHOLD:,}. "
        "Update config.py to adjust thresholds."
    )

    return df_flag_non_comp, df_filtered_non_comp


# === Save both summary and row-level outputs ===
def save_outputs(df_flag_non_comp, df_all_tenders_non_comp, country_code):
    """Persist bidder summary and the full list of non-competitive tenders to /output/ancillary."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    out_dir = os.path.join(base_dir, "output\\ancillary")
    df_flag_non_comp.to_parquet(os.path.join(out_dir, f"{country_code}_non_competitive_tenders_summary.parquet"), index=False)
    df_all_tenders_non_comp.to_parquet(os.path.join(out_dir, f"{country_code}_non_competitive_tenders_all.parquet"), index=False)
    print(f"✅ Saved non-competitive tenders output to /output/ancillary for {country_code}")


if __name__ == "__main__":
    # === CLI: allow `--country MX` or default to config ===
    import sys
    if len(sys.argv) > 1:
        import argparse
        parser = argparse.ArgumentParser(description="Flag non-competitive tenders")
        parser.add_argument("--country", type=str, required=True, help="2-letter country code")
        args = parser.parse_args()
        country_code = args.country.upper()
    else:
        country_code = DEFAULT_COUNTRY
        print(f"No --country argument passed. Defaulting to {DEFAULT_COUNTRY}.")

    # === Run analysis and save ===
    df_cleaned = load_cleaned_data(country_code)
    df_non_competitive_tenders_summary, df_non_competitive_tenders_all = analyze_non_comp_tenders(df_cleaned)
    save_outputs(df_non_competitive_tenders_summary, df_non_competitive_tenders_all, country_code)