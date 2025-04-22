#!/usr/bin/env python3
"""
fetch_fred_data.py

A script to download historical macroeconomic series from FRED,
written with best practices for readability, debugging, and maintainability.
"""

import os
import sys
from datetime import datetime
from fredapi import Fred
import pandas as pd
#test
# ------------------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------------------

# 1) You must export your FRED API key in your environment:
#    export FRED_API_KEY="your_actual_api_key_here"
FRED_API_KEY = os.getenv("FRED_API_KEY")
if not FRED_API_KEY:
    print("ERROR: Please set the FRED_API_KEY environment variable.", file=sys.stderr)
    sys.exit(1)

# 2) Define the series you want to pull:
# … earlier macro series …
SERIES = {
    "Real_GDP":            "GDPC1",
    "GDP_Deflator":        "GDPDEF",
    "CPI_All":             "CPIAUCSL",
    "CPI_Core":            "CPILFESL",
    "PPI_Commodities":     "PPIACO",
    "Unemployment_Rate":   "UNRATE",
    "Nonfarm_Payroll":     "PAYEMS",
    "Initial_Claims":      "ICSA",
    "Job_Openings":        "JTSJOL",
    "Retail_Sales":        "RSXFS",
    "Industrial_Prod":     "INDPRO",
    "Housing_Starts":      "HOUST",
    "Fed_Funds_Rate_Daily":"DFEDTAR",
    "Fed_Funds_Rate_Monthly":"FEDFUNDS",
    "TenY_Treasury":       "DGS10",
    "M2_Money_Stock":      "M2SL",

    # Major equity indices (all daily, not seasonally adjusted)
    "S&P_500":                         "SP500",     # Broad large‐cap equities :contentReference[oaicite:1]{index=1}
    "Dow_Jones_Industrial_Average":    "DJIA",      # Industrial sector :contentReference[oaicite:2]{index=2}
    "NASDAQ_Composite_Index":          "NASDAQCOM", # Broad, tech‐heavy equities :contentReference[oaicite:3]{index=3}
    "NASDAQ_100_Index":                "NASDAQ100", # Top 100 non‐financial NASDAQ companies :contentReference[oaicite:4]{index=4}

    # Sector‐focused Dow Jones Averages
    "Dow_Jones_Transportation_Average":"DJTA",      # Transportation sector :contentReference[oaicite:5]{index=5}
    "Dow_Jones_Composite_Average":     "DJCA",      # Blue‐chip microcosm (Industrials + Utilities + Transports) :contentReference[oaicite:6]{index=6}
    "Dow_Jones_Utility_Average":       "DJUA",      # Utilities sector :contentReference[oaicite:7]{index=7}
}

# 3) Output directory for CSVs
OUTPUT_DIR = "data/fred"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ------------------------------------------------------------------------------
# FUNCTIONS
# ------------------------------------------------------------------------------

def fetch_series(fred_client, series_id):
    """
    Fetch a time series from FRED.
    Returns a pandas.Series indexed by date.
    """
    print(f"[{datetime.now()}] ▶ Fetching '{series_id}' from FRED...")
    try:
        data = fred_client.get_series(series_id)
        print(f"[{datetime.now()}] ✔ Retrieved {len(data)} observations for {series_id}.")
        return data
    except Exception as e:
        print(f"[{datetime.now()}] ✖ Failed to fetch {series_id}: {e}", file=sys.stderr)
        return None

def save_to_csv(series, name):
    """
    Save a pandas Series to CSV under OUTPUT_DIR.
    """
    filename = os.path.join(OUTPUT_DIR, f"{name}.csv")
    try:
        series.to_csv(filename, header=[name])
        print(f"[{datetime.now()}] ✔ Saved '{name}' to {filename}.")
    except Exception as e:
        print(f"[{datetime.now()}] ✖ Error saving {name}: {e}", file=sys.stderr)

# ------------------------------------------------------------------------------
# MAIN EXECUTION
# ------------------------------------------------------------------------------

def main():
    # Initialize FRED client
    fred = Fred(api_key=FRED_API_KEY)
    print(f"[{datetime.now()}] Initialized FRED client.")

    # Loop through each series, fetch, and save
    for friendly_name, series_id in SERIES.items():
        series = fetch_series(fred, series_id)
        if series is not None:
            save_to_csv(series, friendly_name)

    print(f"[{datetime.now()}] All done!")

if __name__ == "__main__":
    main()