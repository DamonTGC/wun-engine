"""simulation.py

Use your 50k-simulation stat model (engine/simulation.py) to estimate
cover probability and EV for each NormalizedProp, then assign tiers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from normalizer import NormalizedProp
from tiers import Tier, assign_tier
from engine import simulation as core_sim


@dataclass
class PropResult:
    prop: NormalizedProp
    implied_prob: float  # naive implied from decimal odds
    cover_prob: float    # p_cover from your 50k sim
    ev: float            # EV per 1 unit stake
    tier: Tier
    avg_stat: float      # average simulated stat (for display)


def _implied_prob_from_decimal(decimal_odds: float) -> float:
    if decimal_odds <= 1.0:
        return 0.0
    return 1.0 / decimal_odds


def _market_from_prop(p: NormalizedProp) -> dict:
    """Bridge NormalizedProp -> engine.simulation market dict."""
    # Map to the shape simulate_prop_ev expects
    direction = "over"
    if p.side.lower().startswith("u"):
        direction = "under"
    # Yes/No markets we treat like Over/Under with a dummy line
    line = float(p.line or 0.0)
    if p.market_key in ("player_anytime_td",):
        if direction == "over":  # treat yes as over 0.5
            line = 0.5
        else:
            line = 0.5

    market = {
        "sport": p.sport,
        "type": "prop",
        "game_id": p.event_id,
        "book": p.bookmaker,
        "team": p.team,
        "player": p.player_name,
        "stat_type": p.market_key,
        "direction": direction,
        "line": line,
        # engine.simulation expects American odds for EV,
        # but simulate_prop_ev only uses them inside ev_from_prob_and_odds.
        # We'll convert decimal -> American with a helper below.
        "odds": decimal_to_american(p.decimal_odds),
        "home_team": p.home_team,
        "away_team": p.away_team,
    }
    return market


def decimal_to_american(d: float) -> float:
    """Convert decimal odds to American-style odds.

    This keeps EV consistent whether you think in decimal or American.
    """
    if d <= 1.0:
        return 0.0
    if d >= 2.0:
        # positive odds
        return (d - 1.0) * 100.0
    # negative odds
    return -100.0 / (d - 1.0)


def evaluate_props(props: List[NormalizedProp]) -> List[PropResult]:
    """Run your 50k simulation model on each prop and attach EV/tier.

    This does NOT try to build a market-wide consensus; each book's line+price
    is evaluated with the same underlying stat model.
    """
    results: List[PropResult] = []
    for p in props:
        if p.decimal_odds <= 1.0:
            continue

        implied_prob = _implied_prob_from_decimal(p.decimal_odds)
        market = _market_from_prop(p)
        sim_res = core_sim.simulate_prop_ev(market)
        cover_prob = sim_res.get("p_cover", 0.5)
        ev = sim_res.get("ev", 0.0)
        avg_stat = sim_res.get("avg_stat", 0.0)
        tier = assign_tier(ev=ev, cover_prob=cover_prob, market_key=p.market_key)

        results.append(
            PropResult(
                prop=p,
                implied_prob=implied_prob,
                cover_prob=cover_prob,
                ev=ev,
                tier=tier,
                avg_stat=avg_stat,
            )
        )

    results.sort(key=lambda r: r.ev, reverse=True)
    return results
