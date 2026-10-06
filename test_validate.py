"""
Tests for the validation checks in validate.py.

Each check is run against small, hand built DataFrames containing known bad
records, so the tests prove the rules fire on bad data and stay quiet on
clean data. No database connection is needed: the check functions only
operate on DataFrames.

Run with either:
    python3 test_validate.py
    pytest test_validate.py -v
"""

import pandas as pd

from validate import (
    check_nulls,
    check_price_ranges,
    check_high_low,
    check_cross_source,
)


def make_row(ticker="AAPL", date="2026-03-01", source="test",
             open_=100.0, high=105.0, low=95.0, close=102.0, volume=1_000_000):
    return {
        "ticker": ticker,
        "date": date,
        "source": source,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }


def make_df(*rows):
    return pd.DataFrame(list(rows))


# ── Row-level checks ─────────────────────────────────────────────────────────

def test_clean_row_passes_all_checks():
    df = make_df(make_row())
    assert check_nulls(df) == []
    assert check_price_ranges(df) == []
    assert check_high_low(df) == []


def test_null_value_is_flagged():
    df = make_df(make_row(ticker="GOOGL", close=None))
    issues = check_nulls(df)
    assert len(issues) == 1
    assert issues[0]["ticker"] == "GOOGL"
    assert issues[0]["issue_type"] == "null_value"


def test_negative_price_is_flagged():
    df = make_df(make_row(ticker="AAPL", close=-50.0))
    issues = check_price_ranges(df)
    assert len(issues) == 1
    assert issues[0]["ticker"] == "AAPL"
    assert issues[0]["issue_type"] == "invalid_price_range"


def test_zero_price_is_flagged():
    df = make_df(make_row(open_=0.0))
    assert len(check_price_ranges(df)) == 1


def test_negative_volume_is_flagged():
    df = make_df(make_row(volume=-10))
    assert len(check_price_ranges(df)) == 1


def test_zero_volume_is_allowed():
    df = make_df(make_row(volume=0))
    assert check_price_ranges(df) == []


def test_high_below_low_is_flagged():
    df = make_df(make_row(ticker="MSFT", high=390.0, low=410.0))
    issues = check_high_low(df)
    assert len(issues) == 1
    assert issues[0]["ticker"] == "MSFT"
    assert issues[0]["issue_type"] == "high_low_inversion"


def test_only_bad_rows_are_flagged_in_mixed_data():
    df = make_df(
        make_row(ticker="AAPL"),
        make_row(ticker="MSFT", high=390.0, low=410.0),
        make_row(ticker="GOOGL"),
    )
    issues = check_high_low(df)
    assert [i["ticker"] for i in issues] == ["MSFT"]


# ── Cross-source reconciliation ──────────────────────────────────────────────

def cross_source_df(yf_close, av_close):
    return make_df(
        make_row(source="yfinance", close=yf_close),
        make_row(source="alphavantage", close=av_close),
    )


def test_cross_source_flags_difference_above_threshold():
    # 3% difference, default threshold is 2%
    issues = check_cross_source(cross_source_df(100.0, 103.0))
    assert len(issues) == 1
    assert issues[0]["issue_type"] == "price_discrepancy"
    assert issues[0]["source"] == "cross_source"


def test_cross_source_ignores_difference_below_threshold():
    # 1% difference is within the default 2% threshold
    assert check_cross_source(cross_source_df(100.0, 101.0)) == []


def test_cross_source_threshold_is_configurable():
    # The same 1% difference is flagged once the threshold is tightened
    issues = check_cross_source(cross_source_df(100.0, 101.0), threshold=0.005)
    assert len(issues) == 1


def test_cross_source_ignores_unmatched_dates():
    # Same ticker, different dates: nothing to compare, so nothing flagged
    df = make_df(
        make_row(source="yfinance", date="2026-03-01", close=100.0),
        make_row(source="alphavantage", date="2026-03-02", close=150.0),
    )
    assert check_cross_source(df) == []


# ── Simple runner so `python3 test_validate.py` works without pytest ─────────

if __name__ == "__main__":
    tests = [(name, fn) for name, fn in sorted(globals().items())
             if name.startswith("test_") and callable(fn)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError:
            failed += 1
            print(f"FAIL  {name}")
    print(f"\n{len(tests) - failed}/{len(tests)} tests passed")
    raise SystemExit(1 if failed else 0)