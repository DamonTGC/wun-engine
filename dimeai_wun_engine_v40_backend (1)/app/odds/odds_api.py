
import os
from typing import List, Dict, Any
import httpx

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

BASE_URL = "https://api.the-odds-api.com/v4"

async def fetch_odds_nfl() -> List[Dict[str, Any]]:
    if not ODDS_API_KEY:
        return []
    url = f"{BASE_URL}/sports/americanfootball_nfl/odds"
    params = {
        "regions": "us",
        "markets": "h2h,spreads,totals",
        "apiKey": ODDS_API_KEY,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, params=params)
        if r.status_code != 200:
            return []
        return r.json()
