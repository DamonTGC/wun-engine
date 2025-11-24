from __future__ import annotations

"""
props_fetch.py

Fetch player props from The Odds API, normalize them into NormalizedProp
objects so they can be fed into your simulation + EV + goblin/demon engine.
"""

from typing import List, Dict, Any
import time

from config import (
    SPORT_KEY_MAP,
    DEFAULT_REGIONS,
    NFL_PROP_MARKETS,
    NBA_PROP_MARKETS,
    NHL_PROP_MARKETS,
    MLB_PROP_MARKETS,
    ODDS_API_KEY,
    ODDS_API_BASE_URL,
)

from http_client import OddsAPIClient
from normalizer import NormalizedProp, normalize_player_prop

# ============================================================
# 1. Prop market mapping per sport
# ============================================================

# NOTE: NFL_PROP_MARKETS, etc. can be either:
#   - a comma-separated string: "player_pass_yds,player_rush_yds"
#   - or a list[str]: ["player_pass_yds", "player_rush_yds"]
#
# The code below handles BOTH cases safely.

PROP_MARKETS_BY_SPORT: dict[str, list[str] | str] = {
    "NFL": NFL_PROP_MARKETS,
    "NCAAF": NFL_PROP_MARKETS,   # NCAA football uses same categories
    "NBA": NBA_PROP_MARKETS,
    "NCAAB": NBA_PROP_MARKETS,   # Use NBA markets for college props
    "NHL": NHL_PROP_MARKETS,
    "MLB": MLB_PROP_MARKETS,
}

# Single shared client
client = OddsAPIClient(ODDS_API_KEY, ODDS_API_BASE_URL)


# ============================================================
# 2. Fetch event list (basic odds) — just to get event IDs
# ============================================================

def list_events_for_sport(sport_key: str) -> list[dict]:
    """
    Use /v4/sports/{sport}/odds to get a list of events.
    We request only h2h to keep it cheap — we just need event IDs.
    """
    params = {
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "decimal",
        "dateFormat": "iso",
    }

    try:
        events = client.get(f"/sports/{sport_key}/odds", params=params)
        print(f"[DEBUG] list_events_for_sport -> {sport_key}, got {len(events)} events")
        if not events:
            print(f"[WARN] No events for {sport_key}")
        return events
    except Exception as e:
        print(f"[ERROR] Failed to list events for {sport_key}: {e}")
        return []


# ============================================================
# 3. Fetch props for ONE event (per-event endpoint)
# ============================================================

def fetch_props_for_event(
    sport: str,
    event_id: str,
    market_keys: list[str] | str,
) -> list[dict]:
    """
    Call /v4/sports/{sport_key}/events/{event_id}/odds with player prop markets.

    market_keys can be either:
      - list[str]: ["player_pass_yds", "player_rush_yds"]
      - str: "player_pass_yds,player_rush_yds"

    Returns: list of bookmaker objects (per The Odds API docs).
    """
    sport_key = SPORT_KEY_MAP.get(sport.upper())
    if not sport_key:
        print(f"[WARN] Unknown sport {sport}")
        return []

    # --- handle both list and string safely ---
    if isinstance(market_keys, str):
        markets_str = market_keys.strip()
    else:
        # we assume it's an iterable of market strings
        markets_str = ",".join(m.strip() for m in market_keys)

    print(f"[DEBUG] fetch_props_for_event: event={event_id}, markets='{markets_str}'")

    params = {
        "regions": DEFAULT_REGIONS,
        "markets": markets_str,
        "oddsFormat": "decimal",
        "dateFormat": "iso",
    }

    try:
        data = client.get(
            f"/sports/{sport_key}/events/{event_id}/odds",
            params=params,
        )

        # The per-event endpoint returns a list[bookmaker] or [].
        if isinstance(data, list):
            print(
                f"[DEBUG] fetch_props_for_event: event={event_id}, "
                f"got {len(data)} bookmakers"
            )
            return data
        else:
            print(
                f"[DEBUG] fetch_props_for_event: event={event_id}, "
                f"unexpected shape {type(data)}, value={data}"
            )
            return []
    except Exception as e:
        print(f"[WARN] Failed prop fetch for event {event_id}: {e}")
        return []


# ============================================================
# 4. Normalize ALL props from one event
# ============================================================

def normalize_event_props(
    sport: str,
    event: dict,
    bookmakers: list[dict],
    allowed_books: list[str] | None = None,
) -> list[NormalizedProp]:
    """
    Take a single event + its bookmaker list (from per-event props),
    and convert all player_* markets to NormalizedProp objects.
    """

    if allowed_books is None:
        allowed_books = []

    normalized: list[NormalizedProp] = []

    event_id = event.get("id", "")
    home_team = event.get("home_team", "")
    away_team = event.get("away_team", "")
    league = sport  # you can refine later (NFL vs NCAAF etc)

    print(
        f"[DEBUG] normalize_event_props: event {event_id} "
        f"({away_team} @ {home_team}), {len(bookmakers)} bookmakers"
    )

    for bm in bookmakers:
        book_key = bm.get("key")
        if allowed_books and book_key not in allowed_books:
            continue

        markets = bm.get("markets", [])
        for m in markets:
            market_key = m.get("key", "")

            # Only treat player_* markets as props.
            if not market_key.startswith("player_"):
                continue

            outcomes = m.get("outcomes", []) or []

            for o in outcomes:
                # The Odds API player props usually have participant/description
                player_name = (
                    o.get("description")
                    or o.get("participant")
                    or o.get("name", "Unknown Player")
                )

                line = o.get("point")
                prop_dict = {
                    "player": player_name,
                    "market": market_key,
                    "line": line,
                    "outcomes": outcomes,
                }

                norm = normalize_player_prop(
                    event_id=event_id,
                    sport=sport,
                    league=league,
                    prop=prop_dict,
                    bookmaker=book_key,
                )
                normalized.append(norm)

    print(f"[DEBUG] normalize_event_props: -> {len(normalized)} props")
    return normalized


# ============================================================
# 5. Main: fetch ALL player props for a sport
# ============================================================

def fetch_player_props_for_sport(
    sport: str,
    max_events: int | None = None,
    allowed_books: list[str] | None = None,
) -> list[NormalizedProp]:
    """
    High-level function:

    - Look up the Odds API sport key from SPORT_KEY_MAP
    - Get a list of events (h2h) for that sport
    - For each event, fetch player props via /events/{eventId}/odds
    - Normalize all props into NormalizedProp objects
    """

    sport_upper = sport.upper()
    sport_key = SPORT_KEY_MAP.get(sport_upper)
    if not sport_key:
        print(f"[WARN] fetch_player_props_for_sport: unknown sport '{sport}'")
        return []

    market_keys = PROP_MARKETS_BY_SPORT.get(sport_upper)
    if not market_keys:
        print(f"[WARN] No prop markets configured for {sport_upper}")
        return []

    print(f"Fetching player props for {sport_key}...")

    events = list_events_for_sport(sport_key)
    if not events:
        print(f"[WARN] No events for {sport_key}")
        return []

    if max_events is not None:
        events = events[:max_events]

    final_list: list[NormalizedProp] = []

    for ev in events:
        event_id = ev.get("id")
        if not event_id:
            continue

        print(f"  -> Fetching props for event: {event_id} ({sport_upper})")

        books = fetch_props_for_event(sport_upper, event_id, market_keys)
        if not books:
            # Either no props, or your plan doesn't include these props
            print(f"  [INFO] No bookmakers/props returned for event {event_id}")
            continue

        normalized = normalize_event_props(
            sport_upper,
            ev,
            books,
            allowed_books=allowed_books,
        )
        final_list.extend(normalized)

        # Avoid rate-limit issues
        time.sleep(0.4)

    print(f"[INFO] fetch_player_props_for_sport: {sport_upper} -> {len(final_list)} props")
    return final_list


# ============================================================
# 6. Test runner
# ============================================================

if __name__ == "__main__":
    for sport in ["NFL", "NBA", "NHL"]:
        print(f"\n===== TESTING {sport} PLAYER PROPS =====")
        props = fetch_player_props_for_sport(sport, max_events=5)
        print(f"Found {len(props)} props")
        if props:
            import json
            print(json.dumps(props[0].__dict__, indent=2))

