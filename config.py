import os
from dotenv import load_dotenv

# Base directory = wun-engine folder
BASE_DIR = os.path.dirname(__file__)
ENV_PATH = os.path.join(BASE_DIR, ".env")

# Load .env
load_dotenv(ENV_PATH)

# === ODDS API CONFIG ===
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_API_BASE_URL = os.getenv("ODDS_API_BASE_URL", "https://api.the-odds-api.com/v4")

if not ODDS_API_KEY:
    # Don't crash imports, but make it obvious
    print("[WARN] ODDS_API_KEY is missing from .env")

# Regions: us = US books only
DEFAULT_REGIONS = "us"

# Main markets (spreads/totals/moneyline)
DEFAULT_MAIN_MARKETS = "h2h,spreads,totals"

# Player-prop market groups per sport (we will use these later)
NFL_PROP_MARKETS = ",".join([
    "player_pass_yds",
    "player_rush_yds",
    "player_reception_yds",
    "player_receptions",
    "player_pass_tds",
    "player_rush_tds",
    "player_reception_tds",
    "player_pass_rush_reception_yds",
])

NBA_PROP_MARKETS = ",".join([
    "player_points",
    "player_rebounds",
    "player_assists",
    "player_points_rebounds_assists",
    "player_points_rebounds",
    "player_points_assists",
    "player_rebounds_assists",
    "player_threes",
])

NHL_PROP_MARKETS = ",".join([
    "player_points",
    "player_assists",
    "player_goals",
    "player_shots_on_goal",
])

MLB_PROP_MARKETS = ",".join([
    "batter_hits",
    "batter_total_bases",
    "batter_rbis",
    "batter_runs_scored",
    "pitcher_strikeouts",
])

# Map your short sport codes -> Odds API sport keys
SPORT_KEY_MAP = {
    "NFL":   "americanfootball_nfl",
    "NCAAF": "americanfootball_ncaaf",
    "NBA":   "basketball_nba",
    "NCAAB": "basketball_ncaab",
    "NHL":   "icehockey_nhl",
    "MLB":   "baseball_mlb",
}
# Which player prop markets to request per sport from The Odds API

MARKET_KEYS_BY_SPORT: dict[str, list[str]] = {
    # NFL & NCAAF player props
    "NFL": [
        "player_pass_yds",
        "player_rush_yds",
        "player_reception_yds",
        "player_receptions",
        "player_rush_attempts",
        "player_pass_tds",
        "player_rush_tds",
        "player_reception_tds",
        "player_points",  # kickers, etc. if available
    ],
    "NCAAF": [
        "player_pass_yds",
        "player_rush_yds",
        "player_reception_yds",
        "player_receptions",
        "player_rush_attempts",
    ],
    # NBA, NCAAB
    "NBA": [
        "player_points",
        "player_rebounds",
        "player_assists",
        "player_points_rebounds_assists",
        "player_threes",
        "player_turnovers",
    ],
    "NCAAB": [
        "player_points",
        "player_rebounds",
        "player_assists",
        "player_points_rebounds_assists",
    ],
    # NHL
    "NHL": [
        "player_points",
        "player_goals",
        "player_assists",
        "player_shots_on_goal",
        "player_power_play_points",
    ],
    # MLB
    "MLB": [
        "batter_total_bases",
        "batter_hits",
        "batter_hits_runs_rbis",
        "pitcher_strikeouts",
        "pitcher_outs",
    ],
}


