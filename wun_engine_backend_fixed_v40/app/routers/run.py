
from fastapi import APIRouter
from typing import Any, Dict, List
from app.montecarlo.simulate_game import simulate_matchup

router = APIRouter()

@router.post("/run")
async def run_engine(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    # TODO: wire in real odds + news, iterate all games, call simulate_matchup per game.
    # For now, return a couple of dummy tilized picks.
    results: List[Dict[str, Any]] = []

    sample = simulate_matchup("Team A", "Team B", "NFL", sims=20000)
    results.append({
        "id": "NFL-TEAM-A-B",
        "team": sample["team_a"],
        "opponent": sample["team_b"],
        "league": sample["league"],
        "gameTime": "7:20 PM",
        "market": "Spread",
        "odds": "-3.5",
        "ev": 0.07,
        "pctToCover": int(sample["prob_team_a_win"] * 100),
        "avg5": [24, 21, 27, 20, 30],
        "avgSimScore": sample["avg_score"],
    })

    return results
