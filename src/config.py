# config.py

# Default country to run analysis for (2-letter ISO code, e.g., "MX")
DEFAULT_COUNTRY = "MX"

# Year filtering parameters
DEFAULT_MIN_YEAR = 2019  # Earliest year to include
DEFAULT_MAX_YEAR = None  # Set to None to include all years

# Thresholds for flagging non-competitive tender risk
NON_COMP_DOLLAR_THRESHOLD = 1_000_000  # Total value of non-comp tenders for bidder
NON_COMP_MAX_TENDER_THRESHOLD = 1_000_000  # Largest individual non-comp tender

# You can change these thresholds to make the flagging criteria more or less strict.
# For example, lower the dollar amounts to catch more bidders, or raise them to focus on high-risk entities.
