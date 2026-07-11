# market data pipeline

An end to end ETL pipeline that ingests daily market price data from multiple 
sources, validates data quality, and surfaces metrics via a Streamlit dashboard.

## Architecture

- **Ingestion**: Pulls OHLCV price data for 5 tickers from yfinance and Alpha 
  Vantage into a normalized PostgreSQL schema
- **Validation**: Checks for nulls, invalid price ranges, high/low inversions, 
  and cross source price discrepancies (>2% threshold)
- **Audit logging**: Failed records are logged to a quarantine table with 
  structured error reasons rather than silently dropped
- **Dashboard**: Streamlit app showing data quality metrics, source coverage, 
  and an interactive price explorer

## Schema Design Decisions

Three tables separate reference, transactional, and audit data:
- `companies` — static metadata, inserted once
- `raw_prices` — daily OHLCV records tagged by source, with a 
  UNIQUE(ticker, date, source) constraint to enable cross-source comparison 
  while preventing duplicate ingestion
- `validation_log` — audit trail of rejected records with structured reasons

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env  # add your DATABASE_URL and ALPHA_VANTAGE_API_KEY

# Create database schema
psql market_data -f schema.sql

# Run full pipeline
python3 pipeline.py

# Launch dashboard
streamlit run dashboard.py
```

## Tech Stack
Python, PostgreSQL, SQLAlchemy, pandas, yfinance, Alpha Vantage API, Streamlit