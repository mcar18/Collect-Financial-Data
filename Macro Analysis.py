#!/usr/bin/env python3
"""
macro_analysis.py

Load FRED CSVs from a folder, compute year‑over‑year % changes on a monthly basis
(or YoY changes in basis points for selected rate series), print summary statistics,
plot time series and correlations (blue = +1, red = –1), print the correlation
matrix to the console, and identify the top macro drivers for each equity index.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from functools import reduce

# ----------------------------------------------------------------------
# SETTINGS
# ----------------------------------------------------------------------
DATA_DIR       = Path("C:/Users/Owner/OneDrive/Documents/FSU Graduate School/Python Code/Collect-Financial-Data/data/fred")  # ← update to your actual CSV folder
CSV_PATTERN    = "*.csv"
RESAMPLE_FREQ  = "M"               # monthly frequency

# Treat these series’ YoY change as basis‑points (diff ×100) instead of percent‑change:
RATE_SERIES = {
    "Fed_Funds_Rate",
    "Fed_Funds_Rate_Daily",
    "Fed_Funds_Rate_Monthly",
    "Fed_Funds_Rate_Weekly",
    "TenY_Treasury",
    "Unemployment_Rate",
}

# How to detect equity series by filename prefixes:
EQUITY_PREFIXES = ["S&P", "Dow_Jones", "NASDAQ"]
TOP_N_DRIVERS   = 5                # how many top macro correlates to show

# ----------------------------------------------------------------------
# 1. LOAD & MERGE ALL CSVs
# ----------------------------------------------------------------------
def load_all_csvs(folder: Path, pattern: str = "*.csv") -> pd.DataFrame:
    files = sorted(folder.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files found in {folder} matching {pattern}")
    dfs = []
    for f in files:
        # first column = date index, second column = values
        df = pd.read_csv(f, index_col=0, parse_dates=True)
        df.columns = [f.stem]  # name column after filename (without .csv)
        dfs.append(df)
    return reduce(lambda a, b: a.join(b, how="outer"), dfs)

# ----------------------------------------------------------------------
# 2. TRANSFORM: YEAR‑OVER‑YEAR % CHANGE / BPS (MONTHLY)
# ----------------------------------------------------------------------
def transform_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    # Resample to month‑end, take last obs
    df_monthly = df_raw.resample(RESAMPLE_FREQ).last()
    # Forward‑fill gaps
    df_ff = df_monthly.ffill()

    transformed = {}
    for col in df_ff.columns:
        if col in RATE_SERIES:
            # difference in %-points ×100 → basis points
            transformed[f"{col}_yoy_bps"] = df_ff[col].diff(12) * 100
        else:
            # percent change ×100 → % change
            transformed[f"{col}_yoy_pct"] = df_ff[col].pct_change(12) * 100

    df_trans = pd.DataFrame(transformed, index=df_ff.index)
    return df_trans.dropna(how="all")

# ----------------------------------------------------------------------
# 3. PRINT SUMMARY STATISTICS
# ----------------------------------------------------------------------
def print_summary(df: pd.DataFrame):
    print("\n=== Descriptive Statistics ===")
    print(df.describe().T)

# ----------------------------------------------------------------------
# 4. PLOT TIME SERIES
# ----------------------------------------------------------------------
def plot_time_series(df: pd.DataFrame):
    for col in df.columns:
        plt.figure(figsize=(10, 3))
        plt.plot(df.index, df[col], label=col)
        plt.title(col)
        if col.endswith("_yoy_bps"):
            plt.ylabel("YoY Change (bps)")
        else:
            plt.ylabel("YoY Change (%)")
        plt.tight_layout()
        plt.show()

# ----------------------------------------------------------------------
# 5. CORRELATION MATRIX
# ----------------------------------------------------------------------
def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    return df.corr()

def plot_correlation_matrix(df: pd.DataFrame):
    corr = df.corr()
    plt.figure(figsize=(12, 10))
    im = plt.imshow(
        corr.values,
        aspect="auto",
        interpolation="none",
        cmap="bwr_r",  # +1 → blue, -1 → red
        vmin=-1,
        vmax=1
    )
    plt.colorbar(im, label="Correlation")
    plt.xticks(np.arange(len(corr)), corr.columns, rotation=90)
    plt.yticks(np.arange(len(corr)), corr.columns)
    plt.title("Correlation Matrix")
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

    # 4) Print and plot correlation matrix
    corr = correlation_matrix(df)
    print("\n=== Correlation Matrix ===")
    print(corr)
    plot_correlation_matrix(df)

    # 5) Time series plots
    plot_time_series(df)

    # 6) Top macro drivers
    identify_top_macro_drivers(df)

if __name__ == "__main__":
    main()