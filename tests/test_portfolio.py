import pandas as pd
import pytest

from src.portfolio import build_positions_df, portfolio_summary, t212_ticker_to_yahoo


SAMPLE_POSITIONS = [
    {
        "ticker": "AAPL_US_EQ",
        "quantity": 10.0,
        "averagePrice": 150.0,
        "currentPrice": 180.0,
        "ppl": 300.0,
    },
    {
        "ticker": "TSLA_US_EQ",
        "quantity": 2.0,
        "averagePrice": 250.0,
        "currentPrice": 200.0,
        "ppl": -100.0,
    },
]

SAMPLE_INSTRUMENTS = [
    {"ticker": "AAPL_US_EQ", "name": "Apple Inc."},
    {"ticker": "TSLA_US_EQ", "name": "Tesla Inc."},
]


def test_t212_ticker_to_yahoo():
    assert t212_ticker_to_yahoo("AAPL_US_EQ") == "AAPL"
    assert t212_ticker_to_yahoo("MSFT_US_EQ") == "MSFT"
    assert t212_ticker_to_yahoo("VOD_LSE") == "VOD"


def test_build_positions_df_empty():
    df = build_positions_df([])
    assert df.empty


def test_build_positions_df_computes_value_and_pnl():
    df = build_positions_df(SAMPLE_POSITIONS, SAMPLE_INSTRUMENTS)

    aapl = df[df["ticker"] == "AAPL_US_EQ"].iloc[0]
    assert aapl["marketValue"] == pytest.approx(1800.0)
    assert aapl["costBasis"] == pytest.approx(1500.0)
    assert aapl["pnl"] == pytest.approx(300.0)
    assert aapl["pnlPct"] == pytest.approx(20.0)
    assert aapl["name"] == "Apple Inc."
    assert aapl["yahooTicker"] == "AAPL"

    # Sorted by market value descending: AAPL (1800) before TSLA (400)
    assert list(df["ticker"]) == ["AAPL_US_EQ", "TSLA_US_EQ"]

    total_value = 1800.0 + 400.0
    assert df.iloc[0]["allocationPct"] == pytest.approx(1800.0 / total_value * 100)


def test_build_positions_df_without_instruments_falls_back_to_ticker():
    df = build_positions_df(SAMPLE_POSITIONS)
    assert (df["name"] == df["ticker"]).all()


def test_portfolio_summary():
    df = build_positions_df(SAMPLE_POSITIONS, SAMPLE_INSTRUMENTS)
    cash = {"free": 500.0, "total": 500.0}

    summary = portfolio_summary(df, cash)

    assert summary["invested_value"] == pytest.approx(2200.0)
    assert summary["unrealized_pnl"] == pytest.approx(200.0)
    assert summary["free_cash"] == pytest.approx(500.0)
    assert summary["total_equity"] == pytest.approx(2700.0)
    assert summary["num_positions"] == 2


def test_portfolio_summary_with_no_positions():
    summary = portfolio_summary(pd.DataFrame(), {"free": 1000.0, "total": 1000.0})
    assert summary["invested_value"] == 0.0
    assert summary["unrealized_pnl"] == 0.0
    assert summary["total_equity"] == pytest.approx(1000.0)
    assert summary["num_positions"] == 0
