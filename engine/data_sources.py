"""
data_sources.py
Feeds raw markets + simple stats into the WUN engine.

We define:
- get_straight_markets(sport, prompt)
- get_prop_markets(sport, prompt)
- get_simple_team_stats(game_id)

These names MUST exist because tiles.py imports them.
"""

from typing import List, Dict, Any


def get_simple_team_stats(game_id: str) -> Dict[str, Any]:
    """
    Very simple placeholder team stats.
    Used by total + fallback sims.
    """
    # NFL example
    if game_id == "BUF vs NYJ":
        return {
            "home": "BUF",
            "away": "NYJ",
            "home_ppg": 24.3,
            "away_ppg": 17.1,
        }

    # NBA example
    if game_id == "LAC @ ORL":
        return {
            "home": "ORL",
            "away": "LAC",
            "home_ppg": 110.0,
            "away_ppg": 114.0,
        }

    # Fallback
    return {
        "home": "HOME",
        "away": "AWAY",
        "home_ppg": 24.0,
        "away_ppg": 21.0,
    }


def get_straight_markets(sport: str, prompt: str) -> List[Dict[str, Any]]:
    """
    Return straight markets (Spread, Total, ML if you add it).
    Signature MUST be (sport, prompt) because tiles.py calls it that way.
    'prompt' is unused for now but kept for compatibility.
    """
    sport = sport.upper()
    markets: List[Dict[str, Any]] = []

    # ---------- NFL EXAMPLE ----------
    if sport in ("NFL", "ALL"):
        markets.extend([
            {
                "id": "buf_nyj_spread",
                "sport": "NFL",
                "game": "BUF vs NYJ",
                "market": "Spread",
                "team": "BUF",  # home team
                "lines": [
                    {"book": "BetMGM",     "line": -5.5, "american_odds": -110},
                    {"book": "DraftKings", "line": -5.0, "american_odds": -115},
                    {"book": "FanDuel",    "line": -6.0, "american_odds": +100},
                ],
            },
            {
                "id": "buf_nyj_total",
                "sport": "NFL",
                "game": "BUF vs NYJ",
                "market": "Total",
                "team": "BUF/NYJ",
                "lines": [
                    {"book": "BetMGM",     "line": 42.5, "american_odds": -110},
                    {"book": "DraftKings", "line": 43.0, "american_odds": -105},
                ],
            },
        ])

    # ---------- NBA EXAMPLE (optional now, used later) ----------
    if sport in ("NBA", "ALL"):
        markets.extend([
            {
                "id": "lac_orl_spread",
                "sport": "NBA",
                "game": "LAC @ ORL",
                "market": "Spread",
                "team": "LAC",
                "lines": [
                    {"book": "BetMGM",     "line": -4.5, "american_odds": -110},
                    {"book": "DraftKings", "line": -4.0, "american_odds": -115},
                    {"book": "FanDuel",    "line": -5.0, "american_odds": -105},
                ],
            },
        ])

    return markets


def get_prop_markets(sport: str, prompt: str) -> List[Dict[str, Any]]:
    """
    Return basic prop markets.
    Signature MUST be (sport, prompt) because tiles.py calls it that way.
    Placeholder for now so engine runs; we’ll make it real later.
    """
    sport = sport.upper()
    markets: List[Dict[str, Any]] = []

    if sport in ("NFL", "ALL"):
        markets.extend([
            {
                "id": "allen_passyards",
                "sport": "NFL",
                "game": "BUF vs NYJ",
                "market": "PROP",
                "team": "BUF",
                "player": "Josh Allen",
                "stat": "Passing Yards",
                "lines": [
                    {"book": "BetMGM",     "line": 255.5, "american_odds": -115},
                    {"book": "DraftKings", "line": 250.5, "american_odds": -120},
                ],
            },
        ])

    if sport in ("NBA", "ALL"):
        markets.extend([
            {
                "id": "harden_pra",
                "sport": "NBA",
                "game": "LAC @ ORL",
                "market": "PROP",
                "team": "LAC",
                "player": "James Harden",
                "stat": "PRA",
                "lines": [
                    {"book": "PrizePicks", "line": 41.5, "american_odds": -119},
                    {"book": "BetMGM",     "line": 40.5, "american_odds": -130},
                ],
            },
        ])

    return markets
