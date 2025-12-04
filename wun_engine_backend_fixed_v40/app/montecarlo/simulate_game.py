
import random
from typing import Dict, Any

def simulate_matchup(team_a: str, team_b: str, league: str, sims: int = 10000) -> Dict[str, Any]:
    # NOTE: This is a **placeholder** Monte Carlo – you should replace with your full model.
    # Right now it just samples random scores around simple baselines.
    base_scores = {
        "NFL": (24, 21),
        "NCAAF": (30, 24),
        "NBA": (112, 108),
        "NCAAB": (71, 67),
        "MLB": (4, 3),
        "NHL": (3, 2),
    }
    a_base, b_base = base_scores.get(league, (24, 21))

    a_scores = []
    b_scores = []
    for _ in range(sims):
        a_scores.append(random.gauss(a_base, a_base * 0.15))
        b_scores.append(random.gauss(b_base, b_base * 0.15))

    a_avg = sum(a_scores) / len(a_scores)
    b_avg = sum(b_scores) / len(b_scores)

    # simple win prob
    wins_a = sum(1 for a, b in zip(a_scores, b_scores) if a > b)
    prob_a_win = wins_a / sims

    return {
        "team_a": team_a,
        "team_b": team_b,
        "league": league,
        "avg_score": [round(a_avg,1), round(b_avg,1)],
        "prob_team_a_win": round(prob_a_win,4),
        "prob_team_b_win": round(1-prob_a_win,4),
        "sims": sims,
    }
