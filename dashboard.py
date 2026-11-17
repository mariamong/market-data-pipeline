import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

st.set_page_config(page_title="Market Data Pipeline", layout="wide")
st.title("Market Data Pipeline — Quality Dashboard")

# ── Load data ─────────────────────────────────────────────────────────────────

@st.cache_data
def load_prices():
    with engine.connect() as conn:
        return pd.read_sql("SELECT * FROM raw_prices", conn)

@st.cache_data
def load_validation_log():
    with engine.connect() as conn:
        return pd.read_sql("SELECT * FROM validation_log", conn)

@st.cache_data
def load_companies():
    with engine.connect() as conn:
        return pd.read_sql("SELECT * FROM companies", conn)

@st.cache_data
def load_comparison():
    query = text("""
        SELECT y.ticker, y.date,
               y.close::float AS yfinance_close,
               a.close::float AS alphavantage_close,
               (ABS(y.close - a.close) / y.close * 100)::float AS gap_pct
        FROM raw_prices y
        JOIN raw_prices a ON y.ticker = a.ticker AND y.date = a.date
        WHERE y.source = 'yfinance' AND a.source = 'alphavantage'
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn)

prices = load_prices()
validation = load_validation_log()
companies = load_companies()

# ── Summary metrics ───────────────────────────────────────────────────────────

st.subheader("Pipeline Summary")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Records", len(prices))
col2.metric("Tickers Tracked", prices["ticker"].nunique())
col3.metric("Data Sources", prices["source"].nunique())
col4.metric("Validation Issues", len(validation))

st.divider()

# ── Records per source ────────────────────────────────────────────────────────

st.subheader("Records by Source")
source_counts = prices.groupby("source").size().reset_index(name="count")
st.bar_chart(source_counts.set_index("source"))

st.divider()

# ── Date coverage per source ──────────────────────────────────────────────────

st.subheader("Date Coverage by Source")
coverage = prices.groupby("source").agg(
    earliest=("date", "min"),
    latest=("date", "max"),
    total_records=("date", "count")
).reset_index()
st.dataframe(coverage, width='stretch')

st.divider()

# ── Validation log ────────────────────────────────────────────────────────────

st.subheader("Validation Issues")
if len(validation) == 0:
    st.success("No validation issues found in current data.")
else:
    issue_counts = validation.groupby("issue_type").size().reset_index(name="count")
    st.bar_chart(issue_counts.set_index("issue_type"))
    st.dataframe(validation, width='stretch')

st.divider()

# ── Source comparison ─────────────────────────────────────────────────────────

st.subheader("Source Comparison")
threshold = st.slider("Flag close-price gaps above (%)", 0.1, 2.0, 2.0, 0.1)

comparison = load_comparison()
flagged = comparison[comparison["gap_pct"] > threshold]

c1, c2, c3 = st.columns(3)
c1.metric("Days compared", len(comparison))
c2.metric("Largest gap (%)", f"{comparison['gap_pct'].max():.2f}")
c3.metric("Flagged at threshold", len(flagged))
st.dataframe(flagged.sort_values("gap_pct", ascending=False), width='stretch')

st.divider()

# ── Price explorer ────────────────────────────────────────────────────────────

st.subheader("Price Explorer")
ticker = st.selectbox("Select ticker", sorted(prices["ticker"].unique()))
source = st.selectbox("Select source", sorted(prices["source"].unique()))

filtered = prices[(prices["ticker"] == ticker) & (prices["source"] == source)].sort_values("date")

if len(filtered) == 0:
    st.warning("No data for this combination.")
else:
    st.line_chart(filtered.set_index("date")[["close", "high", "low"]])
    st.dataframe(filtered, width='stretch')