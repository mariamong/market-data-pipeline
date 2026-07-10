import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

# ── 1. Load data ──────────────────────────────────────────────────────────────

def load_raw_prices():
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM raw_prices", conn)
    return df

# ── 2. Validation functions ───────────────────────────────────────────────────

def check_nulls(df):
    """Flag rows with nulls in required fields."""
    required = ["ticker", "date", "open", "high", "low", "close", "volume"]
    issues = []
    for _, row in df[df[required].isnull().any(axis=1)].iterrows():
        issues.append({
            "ticker": row["ticker"],
            "date": row["date"],
            "source": row["source"],
            "issue_type": "null_value",
            "description": f"Null found in one or more required fields"
        })
    return issues

def check_price_ranges(df):
    """Flag rows where prices or volume are negative or zero."""
    issues = []
    invalid = df[(df["close"] <= 0) | (df["open"] <= 0) |
                 (df["high"] <= 0) | (df["low"] <= 0) | (df["volume"] < 0)]
    for _, row in invalid.iterrows():
        issues.append({
            "ticker": row["ticker"],
            "date": row["date"],
            "source": row["source"],
            "issue_type": "invalid_price_range",
            "description": f"One or more price/volume fields are <= 0: close={row['close']}"
        })
    return issues

def check_high_low(df):
    """Flag rows where high < low (logically impossible)."""
    issues = []
    invalid = df[df["high"] < df["low"]]
    for _, row in invalid.iterrows():
        issues.append({
            "ticker": row["ticker"],
            "date": row["date"],
            "source": row["source"],
            "issue_type": "high_low_inversion",
            "description": f"High ({row['high']}) is less than low ({row['low']})"
        })
    return issues

def check_cross_source(df, threshold=0.02):
    """Flag dates where yfinance and alphavantage close prices differ by more than threshold."""
    issues = []
    yf = df[df["source"] == "yfinance"][["ticker", "date", "close"]].rename(columns={"close": "close_yf"})
    av = df[df["source"] == "alphavantage"][["ticker", "date", "close"]].rename(columns={"close": "close_av"})
    merged = yf.merge(av, on=["ticker", "date"])
    merged["pct_diff"] = abs(merged["close_yf"] - merged["close_av"]) / merged["close_yf"]
    flagged = merged[merged["pct_diff"] > threshold]
    for _, row in flagged.iterrows():
        issues.append({
            "ticker": row["ticker"],
            "date": row["date"],
            "source": "cross_source",
            "issue_type": "price_discrepancy",
            "description": f"yfinance close={row['close_yf']:.2f} vs alphavantage close={row['close_av']:.2f} ({row['pct_diff']*100:.2f}% difference)"
        })
    return issues

# ── 3. Log issues to validation_log ──────────────────────────────────────────

def log_issues(issues):
    if not issues:
        print("No issues found.")
        return
    with engine.connect() as conn:
        for issue in issues:
            conn.execute(text("""
                INSERT INTO validation_log (ticker, date, source, issue_type, description)
                VALUES (:ticker, :date, :source, :issue_type, :description)
            """), issue)
        conn.commit()
    print(f"Logged {len(issues)} issues to validation_log")

# ── 4. Run all validations ────────────────────────────────────────────────────

def run_validations():
    print("Loading raw prices...")
    df = load_raw_prices()
    print(f"Loaded {len(df)} rows")

    all_issues = []
    all_issues += check_nulls(df)
    all_issues += check_price_ranges(df)
    all_issues += check_high_low(df)
    all_issues += check_cross_source(df)

    print(f"\nValidation summary:")
    print(f"  Null checks:          {len(check_nulls(df))} issues")
    print(f"  Price range checks:   {len(check_price_ranges(df))} issues")
    print(f"  High/low checks:      {len(check_high_low(df))} issues")
    print(f"  Cross-source checks:  {len(check_cross_source(df))} issues")
    print(f"  Total:                {len(all_issues)} issues")

    log_issues(all_issues)

if __name__ == "__main__":
    run_validations()