"""Market data access, backed by yfinance. Every public function is a thin,
cacheable wrapper so the Streamlit app can call it directly.
"""

import pandas as pd
import streamlit as st
import yfinance as yf


@st.cache_data(ttl=300, show_spinner=False)
def fetch_price_history(
    ticker: str, period: str = "6mo", interval: str = "1d"
) -> pd.DataFrame:
    """OHLCV history for a single ticker. Empty DataFrame if the ticker is
    invalid or no data is available for the requested range.
    """
    df = yf.Ticker(ticker).history(period=period, interval=interval)
    if df.empty:
        return df
    df.index.name = "Date"
    return df[["Open", "High", "Low", "Close", "Volume"]]


@st.cache_data(ttl=300, show_spinner=False)
def fetch_quotes(tickers: list[str]) -> pd.DataFrame:
    """Latest quote snapshot (last price, prior close, % change, volume) for
    a batch of tickers, one row per ticker.
    """
    rows = []
    for ticker in tickers:
        hist = yf.Ticker(ticker).history(period="5d", interval="1d")
        if hist.empty:
            continue
        last = hist.iloc[-1]
        prior_close = hist.iloc[-2]["Close"] if len(hist) > 1 else last["Open"]
        change_pct = (last["Close"] - prior_close) / prior_close * 100
        rows.append(
            {
                "Ticker": ticker,
                "Last": round(last["Close"], 2),
                "Change %": round(change_pct, 2),
                "Volume": int(last["Volume"]),
            }
        )
    return pd.DataFrame(rows)
