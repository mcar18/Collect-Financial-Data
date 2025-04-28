import os
import pandas as pd
import numpy as np

# Base folders
INPUT_BASE  = "fundamental data gathered"
OUTPUT_BASE = "cleaned fundamentals"

# Which line‐items we’ll derive YoY% for and consider “core”
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

def process_ticker(ticker):
    in_path  = os.path.join(INPUT_BASE, ticker, "fundamentals_full.csv")
    out_dir  = os.path.join(OUTPUT_BASE, ticker)
    out_path = os.path.join(out_dir, "cleaned_fundamentals.csv")

    df = pd.read_csv(in_path, index_col="period_end", parse_dates=True)

    # 1) Fill COGS ↔ GrossProfit relationships
    if "CostOfGoodsAndServicesSold" in df and "Revenues" in df:
        df["GrossProfit"] = df["GrossProfit"].fillna(df["Revenues"] - df["CostOfGoodsAndServicesSold"])
    if "GrossProfit" in df and "Revenues" in df:
        df["CostOfGoodsAndServicesSold"] = df["CostOfGoodsAndServicesSold"].fillna(df["Revenues"] - df["GrossProfit"])

    # 2) Compute margins
    if {"GrossProfit","Revenues"}.issubset(df):
        df["GrossMargin"] = df["GrossProfit"] / df["Revenues"]
    if {"OperatingIncomeLoss","Revenues"}.issubset(df):
        df["OperatingMargin"] = df["OperatingIncomeLoss"] / df["Revenues"]
    if {"NetIncomeLoss","Revenues"}.issubset(df):
        df["NetMargin"] = df["NetIncomeLoss"] / df["Revenues"]
    if {"OperatingCashFlow","Revenues"}.issubset(df):
        df["OpCFMargin"] = df["OperatingCashFlow"] / df["Revenues"]

    # 3) Liquidity & leverage ratios
    if {"CurrentAssets","CurrentLiabilities"}.issubset(df):
        df["CurrentRatio"] = df["CurrentAssets"] / df["CurrentLiabilities"]
    if {"CurrentAssets","InventoryNet","CurrentLiabilities"}.issubset(df):
        df["QuickRatio"] = (df["CurrentAssets"] - df["InventoryNet"]) / df["CurrentLiabilities"]
    # total debt = short + long
    if {"ShortTermDebt","LongTermDebtNoncurrent","StockholdersEquity"}.issubset(df):
        total_debt = df["ShortTermDebt"].fillna(0) + df["LongTermDebtNoncurrent"].fillna(0)
        df["DebtToEquity"] = total_debt / df["StockholdersEquity"]

    # 4) Returns
    if {"NetIncomeLoss","Assets"}.issubset(df):
        df["ROA"] = df["NetIncomeLoss"] / df["Assets"]
    if {"NetIncomeLoss","StockholdersEquity"}.issubset(df):
        df["ROE"] = df["NetIncomeLoss"] / df["StockholdersEquity"]

    # 5) YoY % changes for all KEY_ITEMS that exist
    for item in KEY_ITEMS:
        if item in df:
            df[f"{item}_YoY_%"] = df[item].pct_change(periods=4, fill_method=None) * 100

    # 6) Clean up infinities & sort
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.sort_index(inplace=True)

    # 7) Save
    os.makedirs(out_dir, exist_ok=True)
    df.to_csv(out_path, index_label="period_end")
    print(f"{ticker}: saved {df.shape[0]} rows × {df.shape[1]} cols → {out_path}")

if __name__ == "__main__":
    os.makedirs(OUTPUT_BASE, exist_ok=True)
    for ticker in os.listdir(INPUT_BASE):
        path = os.path.join(INPUT_BASE, ticker, "fundamentals_full.csv")
        if os.path.isfile(path):
            process_ticker(ticker)