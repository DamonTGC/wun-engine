"""ev.py

Standalone helpers for working with EV (expected value).
"""
from __future__ import annotations

from typing import Optional


def implied_prob_from_decimal(decimal_odds: float) -> float:
    if decimal_odds <= 1.0:
        return 0.0
    return 1.0 / decimal_odds


def ev_from_prob(decimal_odds: float, true_prob: float, stake: float = 1.0) -> float:
    """Expected profit for a bet with decimal odds and true_prob.

    EV = p * (odds - 1) * stake - (1 - p) * stake
    """
    if decimal_odds <= 1.0:
        return 0.0
    return true_prob * (decimal_odds - 1.0) * stake - (1.0 - true_prob) * stake
