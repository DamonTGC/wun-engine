# engine/live_odds.py

import os
import requests
from typing import List, Dict, Any
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the wun-engine root folder
ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
if not ODDS_API_KEY:
    print("[WARN] ODDS_API_KEY not found in environment!", ENV_PATH)

# Base URL for The Odds API
BASE_URL = "https://api.the-odds-api.com/v4/sports"

# Map your sport names to The Odds API sport keys
SPORT_KEYS: Dict[str, str] = {
    "NFL": "americanfootball_nfl",
    "CFB": "americanfootball_ncaaf",
    "NCAAF": "americanfootball_ncaaf",
    "NBA": "basketball_nba",
    "NCAAB": "basketball_ncaab",
    "NHL": "icehockey_nhl",
    "MLB": "baseball_mlb",
}


def fetch_live_events(sport: str, markets: List[str]) -> List[Dict[str, Any]]:
    """
    Unified fetch:
      - team markets (spreads/totals/h2h) via /odds
      - player props via /events/{eventId}/odds
    Returns combined list of event objects.
    """
    # Separate team vs prop markets
    team_markets = [
        m for m in markets
        if not (m.startswith("player_") or m.startswith("batter_") or m.startswith("pitcher_"))
    ]
    prop_markets = [
        m for m in markets
        if (m.startswith("player_") or m.startswith("batter_") or m.startswith("pitcher_"))
    ]

    combined: List[Dict[str, Any]] = []

    if team_markets:
        combined.extend(fetch_team_markets(sport, team_markets))

    if prop_markets:
        combined.extend(fetch_player_props_for_sport(sport, prop_markets))

    return combined



def normalize_all_markets(
    sport: str,
    raw_events: List[Dict[str, Any]],
    wanted_markets: List[str],
) -> List[Dict[str, Any]]:
    """
    Convert raw The Odds API response into a universal format used by the WUN Engine.
    This ensures ALL sports + ALL markets return in the same structure.
    """

    normalized: List[Dict[str, Any]] = []

    for event in raw_events:
        game_id = event.get("id")
        home = event.get("home_team")
        away = event.get("away_team")

        for b in event.get("bookmakers", []):
            book = b.get("key")

            for m in b.get("markets", []):
                mkey = m.get("key")
                if mkey not in wanted_markets:
                    continue

                # ---------- TEAM MARKETS ----------

                # Spreads
                if mkey == "spreads":
                    for outcome in m.get("outcomes", []):
                        normalized.append({
                            "type": "spread",
                            "sport": sport,
                            "game_id": game_id,
                            "book": book,
                            "team": outcome.get("name"),
                            "line": outcome.get("point"),
                            "odds": outcome.get("price"),
                            "home_team": home,
                            "away_team": away,
                        })

                # Totals (Over/Under)
                elif mkey == "totals":
                    for outcome in m.get("outcomes", []):
                        normalized.append({
                            "type": "total",
                            "sport": sport,
                            "game_id": game_id,
                            "book": book,
                            "side": outcome.get("name"),  # Over / Under
                            "line": outcome.get("point"),
                            "odds": outcome.get("price"),
                            "home_team": home,
                            "away_team": away,
                        })

                # Moneyline (h2h)
                elif mkey == "h2h":
                    for outcome in m.get("outcomes", []):
                        normalized.append({
                            "type": "moneyline",
                            "sport": sport,
                            "game_id": game_id,
                            "book": book,
                            "team": outcome.get("name"),
                            "odds": outcome.get("price"),
                            "home_team": home,
                            "away_team": away,
                        })

# engine/live_odds.py

SPORT_KEYS = {
    "NFL":   "americanfootball_nfl",
    "NCAAF": "americanfootball_ncaaf",
    "NBA":   "basketball_nba",
    "NCAAB": "basketball_ncaab",
    "NHL":   "icehockey_nhl",
    "MLB":   "baseball_mlb",
}

# Which prop markets to request per sport
SPORT_PROP_MARKETS = {
    "NFL": [
        "player_pass_yds",
        "player_pass_tds",
        "player_rush_yds",
        "player_reception_yds",
        "player_receptions",
        "player_rush_attempts",
        "player_tds_over",
    ],
    "NCAAF": [
        "player_pass_yds",
        "player_pass_tds",
        "player_rush_yds",
        "player_reception_yds",
        "player_receptions",
    ],
    "NBA": [
        "player_points",
        "player_rebounds",
        "player_assists",
        "player_threes",
        "player_points_rebounds_assists",
        "player_points_rebounds",
        "player_points_assists",
        "player_rebounds_assists",
    ],
    "NCAAB": [
        "player_points",
        "player_rebounds",
        "player_assists",
        "player_threes",
    ],
    "NHL": [
        "player_points",
        "player_assists",
        "player_goals",
        "player_shots_on_goal",
    ],
    "MLB": [
        "batter_hits",
        "batter_total_bases",
        "batter_home_runs",
        "batter_rbis",
        "pitcher_strikeouts",
        "pitcher_outs",
    ],
}
import os
import requests
from typing import List, Dict, Any

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
BASE_URL = "https://api.the-odds-api.com/v4/sports"


def fetch_team_markets(sport: str, markets: List[str]) -> List[Dict[str, Any]]:
    """Fetch spreads/totals/h2h for a sport via /odds."""
    sport_key = SPORT_KEYS.get(sport.upper())
    if not sport_key:
        print(f"[WARN] Unknown sport for team markets: {sport}")
        return []

    if not ODDS_API_KEY:
        print("[ERROR] ODDS_API_KEY missing")
        return []

    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": ",".join(markets),
        "oddsFormat": "american",
    }

    url = f"{BASE_URL}/{sport_key}/odds"

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[ERROR] fetch_team_markets failed for {sport}: {e}")
        return []
def fetch_player_props_for_sport(sport: str, markets: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch player props for a sport:
      1) /events to get list of events
      2) /events/{eventId}/odds with player_* (or batter_ / pitcher_) markets
    Returns a list of event objects (Odds API shape) with only prop markets.
    """
    sport = sport.upper()
    sport_key = SPORT_KEYS.get(sport)
    if not sport_key:
        print(f"[WARN] Unknown sport for props: {sport}")
        return []

    if not ODDS_API_KEY:
        print("[ERROR] ODDS_API_KEY missing")
        return []

    # 1) get events for this sport
    events_url = f"{BASE_URL}/{sport_key}/events"
    events_params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "oddsFormat": "american",
    }

    try:
        ev_resp = requests.get(events_url, params=events_params, timeout=10)
        ev_resp.raise_for_status()
        events = ev_resp.json()
    except Exception as e:
        print(f"[ERROR] fetch_player_props_for_sport /events failed for {sport}: {e}")
        return []

    all_prop_events: List[Dict[str, Any]] = []

    # 2) loop events and pull props
    for ev in events:
        event_id = ev.get("id")
        if not event_id:
            continue

        odds_url = f"{BASE_URL}/{sport_key}/events/{event_id}/odds"
        odds_params = {
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": ",".join(markets),
            "oddsFormat": "american",
        }

        try:
            o_resp = requests.get(odds_url, params=odds_params, timeout=10)

            # If no props exist for this game, Odds API may return 404 or empty list
            if o_resp.status_code == 404:
                continue

            o_resp.raise_for_status()
            prop_events = o_resp.json()  # usually a list with 1 event

            # Append them all so your normalizer sees every event
            all_prop_events.extend(prop_events)

        except Exception as e:
            print(f"[WARN] props fetch failed for event={event_id}, sport={sport}: {e}")
            continue

    return all_prop_events
