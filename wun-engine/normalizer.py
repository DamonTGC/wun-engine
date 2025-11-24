"""normalizer.py

Convert raw The Odds API player prop responses into a standard NormalizedProp
structure that the rest of Wun Engine can use.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime

from config import YES_NO_MARKETS


@dataclass
class NormalizedProp:
    """Canonical representation of a player prop from any book."""

    id: str

    sport: str           # "NBA", "NFL"
    league: str          # "basketball_nba"
    event_id: str
    event_name: str
    commence_time: datetime
    home_team: str
    away_team: str

    player_name: str
    team: Optional[str]
    opponent: Optional[str]

    market_key: str      # e.g. "player_points"
    line: float          # 27.5
    side: str            # "Over", "Under", "Yes", "No"

    bookmaker: str       # "draftkings"
    decimal_odds: float

    raw_bookmaker: Dict[str, Any]
    raw_market: Dict[str, Any]
    raw_outcome: Dict[str, Any]


def _parse_commence_time(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return datetime.utcnow()


def _normalize_side(market_key: str, outcome: Dict[str, Any]) -> str:
    """Convert Odds API outcome names/descriptions into Over/Under/Yes/No."""
    desc = (outcome.get("description") or outcome.get("name") or "").lower()
    if market_key in YES_NO_MARKETS:
        if "no" in desc:
            return "No"
        return "Yes"
    if "under" in desc:
        return "Under"
    if "over" in desc:
        return "Over"
    # Fallback: guess based on presence of '+' or '-' is too hacky; default Over
    return "Over"


def _build_prop_id(
    league: str,
    event_id: str,
    market_key: str,
    player_name: str,
    line: float,
    side: str,
    bookmaker: str,
) -> str:
    return "|".join(
        [
            league,
            event_id,
            market_key,
            player_name.replace("|", " "),
            f"{line:.3f}",
            side,
            bookmaker,
        ]
    )


def normalize_event_player_props(
    sport_label: str,
    league_key: str,
    event: Dict[str, Any],
    bookmakers: List[Dict[str, Any]],
    allowed_markets: List[str],
) -> List[NormalizedProp]:
    """Normalize all player prop markets for a single event.

    This expects the shape returned from:
      GET /v4/sports/{league_key}/events/{event_id}/odds
    with the bookmakers list included.
    """
    props: List[NormalizedProp] = []

    event_id = event.get("id") or ""
    event_name = event.get("name") or ""
    commence_time = _parse_commence_time(event.get("commence_time") or "")
    home_team = event.get("home_team") or ""
    away_team = event.get("away_team") or ""

    for bm in bookmakers:
        bm_key = bm.get("key") or "unknown_book"
        markets = bm.get("markets") or []
        for m in markets:
            market_key = m.get("key") or ""
            if allowed_markets and market_key not in allowed_markets:
                continue
            outcomes = m.get("outcomes") or []
            for outcome in outcomes:
                player_name = outcome.get("description") or outcome.get("name") or ""
                line = float(outcome.get("point") or 0.0)
                price = float(outcome.get("price") or outcome.get("odds") or 0.0)
                side = _normalize_side(market_key, outcome)

                # Try to infer team / opponent from description if Odds API provides
                team = outcome.get("team") or None
                opponent = None  # could be enriched later

                pid = _build_prop_id(
                    league_key,
                    event_id,
                    market_key,
                    player_name,
                    line,
                    side,
                    bm_key,
                )
                p = NormalizedProp(
                    id=pid,
                    sport=sport_label.upper(),
                    league=league_key,
                    event_id=event_id,
                    event_name=event_name,
                    commence_time=commence_time,
                    home_team=home_team,
                    away_team=away_team,
                    player_name=player_name,
                    team=team,
                    opponent=opponent,
                    market_key=market_key,
                    line=line,
                    side=side,
                    bookmaker=bm_key,
                    decimal_odds=price,
                    raw_bookmaker=bm,
                    raw_market=m,
                    raw_outcome=outcome,
                )
                props.append(p)

    return props
