from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple


@dataclass
class NormalizedProp:
    """
    Unified representation of a single player prop line across all books.
    """

    id: str
    sport: str
    league: str
    event_id: str
    event_start: datetime
    home_team: str
    away_team: str

    player_name: str
    market: str
    line: float

    bookmaker: str
    over_price: Optional[int]
    under_price: Optional[int]

    # Calculated fields
    best_side: Optional[str] = None  # "over" / "under"
    best_side_prob: Optional[float] = None  # market-implied probability for best side
    confidence_score: Optional[float] = None  # same as best_side_prob (shortcut)


def _parse_commence_time(raw: str) -> datetime:
    """
    Odds API uses ISO8601 timestamps. Always normalize to UTC-aware datetime.
    """
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _american_to_prob(odds: int) -> float:
    """
    Convert American odds to implied probability (ignoring vig).
    """
    if odds is None:
        return 0.0
    if odds > 0:
        return 100.0 / (odds + 100.0)
    return -odds / (-odds + 100.0)


def _normalize_market_key(key: str) -> str:
    """
    Map Odds API market keys to short internal names.
    """
    key = key.lower()
    mapping = {
        "player_points": "points",
        "player_rebounds": "rebounds",
        "player_assists": "assists",
        "player_threes": "threes",
        "player_pass_yards": "pass_yards",
        "player_rush_yards": "rush_yards",
        "player_receiving_yards": "rec_yards",
    }
    return mapping.get(key, key)


def normalize_odds_api_events(
    sport: str, league: str, raw_events: Iterable[Dict[str, Any]]
) -> List[NormalizedProp]:
    """
    Take the raw Odds API response for a sport and return a flat list of NormalizedProp.
    We only keep markets that look like two-way Over/Under player props.
    """
    normalized: List[NormalizedProp] = []

    for ev in raw_events:
        event_id = ev.get("id", "")
        commence_raw = ev.get("commence_time")
        if not commence_raw:
            continue

        event_start = _parse_commence_time(commence_raw)
        home_team = ev.get("home_team", "")
        away_team = ev.get("away_team", "")

        bookmakers = ev.get("bookmakers") or []
        if not bookmakers:
            # This is the "no bookmakers returned" situation you were seeing.
            # We just skip that event instead of blowing up.
            continue

        for book in bookmakers:
            book_title = book.get("title") or book.get("key") or "unknown"
            markets = book.get("markets") or []
            for m in markets:
                raw_key = m.get("key", "")
                market_key = _normalize_market_key(raw_key)

                outcomes = m.get("outcomes") or []
                if len(outcomes) < 2:
                    # Not a standard two-way market; skip
                    continue

                # Odds API usually encodes Over/Under as two outcomes that share
                # the same "point" and "description" (player name).
                # We group by (player, line).
                buckets: Dict[Tuple[str, float], Dict[str, Any]] = {}

                for o in outcomes:
                    name = (o.get("name") or "").lower()
                    line = o.get("point")
                    desc = (
                        o.get("description")
                        or o.get("player")
                        or o.get("participant")
                        or ""
                    )
                    player_name = desc.strip()
                    if player_name == "" or line is None:
                        continue

                    key_tuple = (player_name, float(line))
                    bucket = buckets.setdefault(
                        key_tuple,
                        {
                            "player": player_name,
                            "line": float(line),
                            "over": None,
                            "under": None,
                        },
                    )

                    if "over" in name:
                        bucket["over"] = o.get("price")
                    elif "under" in name:
                        bucket["under"] = o.get("price")

                for (player_name, line), info in buckets.items():
                    over_price = info["over"]
                    under_price = info["under"]

                    if over_price is None and under_price is None:
                        continue

                    # Compute simple confidence score from market-implied probability
                    p_over = _american_to_prob(over_price) if over_price is not None else 0.0
                    p_under = _american_to_prob(under_price) if under_price is not None else 0.0

                    if p_over >= p_under:
                        best_side = "over"
                        best_prob = p_over
                    else:
                        best_side = "under"
                        best_prob = p_under

                    prop_id = f"{event_id}:{book_title}:{player_name}:{market_key}:{line}"

                    normalized.append(
                        NormalizedProp(
                            id=prop_id,
                            sport=sport,
                            league=league,
                            event_id=event_id,
                            event_start=event_start,
                            home_team=home_team,
                            away_team=away_team,
                            player_name=player_name,
                            market=market_key,
                            line=float(line),
                            bookmaker=book_title,
                            over_price=over_price,
                            under_price=under_price,
                            best_side=best_side,
                            best_side_prob=best_prob,
                            confidence_score=best_prob,
                        )
                    )

    return normalized
