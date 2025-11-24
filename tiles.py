from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from normalizer import NormalizedProp, normalize_odds_api_events
from props_fetch import fetch_odds_for_sport


# ---------- Prompt parsing helpers ----------


def _detect_sport_from_prompt(prompt: str) -> Tuple[str, str]:
    """
    Map a free-text prompt to an Odds API sport key + human label.
    Default: NBA.
    """
    p = prompt.lower()

    if "nfl" in p or "football" in p:
        return "americanfootball_nfl", "NFL"
    if "nhl" in p or "hockey" in p:
        return "icehockey_nhl", "NHL"
    if "cbb" in p or "college basketball" in p or "ncaa basketball" in p:
        return "basketball_ncaab", "NCAA Basketball"
    if "cfb" in p or "college football" in p:
        return "americanfootball_ncaaf", "NCAA Football"
    if "wnba" in p:
        return "basketball_wnba", "WNBA"

    # default
    return "basketball_nba", "NBA"


def _tier_for_confidence(conf: float) -> str:
    """
    Very simple tiering based ONLY on market-implied probability.

    - demon  : super high confidence (market thinks it's ~62%+)
    - goblin : solid lean (~57–62%)
    - free   : everything else
    """
    if conf >= 0.62:
        return "demon"
    if conf >= 0.57:
        return "goblin"
    return "free"


# ---------- Core tile generation ----------


def _prop_to_tile(p: NormalizedProp) -> Dict[str, Any]:
    """
    Convert a NormalizedProp to a front-end-friendly dict ("tile").
    """
    return {
        "id": p.id,
        "sport": p.sport,
        "league": p.league,
        "event_id": p.event_id,
        "event_start": p.event_start.isoformat(),
        "home_team": p.home_team,
        "away_team": p.away_team,
        "player": p.player_name,
        "market": p.market,
        "line": p.line,
        "bookmaker": p.bookmaker,
        "over_price": p.over_price,
        "under_price": p.under_price,
        "best_side": p.best_side,
        "best_side_prob": p.best_side_prob,
        "confidence_score": p.confidence_score,
        "tier": _tier_for_confidence(p.confidence_score or 0.0),
    }


def _build_summary(
    prompt: str,
    sport_label: str,
    props: List[NormalizedProp],
) -> str:
    """
    Build a short "Dime analysis" string that you can show above the tiles.
    """
    if not props:
        return (
            f"Dime AI read your prompt \"{prompt}\" but couldn't find live "
            f"{sport_label} player props right now."
        )

    n_props = len(props)
    n_games = len({p.event_id for p in props})

    top = sorted(props, key=lambda p: (p.confidence_score or 0.0), reverse=True)[:3]

    lines = [
        f"Dime AI interpretation → {sport_label} slate, focusing on player props.",
        f"Found {n_props} props across {n_games} games.",
        "Top edges by market-implied confidence:",
    ]

    for p in top:
        side = p.best_side or "over"
        prob = (p.confidence_score or 0.0) * 100.0
        lines.append(
            f"• {p.player_name} {side} {p.line} {p.market} at {p.bookmaker} "
            f"(~{prob:.1f}% implied)."
        )

    return "\n".join(lines)


def generate_tiles(
    sport: Optional[str] = None,
    page: Optional[str] = None,
    prompt: Optional[str] = None,
    tier: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main entry point used by api/main.py.

    - If `sport` is given (e.g., "NBA"), we respect it.
    - Otherwise, we infer sport from the free-text `prompt`.

    Returns a dict with:
      {
        "summary": str,
        "tiles": [ { ...tile... }, ... ]
      }
    """
    prompt = (prompt or "").strip() or "today's slate"

    # decide sport
    if sport:
        sport_lower = sport.lower()
        if sport_lower in {"nba", "basketball_nba"}:
            sport_key, sport_label = "basketball_nba", "NBA"
        elif sport_lower in {"nfl", "americanfootball_nfl"}:
            sport_key, sport_label = "americanfootball_nfl", "NFL"
        elif sport_lower in {"nhl", "icehockey_nhl"}:
            sport_key, sport_label = "icehockey_nhl", "NHL"
        elif sport_lower in {"cbb", "ncaab", "basketball_ncaab"}:
            sport_key, sport_label = "basketball_ncaab", "NCAA Basketball"
        elif sport_lower in {"cfb", "ncaaf", "americanfootball_ncaaf"}:
            sport_key, sport_label = "americanfootball_ncaaf", "NCAA Football"
        else:
            sport_key, sport_label = _detect_sport_from_prompt(prompt)
    else:
        sport_key, sport_label = _detect_sport_from_prompt(prompt)

    # 1) fetch raw odds for that sport
    raw_events = fetch_odds_for_sport(sport_key)

    # 2) normalize to a flat list of props
    props = normalize_odds_api_events(
        sport=sport_key, league=sport_label, raw_events=raw_events
    )

    # Optional: filter by requested tier
    if tier and tier.lower() in {"free", "goblin", "demon"}:
        wanted = tier.lower()
        props = [
            p
            for p in props
            if _tier_for_confidence(p.confidence_score or 0.0) == wanted
        ]

    # Sort by descending confidence
    props.sort(key=lambda p: (p.confidence_score or 0.0), reverse=True)

    # Simple pagination by "page" (each "page" = 25 tiles)
    page_index = 0
    try:
        if page is not None:
            page_index = max(int(page), 0)
    except ValueError:
        page_index = 0

    PAGE_SIZE = 25
    start = page_index * PAGE_SIZE
    end = start + PAGE_SIZE
    page_props = props[start:end]

    tiles = [_prop_to_tile(p) for p in page_props]
    summary = _build_summary(prompt, sport_label, props)

    return {"summary": summary, "tiles": tiles}
