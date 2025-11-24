from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from engine.tiles import generate_tiles

app = FastAPI(title="WUN Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/tiles")
def tiles(body: dict):
    sport = body.get("sport", "ALL")
    page = body.get("page", "straights")
    prompt = body.get("prompt", "")
    tier = body.get("tier", "free")

    return generate_tiles(sport, page, prompt, tier)
