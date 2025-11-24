# ev.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from normalizer import NormalizedProp


def american_to_decimal(odds: float | int | None) -> Optional[float]:
    """Convert American odds to decimal odds."""
    if odds is None:
        return None
    odds = float(odds)
    if odds > 0:
        return 1.0 + odds / 100.0
    elif odds < 0:
        return 1.0 + 100.0 / abs(odds)
    else:
        # treat 0 as +100 (even money) just in case
        return 2.0


def american_to_implied_prob(odds: float | int | None) -> Optional[float]:
    """Convert American odds to implied probability (no vig removed)."""
    if odds is None:
        return None
    odds = float(odds)
    if odds > 0:
        return 100.0 / (odds + 100.0)
    elif odds < 0:
        return -odds / (-odds + 100.0)
    else:
        return 0.5


@dataclass
class PropEV:
    prop: NormalizedProp
    side: Literal["over", "under"]
    prob: float          # “true” prob (can include your model edge later)
    decimal_odds: float  # decimal odds at the book
    ev_per_unit: float   # expected profit per 1 unit risked


def calc_side_ev(prob: float, american_odds: float) -> float:
    """
    Expected profit per 1 unit risked:
      EV = p * (decimal - 1) - (1 - p) * 1
    """
    dec = american_to_decimal(american_odds)
    if dec is None:
        return 0.0
    win_profit = dec - 1.0
    lose_cost = 1.0
    return prob * win_profit - (1.0 - prob) * lose_cost


def estimate_prop_ev(
    prop: NormalizedProp,
    edge_boost: float = 0.0,
) -> dict[str, PropEV]:
    """
    Given a NormalizedProp, estimate EV for over and under.

    Right now, we use implied probability from the odds and optionally tilt by
    edge_boost. Later, you will plug in your full simulation model here
    (replace or modify over_prob / under_prob).
    """
    over_prob = american_to_implied_prob(prop.over_price)
    under_prob = american_to_implied_prob(prop.under_price)

    # Basic fallbacks if one side is missing
    if over_prob is None and under_prob is None:
        return {}

    if over_prob is None and under_prob is not None:
        over_prob = 1.0 - under_prob
    if under_prob is None and over_prob is not None:
        under_prob = 1.0 - over_prob

    # Apply a generic model edge if you want (push prob toward the better side)
    if (
        edge_boost != 0.0
        and over_prob is not None
        and under_prob is not None
    ):
        if over_prob >= under_prob:
            over_prob = min(1.0, max(0.0, over_prob + edge_boost))
            under_prob = 1.0 - over_prob
        else:
            under_prob = min(1.0, max(0.0, under_prob + edge_boost))
            over_prob = 1.0 - under_prob

    result: dict[str, PropEV] = {}

    if over_prob is not None and prop.over_price is not None:
        ev_over = calc_side_ev(over_prob, prop.over_price)
        result["over"] = PropEV(
            prop=prop,
            side="over",
            prob=over_prob,
            decimal_odds=american_to_decimal(prop.over_price) or 0.0,
            ev_per_unit=ev_over,
        )

    if under_prob is not None and prop.under_price is not None:
        ev_under = calc_side_ev(under_prob, prop.under_price)
        result["under"] = PropEV(
            prop=prop,
            side="under",
            prob=under_prob,
            decimal_odds=american_to_decimal(prop.under_price) or 0.0,
            ev_per_unit=ev_under,
        )

    return result

