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
        # read, take header row as column names (first col is blank/unnamed)
        df = pd.read_csv(f, header=0)
        # rename the first column (whatever its name is) to "DATE"
        first_col = df.columns[0]
        df = df.rename(columns={first_col: "DATE"})
        # parse that column as datetime
        df["DATE"] = pd.to_datetime(df["DATE"])
        # the second column is the values; rename it to the series_name
        value_col = df.columns[1]
        df = df.rename(columns={value_col: series_name})
        # keep only DATE + this series, set DATE index
        df = df[["DATE", series_name]].set_index("DATE")
        dfs.append(df)

    # outer-join on DATE to keep all dates
    df_raw = reduce(lambda left, right: left.join(right, how="outer"), dfs)
    # if frequency inference works, set it
    if df_raw.index.inferred_freq:
        df_raw = df_raw.asfreq(df_raw.index.inferred_freq)
    return df_raw

# 3. Transformations
def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    df_trans = pd.DataFrame(index=df.index)
    if "Real_GDP" in df:
        df_trans["GDP_qoq_ann_pct"] = df["Real_GDP"].pct_change(1) * 100 * 4
    if "CPI_All" in df:
        df_trans["CPI_mom_pct"] = df["CPI_All"].pct_change(1) * 100
    if "Unemployment_Rate" in df:
        df_trans["Unemp_lvl"] = df["Unemployment_Rate"]
    if "SP500" in df:
        df_trans["SP500_mom_pct"] = df["SP500"].pct_change(1) * 100
    # … add more transforms here …
    return df_trans.dropna()

# 4. Summary & plotting (same as before)
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
    plt.matshow(corr, fignum=1)
    plt.xticks(range(len(corr)), corr.columns, rotation=90)
    plt.yticks(range(len(corr)), corr.columns)
    plt.colorbar()
    plt.title("Correlation Matrix", pad=20)
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
    # 2. load & merge raw series
    df_raw = load_all_csvs(DATA_DIR, CSV_PATTERN)
    print(f"Loaded {df_raw.shape[1]} series from {DATA_DIR}")

    # 3. apply transforms
    df = transform_data(df_raw)

    # 4. summary & plots
    print_summary(df)
    plot_series(df)
    plot_corr_heatmap(df)

    # example rolling correlate
    if {"GDP_qoq_ann_pct", "SP500_mom_pct"}.issubset(df.columns):
        plot_rolling_corr(df, "GDP_qoq_ann_pct", "SP500_mom_pct", window=12)

if __name__ == "__main__":
    main()