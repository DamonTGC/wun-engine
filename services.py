# services.py
from props_fetch import fetch_player_props_for_sport
from simulation import simulate_prop
from tiers import tag_tier
from normalizer import NormalizedProp

def _enrich_props(props: list[NormalizedProp]) -> list[NormalizedProp]:
    enriched = []
    for p in props:
        p = simulate_prop(p)
        p = tag_tier(p)
        enriched.append(p)
    return enriched

def get_top_props(sport: str, limit: int = 50) -> list[NormalizedProp]:
    props = fetch_player_props_for_sport(sport)
    enriched = _enrich_props(props)

    # Keep only those with EV and cover_prob
    enriched = [p for p in enriched if p.ev_pct is not None and p.cover_prob is not None]

    enriched.sort(key=lambda p: (p.ev_pct, p.cover_prob), reverse=True)
    return enriched[:limit]
def search_props(sport: str, query: str, limit: int = 15) -> list[NormalizedProp]:
    props = fetch_player_props_for_sport(sport)
    enriched = _enrich_props(props)

    q = query.lower()

    filtered = [
        p for p in enriched
        if q in p.player.lower()
        or q in (p.team or "").lower()
        or q in p.market_key.lower()
        or q in p.display_market.lower()
    ]

    if not filtered:
        filtered = enriched

    plus_ev = [p for p in filtered if p.ev_pct is not None and p.ev_pct > 0]

    candidates = plus_ev if plus_ev else filtered

    candidates.sort(key=lambda p: (p.ev_pct or -999, p.cover_prob or 0), reverse=True)
    return candidates[:limit]
def get_prop_detail(prop_id: str) -> dict:
    # In a real app you’d look this up from a cache or DB.
    # For now, re-fetch everything and find the prop.
    # (Later: use caching in Phase 5 to avoid this.)
    all_sports = ["NFL", "NBA", "NCAAF", "NCAAB", "NHL", "MLB"]
    for sport in all_sports:
        props = _enrich_props(fetch_player_props_for_sport(sport))
        for p in props:
            if p.id == prop_id:
                history = []  # TODO: plug in your stats source
                return {
                    "prop": p,
                    "history": history,
                    "top_books": [b.__dict__ for b in p.all_books[:5]],
                }
    return {}
