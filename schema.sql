-- Companies reference table
CREATE TABLE IF NOT EXISTS companies (
    ticker          VARCHAR(10) PRIMARY KEY,
    name            VARCHAR(255),
    sector          VARCHAR(100),
    industry        VARCHAR(100),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Raw prices from ingestion (unvalidated)
CREATE TABLE IF NOT EXISTS raw_prices (
    id              SERIAL PRIMARY KEY,
    ticker          VARCHAR(10) REFERENCES companies(ticker),
    date            DATE NOT NULL,
    open            NUMERIC(12, 4),
    high            NUMERIC(12, 4),
    low             NUMERIC(12, 4),
    close           NUMERIC(12, 4),
    volume          BIGINT,
    source          VARCHAR(50) NOT NULL,
    ingested_at     TIMESTAMP DEFAULT NOW(),
    UNIQUE(ticker, date, source)
);

-- Validation log for rejected or flagged records
CREATE TABLE IF NOT EXISTS validation_log (
    id              SERIAL PRIMARY KEY,
    ticker          VARCHAR(10),
    date            DATE,
    source          VARCHAR(50),
    issue_type      VARCHAR(100) NOT NULL,
    description     TEXT,
    flagged_at      TIMESTAMP DEFAULT NOW()
);