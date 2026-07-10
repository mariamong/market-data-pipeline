import os
import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

TICKERS = ["AAPL", "MSFT", "GOOGL", "JPM", "GS"]

def ingest_companies():
    rows = []
    for ticker in TICKERS:
        info = yf.Ticker(ticker).info
        rows.append({
            "ticker": ticker,
            "name": info.get("longName"),
            "sector": info.get("sector"),
            "industry": info.get("industry")
        })
    df = pd.DataFrame(rows)
    
    with engine.connect() as conn:
        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO companies (ticker, name, sector, industry)
                VALUES (:ticker, :name, :sector, :industry)
                ON CONFLICT (ticker) DO NOTHING
            """), row.to_dict())
        conn.commit()
    print(f"Processed {len(df)} companies")

def ingest_prices():
    for ticker in TICKERS:
        df = yf.download(ticker, start="2026-02-01", end="2026-07-07", auto_adjust=True)
        df = df.reset_index()
        df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]
        df = df.rename(columns={"date": "date"})
        df["ticker"] = ticker
        df["source"] = "yfinance"
        df = df[["ticker", "date", "open", "high", "low", "close", "volume", "source"]]
        df.to_sql("raw_prices", engine, if_exists="append", index=False, method="multi")
        print(f"Inserted {len(df)} rows for {ticker}")

if __name__ == "__main__":
    ingest_companies()
    ingest_prices()