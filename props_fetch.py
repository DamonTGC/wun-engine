"""props_fetch.py

High-level helpers to fetch player props from The Odds API and normalize
them into NormalizedProp objects.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import time

from config import (
    SPORT_KEY_MAP,
    DEFAULT_REGIONS,
    DEFAULT_ODDS_FORMAT,
    DEFAULT_DATE_FORMAT,
    PROP_MARKETS_BY_SPORT,
    PREFERRED_BOOKMAKERS,
    ODDS_API_KEY,
    ODDS_API_BASE_URL,
)
from http_client import OddsAPIClient
from normalizer import NormalizedProp, normalize_event_player_props


client = OddsAPIClient(ODDS_API_KEY, ODDS_API_BASE_URL)


def list_events_for_sport(sport_short: str, markets: str = "h2h") -> List[Dict[str, Any]]:
    """Get a list of live/upcoming events for a sport via /v4/sports/{sport}/odds.

    We only request a cheap featured market (h2h) here because we mainly
    need event IDs, teams, and commence times.
    """
    sport_key = SPORT_KEY_MAP.get(sport_short.upper())
    if not sport_key:
        raise ValueError(f"Unknown sport '{sport_short}'")

    params = {
        "regions": DEFAULT_REGIONS,
        "markets": markets,
        "oddsFormat": DEFAULT_ODDS_FORMAT,
        "dateFormat": DEFAULT_DATE_FORMAT,
    }
    data = client.get(f"/sports/{sport_key}/odds", params=params)
    if not isinstance(data, list):
        raise RuntimeError("Unexpected events response from Odds API (expected list)")
    return data


def fetch_props_for_event(
    sport_short: str,
    event: Dict[str, Any],
    allowed_books: Optional[List[str]] = None,
    allowed_markets: Optional[List[str]] = None,
) -> List[NormalizedProp]:
    """Fetch all player props for a single event and normalize them."""
    sport_label = sport_short.upper()
    league_key = SPORT_KEY_MAP[sport_label]
    event_id = event.get("id")
    if not event_id:
        return []

    markets = allowed_markets or PROP_MARKETS_BY_SPORT.get(sport_label, [])
    markets_param = ",".join(markets)

    params: Dict[str, Any] = {
        "regions": DEFAULT_REGIONS,
        "markets": markets_param,
        "oddsFormat": DEFAULT_ODDS_FORMAT,
        "dateFormat": DEFAULT_DATE_FORMAT,
    }
    if allowed_books:
        params["bookmakers"] = ",".join(allowed_books)

    data = client.get(f"/sports/{league_key}/events/{event_id}/odds", params=params)
    bookmakers = data.get("bookmakers") or []
    return normalize_event_player_props(
        sport_label=sport_label,
        league_key=league_key,
        event=event,
        bookmakers=bookmakers,
        allowed_markets=markets,
    )


def fetch_player_props_for_sport(
    sport_short: str,
    max_events: int = 20,
    allowed_books: Optional[List[str]] = None,
) -> List[NormalizedProp]:
    """Fetch and normalize player props for up to max_events games in a sport."""
    sport_label = sport_short.upper()
    league_key = SPORT_KEY_MAP.get(sport_label)
    if not league_key:
        raise ValueError(f"Unknown sport '{sport_short}'")

    events = list_events_for_sport(sport_label)
    events = events[:max_events]

    markets = PROP_MARKETS_BY_SPORT.get(sport_label, [])
    all_props: List[NormalizedProp] = []

    for ev in events:
        try:
            props = fetch_props_for_event(
                sport_short=sport_label,
                event=ev,
                allowed_books=allowed_books or PREFERRED_BOOKMAKERS,
                allowed_markets=markets,
            )
            all_props.extend(props)
        except Exception as exc:
            print(f"[WARN] Failed props fetch for event {ev.get('id')}: {exc}")
        time.sleep(0.4)  # be nice to rate limits

    return all_props
