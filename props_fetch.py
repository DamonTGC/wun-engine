from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests


ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")

DEFAULT_REGIONS = "us"
DEFAULT_MARKETS = ",".join(
    [
        "player_points",
        "player_rebounds",
        "player_assists",
        "player_threes",
        "player_pass_yards",
        "player_rush_yards",
        "player_receiving_yards",
    ]
)


def fetch_odds_for_sport(
    sport_key: str,
    regions: str = DEFAULT_REGIONS,
    markets: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Thin wrapper around The Odds API "odds" endpoint.

    Returns the raw list of events for the given sport key.
    """
    if not ODDS_API_KEY:
        raise RuntimeError(
            "ODDS_API_KEY environment variable is not set. "
            "Set it to your TheOddsAPI key before running the engine."
        )

    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": regions,
        "markets": markets or DEFAULT_MARKETS,
        "oddsFormat": "american",
    }

    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    # Ensure we always return a list
    if isinstance(data, dict):
        # Some errors come back as dicts; pass them up
        if "message" in data and "error" in data:
            raise RuntimeError(f"Odds API error: {data}")
        return []

    return data or []
