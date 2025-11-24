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
    Fetch live odds events for a sport from The Odds API.
    Returns list of raw event objects.
    """

    sport = sport.upper()
    sport_key = SPORT_KEYS.get(sport)

    if not sport_key:
        print(f"[WARN] No SPORT_KEY mapping for sport={sport}")
        return []

    if not ODDS_API_KEY:
        print("[WARN] ODDS_API_KEY missing, cannot call odds API.")
        return []

    url = f"{BASE_URL}/{sport_key}/odds"

    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": ",".join(markets),
        "oddsFormat": "american",
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[ERROR] fetch_live_events failed for {sport}: {e}")
        return []


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

                # ---------- PLAYER PROPS ----------

                # Anything like player_points, player_assists, player_rebounds, etc.
                elif mkey.startswith("player_"):
                    stat_type = mkey  # e.g. "player_points"
                    for outcome in m.get("outcomes", []):
                        normalized.append({
                            "type": "prop",
                            "sport": sport,
                            "game_id": game_id,
                            "book": book,
                            "player": outcome.get("name"),   # PLAYER NAME
                            "team": None,                     # (add team later if needed)
                            "stat_type": stat_type,           # STAT TYPE
                            "direction": "over",              # assume over for that line
                            "line": outcome.get("point"),
                            "odds": outcome.get("price"),
                            "home_team": home,
                            "away_team": away,
                        })

    return normalized
