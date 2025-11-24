"""
tiers.py

Adds goblin / demon / premium tagging based on:
- EV strength
- Cover probability
- Market type

This file makes your PrizePicks-style Goblin + Demon system work.
"""

from __future__ import annotations
from typing import Literal

Tier = Literal["demon", "goblin", "standard"]

def assign_tier(ev: float, cover_prob: float) -> Tier:
    """
    Assign a tier based on EV & cover probability.
    These thresholds can be tuned to your exact PrizePicks strategy.
    """

    # --- DEMON TIER ---
    # Extremely high confidence picks
    if ev >= 0.20 and cover_prob >= 0.62:
        return "demon"

    # --- GOBLIN TIER ---
    # Good EV but not elite
    if ev >= 0.10 and cover_prob >= 0.55:
        return "goblin"

    # --- STANDARD ---
    return "standard"


def tier_weight(tier: Tier) -> float:
    """
    Utility weighting for sorting & selecting prop combos.
    """
    if tier == "demon":
        return 3.0
    if tier == "goblin":
        return 2.0
    return 1.0
