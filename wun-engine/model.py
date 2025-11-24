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
# --- Account & social models (for future DB integration) ---
from dataclasses import dataclass
from typing import Optional, Literal


@dataclass
class UserAccount:
    id: str
    email: str
    display_name: str
    subscription_tier: str = "free"  # "free", "pro", "whale"


@dataclass
class SubscriptionTier:
    tier_id: str  # "free", "pro", "whale"
    name: str
    max_sports: int
    max_slip_size: int
    description: str


@dataclass
class SocialPost:
    id: str
    user_id: str
    text: str
    sport: Optional[str] = None
    created_at: Optional[str] = None
