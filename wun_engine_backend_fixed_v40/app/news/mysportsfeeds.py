
import os
from typing import Any, Dict, List
import httpx
import base64

MSF_KEY = os.getenv("MSF_KEY")
MSF_PASS = os.getenv("MSF_PASSWORD")

async def fetch_nfl_news() -> List[Dict[str, Any]]:
    if not MSF_KEY or not MSF_PASS:
        return []
    auth_raw = f"{MSF_KEY}:{MSF_PASS}"
    token = base64.b64encode(auth_raw.encode()).decode()
    headers = {"Authorization": f"Basic {token}"}
    url = "https://api.mysportsfeeds.com/v2.1/pull/nfl/latest/news.json"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, headers=headers)
        if r.status_code != 200:
            return []
        data = r.json()
        # you can shape this however you want later
        return data.get("news", [])
