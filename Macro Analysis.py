#!/usr/bin/env python3
"""
macro_analysis.py

Load FRED CSVs from a folder, compute year‑over‑year % changes on a monthly basis,
print summary statistics, plot time series and correlations, and identify
the top macro drivers for each equity index.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from functools import reduce

# ----------------------------------------------------------------------
# SETTINGS
# ----------------------------------------------------------------------
DATA_DIR = Path("C:/Users/Owner/OneDrive/Documents/FSU Graduate School/Python Code/Collect-Financial-Data/data/fred")        # ← update to your actual CSV folder
CSV_PATTERN = "*.csv"
RESAMPLE_FREQ = "M"                 # monthly frequency
EQUITY_PREFIXES = ["S&P", "Dow_Jones", "NASDAQ"]  # detect equity series by these prefixes
TOP_N_DRIVERS = 5                   # how many top correlates to show

# ----------------------------------------------------------------------
# 1. LOAD & MERGE ALL CSVs
# ----------------------------------------------------------------------
def load_all_csvs(folder: Path, pattern: str = "*.csv") -> pd.DataFrame:
    files = sorted(folder.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files found in {folder} matching {pattern}")
    dfs = []
    for f in files:
        # each CSV: first column is date, unnamed header; second column is the series
        df = pd.read_csv(f, index_col=0, parse_dates=True)
        df.columns = [f.stem]               # rename value column to filename stem
        dfs.append(df)
    # outer‑join on the datetime index
    df_raw = reduce(lambda left, right: left.join(right, how="outer"), dfs)
    return df_raw

# ----------------------------------------------------------------------
# 2. TRANSFORM: YEAR‑OVER‑YEAR % CHANGE (MONTHLY)
# ----------------------------------------------------------------------
def transform_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    # Resample to month‑end frequency and take last observation
    df_monthly = df_raw.resample(RESAMPLE_FREQ).last()
    # Forward‑fill missing values
    df_ff = df_monthly.ffill()
    # Compute YoY % change
    df_yoy = df_ff.pct_change(12) * 100
    # Drop the first 12 rows (all-NaN)
    return df_yoy.dropna(how="all")

# ----------------------------------------------------------------------
# 3. PRINT SUMMARY STATISTICS
# ----------------------------------------------------------------------
def print_summary(df: pd.DataFrame):
    print("\n=== Descriptive Statistics (Year‑over‑Year % Change) ===")
    print(df.describe().T)

# ----------------------------------------------------------------------
# 4. PLOT TIME SERIES
# ----------------------------------------------------------------------
def plot_time_series(df: pd.DataFrame):
    for col in df.columns:
        plt.figure(figsize=(10, 3))
        plt.plot(df.index, df[col], label=col)
        plt.title(f"YoY % Change: {col}")
        plt.ylabel("% Change")
        plt.legend()
        plt.tight_layout()
        plt.show()

# ----------------------------------------------------------------------
# 5. PLOT CORRELATION MATRIX
# ----------------------------------------------------------------------
def plot_correlation_matrix(df: pd.DataFrame):
    corr = df.corr()
    plt.figure(figsize=(12, 10))
    im = plt.imshow(corr.values, aspect="auto", interpolation="none")
    plt.colorbar(im, label="Correlation")
    plt.xticks(np.arange(len(corr)), corr.columns, rotation=90)
    plt.yticks(np.arange(len(corr)), corr.columns)
    plt.title("Correlation Matrix (YoY % Change)")
    plt.tight_layout()
    plt.show()

# ----------------------------------------------------------------------
# 6. IDENTIFY TOP MACRO DRIVERS FOR EQUITIES
# ----------------------------------------------------------------------
def identify_top_macro_drivers(df: pd.DataFrame,
                               equity_prefixes=None,
                               top_n: int = TOP_N_DRIVERS):
    if equity_prefixes is None:
        equity_prefixes = EQUITY_PREFIXES
    # equity columns = those starting with any of the equity_prefixes
    eq_cols = [c for c in df.columns if any(c.startswith(p) for p in equity_prefixes)]
    macro_cols = [c for c in df.columns if c not in eq_cols]
    corr = df.corr()
    for eq in eq_cols:
        top = corr[eq].loc[macro_cols].abs().sort_values(ascending=False).head(top_n)
        print(f"\nTop {top_n} macro correlates for {eq}:")
        print(top)

# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def main():
    # 1) Load raw data
    df_raw = load_all_csvs(DATA_DIR, CSV_PATTERN)
    print(f"Loaded {df_raw.shape[1]} series from '{DATA_DIR}'")
    print("Series names:", list(df_raw.columns))
    # 2) Transform
    df = transform_data(df_raw)
    # 3) Summary
    print_summary(df)
    # 4) Plots
    plot_time_series(df)
    plot_correlation_matrix(df)
    # 5) Top drivers
    identify_top_macro_drivers(df)

if __name__ == "__main__":
    main()