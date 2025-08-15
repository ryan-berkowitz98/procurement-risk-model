# src/05_flag_short_bidding_window.py
#
# This script flags tenders with unusually short bidding windows and identifies bidders 
# who frequently win such tenders. Short bidding windows can reduce competition and 
# may indicate procurement processes tailored for a specific supplier.
#
# Rationale:
#   A bidding window that is too short may prevent qualified competitors from preparing 
#   a compliant bid, which can advantage pre-selected bidders. Detecting patterns of 
#   short windows helps highlight buyers and bidders that merit closer review.
#
# Key operations:
#   - Filter dataset to open tenders only
#   - Calculate the number of days between tender publication and bid deadline
#   - Impute missing bid deadlines using available award or contract signature dates
#   - Identify the short bidding window threshold dynamically (10th percentile)
#   - Flag all tenders with bidding windows below the threshold
#   - Summarize flagged tenders at the bidder level and compute a short bid window risk score
#   - Identify the top buyer for each flagged bidder
#   - Generate a histogram visualizing bidding window duration distribution
#
# Output:
#   1. {country_code}_short_bid_window_all.parquet  
#      - Detailed record of all tenders flagged for short bidding windows.
#
#   2. {country_code}_short_bid_window_summary.parquet  
#      - Bidder-level summary including count, average, minimum bidding window days, 
#        total dollars at risk, top buyer, and calculated risk score.
#
#   3. {country_code}_short_bid_window_histogram.png  
#      - Visualization showing the distribution of bidding window durations with 
#        threshold, mean, and median marked.
#
# Notes:
#   - Ensure 02_cleaning_and_prep.py has been run prior to executing this script.
#   - The short bidding window threshold is calculated dynamically from the dataset 
#     (10th percentile of bidding window days).
#   - Output files are stored in the /output/ancillary directory for integration with the 
#     aggregate risk scoring process.


import pandas as pd
import os
import matplotlib.pyplot as plt
from config import DEFAULT_COUNTRY


def load_cleaned_data(country_code):
    """
    Load the cleaned, normalized dataset produced by 02_cleaning_and_prep.py.
    Raises a clear error if the expected parquet does not exist.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    path = os.path.join(base_dir, "output\\ancillary", f"{country_code}_cleaned.parquet")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing cleaned file: {path}")
    return pd.read_parquet(path)


def analyze_short_bid_windows(df):
    """
    Compute bidding window lengths for open tenders, derive a dynamic short-window
    threshold (10th percentile), and produce:
      - A detailed list of short-window tenders
      - A bidder-level summary with a risk score
    Returns: (df_short_bid_windows_all, df_short_bid_windows_summary, df_open_tenders_all, short_window_threshold)
    """

    # === Filter to open tenders only (exclude non-competitive) ===
    df_open_tenders_all = df[df['flag_non_competitive'] == False].copy()

    # === Ensure critical date fields are in datetime ===
    date_columns = [
        'tender_publications_firstcallfortenderdate',
        'tender_biddeadline',
        'tender_awarddecisiondate',
        'tender_publications_firstdcontractawarddate',
        'tender_contractsignaturedate'
    ]
    for col in date_columns:
        # Coerce invalid strings to NaT rather than error
        df_open_tenders_all[col] = pd.to_datetime(df_open_tenders_all[col], errors='coerce')

    # === Impute missing bid deadlines with the earliest downstream milestone available ===
    # Start with original deadline; fill gaps with award/contract dates if needed
    df_open_tenders_all['tender_biddeadline_filled'] = df_open_tenders_all['tender_biddeadline']
    for col in ['tender_awarddecisiondate', 'tender_publications_firstdcontractawarddate', 'tender_contractsignaturedate']:
        df_open_tenders_all['tender_biddeadline_filled'] = df_open_tenders_all['tender_biddeadline_filled'].fillna(
            df_open_tenders_all[col]
        )

    # === Compute bidding window in days: publication → (imputed) bid deadline ===
    df_open_tenders_all['bidding_window_days'] = (
        df_open_tenders_all['tender_biddeadline_filled'] - df_open_tenders_all['tender_publications_firstcallfortenderdate']
    ).dt.days

    # === Keep sensible windows and material tenders (>$1M) ===
    #  - Positive windows only
    #  - Cap at 365 to remove outliers/data errors
    #  - Focus on higher-value tenders (possible config knob later)
    df_open_tenders_all = df_open_tenders_all[
        (df_open_tenders_all['bidding_window_days'] > 0)
        & (df_open_tenders_all['bidding_window_days'] <= 365)
        & (df_open_tenders_all['cleaned_bid_price_usd'] >= 1_000_000)
    ].copy()

    # === Dynamic short-window threshold (10th percentile of observed windows) ===
    short_window_threshold = df_open_tenders_all['bidding_window_days'].quantile(0.10)

    # === Flag short-window tenders ===
    df_open_tenders_all['short_bidding_window_flag'] = (
        df_open_tenders_all['bidding_window_days'] < short_window_threshold
    )

    # === Detailed output: all short-window tenders for review ===
    df_short_bid_windows_all = df_open_tenders_all[df_open_tenders_all['short_bidding_window_flag']].copy()

    df_short_bid_windows_all = df_short_bid_windows_all[[
        'tender_id', 'bidder_name', 'bidder_country', 'buyer_name', 'tender_title', 'lot_title', 'lot_status',
        'tender_supplytype', 'cleaned_bid_price_usd', 'tender_publications_firstcallfortenderdate',
        'tender_biddeadline', 'tender_awarddecisiondate', 'tender_contractsignaturedate', 'bidding_window_days'
    ]]

    # === Helper: identify top buyer (by total payment) for each flagged bidder ===
    buyer_payments = df_short_bid_windows_all.groupby(
        ['bidder_name', 'bidder_country', 'buyer_name'], dropna=False
    ).agg(total_payment_usd=('cleaned_bid_price_usd', 'sum')).reset_index()

    top_buyers = buyer_payments.sort_values(
        ['bidder_name', 'bidder_country', 'total_payment_usd'],
        ascending=[True, True, False]
    ).groupby(['bidder_name', 'bidder_country']).first().reset_index()

    top_buyers.rename(columns={
        'buyer_name': 'short_bid_window_top_buyer',
        'total_payment_usd': 'short_bid_window_top_buyer_payments'
    }, inplace=True)

    # === Bidder-level summary + risk scoring ===
    df_short_bid_windows_summary = df_short_bid_windows_all.groupby(
        ['bidder_name', 'bidder_country'], dropna=False
    ).agg(
        short_bid_window_count=('tender_id', 'count'),
        avg_short_bid_window_days=('bidding_window_days', 'mean'),
        min_short_bid_window=('bidding_window_days', 'min'),
        short_bid_window_avg_payment=('cleaned_bid_price_usd', 'mean'),
        short_bid_window_dollars_at_risk=('cleaned_bid_price_usd', 'sum')
    ).reset_index()

    # Attach top-buyer context
    df_short_bid_windows_summary = df_short_bid_windows_summary.merge(
        top_buyers,
        on=['bidder_name', 'bidder_country'],
        how='left'
    )

    # Percentile-based scoring: more flagged tenders + shorter average window → higher risk
    df_short_bid_windows_summary['short_bid_window_count_rank'] = df_short_bid_windows_summary['short_bid_window_count'].rank(pct=True)
    df_short_bid_windows_summary['avg_short_bid_window_days_rank'] = 1 - df_short_bid_windows_summary['avg_short_bid_window_days'].rank(pct=True)
    df_short_bid_windows_summary['short_bid_window_risk_score'] = (
        100 * df_short_bid_windows_summary['short_bid_window_count_rank'] *
        df_short_bid_windows_summary['avg_short_bid_window_days_rank']
    )

    # Final column order + sort for readability
    df_short_bid_windows_summary = df_short_bid_windows_summary[[
        'bidder_name', 'bidder_country', 'short_bid_window_count', 'avg_short_bid_window_days',
        'min_short_bid_window', 'short_bid_window_avg_payment', 'short_bid_window_dollars_at_risk',
        'short_bid_window_top_buyer', 'short_bid_window_top_buyer_payments', 'short_bid_window_risk_score'
    ]].sort_values(by='short_bid_window_risk_score', ascending=False)

    return df_short_bid_windows_all, df_short_bid_windows_summary, df_open_tenders_all, short_window_threshold


def save_outputs(df_short_bid_windows_all, df_short_bid_windows_summary, df_open_tenders_all, threshold, country_code):
    """
    Persist parquet outputs and a histogram plot that visualizes the distribution
    of bidding windows with the threshold, mean, and median annotated.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    output_dir = os.path.join(base_dir, "output\\ancillary")

    # === Save parquet outputs ===
    df_short_bid_windows_all.to_parquet(os.path.join(output_dir, f"{country_code}_short_bid_window_all.parquet"), index=False)
    df_short_bid_windows_summary.to_parquet(os.path.join(output_dir, f"{country_code}_short_bid_window_summary.parquet"), index=False)

    # === Plot distribution with annotations (threshold / mean / median) ===
    plt.figure(figsize=(10, 6))
    plt.hist(df_open_tenders_all['bidding_window_days'], bins=50, edgecolor='black', alpha=0.7)
    plt.title('Distribution of Bidding Window Durations')
    plt.xlabel('Bidding Window (days)')
    plt.ylabel('Number of Tenders')

    mean_days = df_open_tenders_all['bidding_window_days'].mean()
    median_days = df_open_tenders_all['bidding_window_days'].median()

   
    plt.axvline(
                    x=threshold, linestyle='--', linewidth=2,
                    label=f"Short Window Threshold ({threshold:.1f} days)",
                    color='red'
                )
    plt.axvline(
                    x=mean_days, linestyle='-.', linewidth=2,
                    label=f"Mean ({mean_days:.1f} days)",
                    color='blue'
                )
    plt.axvline(
                    x=median_days, linestyle=':', linewidth=2,
                    label=f"Median ({median_days:.1f} days)",
                    color='green'
                )

    plt.legend(loc='best')
    plt.grid(axis='y', alpha=0.75)
    plot_path = os.path.join(output_dir, f"{country_code}_short_bid_window_histogram.png")
    plt.savefig(plot_path, bbox_inches='tight')
    plt.close()

    print(f"Saved short bidding window outputs for {country_code} to /output/ancillary")


if __name__ == "__main__":
    # === CLI: allow `--country MX` or default to config ===
    import sys
    if len(sys.argv) > 1:
        import argparse
        parser = argparse.ArgumentParser(description="Flag short bid windows")
        parser.add_argument("--country", type=str, required=True, help="2-letter country code (e.g., MX)")
        args = parser.parse_args()
        country_code = args.country.upper()
    else:
        country_code = DEFAULT_COUNTRY
        print(f"No --country argument passed. Defaulting to {DEFAULT_COUNTRY}.")

    # === Run analysis and persist outputs ===
    df_cleaned = load_cleaned_data(country_code)
    df_short_bid_windows_all, df_short_bid_windows_summary, df_open_tenders_all, threshold = analyze_short_bid_windows(df_cleaned)
    save_outputs(df_short_bid_windows_all, df_short_bid_windows_summary, df_open_tenders_all, threshold, country_code)