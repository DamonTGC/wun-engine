# engine/tiles.py

from typing import List, Dict, Any

from .market_loader import get_markets_for_page
from .simulation import (
    best_line_for_straight_market,
    best_line_for_prop_market,
    american_to_implied,
    ev_from_prob_and_odds,  # <-- NEW: fallback EV if needed
)


def decide_top_n(page: str, tier: str) -> int:
    """
    How many tiles to show for different pages and tiers.
    """
    if tier == "free":
        if page == "straights":
            return 10
        if page == "props":
            return 5
        if page == "parlays":
            return 5
        if page == "teasers":
            return 3

    # subscriber tiers
    if page in ("straights", "props"):
        return 50
    if page == "parlays":
        return 20
    if page == "teasers":
        return 10
    return 20


def dedupe_markets_one_per_team_per_game(
    markets: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Enforce 'one market per team per game' (or per team/side/stat).
    """
    groups: Dict[tuple, List[Dict[str, Any]]] = {}

    for m in markets:
        key = (
            m.get("sport"),
            m.get("game_id"),
            m.get("type"),      # spread/total/moneyline/prop
            m.get("team"),
            m.get("side"),
            m.get("stat_type"),
            m.get("direction"),
        )
        groups.setdefault(key, []).append(m)

    deduped: List[Dict[str, Any]] = []
    for _, group in groups.items():
        best = sorted(
            group,
            key=lambda g: american_to_implied(g.get("odds") or 0),
            reverse=True,
        )[0]
        deduped.append(best)

    return deduped


def generate_single_leg_tiles(
    sport: str,
    page: str,
    prompt: str,
    tier: str,
) -> List[Dict[str, Any]]:
    """
    Straights & props: one leg per tile.
    """
    page = page.lower()
    sport = sport.upper()

    # 1) Get markets for this page
    if page == "straights":
        markets = get_markets_for_page(sport, "straights")
    else:
        markets = get_markets_for_page(sport, "props")

    # 2) Enforce one market per team per game
    markets = dedupe_markets_one_per_team_per_game(markets)

    tiles: List[Dict[str, Any]] = []

    # 3) Convert each market into a tile
    for m in markets:
        if page == "straights":
            base = best_line_for_straight_market(m)
        else:
            base = best_line_for_prop_market(m)

        # If our EV engine can't handle this market, skip it
        if not base:
            continue

        # ---------- FALLBACKS: make sure pCover / ev / avgMetric never null ----------

        odds = base.get("odds")
        p_cover = base.get("pCover")
        ev = base.get("ev")

        # If pCover missing, approximate from odds
        if p_cover is None and odds is not None:
            approx_p = american_to_implied(odds)
            p_cover = round(approx_p, 4)
            ev = round(ev_from_prob_and_odds(approx_p, odds), 4)
            base["pCover"] = p_cover
            base["ev"] = ev

        # avgMetric / avgStat for UI display
        if page == "straights":
            avg_score_or_stat = base.get("avgMetric")
            if avg_score_or_stat is None:
                # fallback: use line as rough center if sim didn't give avg
                avg_score_or_stat = base.get("line")
        else:
            avg_score_or_stat = base.get("avgStat")
            if avg_score_or_stat is None:
                avg_score_or_stat = base.get("line")

        # ---------- Build tile ----------

        tile = {
            "page": page,
            "sport": base.get("sport"),
            "gameId": base.get("gameId"),
            "book": base.get("book"),
            "marketType": base.get("marketType"),
            "team": base.get("team"),
            "player": base.get("player"),
            "statType": base.get("statType"),
            "direction": base.get("direction"),
            "line": base.get("line"),
            "odds": base.get("odds"),
            "pCover": p_cover,
            "ev": ev,
            "avgScoreOrStat": avg_score_or_stat,
            "homeTeam": base.get("homeTeam"),
            "awayTeam": base.get("awayTeam"),
            "legs": 1,
            "blurred": (tier == "free"),
        }

        tiles.append(tile)

    tiles.sort(key=lambda t: (t.get("ev") or 0), reverse=True)
    top_n = decide_top_n(page, tier)
    return tiles[:top_n]


def generate_parlay_tiles(sport: str, prompt: str, tier: str) -> List[Dict[str, Any]]:
    """
    Bundle straight-leg tiles into basic parlays.
    """
    base_legs = generate_single_leg_tiles(sport, "straights", prompt, tier="sub")
    base_legs = base_legs[:20]

    parlays: List[Dict[str, Any]] = []

    for i in range(len(base_legs)):
        for j in range(i + 1, min(i + 5, len(base_legs))):
            legs = [base_legs[i], base_legs[j]]

            p = 1.0
            for leg in legs:
                p *= (leg.get("pCover") or 0.5)

            ev = p * 2.6 - (1 - p)

            parlays.append({
                "page": "parlays",
                "sport": sport,
                "legs": len(legs),
                "legsDetail": legs,
                "pHit": round(p, 4),
                "parlayEV": round(ev, 4),
                "blurred": (tier == "free"),
            })

    parlays.sort(key=lambda t: t["parlayEV"], reverse=True)
    return parlays[:decide_top_n("parlays", tier)]


def generate_teaser_tiles(sport: str, prompt: str, tier: str) -> List[Dict[str, Any]]:
    """
    Simple teaser tiles built from many straights.
    """
    base_legs = generate_single_leg_tiles(sport, "straights", prompt, tier="sub")
    base_legs = base_legs[:40]

    teasers: List[Dict[str, Any]] = []
    chunk = 10

    for i in range(0, len(base_legs), chunk):
        legs = base_legs[i:i + chunk]
        if len(legs) < 10:
            break

        p = 1.0
        for leg in legs:
            p *= (leg.get("pCover") or 0.5)

        ev = p * 6.0 - (1 - p)

        teasers.append({
            "page": "teasers",
            "sport": sport,
            "legs": len(legs),
            "legsDetail": legs,
            "pHit": round(p, 4),
            "teaserEV": round(ev, 4),
            "blurred": (tier == "free"),
        })

    teasers.sort(key=lambda t: t["teaserEV"], reverse=True)
    return teasers[:decide_top_n("teasers", tier)]


def generate_tiles(sport: str, page: str, prompt: str, tier: str = "free"):
    """
    Main entry point for WUN tiles.
    """
    page = page.lower()
    sport = sport.upper()

    if page in ("straights", "props"):
        return generate_single_leg_tiles(sport, page, prompt, tier)
    if page == "parlays":
        return generate_parlay_tiles(sport, prompt, tier)
    if page == "teasers":
        return generate_teaser_tiles(sport, prompt, tier)

    print(f"[WARN] Unknown page: {page}")
    return []
