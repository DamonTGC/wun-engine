from typing import Any, Dict, List

from config import (
    SPORT_KEY_MAP,
    DEFAULT_REGIONS,
    DEFAULT_MAIN_MARKETS,
)
from http_client import odds_get


def get_main_odds_for_sport(
    sport_code: str,
    markets: str | None = None,
    regions: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Fetch main markets (h2h, spreads, totals) for a given sport.

    sport_code: "NFL", "NBA", "NHL", etc.
    returns: list of events (as dicts from Odds API)
    """
    if sport_code not in SPORT_KEY_MAP:
        raise ValueError(f"Unknown sport_code: {sport_code}")

    sport_key = SPORT_KEY_MAP[sport_code]

    params: Dict[str, Any] = {
        "regions": regions or DEFAULT_REGIONS,
        "markets": markets or DEFAULT_MAIN_MARKETS,
    }

    data, _ = odds_get(f"sports/{sport_key}/odds", params)
    # data is already a list of events
    return data


if __name__ == "__main__":
    # Quick manual test, similar to test_https.py but reusing your engine code
    from pprint import pprint

    for code in ["NFL", "NBA", "NHL", "MLB", "NCAAF", "NCAAB"]:
        try:
            events = get_main_odds_for_sport(code)
            print(f"\n=== {code}: {len(events)} events ===")
            if events:
                pprint(events[0])
        except Exception as e:
            print(f"[{code}] ERROR:", e)
