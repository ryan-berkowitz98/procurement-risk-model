# src/01_data_import.py
# This script loads a raw CSV from the user's local /input folder.
# Please ensure raw CSV adheres to the naming convention: '{country_code}_DIB_[YYYY].csv'
#
# Source: The raw procurement data comes from the Government Transparency Institute's
# Global Contract-Level Public Procurement Dataset.
# More information about the methodology and coverage is available at:
# https://www.govtransparency.eu/global-contract-level-public-procurement-dataset/
#
# The dataset itself can be downloaded on a country-by-country basis here:
# https://input.mendeley.com/inputsets/fwzpywbhgw/3


import pandas as pd
import os
from config import DEFAULT_COUNTRY

# Define the data types for consistent parsing.
# Defining data types for all vaariables even though most variables will be dropped.
# This was the most consistent way to bypass errors on the import.
dtype_dict = {
    'persistent_id': 'object',
    'tender_id': 'object',
    'tender_title': 'object',
    'tender_proceduretype': 'object',
    'tender_nationalproceduretype': 'object',
    'tender_isawarded': 'object',
    'tender_supplytype': 'object',
    'tender_biddeadline': 'object',
    'tender_isjointprocurement': 'object',
    'tender_lotscount': 'float64',
    'tender_recordedbidscount': 'float64',
    'tender_isframeworkagreement': 'object',
    'tender_isdps': 'object',
    'tender_contractsignaturedate': 'object',
    'tender_cpvs': 'object',
    'tender_maincpv': 'object',
    'tender_iseufunded': 'object',
    'tender_selectionmethod': 'object',
    'tender_awardcriteria_count': 'float64',
    'tender_cancellationdate': 'object',
    'cancellation_reason': 'object',
    'tender_awarddecisiondate': 'object',
    'tender_estimatedprice': 'float64',
    'tender_finalprice': 'float64',
    'lot_estimatedprice': 'float64',
    'bid_price': 'float64',
    'tender_corrections_count': 'float64',
    'lot_row_nr': 'object',
    'lot_title': 'object',
    'lot_status': 'object',
    'lot_bidscount': 'float64',
    'lot_validbidscount': 'float64',
    'lot_electronicbidscount': 'float64',
    'lot_smebidscount': 'float64',
    'lot_updateddurationdays': 'float64',
    'buyer_id': 'object',
    'buyer_masterid': 'object',
    'buyer_name': 'object',
    'buyer_nuts': 'object',
    'buyer_city': 'object',
    'buyer_country': 'object',
    'buyer_mainactivities': 'object',
    'buyer_buyertype': 'object',
    'buyer_postcode': 'object',
    'buyer_nuts_1': 'object',
    'buyer_nuts_2': 'object',
    'buyer_nuts_3': 'object',
    'bidder_name': 'object',
    'bidder_country': 'object',
    'bid_priceUsd': 'float64',
    'tender_estimatedpriceUsd': 'float64',
    'tender_finalpriceUsd': 'float64',
    'tender_year': 'float64',
    'tender_description_length': 'float64',
    'lot_description_length': 'float64',
    'source': 'object',
    'currency': 'object'
}

# Call out date variables for parsing.
parse_dates = [
    'tender_biddeadline',
    'tender_contractsignaturedate',
    'tender_cancellationdate',
    'tender_awarddecisiondate',
    'tender_publications_firstdcontractawarddate',
    'tender_publications_firstcallfortenderdate'
]

# Define a function for importing the raw data and outputting a parquet file for later use.
def import_data(country_code):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(base_dir, "input")
    output_dir = os.path.join(base_dir, "output\\ancillary")

    matching_files = [f for f in os.listdir(data_dir) if f.startswith(country_code) and f.endswith(".csv")]
    if not matching_files:
        raise FileNotFoundError(f"No CSV file found in /input for {country_code}.")

    # Select the latest file based on year extracted from filename
    matching_files.sort(reverse=True)
    selected_file = matching_files[0]

    print(f"📥 Importing data from {selected_file}")
    df = pd.read_csv(
        os.path.join(data_dir, selected_file),
        dtype=dtype_dict,
        parse_dates=parse_dates,
        low_memory=False
    )

    out_path = os.path.join(output_dir, f"{country_code}_raw.parquet")
    df.to_parquet(out_path, index=False)
    print(f"✅ Data imported and saved to {out_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        import argparse
        parser = argparse.ArgumentParser(description="Import procurement data")
        parser.add_argument("--country", type=str, required=True, help="2-letter country code (e.g., MX)")
        args = parser.parse_args()
        country_code = args.country.upper()
    else:
        country_code = DEFAULT_COUNTRY
        print(f"No --country argument passed. Defaulting to {DEFAULT_COUNTRY}.")

    import_data(country_code)
