"""http_client.py
Simple HTTP wrapper for The Odds API.
"""
from __future__ import annotations

from typing import Any, Dict, Tuple
import requests

from config import ODDS_API_KEY, ODDS_API_BASE_URL


class OddsAPIError(RuntimeError):
    """Raised when The Odds API returns an error response."""


class OddsAPIClient:
    """Lightweight client around The Odds API v4."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or ODDS_API_KEY
        self.base_url = (base_url or ODDS_API_BASE_URL).rstrip("/")
        if not self.api_key:
            raise OddsAPIError("ODDS_API_KEY is not configured. Set it in .env or environment.")

    def _build_url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path

    def get(self, path: str, params: Dict[str, Any] | None = None) -> Any:
        """Perform a GET request and return decoded JSON, or raise OddsAPIError."""
        url = self._build_url(path)
        params = dict(params or {})
        params.setdefault("apiKey", self.api_key)

        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            # Try to include Odds API error body for easier debugging
            try:
                data = resp.json()
            except Exception:
                data = {"message": resp.text}
            raise OddsAPIError(
                f"Odds API error {resp.status_code}: {data.get('message')}"
            )
        try:
            return resp.json()
        except Exception as exc:
            raise OddsAPIError(f"Failed to decode JSON from Odds API: {exc}") from exc


def odds_get(path: str, params: Dict[str, Any] | None = None) -> Tuple[Any, int]:
    """Convenience function for simple scripts.

    Returns (data, status_code). On error, raises OddsAPIError.
    """
    client = OddsAPIClient()
    data = client.get(path, params or {})
    return data, 200
