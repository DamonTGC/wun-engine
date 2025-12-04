
from fastapi import APIRouter
from typing import Any, Dict
from app.montecarlo.simulate_game import simulate_matchup

router = APIRouter()

@router.post("/simulate")
async def simulate_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    team_a = payload.get("teamA", "Team A")
    team_b = payload.get("teamB", "Team B")
    league = payload.get("league", "NFL")
    sims = payload.get("sims", 10000)
    return simulate_matchup(team_a, team_b, league, sims)
