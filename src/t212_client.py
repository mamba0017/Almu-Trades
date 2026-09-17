"""Minimal client for the Trading212 public Equity API.

Docs: https://t212public-api-docs.redoc.ly/

The API key is never read from anywhere except an explicit argument, the
T212_API_KEY environment variable, or Streamlit secrets (handled by the
caller) — this module has no knowledge of where the key ultimately comes
from and never logs or persists it.
"""

import os

import requests

BASE_URLS = {
    "live": "https://live.trading212.com/api/v0",
    "demo": "https://demo.trading212.com/api/v0",
}


class Trading212Error(RuntimeError):
    """Raised for any non-2xx response or missing configuration."""


class Trading212Client:
    def __init__(
        self, api_key: str | None = None, mode: str = "live", timeout: float = 10.0
    ):
        self.api_key = api_key or os.environ.get("T212_API_KEY")
        if not self.api_key:
            raise Trading212Error(
                "No Trading212 API key found. Pass api_key=, or set T212_API_KEY."
            )
        if mode not in BASE_URLS:
            raise Trading212Error(f"Unknown mode '{mode}'; expected 'live' or 'demo'.")

        self.mode = mode
        self.base_url = BASE_URLS[mode]
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"Authorization": self.api_key})

    def _get(self, path: str, params: dict | None = None):
        url = f"{self.base_url}{path}"
        try:
            resp = self._session.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            raise Trading212Error(f"Request to {path} failed: {exc}") from exc

        if resp.status_code == 401:
            raise Trading212Error("Trading212 rejected the API key (401 Unauthorized).")
        if resp.status_code == 429:
            raise Trading212Error(
                "Rate limited by Trading212 (429). This API has tight per-endpoint "
                "limits — wait a few seconds before retrying."
            )
        if not resp.ok:
            raise Trading212Error(f"Trading212 API error {resp.status_code}: {resp.text[:200]}")
        return resp.json()

    def get_portfolio(self) -> list[dict]:
        """Open equity positions: ticker, quantity, averagePrice, currentPrice, ppl, ..."""
        return self._get("/equity/portfolio")

    def get_account_cash(self) -> dict:
        """Free / invested / total cash and overall P&L for the account."""
        return self._get("/equity/account/cash")

    def get_account_info(self) -> dict:
        """Account id and base currency."""
        return self._get("/equity/account/info")

    def get_instruments(self) -> list[dict]:
        """Full tradable instrument catalog (ticker -> name/type/currency). Large & slow-changing."""
        return self._get("/equity/metadata/instruments")
