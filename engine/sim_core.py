# engine/sim_core.py

from typing import Dict, Any, List
import random


def simulate_spread_50000(mu_diff: float, sigma_diff: float) -> Dict[str, Any]:
    """
    Simulate 50,000 point-diff outcomes (home - away).
    Uses your idea:
      - 50% = both average
      - 25% = home bad / away good
      - 25% = home good / away bad
    """
    n = 50000
    diffs: List[float] = []

    n_base = int(0.5 * n)
    n_home_bad = int(0.25 * n)
    n_home_good = n - n_base - n_home_bad

    # 50% average
    for _ in range(n_base):
        d = random.gauss(mu_diff, sigma_diff)
        diffs.append(d)

    # 25% home bad / away good (shift mean down)
    for _ in range(n_home_bad):
        d = random.gauss(mu_diff - 3.0, sigma_diff)
        diffs.append(d)

    # 25% home good / away bad (shift mean up)
    for _ in range(n_home_good):
        d = random.gauss(mu_diff + 3.0, sigma_diff)
        diffs.append(d)

    avg_diff = sum(diffs) / len(diffs)

    return {
        "avg_diff": avg_diff,
        "samples": diffs,
    }


def simulate_total_50000(mu_total: float, sigma_total: float) -> Dict[str, Any]:
    """
    Simulate 50,000 game totals (home + away points).
    Same pattern: 50% average, 25% low, 25% high.
    """
    n = 50000
    totals: List[float] = []

    n_base = int(0.5 * n)
    n_low = int(0.25 * n)
    n_high = n - n_base - n_low

    for _ in range(n_base):
        t = random.gauss(mu_total, sigma_total)
        totals.append(t)

    for _ in range(n_low):
        t = random.gauss(mu_total - 7.0, sigma_total)
        totals.append(t)

    for _ in range(n_high):
        t = random.gauss(mu_total + 7.0, sigma_total)
        totals.append(t)

    avg_total = sum(totals) / len(totals)

    return {
        "avg_total": avg_total,
        "samples": totals,
    }


def simulate_prop_50000(mu_stat: float, sigma_stat: float) -> Dict[str, Any]:
    """
    Simulate 50,000 outcomes for a player stat (points, yards, etc.).
    """
    n = 50000
    stats: List[float] = []

    n_base = int(0.5 * n)
    n_low = int(0.25 * n)
    n_high = n - n_base - n_low

    for _ in range(n_base):
        s = random.gauss(mu_stat, sigma_stat)
        stats.append(s)

    for _ in range(n_low):
        s = random.gauss(mu_stat - sigma_stat, sigma_stat)
        stats.append(s)

    for _ in range(n_high):
        s = random.gauss(mu_stat + sigma_stat, sigma_stat)
        stats.append(s)

    avg_stat = sum(stats) / len(stats)

    return {
        "avg_stat": avg_stat,
        "samples": stats,
    }

