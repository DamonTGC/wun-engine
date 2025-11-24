from __future__ import annotations

"""
tiles.py

Standalone tile generator for the WUN Engine.

Right now this DOES NOT CALL The Odds API – it uses
pattern data plus some variation to:

- Build straights / props / parlay / teaser tiles
- Assign EV and a tier (standard / nickel / dime)
- Respect the requested user tier ("free", "nickel", "dime")
  by marking tiles as blurred or visible
- Apply simple prompt filtering (team / player / market words)

This keeps the engine running cleanly on Railway while we
finish wiring in the full Odds API + 50k-sim model.
"""

from typing import Any, Dict, List, Tuple


# -------------------------------------------------------
# Base pattern data (mirrors the look of your frontend)
# -------------------------------------------------------

BASE_STRAIGHTS: List[Dict[str, Any]] = [
    {
        "page": "straights",
        "sport": "NFL",
        "label": "Bills @ Jets",
        "stat": "Spread",
        "line": "BUF -3.5",
        "ev": 6.4,
        "team_name": "Buffalo Bills vs New York Jets",
        "jersey": "17",
        "primary_color": "#00338D",
        "secondary_color": "#C60C30",
        "game": "Pre-match • Spread",
        "price": "-110",
    },
    {
        "page": "straights",
        "sport": "NBA",
        "label": "Lakers @ Warriors",
        "stat": "Total",
        "line": "O 228.5",
        "ev": 5.1,
        "team_name": "Los Angeles Lakers vs Golden State Warriors",
        "jersey": "23",
        "primary_color": "#FDB927",
        "secondary_color": "#552583",
        "game": "Pre-match • O/U",
        "price": "-110",
    },
    {
        "page": "straights",
        "sport": "NHL",
        "label": "Avs @ Canucks",
        "stat": "Moneyline",
        "line": "COL -125",
        "ev": 4.2,
        "team_name": "Colorado Avalanche vs Vancouver Canucks",
        "jersey": "29",
        "primary_color": "#6F263D",
        "secondary_color": "#236192",
        "game": "Pre-match • ML",
        "price": "-125",
    },
]

BASE_PROPS: List[Dict[str, Any]] = [
    {
        "page": "props",
        "sport": "NBA",
        "player": "James Harden",
        "stat": "PRA",
        "line": "41.5",
        "ev": 9.3,
        "team_name": "Los Angeles Clippers",
        "jersey": "1",
        "primary_color": "#C8102E",
        "secondary_color": "#1D428A",
        "game": "LAC @ ORL • Prop",
        "price": "-119",
    },
    {
        "page": "props",
        "sport": "NFL",
        "player": "Josh Allen",
        "stat": "Pass+Rush YDS",
        "line": "295.5",
        "ev": 6.8,
        "team_name": "Buffalo Bills",
        "jersey": "17",
        "primary_color": "#00338D",
        "secondary_color": "#C60C30",
        "game": "BUF @ NYJ • Prop",
        "price": "-115",
    },
    {
        "page": "props",
        "sport": "NBA",
        "player": "Devin Booker",
        "stat": "Points",
        "line": "29.5",
        "ev": 7.4,
        "team_name": "Phoenix Suns",
        "jersey": "1",
        "primary_color": "#E56020",
        "secondary_color": "#1D1160",
        "game": "PHX @ LAL • Prop",
        "price": "-113",
    },
]

BASE_PARLAYS: List[Dict[str, Any]] = [
    {
        "page": "parlays",
        "sport": "NFL",
        "label": "3-leg NFL parlay",
        "stat": "Spread",
        "line": "+600",
        "ev": 12.3,
        "team_name": "Sunday slate",
        "jersey": "3",
        "primary_color": "#125740",
        "secondary_color": "#FFB81C",
        "game": "3 legs • ML / Spread / Total",
        "price": "+600",
        "legs": [
            {"label": "Leg 1", "team": "Bills", "market": "Spread", "line": "-1.5"},
            {"label": "Leg 2", "team": "Chiefs", "market": "ML", "line": "KC ML"},
            {"label": "Leg 3", "team": "Eagles", "market": "Total", "line": "O 44.5"},
        ],
    },
]

BASE_TEASERS: List[Dict[str, Any]] = [
    {
        "page": "teasers",
        "sport": "NFL",
        "label": "10-leg NFL teaser",
        "stat": "Spread",
        "line": "+1000",
        "ev": 22.5,
        "team_name": "Sunday mega teaser",
        "jersey": "10",
        "primary_color": "#FF6F00",
        "secondary_color": "#1B5E20",
        "game": "+7 teaser • 10 legs",
        "price": "+1000",
        "legs": [
            {"label": "Leg 1", "team": "BUF", "market": "+7", "line": "BUF -3.5 ➜ +3.5"},
            {"label": "Leg 2", "team": "KC", "market": "+7", "line": "KC -2.5 ➜ +4.5"},
            {"label": "Leg 3", "team": "PHI", "market": "+7", "line": "PHI -1.5 ➜ +5.5"},
        ],
    },
]


# -------------------------------------------------------
# Tier logic: Standard / Nickel / Dime Plays
# -------------------------------------------------------


def compute_tier(ev: float) -> Tuple[str, str]:
    """
    Map EV% to a tier + label.

    You can tune the thresholds easily here without touching the rest.

    - ev >= 10.0  => "dime"   / "Dime Play"
    - ev >=  6.0  => "nickel" / "Nickel Play"
    - else        => "standard" / "Standard Play"
    """
    if ev >= 10.0:
        return "dime", "Dime Play"
    if ev >= 6.0:
        return "nickel", "Nickel Play"
    return "standard", "Standard Play"


def is_tier_visible_for_user(tile_tier: str, user_tier: str) -> bool:
    """
    Access rules based on subscription tier:

    - free   (tier="free")   => can see only STANDARD plays
    - nickel (tier="nickel") => can see STANDARD + NICKEL
    - dime   (tier="dime")   => can see everything
    """
    user_tier = (user_tier or "free").lower()
    tile_tier = tile_tier.lower()

    if user_tier == "dime":
        return True
    if user_tier == "nickel":
        return tile_tier in {"standard", "nickel"}
    # default = free
    return tile_tier == "standard"


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------


def _base_for_page(page: str) -> List[Dict[str, Any]]:
    page = (page or "").lower()
    if page == "straights":
        return BASE_STRAIGHTS
    if page == "props":
        return BASE_PROPS
    if page == "parlays":
        return BASE_PARLAYS
    if page == "teasers":
        return BASE_TEASERS
    return []


def _clone_tiles(base: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
    """
    Take the small base pattern list and expand up to n tiles with
    small EV / avgLast5 variation so the UI looks populated.

    This is just a front-end demo layer until the real sim hooks in.
    """
    tiles: List[Dict[str, Any]] = []
    for i in range(n):
        pattern = base[i % len(base)]
        bump = ((i % 5) - 2) * 0.5  # -1.0 .. +1.0
        ev = float(pattern["ev"]) + bump
        avg_last5 = max(0.0, ev * 3.0 + 10.0)
        model_val = max(0.0, ev * 6.0 + 200.0)

        t = dict(pattern)
        t["id"] = f"{pattern['page']}-{i+1}"
        t["ev"] = round(ev, 1)
        t["avgLast5"] = round(avg_last5, 1)
        t["model"] = round(model_val, 1)
        tiles.append(t)
    return tiles


def _filter_by_sport(tiles: List[Dict[str, Any]], sport: str) -> List[Dict[str, Any]]:
    sport = (sport or "ALL").upper()
    if sport in ("", "ALL"):
        return tiles
    return [t for t in tiles if t.get("sport", "").upper() == sport]


def _filter_by_prompt(tiles: List[Dict[str, Any]], prompt: str) -> List[Dict[str, Any]]:
    if not prompt:
        return tiles
    q = prompt.lower()

    def match(t: Dict[str, Any]) -> bool:
        pieces = [
            t.get("label", ""),
            t.get("player", ""),
            t.get("team_name", ""),
            t.get("game", ""),
            t.get("stat", ""),
            t.get("line", ""),
        ]
        text = " ".join(str(x) for x in pieces).lower()
        return q in text

    return [t for t in tiles if match(t)]


def _build_summary(prompt: str, page: str, sport: str, total: int) -> str:
    page = (page or "").lower()
    sport = (sport or "ALL").upper()

    if not prompt:
        if sport == "ALL":
            return f"Showing top {total} {page} edges across all sports."
        return f"Showing top {total} {page} edges for {sport}."

    return (
        f"Search for “{prompt}” on {page} – "
        f"{total} high-EV candidates after filters."
    )


# -------------------------------------------------------
# Public entrypoint used by FastAPI (api/main.py)
# -------------------------------------------------------


def generate_tiles(
    sport: str = "ALL",
    page: str = "straights",
    prompt: str = "",
    tier: str = "free",
) -> Dict[str, Any]:
    """
    Main function the FastAPI layer calls.

    Returns JSON shape like:

      {
        "summary": "...",
        "tiles": [
           {
             "id": "props-1",
             "page": "props",
             "sport": "NFL",
             "player": "Josh Allen",
             "stat": "Pass+Rush YDS",
             "line": "295.5",
             "ev": 6.8,
             "avgLast5": 30.1,
             "model": 245.6,
             "tier": "nickel",
             "tier_label": "Nickel Play",
             "visible": false,
             "blurred": true,
             ...
           }
        ]
      }
    """
    page = (page or "straights").lower()
    sport = sport or "ALL"
    prompt = (prompt or "").strip()
    user_tier = (tier or "free").lower()

    base = _base_for_page(page)
    if not base:
        return {"summary": "No tiles for this page yet.", "tiles": []}

    # For straights / props: 50, parlays / teasers: 25
    target_n = 50 if page in ("straights", "props") else 25
    tiles = _clone_tiles(base, target_n)
    tiles = _filter_by_sport(tiles, sport)
    tiles = _filter_by_prompt(tiles, prompt)

    # Attach tier + visibility flags
    for t in tiles:
        ev = float(t.get("ev", 0.0))
        tier_key, tier_label = compute_tier(ev)
        t["tier"] = tier_key          # "standard" | "nickel" | "dime"
        t["tier_label"] = tier_label  # "Standard Play" | "Nickel Play" | "Dime Play"
        t["visible"] = is_tier_visible_for_user(tier_key, user_tier)
        t["blurred"] = not t["visible"]

    summary = _build_summary(prompt, page, sport, len(tiles))

    return {
        "summary": summary,
        "tiles": tiles,
    }

