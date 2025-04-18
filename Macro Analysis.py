#!/usr/bin/env python3
"""
macro_analysis.py

Load FRED CSVs from a folder, compute year‑over‑year % changes on a monthly basis
(or YoY changes in basis points for selected rate series), print summary statistics,
plot time series and correlations (blue = +1, red = –1), and identify
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

# Series for which we compute YoY change in bps instead of %:
RATE_SERIES = {
    "Fed_Funds_Rate_Daily",
    "Fed_Funds_Rate_Monthly",
    "TenY_Treasury",
    "Unemployment_Rate",
}

# How we detect equity series by their filename prefixes:
EQUITY_PREFIXES = ["S&P", "Dow_Jones", "NASDAQ"]
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
        # Read CSV: first column = date (index), second column = series values
        df = pd.read_csv(f, index_col=0, parse_dates=True)
        df.columns = [f.stem]  # rename column to the filename stem
        dfs.append(df)
    # Outer‑join all on the datetime index
    return reduce(lambda a, b: a.join(b, how="outer"), dfs)

# ----------------------------------------------------------------------
# 2. TRANSFORM: YEAR‑OVER‑YEAR % CHANGE / BPS (MONTHLY)
# ----------------------------------------------------------------------
def transform_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    # 2.1 Resample to month‑end, take last obs
    df_m = df_raw.resample(RESAMPLE_FREQ).last()
    # 2.2 Forward‑fill gaps
    df_ff = df_m.ffill()
    # 2.3 Compute YoY transforms
    trans = {}
    for col in df_ff.columns:
        if col in RATE_SERIES:
            # diff in %-points ×100 → basis points
            trans[f"{col}_yoy_bps"] = df_ff[col].diff(12) * 100
        else:
            # percent change ×100 → % change
            trans[f"{col}_yoy_pct"] = df_ff[col].pct_change(12) * 100
    df_trans = pd.DataFrame(trans, index=df_ff.index)
    # drop the initial 12 rows (all‑NaN)
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
        plt.ylabel("YoY % Change" if col.endswith("_pct") else "YoY bps")
        plt.tight_layout()
        plt.show()

# ----------------------------------------------------------------------
# 5. PLOT CORRELATION MATRIX
# ----------------------------------------------------------------------
def plot_correlation_matrix(df: pd.DataFrame):
    corr = df.corr()
    plt.figure(figsize=(12, 10))
    im = plt.imshow(
        corr.values,
        aspect="auto",
        interpolation="none",
        cmap="bwr_r",   # reversed blue-white-red: +1→blue, –1→red
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
    df_raw = load_all_csvs(DATA_DIR, CSV_PATTERN)
    print(f"Loaded {df_raw.shape[1]} series from '{DATA_DIR}'")
    print("Series names:", list(df_raw.columns))

    df = transform_data(df_raw)
    print_summary(df)
    plot_time_series(df)
    plot_correlation_matrix(df)
    identify_top_macro_drivers(df)

if __name__ == "__main__":
    main()