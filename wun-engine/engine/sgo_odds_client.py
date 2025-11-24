# sgo_odds_client.py

import os
import requests
from typing import Dict, Any, List, Optional

BASE_URL = "https://api.sportsgameodds.com/v2"

# 🔑 API KEY: read from env for safety
API_KEY = os.getenv("SPORTSGAME_API_KEY") or "REPLACE_WITH_YOUR_KEY"

if not API_KEY or API_KEY.startswith("REPLACE_WITH"):
    print("[WARN] SPORTSGAME_API_KEY missing. Set it in your environment or update this file.")


# 🏈🏀🏒 Mapping from YOUR short sport code -> SportsGameOdds sportID + leagueID
SPORT_LEAGUE_MAP: Dict[str, Dict[str, str]] = {
    "NFL":   {"sportID": "FOOTBALL",  "leagueID": "NFL"},
    "NCAAF": {"sportID": "FOOTBALL",  "leagueID": "NCAAF"},
    "NBA":   {"sportID": "BASKETBALL","leagueID": "NBA"},
    "NCAAB": {"sportID": "BASKETBALL","leagueID": "NCAAB"},
    "NHL":   {"sportID": "HOCKEY",    "leagueID": "NHL"},
    "MLB":   {"sportID": "BASEBALL",  "leagueID": "MLB"},
}


def _get_headers() -> Dict[str, str]:
    return {
        "x-api-key": API_KEY,
        "Accept": "application/json",
    }


def fetch_events_for_league(
    sport_code: str,
    max_events: int = 300,
    only_with_odds: bool = True,
) -> List[Dict[str, Any]]:
    """
    Fetch Events (with odds) for a single sport/league combo
    using /events endpoint + cursor paging.

    sport_code: one of ["NFL","NCAAF","NBA","NCAAB","NHL","MLB"]
    """
    if sport_code not in SPORT_LEAGUE_MAP:
        raise ValueError(f"Unknown sport_code: {sport_code}")

    conf = SPORT_LEAGUE_MAP[sport_code]
    sport_id = conf["sportID"]
    league_id = conf["leagueID"]

    params: Dict[str, Any] = {
        "sportID": sport_id,
        "leagueID": league_id,
        "limit": 100,  # page size
    }

    # Filter to only events that have odds
    if only_with_odds:
        params["oddsPresent"] = "true"

    url = f"{BASE_URL}/events"
    headers = _get_headers()

    all_events: List[Dict[str, Any]] = []
    cursor: Optional[str] = None

    while True:
        if cursor:
            params["cursor"] = cursor

        resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code != 200:
            print(
                f"[ERROR] /events failed for {sport_code}: "
                f"{resp.status_code} {resp.text[:300]}"
            )
            break

        payload = resp.json()
        if not payload.get("success"):
            print(f"[ERROR] /events not success for {sport_code}: {payload}")
            break

        data = payload.get("data", [])
        all_events.extend(data)

        if len(all_events) >= max_events:
            break

        cursor = payload.get("nextCursor")
        if not cursor:
            break

    print(f"[INFO] fetched {len(all_events)} events for {sport_code}")
    return all_events[:max_events]


def _normalize_odd_item(
    sport_code: str,
    league_id: str,
    event: Dict[str, Any],
    odd: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Turn a single odd object into a standard structure
    your app/engine can work with.
    """
    event_id = event.get("eventID")
    event_type = event.get("type")

    # Teams info can be extracted more deeply if you want; keep simple for now.
    # Many payloads also include teams/homeTeam/awayTeam mappings.
    info = event.get("info", {}) or {}
    home_team = info.get("homeTeam") or info.get("homeTeamName")
    away_team = info.get("awayTeam") or info.get("awayTeamName")

    bet_type_id = odd.get("betTypeID")  # "ml", "sp", "ou", "prop"
    stat_id = odd.get("statID")
    stat_entity_id = odd.get("statEntityID")
    side_id = odd.get("sideID")
    market_name = odd.get("marketName")
    fair_odds = odd.get("fairOdds")
    book_odds = odd.get("bookOdds")
    period_id = odd.get("periodID")

    # Line fields: spread vs total vs props
    fair_line = None
    book_line = None
    if "fairSpread" in odd:
        fair_line = odd.get("fairSpread")
        book_line = odd.get("bookSpread")
        market_type = "spread"
    elif "fairOverUnder" in odd:
        fair_line = odd.get("fairOverUnder")
        book_line = odd.get("bookOverUnder")
        market_type = "total_or_prop"
    else:
        market_type = "moneyline_or_other"

    # Player-based markets will usually have playerID
    player_id = odd.get("playerID")

    return {
        "sport": sport_code,
        "sportID": SPORT_LEAGUE_MAP[sport_code]["sportID"],
        "leagueID": league_id,
        "eventId": event_id,
        "eventType": event_type,
        "homeTeam": home_team,
        "awayTeam": away_team,
        "period": period_id,
        "marketName": market_name,
        "marketType": market_type,
        "betTypeID": bet_type_id,
        "sideID": side_id,
        "statID": stat_id,
        "statEntityID": stat_entity_id,
        "playerID": player_id,
        "fairOdds": fair_odds,
        "bookOdds": book_odds,
        "fairLine": fair_line,
        "bookLine": book_line,
        # extra scoring info if present:
        "score": odd.get("score"),
        "started": odd.get("started"),
        "ended": odd.get("ended"),
        "cancelled": odd.get("cancelled"),
    }


def normalize_events_to_markets(
    sport_code: str,
    events: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Flatten Events -> list of normalized odds markets.
    """
    league_id = SPORT_LEAGUE_MAP[sport_code]["leagueID"]
    markets: List[Dict[str, Any]] = []

    for event in events:
        odds_obj = event.get("odds") or {}
        # odds is an object keyed by oddID; we care about the values
        for odd_id, odd in odds_obj.items():
            if not isinstance(odd, dict):
                continue
            normalized = _normalize_odd_item(sport_code, league_id, event, odd)
            markets.append(normalized)

    print(f"[INFO] normalized {len(markets)} markets for {sport_code}")
    return markets


def fetch_all_sports_odds() -> List[Dict[str, Any]]:
    """
    Fetch odds for all 6 main sports and return
    a single combined list of normalized market dicts.
    """
    all_markets: List[Dict[str, Any]] = []

    for sport_code in ["NFL", "NCAAF", "NBA", "NCAAB", "NHL", "MLB"]:
        try:
            events = fetch_events_for_league(sport_code)
            markets = normalize_events_to_markets(sport_code, events)
            all_markets.extend(markets)
        except Exception as e:
            print(f"[ERROR] failed to fetch/normalize for {sport_code}: {e}")

    print(f"[INFO] TOTAL markets across all sports: {len(all_markets)}")
    return all_markets


if __name__ == "__main__":
    # Quick manual test: run "python sgo_odds_client.py"
    markets = fetch_all_sports_odds()
    # Show just a few so console isn't spammed
    from pprint import pprint
    print("\n=== SAMPLE MARKETS (first 5) ===")
    pprint(markets[:5])
