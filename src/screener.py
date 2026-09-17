"""Scan a watchlist of tickers against simple technical criteria."""

import pandas as pd

from src.data import fetch_price_history
from src.indicators import rsi, sma, volume_spike_ratio


def screen(
    tickers: list[str],
    rsi_oversold: float = 30.0,
    rsi_overbought: float = 70.0,
    volume_spike_threshold: float = 1.5,
) -> pd.DataFrame:
    """For each ticker, compute the latest RSI, trend vs. its 50-day SMA, and
    volume spike ratio, then flag it as Oversold / Overbought / Volume Spike
    / Neutral. Tickers with insufficient history are skipped.
    """
    rows = []
    for ticker in tickers:
        hist = fetch_price_history(ticker, period="6mo", interval="1d")
        if hist.empty or len(hist) < 50:
            continue

        close = hist["Close"]
        latest_rsi = rsi(close).iloc[-1]
        latest_sma50 = sma(close, 50).iloc[-1]
        latest_close = close.iloc[-1]
        latest_spike = volume_spike_ratio(hist["Volume"]).iloc[-1]

        signals = []
        if pd.notna(latest_rsi):
            if latest_rsi <= rsi_oversold:
                signals.append("Oversold")
            elif latest_rsi >= rsi_overbought:
                signals.append("Overbought")
        if pd.notna(latest_spike) and latest_spike >= volume_spike_threshold:
            signals.append("Volume Spike")

        rows.append(
            {
                "Ticker": ticker,
                "Price": round(latest_close, 2),
                "RSI": round(latest_rsi, 1) if pd.notna(latest_rsi) else None,
                "Trend": "Above SMA50" if latest_close >= latest_sma50 else "Below SMA50",
                "Volume Spike x": round(latest_spike, 2) if pd.notna(latest_spike) else None,
                "Signals": ", ".join(signals) if signals else "Neutral",
            }
        )

    return pd.DataFrame(rows)
