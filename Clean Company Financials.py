import os
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

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
    """ Fill relationships, compute margins, leverage, ROA/ROE, YoY% """
    # COGS <-> GrossProfit
    if "Revenues" in df.columns:
        cogs = df.get("CostOfGoodsAndServicesSold", pd.Series(np.nan, index=df.index))
        gp = df.get("GrossProfit", pd.Series(np.nan, index=df.index))
        df["GrossProfit"] = gp.fillna(df["Revenues"] - cogs)
        df["CostOfGoodsAndServicesSold"] = cogs.fillna(df["Revenues"] - gp)

    # Margins
    if {"GrossProfit","Revenues"}.issubset(df.columns):
        df["GrossMargin"] = df["GrossProfit"] / df["Revenues"]
    if {"OperatingIncomeLoss","Revenues"}.issubset(df.columns):
        df["OperatingMargin"] = df["OperatingIncomeLoss"] / df["Revenues"]
    if {"NetIncomeLoss","Revenues"}.issubset(df.columns):
        df["NetMargin"] = df["NetIncomeLoss"] / df["Revenues"]
    if {"OperatingCashFlow","Revenues"}.issubset(df.columns):
        df["OpCFMargin"] = df["OperatingCashFlow"] / df["Revenues"]

    # Liquidity & leverage
    ca = df.get("CurrentAssets", pd.Series(np.nan, index=df.index))
    cl = df.get("CurrentLiabilities", pd.Series(np.nan, index=df.index))
    if not ca.isna().all() and not cl.isna().all():
        df["CurrentRatio"] = ca / cl
        inv = df.get("InventoryNet", pd.Series(0, index=df.index))
        df["QuickRatio"] = (ca - inv) / cl

    std = df.get("ShortTermDebt", pd.Series(0, index=df.index)).fillna(0)
    ltd = df.get("LongTermDebtNoncurrent", pd.Series(0, index=df.index)).fillna(0)
    eq = df.get("StockholdersEquity", pd.Series(np.nan, index=df.index))
    if not eq.isna().all():
        df["DebtToEquity"] = (std + ltd) / eq

    # Returns
    assets = df.get("Assets", pd.Series(np.nan, index=df.index))
    ni = df.get("NetIncomeLoss", pd.Series(np.nan, index=df.index))
    if not assets.isna().all():
        df["ROA"] = ni / assets
    if not eq.isna().all():
        df["ROE"] = ni / eq

    # YoY% changes
    for item in KEY_ITEMS:
        if item in df.columns:
            df[f"{item}_YoY_%"] = df[item].pct_change(periods=4, fill_method=None) * 100

    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    return df

def process_ticker(ticker):
    # 1) Load quarterly full fundamentals
    in_path = os.path.join(INPUT_BASE, ticker, "fundamentals_full.csv")
    df_q = pd.read_csv(in_path, index_col="period_end", parse_dates=True).sort_index()

    # 2) Clean & engineer quarterlies
    df_q = df_q.astype(float)
    df_q = clean_quarterly(df_q)

    # 3) Pull daily prices
    tkr = yf.Ticker(ticker)
    start = df_q.index.min().strftime("%Y-%m-%d")
    today = datetime.today().strftime("%Y-%m-%d")
    price = tkr.history(start=start, end=today)["Close"].rename("Close")
    if price.index.tz is not None:
        price.index = price.index.tz_localize(None)

    # 4) Build a daily DataFrame, reindex the quarterly onto it, then forward-fill
    df_daily = pd.DataFrame(index=price.index)
    df_daily["Close"] = price
    df_q_daily = df_q.reindex(df_daily.index, method="ffill")
    df_daily = df_daily.join(df_q_daily)

    # 5) Market Cap & Enterprise Value
    shares = tkr.info.get("sharesOutstanding", np.nan)
    df_daily["MarketCap"] = df_daily["Close"] * shares

    std = df_daily.get("ShortTermDebt", pd.Series(0, index=df_daily.index)).fillna(0)
    ltd = df_daily.get("LongTermDebtNoncurrent", pd.Series(0, index=df_daily.index)).fillna(0)
    cash = pd.Series(0, index=df_daily.index)
    for ctag in [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsAndShortTermInvestments"
    ]:
        if ctag in df_daily.columns:
            cash = df_daily[ctag].fillna(0)
            break

    df_daily["EV"] = df_daily["MarketCap"] + std + ltd - cash

    # 6) Valuation multiples
    ni_yoy = df_daily.get("NetIncomeLoss_YoY_%", pd.Series(np.nan, index=df_daily.index)) / 100
    df_daily["PE"] = df_daily["MarketCap"] / df_daily.get("NetIncomeLoss", pd.Series(np.nan, index=df_daily.index))
    df_daily["PEG"] = df_daily["PE"] / ni_yoy
    df_daily["EV_GP"] = df_daily["EV"] / df_daily.get("GrossProfit", pd.Series(np.nan, index=df_daily.index))
    df_daily["PS"] = df_daily["MarketCap"] / df_daily.get("Revenues", pd.Series(np.nan, index=df_daily.index))
    df_daily["EV_S"] = df_daily["EV"] / df_daily.get("Revenues", pd.Series(np.nan, index=df_daily.index))

    # 7) Save
    out_dir = os.path.join(OUTPUT_BASE, ticker)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "cleaned_fundamentals.csv")
    df_daily.to_csv(out_path, index_label="date")
    print(f"{ticker}: {df_daily.shape[0]} days × {df_daily.shape[1]} cols → {out_path}")

if __name__ == "__main__":
    os.makedirs(OUTPUT_BASE, exist_ok=True)
    for ticker in os.listdir(INPUT_BASE):
        if os.path.isdir(os.path.join(INPUT_BASE, ticker)):
            process_ticker(ticker)