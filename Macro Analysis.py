#!/usr/bin/env python3
"""
macro_analysis.py

Load a folder of FRED CSVs (with an unnamed first column), combine them,
then analyze macro & market data.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from functools import reduce

# 1. Settings
DATA_DIR    = Path("C:/Users/Owner/OneDrive/Documents/FSU Graduate School/Python Code/Collect-Financial-Data/data/fred")  # ← update me
CSV_PATTERN = "*.csv"                         # e.g. "FRED_*.csv"

# 2. Load & merge all CSVs in the folder
def load_all_csvs(folder: Path, pattern: str = "*.csv") -> pd.DataFrame:
    files = sorted(folder.glob(pattern))
    dfs = []
    for f in files:
        series_name = f.stem
        df = pd.read_csv(f, header=0)
        # rename first (unnamed) column to "DATE"
        first_col = df.columns[0]
        df = df.rename(columns={first_col: "DATE"})
        df["DATE"] = pd.to_datetime(df["DATE"])
        # second column → series values
        value_col = df.columns[1]
        df = df.rename(columns={value_col: series_name})
        df = df[["DATE", series_name]].set_index("DATE")
        dfs.append(df)

    # outer-join on DATE
    df_raw = reduce(lambda left, right: left.join(right, how="outer"), dfs)
    # set freq if inferable
    if df_raw.index.inferred_freq:
        df_raw = df_raw.asfreq(df_raw.index.inferred_freq)
    return df_raw

# 3. Transformations (FIXED)
def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    df_trans = pd.DataFrame(index=df.index)

    # 3.1 Real GDP: forward‐fill then pct_change(1) annualized
    if "Real_GDP" in df:
        gdp_ffill = df["Real_GDP"].ffill()
        df_trans["GDP_qoq_ann_pct"] = gdp_ffill.pct_change(1) * 100 * 4

    # 3.2 CPI: forward‐fill then month‐over‐month
    if "CPI_All" in df:
        cpi_ffill = df["CPI_All"].ffill()
        df_trans["CPI_mom_pct"] = cpi_ffill.pct_change(1) * 100

    # 3.3 Unemployment Rate: just the level, forward‐filled
    if "Unemployment_Rate" in df:
        df_trans["Unemp_lvl"] = df["Unemployment_Rate"].ffill()

    # 3.4 S&P 500: forward‐fill then MoM returns
    if "SP500" in df:
        sp_ffill = df["SP500"].ffill()
        df_trans["SP500_mom_pct"] = sp_ffill.pct_change(1) * 100

    # … add more transforms as you like …

    # drop only the very first row(s) where your pct_change is NaN
    return df_trans.dropna()

# 4. Summary & plotting (unchanged)
def print_summary(df: pd.DataFrame):
    print("\nDescriptive Statistics:")
    print(df.describe().T)

def plot_series(df: pd.DataFrame, cols=None):
    for col in (cols or df.columns):
        plt.figure(figsize=(10, 3))
        plt.plot(df[col], label=col)
        plt.title(col)
        plt.tight_layout()
        plt.show()

def plot_corr_heatmap(df: pd.DataFrame):
    corr = df.corr()
    plt.figure(figsize=(8, 6))
    plt.imshow(corr.values, aspect="auto")
    plt.colorbar()
    plt.xticks(range(len(corr)), corr.columns, rotation=90)
    plt.yticks(range(len(corr)), corr.columns)
    plt.title("Correlation Matrix", pad=20)
    plt.tight_layout()
    plt.show()

def plot_rolling_corr(df: pd.DataFrame, x: str, y: str, window: int = 12):
    roll_corr = df[x].rolling(window).corr(df[y])
    plt.figure(figsize=(10, 3))
    plt.plot(roll_corr, label=f"{x} vs {y} ({window}-period)")
    plt.title(f"Rolling {window}-period Corr: {x} & {y}")
    plt.tight_layout()
    plt.show()

# 5. Main
def main():
    df_raw = load_all_csvs(DATA_DIR, CSV_PATTERN)
    print(f"Loaded {df_raw.shape[1]} series from {DATA_DIR}")
    print("Raw series names:", df_raw.columns.tolist())   # ← debug

    df = transform_data(df_raw)
    print_summary(df)

    plot_series(df)
    plot_corr_heatmap(df)
    if {"GDP_qoq_ann_pct", "SP500_mom_pct"}.issubset(df.columns):
        plot_rolling_corr(df, "GDP_qoq_ann_pct", "SP500_mom_pct", window=12)

if __name__ == "__main__":
    main()