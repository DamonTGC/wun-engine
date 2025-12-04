
from typing import Dict, Any

def compute_ev(prob: float, decimal_odds: float) -> float:
    """Return expected value as a decimal (e.g. 0.05 = +5% EV)."""
    return prob * decimal_odds - 1.0

def american_to_decimal(american: float) -> float:
    if american > 0:
        return american / 100.0 + 1.0
    else:
        return 100.0 / abs(american) + 1.0
