# Almu Trades

A market analysis and dashboard tool for day trading: live/historical price
charts with technical indicators, a watchlist, and a simple signal screener.
Read-only analysis — no order execution or broker connection.

## Features

- **Chart** — candlestick price chart per ticker with SMA/EMA overlays,
  Bollinger Bands, RSI, and MACD.
- **Watchlist** — manage a list of tickers and see last price, % change, and
  volume at a glance.
- **Screener** — scans your watchlist and flags tickers as Oversold /
  Overbought (RSI) or on a Volume Spike, relative to trailing average volume.

Price data comes from Yahoo Finance via [`yfinance`](https://pypi.org/project/yfinance/).

## Project layout

```text
almu-trades/
├── app.py               # Streamlit UI (Chart / Watchlist / Screener pages)
├── src/
│   ├── data.py           # yfinance-backed data fetching, cached
│   ├── indicators.py      # SMA, EMA, RSI, MACD, Bollinger Bands (pure pandas)
│   └── screener.py        # Watchlist scan against simple RSI/volume rules
├── tests/
│   └── test_indicators.py # Unit tests for the indicator math (no network)
└── requirements.txt
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (defaults to http://localhost:8501).

## Tests

```bash
pytest tests/ -q
```

## Roadmap

- [ ] Configurable screener criteria presets
- [ ] Persist watchlist across sessions (currently in-memory per session)
- [ ] Sector/market breadth view
- [ ] Backtest a simple strategy against historical data
