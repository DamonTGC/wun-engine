"""config.py
Configuration for Wun Engine / Dime AI betting engine.
"""
from __future__ import annotations

import os
from typing import Dict, List
from dotenv import load_dotenv

# Base directory = wun-engine folder
BASE_DIR = os.path.dirname(__file__)
ENV_PATH = os.path.join(BASE_DIR, ".env")

# Load .env file if present
load_dotenv(ENV_PATH)

# === ODDS API CONFIG ===
ODDS_API_KEY: str | None = os.getenv("ODDS_API_KEY")
ODDS_API_BASE_URL: str = os.getenv("ODDS_API_BASE_URL", "https://api.the-odds-api.com/v4")

DEFAULT_REGIONS = os.getenv("ODDS_DEFAULT_REGIONS", "us")
DEFAULT_ODDS_FORMAT = os.getenv("ODDS_DEFAULT_ODDS_FORMAT", "decimal")
DEFAULT_DATE_FORMAT = os.getenv("ODDS_DEFAULT_DATE_FORMAT", "iso")

# === SQLITE CACHE CONFIG ===
DB_PATH: str = os.path.join(BASE_DIR, "wun_engine_cache.sqlite3")

# === SPORT + MARKET CONFIG ===

# Map your short sport labels (what you use in the UI) to Odds API sport_keys.
SPORT_KEY_MAP: Dict[str, str] = {
    "NFL": "americanfootball_nfl",
    "NCAAF": "americanfootball_ncaaf",
    "NBA": "basketball_nba",
    "NCAAB": "basketball_ncaab",
    "NHL": "icehockey_nhl",
    "MLB": "baseball_mlb",
}

# Player prop markets you care about per sport, using Odds API market keys.
NFL_PROP_MARKETS: List[str] = [
    "player_pass_yds",
    "player_rush_yds",
    "player_receptions",
    "player_reception_yds",
    "player_rush_attempts",
    "player_rush_reception_yds",
    "player_anytime_td",
]

NCAAF_PROP_MARKETS: List[str] = [
    "player_pass_yds",
    "player_rush_yds",
    "player_receptions",
    "player_reception_yds",
    "player_rush_attempts",
]

NBA_PROP_MARKETS: List[str] = [
    "player_points",
    "player_rebounds",
    "player_assists",
    "player_points_rebounds_assists",
    "player_points_rebounds",
    "player_points_assists",
    "player_rebounds_assists",
    "player_threes",
    "player_turnovers",
]

NCAAB_PROP_MARKETS: List[str] = [
    "player_points",
    "player_rebounds",
    "player_assists",
    "player_points_rebounds_assists",
    "player_threes",
]

NHL_PROP_MARKETS: List[str] = [
    "player_shots_on_goal",
    "player_points",
    "player_goals",
    "player_assists",
]

MLB_PROP_MARKETS: List[str] = [
    "pitcher_strikeouts",
    "batter_total_bases",
    "batter_hits",
    "batter_hits_runs_rbis",
]

PROP_MARKETS_BY_SPORT: Dict[str, List[str]] = {
    "NFL": NFL_PROP_MARKETS,
    "NCAAF": NCAAF_PROP_MARKETS,
    "NBA": NBA_PROP_MARKETS,
    "NCAAB": NCAAB_PROP_MARKETS,
    "NHL": NHL_PROP_MARKETS,
    "MLB": MLB_PROP_MARKETS,
}

# Markets that are naturally "Yes/No" style instead of Over/Under
YES_NO_MARKETS = {
    "player_anytime_td",
}

# Preferred bookmakers (you can tweak or limit to your states)
PREFERRED_BOOKMAKERS: List[str] = [
    "fanduel",
    "draftkings",
    "betmgm",
    "pointsbetus",
    "barstool",
    "betrivers",
    "caesars",
]

def implied_prob_from_decimal(decimal_odds: float) -> float:
    if decimal_odds <= 1.0:
        return 0.0
    return 1.0 / decimal_odds

def ev_from_prob(decimal_odds: float, true_prob: float, stake: float = 1.0) -> float:
    """Expected profit for a bet with decimal odds and true_prob.

    EV = p * (odds - 1) * stake - (1 - p) * stake
    """
    if decimal_odds <= 1.0:
        return 0.0
    return true_prob * (decimal_odds - 1.0) * stake - (1.0 - true_prob) * stake
