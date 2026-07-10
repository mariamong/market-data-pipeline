import os
import time
import requests
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

TICKERS = ["AAPL", "MSFT", "GOOGL", "JPM", "GS"]

def fetch_daily_prices(ticker):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker,
        "outputsize": "compact",
        "apikey": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()

    if "Time Series (Daily)" not in data:
        print(f"Error fetching {ticker}: {data.get('Note') or data.get('Information') or 'Unknown error'}")
        return None

    rows = []
    for date_str, values in data["Time Series (Daily)"].items():
        rows.append({
            "ticker": ticker,
            "date": date_str,
            "open": float(values["1. open"]),
            "high": float(values["2. high"]),
            "low": float(values["3. low"]),
            "close": float(values["4. close"]),
            "volume": int(values["5. volume"]),
            "source": "alphavantage"
        })

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    print(f"Date range from API: {df['date'].min()} to {df['date'].max()}")
    df = df[(df["date"] >= pd.Timestamp("2026-02-01").date()) &
            (df["date"] <= pd.Timestamp("2026-07-07").date())]
    return df

def ingest_prices():
    for ticker in TICKERS:
        print(f"Fetching {ticker} from Alpha Vantage...")
        df = fetch_daily_prices(ticker)
        if df is None:
            continue

        with engine.connect() as conn:
            for _, row in df.iterrows():
                conn.execute(text("""
                    INSERT INTO raw_prices (ticker, date, open, high, low, close, volume, source)
                    VALUES (:ticker, :date, :open, :high, :low, :close, :volume, :source)
                    ON CONFLICT (ticker, date, source) DO NOTHING
                """), row.to_dict())
            conn.commit()
        print(f"Inserted {len(df)} rows for {ticker}")

        time.sleep(60)

if __name__ == "__main__":
    ingest_prices()