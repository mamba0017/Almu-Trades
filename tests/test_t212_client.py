from unittest.mock import MagicMock, patch

import pytest
import requests

from src.t212_client import Trading212Client, Trading212Error


def test_missing_api_key_raises():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(Trading212Error):
            Trading212Client(api_key=None)


def test_invalid_mode_raises():
    with pytest.raises(Trading212Error):
        Trading212Client(api_key="dummy-key", mode="paper")


def test_uses_live_base_url_by_default():
    client = Trading212Client(api_key="dummy-key")
    assert client.base_url == "https://live.trading212.com/api/v0"


def test_uses_demo_base_url_when_requested():
    client = Trading212Client(api_key="dummy-key", mode="demo")
    assert client.base_url == "https://demo.trading212.com/api/v0"


def test_authorization_header_set_from_key():
    client = Trading212Client(api_key="secret-123")
    assert client._session.headers["Authorization"] == "secret-123"


def _mock_response(status_code=200, json_data=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.ok = 200 <= status_code < 300
    resp.json.return_value = json_data or {}
    resp.text = text
    return resp


def test_get_portfolio_returns_parsed_json():
    client = Trading212Client(api_key="dummy-key")
    positions = [{"ticker": "AAPL_US_EQ", "quantity": 1.0}]
    with patch.object(client._session, "get", return_value=_mock_response(200, positions)):
        result = client.get_portfolio()
    assert result == positions


def test_401_raises_trading212_error():
    client = Trading212Client(api_key="bad-key")
    with patch.object(client._session, "get", return_value=_mock_response(401)):
        with pytest.raises(Trading212Error, match="401"):
            client.get_account_cash()


def test_429_raises_trading212_error():
    client = Trading212Client(api_key="dummy-key")
    with patch.object(client._session, "get", return_value=_mock_response(429)):
        with pytest.raises(Trading212Error, match="Rate limited"):
            client.get_portfolio()


def test_network_error_raises_trading212_error():
    client = Trading212Client(api_key="dummy-key")
    with patch.object(client._session, "get", side_effect=requests.ConnectionError("boom")):
        with pytest.raises(Trading212Error, match="Request to"):
            client.get_account_info()
