"""api.py

FastAPI app exposing Wun Engine functionality.

Core endpoints:
  GET  /health
  GET  /props/top
  GET  /props/search
  GET  /props/search_nlp
  GET  /props/{prop_id}

Plus early stubs for:
  - account system & subscription tiers
  - basic social feed
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from services import (
    get_top_props_by_sport,
    search_props,
    search_props_advanced,
    get_prop_detail,
)

app = FastAPI(title="Wun Engine", version="0.2.0")


# Allow your Netlify / local dev origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/props/top")
async def props_top(
    sport: str = Query("NBA", description="Sport code, e.g. NBA, NFL, NCAAB"),
    limit: int = Query(50, ge=1, le=200),
    max_events: int = Query(20, ge=1, le=100),
    subscription_tier: int | None = Query(
        0,
        description="User subscription tier: 0=free,1=Nickel access,3=all tiers. None=internal no-limit.",
    ),
):
    """Return top props for a sport, ranked by EV.

    subscription_tier controls which tiers are visible vs blurred.
    """
    data = get_top_props_by_sport(
        sport=sport,
        limit=limit,
        max_events=max_events,
        subscription_tier=subscription_tier,
    )
    return {"sport": sport.upper(), "count": len(data), "props": data}


@app.get("/props/search")
async def props_search(
    sport: str = Query("NBA", description="Sport code, e.g. NBA, NFL, NCAAB"),
    q: str = Query("", description="Search text"),
    limit: int = Query(15, ge=1, le=100),
    max_events: int = Query(20, ge=1, le=100),
    subscription_tier: int | None = Query(
        0,
        description="User subscription tier: 0=free,1=Nickel access,3=all tiers. None=internal no-limit.",
    ),
):
    """Basic substring search across props (player, team, event, market).

    Respects subscription_tier for visibility/blur logic.
    """
    if not q:
        raise HTTPException(status_code=400, detail="q is required for /props/search")
    data = search_props(
        sport=sport,
        query=q,
        limit=limit,
        max_events=max_events,
        subscription_tier=subscription_tier,
    )
    return {"sport": sport.upper(), "query": q, "results": data}


@app.get("/props/search_nlp")
async def props_search_nlp(
    sport: str = Query("NBA", description="Sport code, e.g. NBA, NFL, NCAAB"),
    q: str = Query("", description="Natural language prompt"),
    limit: int = Query(15, ge=1, le=100),
    max_events: int = Query(20, ge=1, le=100),
    subscription_tier: int | None = Query(
        0,
        description="User subscription tier: 0=free,1=Nickel access,3=all tiers. None=internal no-limit.",
    ),
):
    """Advanced prompt based search ("give me Dime Plays only for a 3 pick power play").

    Respects subscription_tier for visibility/blur logic.
    """
    if not q:
        raise HTTPException(status_code=400, detail="q is required for /props/search_nlp")
    payload = search_props_advanced(
        sport=sport,
        query=q,
        limit=limit,
        max_events=max_events,
        subscription_tier=subscription_tier,
    )
    return {
        "sport": sport.upper(),
        "query": q,
        "parsed": payload["parsed"],
        "results": payload["results"],
    }


@app.get("/props/{prop_id}")
async def props_detail(prop_id: str):
    detail = get_prop_detail(prop_id)
    if not detail:
        raise HTTPException(status_code=404, detail="prop_id not found or not in cache yet")
    return detail


# ===========================
# Account & subscription stubs
# ===========================

# NOTE: These are placeholders to make it easy to bolt on a real auth system
# (JWT, OAuth, Supabase, Firebase, etc.). They do NOT implement real
# authentication or persistence yet.

SUBSCRIPTION_PLANS: Dict[str, Dict[str, Any]] = {
    "free": {
        "name": "Free",
        "level": 0,
        "max_sports": 2,
        "max_slip_size": 3,
        "visible_tiers": ["Standard Plays"],
        "description": "Free profile, straights, parlays pages. Only Standard Plays are fully visible.",
    },
    "pro": {
        "name": "Pro",
        "level": 1,
        "max_sports": 6,
        "max_slip_size": 6,
        "visible_tiers": ["Standard Plays", "Nickel Plays"],
        "description": "Access to all pages and Nickel Plays (Standard + Nickel visible, Dime Plays blurred.",
    },
    "whale": {
        "name": "Whale",
        "level": 3,
        "max_sports": 6,
        "max_slip_size": 6,
        "visible_tiers": ["Standard Plays", "Nickel Plays", "Dime Plays"],
        "description": "Top tier: all plays visible including Dime Plays.",
    },
}


@app.get("/account/plans")
async def account_plans():
    """Return static subscription plan definitions.

    Your frontend can use this to show a pricing table while you wire
    a real payment provider.
    """
    return {"plans": SUBSCRIPTION_PLANS}



# ===========================
# Social feed stubs
# ===========================

# Long-term you might back this with Postgres or Supabase. For now, we just
# expose placeholder endpoints that your UI can call & mock.

FAKE_FEED: list[Dict[str, Any]] = [
    {
        "id": "demo-1",
        "user": "DemoWhale",
        "tier": "whale",
        "sport": "NBA",
        "text": "3-pick Dime Plays power play hit last night 💰",            "created_at": "2025-11-23T00:00:00Z",
    }
]


@app.get("/social/feed")
async def social_feed():
    """Temporary social feed stub.

    Later: filter by sport, follow list, etc.
    """
    return {"feed": FAKE_FEED}


@app.post("/social/post")
async def social_post(payload: Dict[str, Any]):
    """Temporary endpoint to accept a new post.

    Currently just echos it back; in real deployment you'd persist to DB.
    """
    post = {
        "id": f"local-{len(FAKE_FEED)+1}",
        "user": payload.get("user", "anon"),
        "tier": payload.get("tier", "free"),
        "sport": payload.get("sport", "NBA"),
        "text": payload.get("text", ""),
        "created_at": payload.get("created_at") or "2025-11-23T00:00:00Z",
    }
    FAKE_FEED.append(post)
    return post
