# pricing.py
"""
Pricing utilities for DimeAI:
- decimal odds <-> implied probability
- American odds <-> decimal
- simple vig removal for two-way markets
"""

from typing import Tuple


# ---------- Basic conversions ----------

def decimal_to_implied_prob(decimal_odds: float) -> float:
    """
    Convert decimal odds (e.g. 1.87) -> implied probability (0-1).
    """
    if decimal_odds <= 0:
        return 0.0
    return 1.0 / decimal_odds


def implied_prob_to_decimal(prob: float) -> float:
    """
    Convert implied probability (0-1) -> decimal odds.
    """
    if prob <= 0:
        return 0.0
    return 1.0 / prob


def american_to_decimal(american: int) -> float:
    """
    Convert American odds to decimal odds.
    e.g. -120 -> 1.83, +150 -> 2.5
    """
    if american == 0:
        return 0.0

    if american > 0:
        return 1.0 + american / 100.0
    else:
        return 1.0 + 100.0 / abs(american)


def decimal_to_american(decimal_odds: float) -> int:
    """
    Convert decimal odds to American odds.
    e.g. 1.83 -> -120 (approx), 2.5 -> +150 (approx)
    """
    if decimal_odds <= 1.0:
        return 0

    if decimal_odds >= 2.0:
        # positive American
        return int(round((decimal_odds - 1.0) * 100.0))
    else:
        # negative American
        return int(round(-100.0 / (decimal_odds - 1.0)))


# ---------- Vig (margin) removal for 2-way markets ----------

def remove_vig_two_way(
    price_over: float,
    price_under: float,
) -> Tuple[float, float]:
    """
    Given decimal odds for Over and Under, return "fair" probabilities
    after removing the bookmaker margin.

    Returns:
        (p_over_fair, p_under_fair)

    If something is wrong (bad prices), will fall back to normalized raw probs.
    """
    p_over_raw = decimal_to_implied_prob(price_over)
    p_under_raw = decimal_to_implied_prob(price_under)

    total = p_over_raw + p_under_raw
    if total <= 0:
        return 0.5, 0.5  # fallback

    # Normalize to 1.0 (remove vig)
    p_over_fair = p_over_raw / total
    p_under_fair = p_under_raw / total

    return p_over_fair, p_under_fair


# ---------- Simple EV helper ----------

def expected_value(
    win_prob: float,
    decimal_odds: float,
    stake: float = 1.0,
) -> float:
    """
    Compute EV (in stake units) of a single bet with decimal odds.

    EV = P(win) * (payout - stake) + (1 - P(win)) * (-stake)
       = P(win) * (decimal_odds * stake - stake) - (1 - P(win)) * stake
    """
    payout_if_win = decimal_odds * stake
    profit_if_win = payout_if_win - stake
    loss_if_lose = stake

    return win_prob * profit_if_win - (1.0 - win_prob) * loss_if_lose
