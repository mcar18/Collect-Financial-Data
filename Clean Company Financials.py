import os
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
#stock price included too
# Base folders
INPUT_BASE  = "fundamental data gathered"
OUTPUT_BASE = "cleaned fundamentals"

# Core items for YoY%
KEY_ITEMS = [
    "Revenues",
    "CostOfGoodsAndServicesSold",
    "GrossProfit",
    "OperatingIncomeLoss",
    "NetIncomeLoss",
    "OperatingCashFlow",
    "Assets",
    "CurrentAssets",
    "CurrentLiabilities",
    "InventoryNet",
    "StockholdersEquity",
    "ShortTermDebt",
    "LongTermDebtNoncurrent",
    "DepreciationAndAmortization"
]

def clean_quarterly(df):
    # ... (same as before) ...
    # you can copy your existing clean_quarterly implementation here
    return df

def process_ticker(ticker):
    # 1) Load & clean quarterly fundamentals
    in_path = os.path.join(INPUT_BASE, ticker, "fundamentals_full.csv")
    df_q = (pd.read_csv(in_path, index_col="period_end", parse_dates=True)
              .sort_index()
              .astype(float))
    df_q = clean_quarterly(df_q)
    df_q = df_q.reset_index().rename(columns={"period_end":"date"})

    # 2) Pull daily prices
    tkr = yf.Ticker(ticker)
    start = df_q["date"].min().strftime("%Y-%m-%d")
    today = datetime.today().strftime("%Y-%m-%d")
    price = tkr.history(start=start, end=today)["Close"].rename("Close")
    if price.index.tz is not None:
        price.index = price.index.tz_localize(None)

    df_daily = price.to_frame().reset_index().rename(columns={"Date":"date"})

    # 3) Merge-as-of
    df_merged = pd.merge_asof(
        df_daily.sort_values("date"),
        df_q.sort_values("date"),
        on="date",
        direction="backward"
    )

    # 4) MarketCap & EV
    df_merged["MarketCap"] = df_merged["Close"] * tkr.info.get("sharesOutstanding", np.nan)

    # debt default → Series of zeros
    std = df_merged.get(
        "ShortTermDebt",
        pd.Series(0, index=df_merged.index)
    ).fillna(0)
    ltd = df_merged.get(
        "LongTermDebtNoncurrent",
        pd.Series(0, index=df_merged.index)
    ).fillna(0)

    # cash default → Series of zeros
    cash = pd.Series(0, index=df_merged.index)
    for tag in [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsAndShortTermInvestments"
    ]:
        if tag in df_merged.columns:
            cash = df_merged[tag].fillna(0)
            break

    df_merged["EV"] = df_merged["MarketCap"] + std + ltd - cash

    # 5) Valuation multiples
    ni  = df_merged.get(
        "NetIncomeLoss",
        pd.Series(np.nan, index=df_merged.index)
    )
    yoy = df_merged.get(
        "NetIncomeLoss_YoY_%",
        pd.Series(np.nan, index=df_merged.index)
    ) / 100

    df_merged["PE"]    = df_merged["MarketCap"] / ni
    df_merged["PEG"]   = df_merged["PE"] / yoy
    df_merged["EV_GP"] = df_merged["EV"] / df_merged.get(
        "GrossProfit", pd.Series(np.nan, index=df_merged.index)
    )
    df_merged["PS"]    = df_merged["MarketCap"] / df_merged.get(
        "Revenues", pd.Series(np.nan, index=df_merged.index)
    )
    df_merged["EV_S"]  = df_merged["EV"] / df_merged.get(
        "Revenues", pd.Series(np.nan, index=df_merged.index)
    )

    # 6) Save
    out_dir = os.path.join(OUTPUT_BASE, ticker)
    os.makedirs(out_dir, exist_ok=True)
    df_merged.set_index("date").to_csv(
        os.path.join(out_dir, "cleaned_fundamentals.csv"),
        index_label="date"
    )
    print(f"{ticker}: {df_merged.shape[0]} rows × {df_merged.shape[1]} cols")

if __name__ == "__main__":
    os.makedirs(OUTPUT_BASE, exist_ok=True)
    for ticker in os.listdir(INPUT_BASE):
        if os.path.isdir(os.path.join(INPUT_BASE, ticker)):
            process_ticker(ticker)