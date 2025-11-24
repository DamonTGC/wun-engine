"""
http_client.py
Wrapper for The Odds API GET requests.
"""

import os
import requests
from typing import Tuple, Dict, Any
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_API_BASE_URL = os.getenv("ODDS_API_BASE_URL", "https://api.the-odds-api.com/v4")


class OddsAPIClient:
    """Simple HTTP client for The Odds API"""

    def __init__(self, api_key: str, base_url: str = ODDS_API_BASE_URL):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

        if not self.api_key:
            raise ValueError("Missing ODDS_API_KEY in .env")

    def get(self, path: str, params: Dict[str, Any] = None) -> Any:
        """Perform GET request to The Odds API"""
        if not path.startswith("/"):
            path = "/" + path
        
        url = self.base_url + path

        if params is None:
            params = {}

        params["apiKey"] = self.api_key

        resp = requests.get(url, params=params)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Odds API error {resp.status_code}: {resp.text}"
            )

        return resp.json()


# ---------------------------
# Legacy simple function wrapper
# ---------------------------

def odds_get(path: str, params: Dict[str, Any]):
    """
    Compatibility wrapper so older code still works.
    Returns: (json, status_code)
    """
    if not path.startswith("/"):
        path = "/" + path

    url = ODDS_API_BASE_URL.rstrip("/") + path

    params = params.copy()
    params["apiKey"] = ODDS_API_KEY

    resp = requests.get(url, params=params)

    try:
        data = resp.json()
    except:
        data = None

    return data, resp.status_code


