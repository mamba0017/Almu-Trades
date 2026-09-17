# Almu Trades

A market analysis and dashboard tool for day trading: live/historical price
charts with technical indicators, a watchlist, a simple signal screener, and
a read-only view of your real Trading212 portfolio.
This app never places orders — it only reads data.

## Features

- **Chart** — candlestick price chart per ticker with SMA/EMA overlays,
  Bollinger Bands, RSI, and MACD.
- **Watchlist** — manage a list of tickers and see last price, % change, and
  volume at a glance.
- **Screener** — scans your watchlist and flags tickers as Oversold /
  Overbought (RSI) or on a Volume Spike, relative to trailing average volume.
- **Portfolio** — pulls your open positions, cash, and P&L from the
  [Trading212 Equity API](https://t212public-api-docs.redoc.ly/) and shows
  allocation and P&L breakdowns. Read-only: the app never places, modifies,
  or cancels orders.

Price/chart data comes from Yahoo Finance via [`yfinance`](https://pypi.org/project/yfinance/).

## Project layout

```text
almu-trades/
├── app.py                    # Streamlit UI (Chart / Watchlist / Screener / Portfolio)
├── src/
│   ├── data.py                # yfinance-backed data fetching, cached
│   ├── indicators.py           # SMA, EMA, RSI, MACD, Bollinger Bands (pure pandas)
│   ├── screener.py             # Watchlist scan against simple RSI/volume rules
│   ├── t212_client.py          # Trading212 Equity API client (auth, error handling)
│   └── portfolio.py            # Turns raw T212 positions into an analysis-ready table
├── tests/
│   ├── test_indicators.py      # Indicator math (no network)
│   ├── test_portfolio.py       # Portfolio calculations (no network)
│   └── test_t212_client.py     # T212 client against mocked HTTP responses (no network, no real key)
├── .streamlit/
│   └── secrets.toml.example    # Template for your local secrets file (safe to commit)
└── requirements.txt
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Connecting your Trading212 account

Your API key stays entirely on your machine — it's read from a local,
git-ignored file (or an environment variable) and is never committed or sent
anywhere except `api.trading212.com`.

1. In Trading212: **Settings → API (Beta)** → generate a key. A read-only
   scope is enough for this app.
2. Copy the template and fill it in:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
3. Edit `.streamlit/secrets.toml`:
   ```toml
   T212_API_KEY = "paste-your-real-key-here"
   T212_MODE = "live"   # or "demo" for a practice account
   ```

`.streamlit/secrets.toml` is already in `.gitignore` — `git status` should
never show it as a file to commit. Alternatively, skip the secrets file and
export `T212_API_KEY` (and optionally `T212_MODE`) as environment variables
before running the app.

Without a key configured, every other page (Chart/Watchlist/Screener) still
works — only the Portfolio page needs it.

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
- [ ] Historical portfolio performance (orders/dividends history from T212)
