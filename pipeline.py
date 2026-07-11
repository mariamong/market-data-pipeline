import os
from dotenv import load_dotenv

load_dotenv()

from ingest_prices import ingest_companies, ingest_prices as ingest_yfinance
from ingest_alphavantage import ingest_prices as ingest_av
from validate import run_validations

def run_pipeline():
    print("=" * 50)
    print("STEP 1: Ingesting company metadata")
    print("=" * 50)
    ingest_companies()

    print("\n" + "=" * 50)
    print("STEP 2: Ingesting yfinance prices")
    print("=" * 50)
    ingest_yfinance()

    print("\n" + "=" * 50)
    print("STEP 3: Ingesting Alpha Vantage prices")
    print("=" * 50)
    ingest_av()

    print("\n" + "=" * 50)
    print("STEP 4: Running validations")
    print("=" * 50)
    run_validations()

    print("\n" + "=" * 50)
    print("Pipeline complete.")
    print("=" * 50)

if __name__ == "__main__":
    run_pipeline()