# src/08_buyer_summary.py
#
# This script generates buyer-level summary statistics, including total tenders,
# total payouts, distinct awarded bidders, and top-bidder information. Results
# are saved to /output for downstream analysis and reporting.
#
# Rationale:
#   Buyer-level rollups help spot concentrated spend patterns, identify dominant
#   suppliers for each buyer, and prioritize entities for deeper review.
#
# Key operations:
#   - Aggregate tenders, payouts, and unique bidders per buyer
#   - Identify each buyer’s top bidder by total payments (plus tender counts)
#   - Sort buyers by total payouts for quick triage
#
# Output:
#   1. {country_code}_buyer_summary.parquet
#      - One row per buyer with totals, unique bidders, and top-bidder context.
#
# Notes:
#   - Ensure 02_cleaning_and_prep.py has been run prior to this script.
#   - Output is written to /output/ancillary
#   - Field expectations:
#       buyer_name, buyer_country, bidder_name, bidder_country,
#       tender_id, cleaned_bid_price_usd


import os
import pandas as pd
from config import DEFAULT_COUNTRY


# === Step 1: Load cleaned data ===
def load_cleaned_data(country_code):
    """Load the cleaned parquet for the given country code, or raise a helpful error."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    path = os.path.join(base_dir, "output\\ancillary", f"{country_code}_cleaned.parquet")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing cleaned file: {path}")
    return pd.read_parquet(path)


# === Step 2: Create buyer-level summary table ===
def generate_buyer_summary(df):
    """
    Build buyer-level metrics:
      - total_tenders_awarded, total_payouts, total_bidders
      - top bidder per buyer (by total payments), with tender count from that bidder
    Returns a DataFrame sorted by total_payouts descending.
    """
    if df.empty:
        return pd.DataFrame(columns=[
            'buyer_name', 'buyer_country', 'total_tenders_awarded', 'total_payouts', 'total_bidders',
            'top_bidder', 'top_bidder_country', 'total_paid_to_top_bidder', 'total_tenders_to_top_bidder'
        ])

    # Base metrics: total tenders, payouts, and unique bidders
    buyer_summary = df.groupby(['buyer_name', 'buyer_country']).agg(
        total_tenders_awarded=('tender_id', 'count'),
        total_payouts=('cleaned_bid_price_usd', 'sum'),
        total_bidders=('bidder_name', pd.Series.nunique)
    ).reset_index()

    # Identify top bidder for each buyer by payment amount
    bidder_stats = df.groupby(['buyer_name', 'buyer_country', 'bidder_name', 'bidder_country']).agg(
        total_paid_to_bidder=('cleaned_bid_price_usd', 'sum'),
        total_tenders_to_bidder=('tender_id', 'count')
    ).reset_index()

    # For each buyer, pick the bidder with the max total_paid_to_bidder
    idx = bidder_stats.groupby(['buyer_name', 'buyer_country'])['total_paid_to_bidder'].idxmax()
    top_bidders = bidder_stats.loc[idx].rename(columns={
        'bidder_name': 'top_bidder',
        'bidder_country': 'top_bidder_country',
        'total_paid_to_bidder': 'total_paid_to_top_bidder',
        'total_tenders_to_bidder': 'total_tenders_to_top_bidder'
    })

    # Merge top bidder context back into the buyer summary
    buyer_summary = buyer_summary.merge(top_bidders, on=['buyer_name', 'buyer_country'], how='left')

    # Sort for readability
    buyer_summary = buyer_summary.sort_values(by='total_payouts', ascending=False).reset_index(drop=True)

    return buyer_summary


# === Step 3: Save results ===
def save_buyer_summary(df, country_code):
    """Persist buyer summary to /output/ancillary as parquet."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    output_path = os.path.join(base_dir, "output\\ancillary", f"{country_code}_buyer_summary.parquet")
    df.to_parquet(output_path, index=False)
    print(f"✅ Saved buyer summary to {output_path}")


# === Step 4: Run via CLI ===
if __name__ == "__main__":
    # CLI: allow `--country MX` or default to config
    import sys
    if len(sys.argv) > 1:
        import argparse
        parser = argparse.ArgumentParser(description="Generate buyer summary statistics")
        parser.add_argument("--country", type=str, required=True, help="2-letter country code (e.g., MX)")
        args = parser.parse_args()
        country_code = args.country.upper()
    else:
        country_code = DEFAULT_COUNTRY
        print(f"No --country argument passed. Defaulting to {DEFAULT_COUNTRY}.")

    # Run pipeline: load → summarize → save
    df_cleaned = load_cleaned_data(country_code)
    df_buyer_summary = generate_buyer_summary(df_cleaned)
    save_buyer_summary(df_buyer_summary, country_code)
