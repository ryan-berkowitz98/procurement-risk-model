# src/02_cleaning_and_prep.py
#
# This script processes the raw procurement data imported from 01_data_import.py.
# It performs cleaning, normalization, and filtering to prepare the dataset 
# for use in the procurement risk model built in subsequent scripts.
#
# Rationale:
#   Clean and standardized data ensures that risk flags and scoring models are 
#   based on accurate, consistent, and comparable information across tenders, 
#   bidders, and buyers.
#
# Key operations:
#   - Standardize column names, formats, and data types
#   - Handle missing values, duplicates, and inconsistent entries
#   - Normalize text fields (e.g., case, spacing, accents)
#   - Filter out irrelevant or low-quality records
#
# Output:
#   1. {country_code}_cleaned.parquet  
#      - Fully cleaned and standardized dataset stored in the /output/ancillary directory.
#
# Notes:
#   - Ensure 01_data_import.py has been run prior to executing this script.
#   - country_code is set in config.py or passed as a parameter.
#   - Running this script will overwrite any existing cleaned output file.



import pandas as pd
import numpy as np
import re
import os
import unicodedata
from config import DEFAULT_COUNTRY, DEFAULT_MIN_YEAR, DEFAULT_MAX_YEAR


# === Helper: remove non-letter/number/space characters from text fields ===
def remove_special_chars(text):
    """Remove all characters except letters, numbers, and spaces."""
    if pd.isnull(text):
        return text
    return ''.join(
        c for c in text
        if unicodedata.category(c)[0] in ['L', 'N', 'Z']  # Letter, Number, or Separator
    )


# === Load the raw parquet dataset produced by 01_data_import.py ===
def load_raw_data(country_code):
    """Load raw procurement data parquet for the given country_code."""
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    except NameError:
        base_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))

    parquet_path = os.path.join(base_dir, "output\\ancillary", f"{country_code}_raw.parquet")
    if not os.path.exists(parquet_path):
        raise FileNotFoundError(f"Missing raw data file: {parquet_path}")

    return pd.read_parquet(parquet_path)


# === Flag tenders as non-competitive based on procedure type or single bid ===
def flag_non_competitive(df):
    """Mark tenders as non-competitive if limited, outright award, or single bid."""
    non_competitive_procedures = ["limited", "outright_award"]
    df.loc[:, "flag_non_competitive"] = (
        df["tender_proceduretype"].str.lower().isin(non_competitive_procedures)
        | (df["tender_recordedbidscount"] == 1)
    )
    return df


# === Main cleaning, normalization, and filtering logic ===
def clean_and_filter(df):
    """
    Standardize, normalize, and filter procurement records for downstream analysis.
    Includes:
      - Name normalization
      - Numeric/date casting
      - Description length fields
      - CPV and award criteria counts
      - Year filtering
      - Duplicate removal
      - Tax haven flagging
    """

    # --- Standardize text fields for consistency in joins/matching ---
    df["bidder_name"] = df["bidder_name"].str.upper().apply(remove_special_chars)
    df["buyer_name"] = df["buyer_name"].str.upper().apply(remove_special_chars)
    df["tender_title"] = df["tender_title"].str.upper()
    df["lot_title"] = df["lot_title"].str.upper()

    # --- Ensure numeric and datetime fields ---
    df['tender_year'] = pd.to_numeric(df['tender_year'], errors='coerce')

    # --- Create unified bid price in USD ---
    df['cleaned_bid_price_usd'] = np.where(
        df['currency'] == 'USD', df['bid_price'], df['bid_priceUsd']
    )

    # --- Add length-based features ---
    df['tender_description_length'] = df['tender_title'].str.len()
    df['lot_description_length'] = df['lot_title'].str.len()

    # --- CPV and award criteria counts ---
    df['cpv_count'] = df['tender_cpvs'].str.count(',').add(1)
    df['tender_awardcriteria_count'] = np.where(
        np.isnan(df['tender_awardcriteria_count']),
        df['cpv_count'],
        df['tender_awardcriteria_count']
    )

    # --- Print available year range and config-based filter ---
    min_year_available = int(df['tender_year'].min())
    max_year_available = int(df['tender_year'].max())
    print(f"📅 Data ranges from {min_year_available} to {max_year_available}.")
    print(f"Filtering from {DEFAULT_MIN_YEAR}" + (f" to {DEFAULT_MAX_YEAR}" if DEFAULT_MAX_YEAR else ".") +
          " Update config.py to adjust year range.")

    # --- Keep only valid, in-scope records ---
    df = df[
        df["bidder_name"].notnull()
        & df["buyer_name"].notnull()
        & (df['cleaned_bid_price_usd'] > 0)
        & (df['tender_year'] >= DEFAULT_MIN_YEAR)
    ]
    if DEFAULT_MAX_YEAR:
        df = df[df['tender_year'] <= DEFAULT_MAX_YEAR]

    df = df.copy()  # Avoid chained assignment issues

    # --- Tax haven binary indicator ---
    tax_haven_countries = ["LT", "IE", "NL", "PA", "PL", "SG"]
    df.loc[:, "tax_haven"] = df["bidder_country"].str.upper().isin(tax_haven_countries)

    # --- Remove duplicates based on tender ID/title + bid price ---
    before_dedup = len(df)
    df = df.drop_duplicates(subset=['tender_id', 'cleaned_bid_price_usd'])
    df = df.drop_duplicates(subset=['tender_title', 'cleaned_bid_price_usd'])
    after_dedup = len(df)
    print(f"🧹 Removed {before_dedup - after_dedup} potential duplicate records based on tender ID/title and bid price.")

    # --- Retain only relevant columns for modeling ---
    keep_columns = [
        'tender_id', 'tender_year', 'tender_title', 'lot_title', 'lot_status',
        'tender_proceduretype', 'tender_supplytype', 'buyer_name', 'buyer_city',
        'buyer_country', 'buyer_mainactivities', 'buyer_buyertype', 'bidder_name',
        'bidder_country', 'cleaned_bid_price_usd', 'tender_estimatedprice',
        'tender_finalprice', 'lot_estimatedprice', 'tender_selectionmethod',
        'tender_awardcriteria_count', 'tender_description_length',
        'lot_description_length', 'tender_recordedbidscount', 'lot_bidscount',
        'lot_validbidscount', 'bid_iswinning', 'tender_cpvs',
        'tender_publications_firstcallfortenderdate', 'tender_biddeadline',
        'tender_awarddecisiondate', 'tender_publications_firstdcontractawarddate',
        'tender_contractsignaturedate', 'source', 'tax_haven'
    ]
    df = df[keep_columns]

    # --- Add non-competitive tender flag ---
    df = flag_non_competitive(df)

    return df


# === Save cleaned dataset to /output/ancillary with country_code in filename ===
def save_cleaned_data(df, country_code):
    """Write the cleaned dataset to parquet format in /output/ancillary."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    output_path = os.path.join(base_dir, "output\\ancillary", f"{country_code}_cleaned.parquet")
    df.to_parquet(output_path, index=False)
    print(f"Cleaned data saved to {output_path}")


if __name__ == "__main__":
    # === CLI: allow `--country MX` or default to config ===
    import sys
    if len(sys.argv) > 1:
        import argparse
        parser = argparse.ArgumentParser(description="Clean and filter procurement data")
        parser.add_argument("--country", type=str, required=True, help="2-letter country code (e.g., MX)")
        args = parser.parse_args()
        country_code = args.country.upper()
    else:
        country_code = DEFAULT_COUNTRY
        print(f"No --country argument passed. Defaulting to {DEFAULT_COUNTRY}.")

    # === Run pipeline: load → clean → save ===
    df_raw = load_raw_data(country_code)
    df_cleaned = clean_and_filter(df_raw)
    save_cleaned_data(df_cleaned, country_code)