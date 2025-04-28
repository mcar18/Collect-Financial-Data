import os
import requests
import pandas as pd
import numpy as np

HEADERS = {
    "User-Agent": "Your Name (your.email@example.com)"
}

# Possible GAAP element names per metric
GAAP_TAGS = {
    "GrossProfit":       ["GrossProfit", "GrossLoss"],
    "Revenues":          ["Revenues", "SalesRevenueNet"],
    "NetIncomeLoss":     ["NetIncomeLoss", "ProfitLoss"],
    "OperatingCashFlow": ["NetCashProvidedByUsedInOperatingActivities"]
}

def get_cik_map():
    url = "https://www.sec.gov/files/company_tickers.json"
    r = requests.get(url, headers=HEADERS); r.raise_for_status()
    data = r.json()
    df = pd.DataFrame.from_dict(data, orient="index")
    df.rename(columns={"title": "company_name"}, inplace=True)
    df["cik"] = df["cik_str"].astype(int).astype(str).str.zfill(10)
    return df.set_index("ticker")["cik"].to_dict()

def fetch_all_facts(cik):
    """
    Returns a DataFrame indexed by period-end containing:
    GrossProfit, Revenues, NetIncomeLoss, OperatingCashFlow,
    plus derived YoY_Revenue_%, GrossMargin, NetMargin, OpCFMargin.
    """
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    r = requests.get(url, headers=HEADERS); r.raise_for_status()
    facts = r.json()["facts"]["us-gaap"]

    records = {}
    for metric, tag_list in GAAP_TAGS.items():
        for tag in tag_list:
            for f in facts.get(tag, {}).get("units", {}).get("USD", []):
                end = f.get("end")
                val = f.get("val")
                if not end or val is None:
                    continue
                rec = records.setdefault(end, {})
                rec[metric] = float(val)
            # stop on first tag that yields any data
            if any(r.get(metric) is not None for r in records.values()):
                break

    df = pd.DataFrame.from_dict(records, orient="index")
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)

    # cast everything to float, so missing slots become NaN
    df = df.astype(float)

    # derived metrics
    df["YoY_Revenue_%"] = df["Revenues"].pct_change(periods=4, fill_method=None) * 100
    df["GrossMargin"]   = df["GrossProfit"] / df["Revenues"]
    df["NetMargin"]     = df["NetIncomeLoss"] / df["Revenues"]
    df["OpCFMargin"]    = df["OperatingCashFlow"] / df["Revenues"]

    return df

if __name__ == "__main__":
    tickers = ["AAPL", "MSFT"]
    cik_map = get_cik_map()

    base_folder = "fundamental data gathered"
    os.makedirs(base_folder, exist_ok=True)

    for ticker in tickers:
        cik = cik_map.get(ticker.upper())
        if not cik:
            print(f"⚠️  No CIK found for {ticker}, skipping.")
            continue

        print(f"Fetching facts for {ticker}…")
        df = fetch_all_facts(cik)
        if df.empty:
            print(f"  ❌ No data returned for {ticker}.")
            continue

        # Create ticker-specific folder
        ticker_folder = os.path.join(base_folder, ticker)
        os.makedirs(ticker_folder, exist_ok=True)

        # Save to CSV
        csv_path = os.path.join(ticker_folder, "fundamentals.csv")
        df.to_csv(csv_path, index_label="period_end")
        print(f"  ✅ Saved {len(df)} rows to `{csv_path}`\n")

    print("Done gathering fundamental data.")