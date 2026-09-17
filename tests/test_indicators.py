import numpy as np
import pandas as pd
import pytest

from src.indicators import bollinger_bands, ema, macd, rsi, sma, volume_spike_ratio


@pytest.fixture
def close():
    return pd.Series([10, 11, 12, 11, 10, 9, 10, 11, 12, 13, 14, 15], dtype=float)


def test_sma_basic():
    s = pd.Series([1, 2, 3, 4, 5], dtype=float)
    result = sma(s, window=3)
    assert np.isnan(result.iloc[0])
    assert np.isnan(result.iloc[1])
    assert result.iloc[2] == pytest.approx(2.0)
    assert result.iloc[4] == pytest.approx(4.0)


def test_ema_matches_pandas_ewm(close):
    result = ema(close, span=5)
    expected = close.ewm(span=5, adjust=False).mean()
    pd.testing.assert_series_equal(result, expected)


def test_rsi_all_gains_is_100():
    rising = pd.Series(range(1, 30), dtype=float)
    result = rsi(rising, window=14)
    assert result.iloc[-1] == pytest.approx(100.0)


def test_rsi_bounded(close):
    result = rsi(close, window=5).dropna()
    assert (result >= 0).all()
    assert (result <= 100).all()


def test_macd_columns_and_alignment(close):
    result = macd(close, fast=3, slow=6, signal=2)
    assert list(result.columns) == ["macd", "signal", "histogram"]
    assert len(result) == len(close)
    pd.testing.assert_series_equal(
        result["histogram"], result["macd"] - result["signal"], check_names=False
    )


def test_bollinger_bands_ordering(close):
    result = bollinger_bands(close, window=5, num_std=2.0)
    valid = result.dropna()
    assert (valid["upper"] >= valid["mid"]).all()
    assert (valid["mid"] >= valid["lower"]).all()


def test_volume_spike_ratio():
    volume = pd.Series([100] * 20 + [500], dtype=float)
    result = volume_spike_ratio(volume, window=20)
    assert result.iloc[-1] == pytest.approx(5.0)
