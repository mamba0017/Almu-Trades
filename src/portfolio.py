"""Pure data transforms for Trading212 portfolio data — no network, no
Streamlit, easy to unit test. Input shapes match the Trading212 Equity API
(see t212_client.py).
"""

import pandas as pd

# Trading212 tickers look like "AAPL_US_EQ" (symbol_exchange_type). Yahoo
# Finance mostly just wants the leading symbol, so this is a best-effort
# mapping, not a guarantee — some instruments (non-US listings, certain
# ETFs) won't resolve to the same symbol on Yahoo.
def t212_ticker_to_yahoo(t212_ticker: str) -> str:
    return t212_ticker.split("_")[0]


def build_positions_df(
    positions: list[dict], instruments: list[dict] | None = None
) -> pd.DataFrame:
    """Combine raw /equity/portfolio rows with instrument metadata (for
    human-readable names) into an analysis-ready DataFrame, sorted by
    market value descending. Returns an empty DataFrame if there are no
    open positions.
    """
    df = pd.DataFrame(positions)
    if df.empty:
        return df

    df["marketValue"] = df["quantity"] * df["currentPrice"]
    df["costBasis"] = df["quantity"] * df["averagePrice"]
    df["pnl"] = df["ppl"]
    df["pnlPct"] = (df["currentPrice"] - df["averagePrice"]) / df["averagePrice"] * 100
    df["yahooTicker"] = df["ticker"].apply(t212_ticker_to_yahoo)

    if instruments:
        name_map = {i["ticker"]: i.get("name", i["ticker"]) for i in instruments}
        df["name"] = df["ticker"].map(name_map).fillna(df["ticker"])
    else:
        df["name"] = df["ticker"]

    total_value = df["marketValue"].sum()
    df["allocationPct"] = (df["marketValue"] / total_value * 100) if total_value else 0.0

    return df.sort_values("marketValue", ascending=False).reset_index(drop=True)


def portfolio_summary(positions_df: pd.DataFrame, cash: dict) -> dict:
    """Roll up headline numbers: total equity value, total cash, combined
    P&L, and how allocated (in positions) vs. free the account currently is.
    """
    invested_value = positions_df["marketValue"].sum() if not positions_df.empty else 0.0
    unrealized_pnl = positions_df["pnl"].sum() if not positions_df.empty else 0.0
    free_cash = cash.get("free", 0.0)
    total_cash = cash.get("total", 0.0)

    return {
        "invested_value": invested_value,
        "unrealized_pnl": unrealized_pnl,
        "free_cash": free_cash,
        "total_cash": total_cash,
        "total_equity": invested_value + free_cash,
        "num_positions": len(positions_df),
    }
