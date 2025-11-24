from fastapi import FastAPI
from engine.fetch import get_events, get_player_props
from engine.normalize import normalize_props
from engine.simulate import simulate_prop
from engine.ev import calculate_ev
from engine.tiers import assign_tier
from engine.search import search_props
from config.settings import settings

app = FastAPI()

@app.get("/health")
def health(): return {"ok": True}

@app.get("/props/top")
def top_props():
    # simplified demo
    sport="NBA"
    events=get_events(sport)
    out=[]
    for e in events[:2]:
        props=get_player_props(e["id"], sport)
        normalized=normalize_props(props, e, sport)
        for p in normalized:
            sim=simulate_prop(p)
            ev=calculate_ev(sim, p)
            tier=assign_tier(ev)
            p.update({"sim":sim,"ev":ev,"tier":tier})
            out.append(p)
    return out

@app.get("/props/search")
def search(q:str):
    return search_props(q)