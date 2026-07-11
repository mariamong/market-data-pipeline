import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
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
st.dataframe(coverage, use_container_width=True)

st.divider()

# ── Validation log ────────────────────────────────────────────────────────────

st.subheader("Validation Issues")
if len(validation) == 0:
    st.success("No validation issues found in current data.")
else:
    issue_counts = validation.groupby("issue_type").size().reset_index(name="count")
    st.bar_chart(issue_counts.set_index("issue_type"))
    st.dataframe(validation, use_container_width=True)

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
    st.dataframe(filtered, use_container_width=True)