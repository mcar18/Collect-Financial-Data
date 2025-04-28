import os
import requests
import pandas as pd
import numpy as np

HEADERS = {
    "User-Agent": "Your Name (your.email@example.com)"
}

def get_cik_map():
    url = "https://www.sec.gov/files/company_tickers.json"
    r = requests.get(url, headers=HEADERS); r.raise_for_status()
    data = r.json()
    df = pd.DataFrame.from_dict(data, orient="index")
    df.rename(columns={"title": "company_name"}, inplace=True)
    df["cik"] = df["cik_str"].astype(int).astype(str).str.zfill(10)
    return df.set_index("ticker")["cik"].to_dict()

def fetch_all_line_items(cik):
    """
    Pulls every US-GAAP line item in USD for each period-end.
    Returns a DataFrame indexed by period_end with one column per tag.
    """
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    r = requests.get(url, headers=HEADERS); r.raise_for_status()
    facts = r.json()["facts"]["us-gaap"]

    records = {}
    for tag, content in facts.items():
        # look only at the USD series
        for f in content.get("units", {}).get("USD", []):
            end = f.get("end")
            val = f.get("val")
            if end is None:
                continue
            rec = records.setdefault(end, {})
            # convert to float or NaN
            rec[tag] = float(val) if val is not None else np.nan

    # build a wide DataFrame
    df = pd.DataFrame.from_dict(records, orient="index")
    # ensure all columns are floats (missing entries become NaN)
    df = df.astype(float)
    # index as datetime
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)
    return df

if __name__ == "__main__":
    tickers = ["AAPL", "MSFT","JPM"]
    cik_map = get_cik_map()

    base_folder = "fundamental data gathered"
    os.makedirs(base_folder, exist_ok=True)

    for ticker in tickers:
        cik = cik_map.get(ticker.upper())
        if not cik:
            print(f"⚠️  No CIK for {ticker}, skipping.")
            continue

        print(f"Fetching all line items for {ticker}…")
        df = fetch_all_line_items(cik)
        if df.empty:
            print(f"  ❌ No data returned for {ticker}.")
            continue

        # Create ticker folder
        ticker_folder = os.path.join(base_folder, ticker)
        os.makedirs(ticker_folder, exist_ok=True)

        # Save the full wide CSV
        csv_path = os.path.join(ticker_folder, "fundamentals_full.csv")
        df.to_csv(csv_path, index_label="period_end")
        print(f"  ✅ Saved {df.shape[0]} periods × {df.shape[1]} items → `{csv_path}`\n")

    print("Done gathering full fundamental line items.")