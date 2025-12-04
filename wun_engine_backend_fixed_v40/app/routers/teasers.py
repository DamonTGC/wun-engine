
from fastapi import APIRouter
from typing import Any, Dict, List

router = APIRouter()

@router.post("/teasers")
async def teasers_engine(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    # TODO: implement real teaser logic; for now, stub.
    return [{
        "id": "TEASER-1",
        "teaserPoints": 6,
        "legs": [
            {"team": "Team A", "opponent": "Team B", "origSpread": "-3.5", "teasedSpread": "+2.5"},
            {"team": "Team C", "opponent": "Team D", "origSpread": "+7.5", "teasedSpread": "+13.5"},
        ],
        "combinedEV": 0.08,
        "combinedProb": 0.42,
        "book": "GenericBook"
    }]
