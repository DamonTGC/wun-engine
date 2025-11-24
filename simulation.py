"""
simulation.py

Takes normalized props and simulates outcomes to estimate:
- cover probability for the listed line
- EV for over and under

This is a simple stub version to get your engine running.
We can make it smarter later by plugging in your true model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional
import math
import random

from normalizer import NormalizedProp


Side = Literal["over", "under", "none"]


@dataclass
class PropSimulationResult:
    prop: NormalizedProp
    cover_prob: float          # probability that OVER covers (>= line)
    ev_over: float             # expected value per 1 unit staked on over
    ev_under: float            # expected value per 1 unit staked on under
    edge_side: Side            # which side has the higher EV
    edge_amount: float         # absolute edge (max(ev_over, ev_under))


def american_to_prob(odds: float) -> float:
    """
    Convert American odds to implied probability.
    odds > 0: 100 / (odds + 100)
    odds < 0: -odds / (-odds + 100)
    """
    if odds == 0:
        return 0.5  # safety fallback
    if odds > 0:
        return 100.0 / (odds + 100.0)
    else:
        return -odds / (-odds + 100.0)


def ev_from_prob(p: float, odds: float) -> float:
    """
    Expected value for 1 unit stake given:
      - p: probability of winning
      - odds: American odds
    """
    if odds == 0:
        return 0.0
    if odds > 0:
        win_return = odds / 100.0      # profit on win for 1 unit staked
    else:
        win_return = 100.0 / -odds     # profit on win for 1 unit staked

    lose_return = -1.0                 # lose stake on loss
    return p * win_return + (1 - p) * lose_return


def simulate_single_prop(
    prop: NormalizedProp,
    num_sims: int = 5000,
    noise_scale: float = 0.15,
) -> PropSimulationResult:
    """
    Very simple simulation:

    - We don't know real mean/variance, so we approximate using the line
      as a central tendency and allow random variation around it.
    - For now, use a normal-ish distribution centered on the line, but
      with some bias to reflect line + implied odds.

    You can later replace this with your real Dime AI model.
    """
    # Base line
    line = prop.line

    # Use odds to shift the “true mean” a bit:
    # if over is juiced (more negative), we move mean slightly above line
    # if under is juiced, move mean slightly below line
    over_imp = american_to_prob(prop.over_price)
    under_imp = american_to_prob(prop.under_price)

    # Normalize to get a “model bias” toward over vs under
    # (this is just a stub; your real model will be much smarter)
    bias = over_imp - under_imp  # positive -> market leans under (since prob higher)
    # shift magnitude in units of stat: e.g. 0.3 -> shift by about 0.3 * noise_scale * line
    shift = -bias * noise_scale * max(1.0, abs(line))

    true_mean = line + shift
    # standard deviation as a fraction of the line, with floor
    true_std = max(1.0, abs(line) * noise_scale)

    over_hits = 0

    for _ in range(num_sims):
        # Draw from normal distro; Python doesn't have directly, so we fake it
        # using Box-Muller or random.gauss if available
        # random.gauss(mu, sigma) is fine here.
        sample = random.gauss(true_mean, true_std)
        if sample >= line:
            over_hits += 1

    cover_prob_over = over_hits / float(num_sims)
    cover_prob_under = 1.0 - cover_prob_over

    ev_over = ev_from_prob(cover_prob_over, prop.over_price)
    ev_under = ev_from_prob(cover_prob_under, prop.under_price)

    if ev_over > ev_under:
        edge_side: Side = "over"
        edge_amount = ev_over
    elif ev_under > ev_over:
        edge_side = "under"
        edge_amount = ev_under
    else:
        edge_side = "none"
        edge_amount = ev_over  # same

    return PropSimulationResult(
        prop=prop,
        cover_prob=cover_prob_over,
        ev_over=ev_over,
        ev_under=ev_under,
        edge_side=edge_side,
        edge_amount=edge_amount,
    )


def simulate_props(
    props: List[NormalizedProp],
    num_sims: int = 5000,
    noise_scale: float = 0.15,
) -> List[PropSimulationResult]:
    """
    Run simulation for a list of normalized props.
    """
    results: List[PropSimulationResult] = []
    for p in props:
        res = simulate_single_prop(p, num_sims=num_sims, noise_scale=noise_scale)
        results.append(res)
    return results
