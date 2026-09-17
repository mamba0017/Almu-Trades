import os
import time

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.data import fetch_price_history, fetch_quotes
from src.indicators import bollinger_bands, ema, macd, rsi, sma
from src.portfolio import build_positions_df, portfolio_summary
from src.screener import screen
from src.t212_client import Trading212Client, Trading212Error

st.set_page_config(page_title="Almu Trades", layout="wide")

DEFAULT_WATCHLIST = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "SPY"]

if "watchlist" not in st.session_state:
    st.session_state.watchlist = DEFAULT_WATCHLIST.copy()

st.sidebar.title("Almu Trades")
page = st.sidebar.radio("View", ["Chart", "Watchlist", "Screener", "Portfolio"])

st.sidebar.divider()
st.sidebar.subheader("Watchlist")
new_ticker = st.sidebar.text_input("Add ticker", placeholder="e.g. AAPL").strip().upper()
if st.sidebar.button("Add") and new_ticker:
    if new_ticker not in st.session_state.watchlist:
        st.session_state.watchlist.append(new_ticker)
remove_ticker = st.sidebar.selectbox(
    "Remove ticker", ["-"] + st.session_state.watchlist
)
if st.sidebar.button("Remove") and remove_ticker != "-":
    st.session_state.watchlist.remove(remove_ticker)


def get_t212_client():
    """Build a Trading212 client from Streamlit secrets, falling back to the
    T212_API_KEY / T212_MODE environment variables. Returns None if no key
    is configured anywhere.
    """
    api_key = None
    mode = "live"
    try:
        api_key = st.secrets.get("T212_API_KEY")
        mode = st.secrets.get("T212_MODE", mode)
    except Exception:
        pass
    api_key = api_key or os.environ.get("T212_API_KEY")
    mode = os.environ.get("T212_MODE", mode)
    if not api_key:
        return None
    return Trading212Client(api_key=api_key, mode=mode)


def cached_fetch(key: str, ttl_seconds: float, fetch_fn):
    """Lightweight per-session cache so we don't hammer Trading212's tight
    per-endpoint rate limits on every Streamlit rerun.
    """
    cache = st.session_state.setdefault("_t212_cache", {})
    entry = cache.get(key)
    now = time.time()
    if entry and now - entry["ts"] < ttl_seconds:
        return entry["value"]
    value = fetch_fn()
    cache[key] = {"ts": now, "value": value}
    return value


def render_chart():
    st.header("Price Chart & Indicators")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        ticker = st.selectbox("Ticker", st.session_state.watchlist)
    with col2:
        period = st.selectbox(
            "Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=2
        )
    with col3:
        interval = st.selectbox("Interval", ["1d", "1wk"], index=0)

    show_sma = st.checkbox("SMA 20 / 50", value=True)
    show_ema = st.checkbox("EMA 12 / 26", value=False)
    show_bbands = st.checkbox("Bollinger Bands (20, 2)", value=False)

    df = fetch_price_history(ticker, period=period, interval=interval)
    if df.empty:
        st.warning(f"No data found for '{ticker}'.")
        return

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.55, 0.2, 0.25],
        vertical_spacing=0.03,
        subplot_titles=(ticker, "RSI (14)", "MACD"),
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name=ticker,
        ),
        row=1,
        col=1,
    )

    if show_sma:
        fig.add_trace(
            go.Scatter(x=df.index, y=sma(df["Close"], 20), name="SMA 20", line=dict(width=1)),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=sma(df["Close"], 50), name="SMA 50", line=dict(width=1)),
            row=1,
            col=1,
        )

    if show_ema:
        fig.add_trace(
            go.Scatter(x=df.index, y=ema(df["Close"], 12), name="EMA 12", line=dict(width=1, dash="dot")),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=ema(df["Close"], 26), name="EMA 26", line=dict(width=1, dash="dot")),
            row=1,
            col=1,
        )

    if show_bbands:
        bb = bollinger_bands(df["Close"])
        for col_name, label in [("upper", "BB Upper"), ("mid", "BB Mid"), ("lower", "BB Lower")]:
            fig.add_trace(
                go.Scatter(x=df.index, y=bb[col_name], name=label, line=dict(width=1, dash="dash")),
                row=1,
                col=1,
            )

    rsi_series = rsi(df["Close"])
    fig.add_trace(go.Scatter(x=df.index, y=rsi_series, name="RSI"), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)

    macd_df = macd(df["Close"])
    fig.add_trace(go.Scatter(x=df.index, y=macd_df["macd"], name="MACD"), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=macd_df["signal"], name="Signal"), row=3, col=1)
    fig.add_trace(
        go.Bar(x=df.index, y=macd_df["histogram"], name="Histogram", opacity=0.5),
        row=3,
        col=1,
    )

    fig.update_layout(height=850, xaxis_rangeslider_visible=False, legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)


def render_watchlist():
    st.header("Watchlist")
    if not st.session_state.watchlist:
        st.info("Your watchlist is empty. Add a ticker from the sidebar.")
        return
    quotes = fetch_quotes(st.session_state.watchlist)
    if quotes.empty:
        st.warning("Could not fetch quotes for your watchlist.")
        return
    st.dataframe(
        quotes.style.map(
            lambda v: "color: green" if isinstance(v, (int, float)) and v > 0
            else ("color: red" if isinstance(v, (int, float)) and v < 0 else ""),
            subset=["Change %"],
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_screener():
    st.header("Screener")
    st.caption("Flags tickers on your watchlist as oversold/overbought (RSI) or on a volume spike.")

    col1, col2, col3 = st.columns(3)
    with col1:
        rsi_oversold = st.slider("RSI oversold threshold", 0, 50, 30)
    with col2:
        rsi_overbought = st.slider("RSI overbought threshold", 50, 100, 70)
    with col3:
        vol_threshold = st.slider("Volume spike (x avg)", 1.0, 5.0, 1.5, step=0.1)

    if not st.session_state.watchlist:
        st.info("Your watchlist is empty. Add a ticker from the sidebar.")
        return

    with st.spinner("Scanning watchlist..."):
        results = screen(
            st.session_state.watchlist,
            rsi_oversold=rsi_oversold,
            rsi_overbought=rsi_overbought,
            volume_spike_threshold=vol_threshold,
        )
    if results.empty:
        st.warning("No results — tickers may lack enough history yet.")
        return
    st.dataframe(results, use_container_width=True, hide_index=True)


def render_portfolio():
    st.header("Portfolio (Trading212)")

    client = get_t212_client()
    if client is None:
        st.info(
            "No Trading212 API key configured. Copy "
            "`.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and add "
            "your key (or set the `T212_API_KEY` environment variable), then restart "
            "the app."
        )
        return

    if st.button("Refresh now"):
        st.session_state.pop("_t212_cache", None)

    try:
        positions = cached_fetch("portfolio", 5, client.get_portfolio)
        cash = cached_fetch("cash", 5, client.get_account_cash)
        instruments = cached_fetch("instruments", 300, client.get_instruments)
    except Trading212Error as exc:
        st.error(f"Trading212 API error: {exc}")
        return

    positions_df = build_positions_df(positions, instruments)
    summary = portfolio_summary(positions_df, cash)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total equity", f"{summary['total_equity']:.2f}")
    col2.metric("Invested", f"{summary['invested_value']:.2f}")
    col3.metric("Free cash", f"{summary['free_cash']:.2f}")
    col4.metric("Unrealized P&L", f"{summary['unrealized_pnl']:.2f}")

    if positions_df.empty:
        st.info("No open positions.")
        return

    left, right = st.columns([3, 2])
    with left:
        st.subheader("Positions")
        display_df = (
            positions_df[
                [
                    "ticker",
                    "name",
                    "quantity",
                    "averagePrice",
                    "currentPrice",
                    "marketValue",
                    "pnl",
                    "pnlPct",
                    "allocationPct",
                ]
            ]
            .rename(
                columns={
                    "ticker": "Ticker",
                    "name": "Name",
                    "quantity": "Qty",
                    "averagePrice": "Avg Price",
                    "currentPrice": "Price",
                    "marketValue": "Value",
                    "pnl": "P&L",
                    "pnlPct": "P&L %",
                    "allocationPct": "Allocation %",
                }
            )
            .round(2)
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    with right:
        st.subheader("Allocation")
        fig = px.pie(positions_df, names="name", values="marketValue", hole=0.4)
        fig.update_layout(showlegend=False)
        fig.update_traces(textinfo="label+percent")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("P&L by position")
    pnl_fig = px.bar(
        positions_df.sort_values("pnl"),
        x="pnl",
        y="name",
        orientation="h",
        color="pnl",
        color_continuous_scale=["red", "gray", "green"],
        color_continuous_midpoint=0,
    )
    pnl_fig.update_layout(
        showlegend=False, coloraxis_showscale=False, yaxis_title="", xaxis_title="P&L"
    )
    st.plotly_chart(pnl_fig, use_container_width=True)

    if st.checkbox("Add portfolio tickers to watchlist"):
        added = 0
        for yahoo_ticker in positions_df["yahooTicker"]:
            if yahoo_ticker not in st.session_state.watchlist:
                st.session_state.watchlist.append(yahoo_ticker)
                added += 1
        st.success(f"Added {added} new ticker(s) to your watchlist.")


if page == "Chart":
    render_chart()
elif page == "Watchlist":
    render_watchlist()
elif page == "Screener":
    render_screener()
else:
    render_portfolio()
