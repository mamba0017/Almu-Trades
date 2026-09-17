"""Technical indicators computed on a DataFrame with a 'Close' column (and
'High'/'Low'/'Volume' where needed). Each function returns a new Series or
DataFrame aligned to the input index; it never mutates the input.
"""

import pandas as pd


def sma(close: pd.Series, window: int) -> pd.Series:
    return close.rolling(window=window, min_periods=window).mean()


def ema(close: pd.Series, span: int) -> pd.Series:
    return close.ewm(span=span, adjust=False).mean()


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss
    result = 100 - (100 / (1 + rs))
    return result.where(avg_loss != 0, 100.0)


def macd(
    close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> pd.DataFrame:
    fast_ema = ema(close, fast)
    slow_ema = ema(close, slow)
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return pd.DataFrame(
        {"macd": macd_line, "signal": signal_line, "histogram": histogram}
    )


def bollinger_bands(
    close: pd.Series, window: int = 20, num_std: float = 2.0
) -> pd.DataFrame:
    mid = sma(close, window)
    std = close.rolling(window=window, min_periods=window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return pd.DataFrame({"mid": mid, "upper": upper, "lower": lower})


def volume_spike_ratio(volume: pd.Series, window: int = 20) -> pd.Series:
    """Today's volume divided by its trailing rolling average (excluding today)."""
    avg_volume = volume.shift(1).rolling(window=window, min_periods=window).mean()
    return volume / avg_volume
