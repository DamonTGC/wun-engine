"""tiers.py

Wun Engine play tiers based on EV and cover probability.

Public names:
  - "Dime Plays"     -> highest confidence, highest EV
  - "Nickel Plays"   -> strong +EV, solid edge
  - "Standard Plays" -> everything else
"""
from __future__ import annotations

from typing import Literal

# We store the human-readable labels directly as the tier value so your
# frontend can show them without extra mapping.
Tier = Literal["Dime Plays", "Nickel Plays", "Standard Plays"]


def assign_tier(ev: float, cover_prob: float, market_key: str) -> Tier:
    """Assign a tier based on EV and cover probability.

    You can tweak these thresholds to match your personal risk profile.
    """
    # Top-shelf: big edge + high hit rate
    if ev >= 0.10 and cover_prob >= 0.60:
        return "Dime Plays"

    # Strong +EV with solid hit rate
    if ev >= 0.05 and cover_prob >= 0.55:
        return "Nickel Plays"

    # Baseline tier
    return "Standard Plays"


def tier_weight(tier: Tier) -> float:
    """Utility weighting for sorting & building slips."""
    if tier == "Dime Plays":
        return 3.0
    if tier == "Nickel Plays":
        return 2.0
    return 1.0


def tier_rank(tier: Tier) -> int:
    """Numeric intensity ranking for tiers.

    Higher is stronger. Useful for sorting and UI hints.
    """
    if tier == "Dime Plays":
        return 3
    if tier == "Nickel Plays":
        return 2
    return 1  # Standard Plays
