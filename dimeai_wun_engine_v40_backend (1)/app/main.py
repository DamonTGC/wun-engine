
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import run, search, parlays, teasers, simulate

app = FastAPI(title="WUN Engine v1.0", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(run.router, prefix="")
app.include_router(search.router, prefix="")
app.include_router(parlays.router, prefix="")
app.include_router(teasers.router, prefix="")
app.include_router(simulate.router, prefix="")
