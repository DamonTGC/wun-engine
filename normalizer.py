# normalizer.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class NormalizedProp:
    event_id: str
    sport: str
    league: str
    player: str
    stat_type: str
    line: float
    over_odds: Optional[float]
    under_odds: Optional[float]
    book: str
    raw: dict


def normalize_player_prop(event_id: str, sport: str, league: str, prop: dict, bookmaker: str) -> NormalizedProp:
    """
    Converts raw OddsAPI player-prop format into our standard format.
    This prevents any null values inside the engine.
    """

    player = prop.get("player", "Unknown Player")
    stat_type = prop.get("market", "unknown_market")

    line = prop.get("line")
    if line is None:
        line = float(prop.get("point", 0))

    over_odds = None
    under_odds = None

    outcomes = prop.get("outcomes", [])
    for o in outcomes:
        name = o.get("name", "").lower()

        if "over" in name:
            over_odds = o.get("price")
        elif "under" in name:
            under_odds = o.get("price")

    return NormalizedProp(
        event_id=event_id,
        sport=sport,
        league=league,
        player=player,
        stat_type=stat_type,
        line=line,
        over_odds=over_odds,
        under_odds=under_odds,
        book=bookmaker,
        raw=prop
    )
