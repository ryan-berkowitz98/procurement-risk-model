# src/99_export_risk_report.py
#
# This script compiles all modeling outputs into a single Excel workbook for review.
# It loads the bidder aggregate scores and each flag’s summary, then writes one
# sheet per artifact with light formatting.
#
# Rationale:
#   Centralizing results in a single, scannable workbook speeds triage and sharing
#   with investigators and stakeholders.
#
# Key operations:
#   - Load parquet outputs from prior steps (03–08) for a given country_code
#   - Create an Excel workbook with one sheet per artifact
#   - Apply basic, readable formatting (currency/score/percent/integers)
#
# Output:
#   1. {country_code}_procurement_risk_report.xlsx
#      - Multi-sheet Excel with the tabs listed below (missing inputs are skipped).
#
# Notes:
#   - Ensure scripts 02–08 have been run for the same country_code before exporting.
#   - Composite bidder score rule (from 07): missing flags are treated as 0; the
#     total_risk_score is the average of four fixed components (03–06).
#   - Excel sheet names are limited to 31 chars; names are truncated accordingly.
#   - Large workbooks shouldn’t be committed to git; keep /output in .gitignore.


import os
import pandas as pd
from config import DEFAULT_COUNTRY


# === Lightweight parquet loader (returns empty DataFrame if file is missing) ===
def load_parquet_if_exists(filename):
    """Read /output/<filename> if present; otherwise return an empty DataFrame."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    path = os.path.join(base_dir, "output\\ancillary", filename)
    return pd.read_parquet(path) if os.path.exists(path) else pd.DataFrame()


# === Build and export the Excel report ===
def export_risk_report(country_code):
    """
    Assemble available parquet outputs into a formatted Excel workbook with one tab per artifact.
    Skips tabs with no data found for the given country_code.
    """
    # --- File → Sheet mapping (values are appended with {country_code}_ prefix when loading) ---
    file_sheet_map = {
        "aggregate_risk_scores": ("aggregate_bidder_risk_scores.parquet", "Bidder Risk Summary"),
        "buyer_summary": ("buyer_summary.parquet", "Buyer Summary"),
        "non_competitive_summary": ("non_competitive_tenders_summary.parquet", "Non-Comp Flag"),
        "spending_concentration_summary": ("spending_concentration_summary.parquet", "Spending Concentration Flag"),
        "short_bid_window_summary": ("short_bid_window_summary.parquet", "Short Bid Windows Flag"),
        "contract_split_summary": ("contract_split_summary.parquet", "Contract Splitting Flag"),
    }

    # --- Load dataframes that exist ---
    data = {}
    for key, (filename, sheet_name) in file_sheet_map.items():
        df = load_parquet_if_exists(f"{country_code}_{filename}")
        if not df.empty:
            data[sheet_name] = df

    if not data:
        print("⚠️  No data found to export.")
        return

    # --- Preferred tab order (only include those that exist) ---
    preferred_order = [
        "Bidder Risk Summary",
        "Buyer Summary",
        "Non-Comp Flag",
        "Spending Concentration Flag",
        "Short Bid Windows Flag",
        "Contract Splitting Flag",
    ]
    ordered_tabs = [name for name in preferred_order if name in data]

    # --- Prepare writer + formats ---
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    output_path = os.path.join(base_dir, "output", f"{country_code}_procurement_risk_report.xlsx")

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        workbook = writer.book

        # Header and body formats
        header_format = workbook.add_format({
            'bold': True, 'text_wrap': True, 'border': 1, 'align': 'center', 'bg_color': '#B8E6FE'
        })
        bold_wrap_border_format = workbook.add_format({
            'bold': False, 'text_wrap': True, 'border': 1
        })
        currency_format = workbook.add_format({
            'num_format': '$#,##0.00', 'border': 1, 'text_wrap': True
        })
        risk_score_format = workbook.add_format({
            'num_format': '#,##0.0', 'border': 1, 'text_wrap': True
        })
        highlight_col_format = workbook.add_format({
            'bold': True, 'text_wrap': True, 'border': 1, 'bg_color': '#E4E4E7'
        })
        whole_number_format = workbook.add_format({
            'num_format': '#,##0', 'border': 1, 'text_wrap': True
        })
        percent_format = workbook.add_format({
            'num_format': '0.0%', 'border': 1, 'text_wrap': True
        })

        # --- Write each tab with per-column formatting rules ---
        for sheet_name in ordered_tabs:
            df = data[sheet_name]

            # Safe defaults (ensures variables are always defined)
            currency_columns = []
            risk_score_columns = []
            whole_number_columns = []
            percent_columns = []

            # Optional: rename / drop columns to be presentation-friendly
            if sheet_name == "Bidder Risk Summary":
                df = df.rename(columns={
                    "bidder_name": "Bidder Name",
                    "bidder_country": "Bidder Country",
                    "total_risk_score": "Total Risk Score",
                    "total_dollars_at_risk": "Total Dollars At Risk",
                    "num_flags": "Number of Risk Flags",
                    "total_tenders_won": "Total Tenders Won",
                    "total_payments": "Total Payments",
                    "total_buyers": "Total Buyers",
                    "top_buyer": "Top Buyer",
                    "total_paid_by_top_buyer": "Total Paid By Top Buyer",
                    "total_tenders_from_top_buyer": "Total Tenders From Top Buyer",
                    "non_competitive_tenders_risk_score": "Non Competitive Tenders Risk Score",
                    "non_competitive_dollars_at_risk": "Non Competitive Dollars At Risk",
                    "spending_concentration_risk_score": "Spending Concentration Risk Score",
                    "spending_concentration_dollars_at_risk": "Spending Concentration Dollars At Risk",
                    "short_bid_window_risk_score": "Short Bid Window Risk Score",
                    "short_bid_window_dollars_at_risk": "Short Bid Window Dollars At Risk",
                    "contract_splitting_risk_score": "Contract Splitting Risk Score",
                    "contract_splitting_dollars_at_risk": "Contract Splitting Dollars At Risk",
                })
                df = df.drop(columns=["rank"], errors="ignore")

                currency_columns = [
                    'Total Dollars At Risk',
                    'Total Payments',
                    'Total Paid By Top Buyer',
                    'Non Competitive Dollars At Risk',
                    'Spending Concentration Dollars At Risk',
                    'Short Bid Window Dollars At Risk',
                    'Contract Splitting Dollars At Risk',
                ]
                risk_score_columns = [
                    "Total Risk Score",
                    "Non Competitive Tenders Risk Score",
                    "Spending Concentration Risk Score",
                    "Short Bid Window Risk Score",
                    "Contract Splitting Risk Score",
                ]
                whole_number_columns = [
                    "Number of Risk Flags",
                    "Total Tenders Won",
                    "Total Buyers",
                    "Total Tenders From Top Buyer",
                ]

            elif sheet_name == "Buyer Summary":
                df = df.rename(columns={
                    "buyer_name": "Buyer Name",
                    "buyer_country": "Buyer Country",
                    "total_tenders_awarded": "Total Tenders Awarded",
                    "total_payouts": "Total Payouts",
                    "total_bidders": "Total Bidders",
                    "top_bidder": "Top Bidder",
                    "top_bidder_country": "Top Bidder Country",
                    "total_paid_to_top_bidder": "Total Paid To Top Bidder",
                    "total_tenders_to_top_bidder": "Total Tenders To Top Bidder",
                })
                currency_columns = ["Total Payouts", "Total Paid To Top Bidder"]
                whole_number_columns = ["Total Tenders Awarded", "Total Bidders", "Total Tenders To Top Bidder"]

            elif sheet_name == "Non-Comp Flag":
                df = df.rename(columns={
                    "bidder_name": "Bidder Name",
                    "bidder_country": "Bidder Country",
                    "non_competitive_tenders_won": "Non Competitive Tenders Won",
                    "total_tenders_won": "Total Tenders Won",
                    "pct_tenders_non_competitive": "Pct Tenders Non Competitive",
                    "non_competitive_dollars_at_risk": "Non Competitive Dollars At Risk",
                    "total_payments": "Total Payments",
                    "pct_payments_non_comp_tenders": "Pct Payments Non Comp Tenders",
                    "avg_price_non_competitive_tenders": "Avg Price Non Competitive Tenders",
                    "most_expensive_non_competitive_tender": "Most Expensive Non Competitive Tender",
                    "top_buyer_non_comp_tenders": "Top Buyer Non Comp Tenders",
                    "total_paid_by_top_buyer_non_comp_tenders": "Total Paid By Top Buyer Non Comp Tenders",
                    "non_competitive_tenders_risk_score": "Non Competitive Tenders Risk Score",
                })
                currency_columns = [
                    "Non Competitive Dollars At Risk",
                    "Total Payments",
                    "Avg Price Non Competitive Tenders",
                    "Most Expensive Non Competitive Tender",
                    "Total Paid By Top Buyer Non Comp Tenders",
                ]
                risk_score_columns = ["Non Competitive Tenders Risk Score"]
                whole_number_columns = ["Non Competitive Tenders Won", "Total Tenders Won"]
                percent_columns = ["Pct Tenders Non Competitive", "Pct Payments Non Comp Tenders"]

            elif sheet_name == "Spending Concentration Flag":
                df = df.rename(columns={
                    "bidder_name": "Bidder Name",
                    "bidder_country": "Bidder Country",
                    "spending_concentration_count": "Spending Concentration Count",
                    "spending_concentration_dollars_at_risk": "Spending Concentration Dollars At Risk",
                    "spending_concentration_risk_score": "Spending Concentration Risk Score",
                    "top_buyer": "Top Buyer",
                    "total_paid_by_top_buyer": "Total Paid By Top Buyer",
                })
                currency_columns = ["Spending Concentration Dollars At Risk", "Total Paid By Top Buyer"]
                risk_score_columns = ["Spending Concentration Risk Score"]
                whole_number_columns = ["Spending Concentration Count"]

            elif sheet_name == "Short Bid Windows Flag":
                df = df.rename(columns={
                    "bidder_name": "Bidder Name",
                    "bidder_country": "Bidder Country",
                    "short_bid_window_count": "Short Bid Window Count",
                    "avg_short_bid_window_days": "Avg Short Bid Window Days",
                    "min_short_bid_window": "Min Short Bid Window",
                    "short_bid_window_avg_payment": "Short Bid Window Avg Payment",
                    "short_bid_window_dollars_at_risk": "Short Bid Window Dollars At Risk",
                    "short_bid_window_top_buyer": "Short Bid Window Top Buyer",
                    "short_bid_window_top_buyer_payments": "Short Bid Window Top Buyer Payments",
                    "short_bid_window_risk_score": "Short Bid Window Risk Score",
                })
                currency_columns = [
                    "Short Bid Window Avg Payment",
                    "Short Bid Window Dollars At Risk",
                    "Short Bid Window Top Buyer Payments",
                ]
                risk_score_columns = [
                    "Short Bid Window Risk Score",
                    "Avg Short Bid Window Days",  # intentionally formatted like a numeric score column
                ]
                whole_number_columns = ["Short Bid Window Count", "Min Short Bid Window"]

            elif sheet_name == "Contract Splitting Flag":
                df = df.rename(columns={
                    "bidder_name": "Bidder Name",
                    "bidder_country": "Bidder Country",
                    "contract_split_clusters_count": "Contract Split Clusters Count",
                    "avg_contracts_per_cluster": "Avg Contracts Per Cluster",
                    "max_contract_cluster_count": "Max Contracts in Cluster Count",
                    "contract_splitting_avg_payment_per_cluster": "Contract Splitting Avg Payment Per Cluster",
                    "contract_splitting_max_cluster_payment": "Contract Splitting Max Cluster Payment",
                    "contract_splitting_dollars_at_risk": "Contract Splitting Dollars At Risk",
                    "contract_splitting_risk_score": "Contract Splitting Risk Score",
                })
                currency_columns = [
                    "Contract Splitting Avg Payment Per Cluster",
                    "Contract Splitting Max Cluster Payment",
                    "Contract Splitting Dollars At Risk",
                ]
                risk_score_columns = [
                    "Contract Splitting Risk Score",
                    "Avg Contracts Per Cluster",  # intentionally formatted like a numeric score column
                ]
                whole_number_columns = ["Contract Split Clusters Count", "Max Contract Cluster Count"]

            # --- Write the sheet (truncate sheet name to Excel's 31-char limit) ---
            safe_sheet_name = sheet_name[:31]
            df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
            worksheet = writer.sheets[safe_sheet_name]

            # Freeze top row and first two columns for readability
            worksheet.freeze_panes(1, 2)

            # Header formatting + column widths
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, 20)

            # Body cell formatting based on column lists
            for row_num in range(1, len(df) + 1):
                for col_num, column in enumerate(df.columns):
                    cell_value = df.iat[row_num - 1, col_num]
                    if column in currency_columns:
                        cell_format = currency_format
                    elif column in risk_score_columns:
                        cell_format = risk_score_format
                    elif column in percent_columns:
                        cell_format = percent_format
                    elif column in whole_number_columns:
                        cell_format = whole_number_format
                    elif col_num in [0, 1]:
                        cell_format = highlight_col_format
                    else:
                        cell_format = bold_wrap_border_format
                    worksheet.write(row_num, col_num, cell_value, cell_format)

    print(f"✅ Exported Excel report with {len(ordered_tabs)} tabs to: {output_path}")


# === CLI entrypoint ===
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        import argparse
        parser = argparse.ArgumentParser(description="Export procurement risk report to Excel")
        parser.add_argument("--country", type=str, required=True, help="2-letter country code (e.g., MX)")
        args = parser.parse_args()
        country_code = args.country.upper()
    else:
        country_code = DEFAULT_COUNTRY
        print(f"No --country argument passed. Defaulting to {DEFAULT_COUNTRY}.")

    export_risk_report(country_code)
