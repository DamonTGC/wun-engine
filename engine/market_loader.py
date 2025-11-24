# engine/market_loader.py

from pathlib import Path
import json
from typing import List, Dict, Any

from .live_odds import fetch_live_events, normalize_all_markets

ROOT = Path(__file__).resolve().parents[1]
MARKETS_CONFIG_PATH = ROOT / "config" / "markets.json"


def load_markets_config() -> Dict[str, Any]:
    with MARKETS_CONFIG_PATH.open() as f:
        return json.load(f)


def get_markets_for_page(sport: str, page: str) -> List[Dict[str, Any]]:
    """
    Universal loader:
      - uses config/markets.json
      - picks the 'live_markets' based on sport + page
      - calls Odds API
      - normalizes them
    """
    sport = sport.upper()
    page = page.lower()

    cfg = load_markets_config()
    sport_cfg = cfg.get(sport, {})

    page_cfg = sport_cfg.get(page)
    if not page_cfg:
        print(f"[WARN] No page config for sport={sport} page={page}")
        return []

    wanted_live_markets = page_cfg.get("live_markets", [])
    if not wanted_live_markets:
        print(f"[WARN] No live_markets defined for sport={sport} page={page}")
        return []

    raw_events = fetch_live_events(sport, wanted_live_markets)
    if not raw_events:
        print(f"[WARN] No raw events from odds API for {sport} {page}")
        return []

    return normalize_all_markets(sport, raw_events, wanted_live_markets)
