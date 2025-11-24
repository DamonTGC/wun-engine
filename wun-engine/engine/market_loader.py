# engine/market_loader.py

from pathlib import Path
import json
from typing import List, Dict, Any

from .live_odds import fetch_live_events, normalize_all_markets

ROOT = Path(__file__).resolve().parents[1]
MARKETS_CONFIG_PATH = ROOT / "config" / "markets.json"


def load_markets_config() -> Dict[str, Any]:
    """Load config/markets.json."""
    with MARKETS_CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_markets_for_page(sport: str, page: str) -> List[Dict[str, Any]]:
    """
    Return normalized markets for a given sport + page.

    sport: "NFL", "NBA", "MLB", etc.
    page:  "straights", "props", ...
    """
    sport = sport.upper()
    cfg = load_markets_config()
    sport_cfg = cfg.get(sport, {})

    if not sport_cfg:
        print(f"[WARN] No config found for sport={sport}")
        return []

    page_cfg = sport_cfg.get(page)
    if not page_cfg:
        print(f"[WARN] No page config for sport={sport} page={page}")
        return []

    live_market_list = page_cfg.get("live_markets", [])
    if not live_market_list:
        print(f"[WARN] No live_markets for sport={sport} page={page}")
        return []

    raw_events = fetch_live_events(sport, live_market_list)
    if not raw_events:
        print(f"[WARN] No raw events from odds API for {sport} {page}")
        return []

    markets = normalize_all_markets(sport, raw_events, live_market_list)
    return markets
