# src/04_flag_spending_concentration.py
#
# This script identifies bidders who receive disproportionately high percentages of annual 
# open-tender payments or contract counts from individual buyers. High spending concentration 
# may indicate preferential treatment, reduced competition, or other procurement irregularities 
# worth further investigation.
#
# Rationale:
#   A buyer consistently awarding a large share of contracts or payments to a single bidder 
#   can be a red flag for corruption or collusion, especially in open-tender contexts where 
#   competition should be expected. Tracking these patterns over time helps surface entities 
#   that warrant closer review.
#
# Key operations:
#   - Filter dataset to open tenders only
#   - Calculate annual totals of tenders and payments by buyer
#   - Calculate annual totals of tenders and payments from each buyer to each bidder
#   - Compute percentages of a buyer’s awards/payments going to a given bidder
#   - Flag cases where a bidder exceeds defined thresholds for payment or tender concentration
#   - Identify the top buyer for each bidder
#   - Produce bidder-level summary with a spending concentration risk score
#
# Output:
#   1. {country_code}_spending_concentration_all.parquet  
#      - Detailed record of all flagged spending concentration cases by buyer and year.
#
#   2. {country_code}_spending_concentration_summary.parquet  
#      - Aggregated bidder-level summary with total dollars at risk, count of high-concentration 
#        instances, top buyer, and a calculated risk score.
#
# Notes:
#   - Ensure 02_cleaning_and_prep.py has been run prior to executing this script.
#   - Thresholds for flagging (percentage and dollar amounts) are defined in the script logic.
#   - Output integrates into the aggregate risk scoring process in later scripts.


import os
import numpy as np
import pandas as pd
from config import DEFAULT_COUNTRY


# === Load cleaned dataset (produced by 02_cleaning_and_prep.py) ===
def load_cleaned_data(country_code):
    """Load the cleaned parquet for the given country code, or raise a helpful error."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    path = os.path.join(base_dir, "output\\ancillary", f"{country_code}_cleaned.parquet")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing cleaned file: {path}")
    return pd.read_parquet(path)


# === Analyze spending concentration across buyers by year ===
def analyze_spending_concentration(df):
    """
    For open tenders, compute buyer-year totals, bidder shares, and flag high concentration
    cases. Returns:
      - df_spending_concentration_all: row-level buyer→bidder-year cases that meet thresholds
      - df_spending_concentration_summary: bidder-level summary with risk score
    """

    # --- Step 1: Filter to open tenders only (exclude non-competitive) ---
    df_filtered_open_bids = df[df['flag_non_competitive'] == False].copy()

    # --- Step 2: Buyer-year totals (counts + payments) ---
    buyer_year_totals = df_filtered_open_bids.groupby(
        ['buyer_name', 'buyer_country', 'tender_year']
    ).agg(
        total_tenders_awarded_by_buyer_in_year=('tender_title', 'count'),
        total_payments_by_buyer_in_year=('cleaned_bid_price_usd', 'sum')
    ).reset_index()

    # --- Step 3: Buyer→Bidder-year totals (counts + payments) ---
    buyer_to_bidder_year = df_filtered_open_bids.groupby(
        ['buyer_name', 'buyer_country', 'bidder_name', 'bidder_country', 'tender_year']
    ).agg(
        total_paid_to_bidder_in_year=('cleaned_bid_price_usd', 'sum'),
        total_tenders_awarded_to_bidder_in_year=('tender_title', 'count')
    ).reset_index()

    # --- Step 4: Merge and compute share metrics (guard against /0) ---
    merged = pd.merge(
        buyer_year_totals,
        buyer_to_bidder_year,
        on=['buyer_name', 'buyer_country', 'tender_year'],
        how='left'
    ).fillna(0)

    denom_pay = merged['total_payments_by_buyer_in_year'].replace(0, np.nan)
    denom_cnt = merged['total_tenders_awarded_by_buyer_in_year'].replace(0, np.nan)

    merged['pct_payments_to_bidder_in_year'] = (
        merged['total_paid_to_bidder_in_year'] / denom_pay
    ).replace([np.inf, -np.inf], np.nan).fillna(0)

    merged['pct_tenders_to_bidder_in_year'] = (
        merged['total_tenders_awarded_to_bidder_in_year'] / denom_cnt
    ).replace([np.inf, -np.inf], np.nan).fillna(0)

    # --- Step 5: Keep buyers with >1 award in a given year (avoid single-award artifacts) ---
    merged = merged[merged['total_tenders_awarded_by_buyer_in_year'] > 1].copy()

    # --- Step 6: All-time buyer totals (for prioritization/sorting context) ---
    total_payments_by_buyer = df_filtered_open_bids.groupby(
        ['buyer_name', 'buyer_country']
    ).agg(
        total_payments_by_buyer_all_time=('cleaned_bid_price_usd', 'sum')
    ).reset_index()

    merged = pd.merge(
        merged,
        total_payments_by_buyer,
        on=['buyer_name', 'buyer_country'],
        how='left'
    )

    # --- Step 7: Top buyer per bidder (by total paid across years) ---
    high_pct_raw = merged.copy()
    bidder_top_buyer_totals = high_pct_raw.groupby(
        ['bidder_name', 'bidder_country', 'buyer_name']
    ).agg(
        total_paid_by_buyer=('total_paid_to_bidder_in_year', 'sum')
    ).reset_index()

    idx = bidder_top_buyer_totals.groupby(
        ['bidder_name', 'bidder_country']
    )['total_paid_by_buyer'].idxmax()

    top_buyers = bidder_top_buyer_totals.loc[idx].reset_index(drop=True).rename(
        columns={'buyer_name': 'top_buyer', 'total_paid_by_buyer': 'total_paid_by_top_buyer'}
    )

    # --- Step 8: Threshold filter: high concentration + material dollars ---
    df_spending_concentration_all = merged[
        (
            (merged['pct_payments_to_bidder_in_year'] > 0.10) |
            (merged['pct_tenders_to_bidder_in_year'] > 0.10)
        ) &
        (merged['total_paid_to_bidder_in_year'] > 1_000_000)
    ].copy()

    # Keep tidy, analysis-ready columns
    df_spending_concentration_all = df_spending_concentration_all[[
        'buyer_name', 'buyer_country', 'total_payments_by_buyer_all_time',
        'tender_year', 'bidder_name', 'bidder_country',
        'total_tenders_awarded_by_buyer_in_year', 'total_tenders_awarded_to_bidder_in_year',
        'pct_tenders_to_bidder_in_year',
        'total_payments_by_buyer_in_year', 'total_paid_to_bidder_in_year',
        'pct_payments_to_bidder_in_year'
    ]].sort_values(
        by=['total_payments_by_buyer_all_time', 'tender_year', 'pct_payments_to_bidder_in_year'],
        ascending=[False, False, False]
    ).reset_index(drop=True)

    # --- Step 9: Bidder-level summary + risk scoring ---
    df_spending_concentration_summary = df_spending_concentration_all.groupby(
        ['bidder_name', 'bidder_country']
    ).agg(
        spending_concentration_dollars_at_risk=('total_paid_to_bidder_in_year', 'sum'),
        spending_concentration_count=('bidder_name', 'count'),
        total_pct_tenders=('pct_tenders_to_bidder_in_year', 'sum'),
        total_pct_payments=('pct_payments_to_bidder_in_year', 'sum')
    ).reset_index()

    df_spending_concentration_summary['total_pct_tenders_pct_rank'] = (
        df_spending_concentration_summary['total_pct_tenders'].rank(pct=True)
    )
    df_spending_concentration_summary['total_pct_payments_pct_rank'] = (
        df_spending_concentration_summary['total_pct_payments'].rank(pct=True)
    )

    df_spending_concentration_summary['spending_concentration_risk_score'] = (
        df_spending_concentration_summary['total_pct_tenders_pct_rank'] *
        df_spending_concentration_summary['total_pct_payments_pct_rank'] * 100
    )

    # --- Step 10: Attach top buyer context ---
    df_spending_concentration_summary = df_spending_concentration_summary.merge(
        top_buyers, on=['bidder_name', 'bidder_country'], how='left'
    )[[
        'bidder_name', 'bidder_country',
        'spending_concentration_count', 'spending_concentration_dollars_at_risk',
        'spending_concentration_risk_score', 'top_buyer', 'total_paid_by_top_buyer'
    ]]

    # --- Step 11: Sort for readability (highest risk first) ---
    df_spending_concentration_summary = df_spending_concentration_summary.sort_values(
        by='spending_concentration_risk_score', ascending=False
    )

    return df_spending_concentration_all, df_spending_concentration_summary


# === Save outputs to /output/ancillary ===
def save_spending_concentration(df_all, df_summary, country_code):
    """Persist detailed and summary spending concentration outputs to /output/ancillary."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    output_dir = os.path.join(base_dir, "output\\ancillary")
    df_all.to_parquet(
        os.path.join(output_dir, f"{country_code}_spending_concentration_all.parquet"), index=False
    )
    df_summary.to_parquet(
        os.path.join(output_dir, f"{country_code}_spending_concentration_summary.parquet"), index=False
    )
    print("Saved both detailed and summary spending concentration outputs to /output/ancillary")


if __name__ == "__main__":
    # === CLI: allow `--country MX` or default to config ===
    import sys
    if len(sys.argv) > 1:
        import argparse
        parser = argparse.ArgumentParser(description="Analyze spending concentration by buyer")
        parser.add_argument("--country", type=str, required=True, help="2-letter country code (e.g., MX)")
        args = parser.parse_args()
        country_code = args.country.upper()
    else:
        country_code = DEFAULT_COUNTRY
        print(f"No --country argument passed. Defaulting to {DEFAULT_COUNTRY}.")

    # === Run analysis and persist outputs ===
    df_cleaned = load_cleaned_data(country_code)
    df_spending_concentration_all, df_spending_concentration_summary = analyze_spending_concentration(df_cleaned)
    save_spending_concentration(df_spending_concentration_all, df_spending_concentration_summary, country_code)