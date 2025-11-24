import json
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"

with open(CONFIG_DIR / "rules.json") as f:
    RULES = json.load(f)

def apply_dedup_rules(tiles, page):
    """Remove duplicate wagers & enforce rules like one market per game."""
    page_rules = RULES["pages"].get(page, {})
    one_market_per_game = page_rules.get("one_market_per_game", False)

    seen_gm = set()
    seen_exact = set()
    out = []

    for t in tiles:
        g = t.get("game", "")
        m = t.get("market", "")
        key_gm = f"{g}|{m}"
        key_exact = f"{m}|{t.get('line') or t.get('line_text')}|{t.get('team') or t.get('player')}"

        if one_market_per_game and key_gm in seen_gm:
            continue

        if key_exact in seen_exact:
            continue

        seen_gm.add(key_gm)
        seen_exact.add(key_exact)
        out.append(t)

    return out


def apply_quota_and_tiers(tiles, sport, page, tier):
    """Assign tiles as free/premium."""
    g = RULES["global"]

    free_all = g["free_tiles_all"]
    free_sport = g["free_tiles_per_sport"]

    if page != "straights":
        for i, t in enumerate(tiles):
            t["tier"] = "free" if i < 2 else "premium"
        return tiles

    if sport == "ALL":
        for i, t in enumerate(tiles):
            t["tier"] = "free" if i < free_all else "premium"
    else:
        for i, t in enumerate(tiles):
            t["tier"] = "free" if i < free_sport else "premium"

    return tiles
