
from fastapi import APIRouter
from typing import Any, Dict, List

router = APIRouter()

@router.post("/parlays")
async def parlays_engine(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    # TODO: build parlay combinations based on engine outputs.
    # For now, return a stub parlay with two legs.
    return [{
        "id": "PARLAY-1",
        "legs": [
            {"team": "Team A", "opponent": "Team B", "market": "Spread", "odds": "-3.5"},
            {"team": "Team C", "opponent": "Team D", "market": "Total", "odds": "O 47.5"},
        ],
        "combinedEV": 0.12,
        "combinedProb": 0.35,
        "book": "GenericBook"
    }]
