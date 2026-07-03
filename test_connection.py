import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

db_url = os.getenv("DATABASE_URL")

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        print("Connected successfully!")
        print(result.fetchone()[0])
except Exception as e:
    print(f"Connection failed: {e}")