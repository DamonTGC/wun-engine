
from fastapi import APIRouter
from typing import Any, Dict, List
from app.montecarlo.simulate_game import simulate_matchup

router = APIRouter()

@router.post("/search")
async def search_engine(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    prompt = payload.get("prompt", "").lower()
    # TODO: parse the prompt into filters; for now just return same sample as /run
    sample = simulate_matchup("Team A", "Team B", "NFL", sims=20000)
    return [{
        "id": "NFL-SEARCH-TEAM-A-B",
        "team": sample["team_a"],
        "opponent": sample["team_b"],
        "league": sample["league"],
        "gameTime": "8:15 PM",
        "market": "Spread",
        "odds": "-2.5",
        "ev": 0.05,
        "pctToCover": int(sample["prob_team_a_win"] * 100),
        "avg5": [24, 21, 27, 20, 30],
        "avgSimScore": sample["avg_score"],
    }]
