# models.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class NormalizedProp:
    sport: str                   # "NBA", "NFL"
    league_key: str             # "basketball_nba"
    event_id: str
    event_name: str             # "Lakers @ Nuggets"
    commence_time: str          # ISO str or datetime

    book: str                   # "draftkings", "fanduel", etc.

    market_key: str             # "player_points", "player_assists"
    player: str                 # "LeBron James"
    side: str                   # "Over" or "Under"
    line: float                 # 28.5
    price: float                # 1.87 (decimal odds)

    team: Optional[str] = None  # may fill later if needed
