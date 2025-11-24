"""services.py

Service layer for Wun Engine.

Exposes high-level functions used by the API and (optionally) by your
frontend directly:
  - get_top_props_by_sport
  - search_props (basic)
  - search_props_advanced (NLP-ish prompt)
  - get_prop_detail
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List, Optional, Tuple

from normalizer import NormalizedProp
from props_fetch import fetch_player_props_for_sport
from simulation import PropResult, evaluate_props
from tiers import Tier
from cache import cache_props_for_sport, get_cached_props_for_sport

# Subscription visibility helpers
# Tier levels (numeric) for accounts:
#   0 = free       -> can see Standard Plays only
#   1 = mid tier   -> can see Standard + Nickel Plays
#   3 = top tier   -> can see all (Dime + Nickel + Standard)


def can_see_tier(subscription_tier: Optional[int], play_tier: str) -> bool:
    """Return True if a user subscription tier can see a given play tier.

    subscription_tier:
      - 0 -> Standard Plays only
      - 1 -> Standard + Nickel Plays
      - 3 -> all tiers
      - None -> no restriction (see everything, e.g. internal use)
    """
    if subscription_tier is None:
        return True

    if subscription_tier >= 3:
        return True

    if subscription_tier >= 1:
        return play_tier in ("Nickel Plays", "Standard Plays")

    # tier 0 or anything lower: Standard only
    return play_tier == "Standard Plays"



# In-process index of latest PropResult per ID. This does not persist, but
# is rebuilt whenever we refresh props for a sport.
_PROP_RESULTS_BY_ID: Dict[str, PropResult] = {}


# ---------------------
# Core refresh helpers
# ---------------------

def _load_props_with_cache(
    sport: str,
    max_events: int,
    cache_max_age_seconds: int = 300,
) -> List[NormalizedProp]:
    """Return NormalizedProp list for sport, using SQLite cache when fresh."""
    sport = sport.upper()
    cached = get_cached_props_for_sport(sport, cache_max_age_seconds)
    props: List[NormalizedProp] = []
    if cached is not None:
        for item in cached:
            # convert dict back to NormalizedProp
            props.append(NormalizedProp(**item))
        return props

    # Cache miss or stale -> fetch from Odds API
    fresh_props = fetch_player_props_for_sport(sport, max_events=max_events)
    # Persist as plain dicts
    serializable = [asdict(p) for p in fresh_props]
    cache_props_for_sport(sport, serializable)
    return fresh_props


def _refresh_results_for_sport(
    sport: str,
    max_events: int,
    cache_max_age_seconds: int = 300,
) -> List[PropResult]:

    props = _load_props_with_cache(sport, max_events=max_events, cache_max_age_seconds=cache_max_age_seconds)
    results = evaluate_props(props)

    # Rebuild in-memory index for this sport
    global _PROP_RESULTS_BY_ID
    for r in results:
        _PROP_RESULTS_BY_ID[r.prop.id] = r
    return results


# ---------------------
# Public services
# ---------------------

# ---------------------
# Public services
# ---------------------

def get_top_props_by_sport(
    sport: str,
    limit: int = 50,
    max_events: int = 20,
    cache_max_age_seconds: int = 300,
    subscription_tier: Optional[int] = None,
) -> List[Dict]:
    """Return top props for a sport, ranked by EV, up to limit.

    If subscription_tier is provided, results include a `visible` flag and are
    sorted so visible (unblurred) picks appear first for that user tier.
    """
    sport = sport.upper()
    results = _refresh_results_for_sport(
        sport, max_events=max_events, cache_max_age_seconds=cache_max_age_seconds
    )

    # For subscription enticement: visible ones first, then blurred ones.
    # We don't drop anything; the frontend can blur locked tiers.
    def sort_key(res: PropResult):
        visible = can_see_tier(subscription_tier, res.tier)
        # visible first, then by tier weight and EV
        tier_bonus = {"Dime Plays": 2, "Nickel Plays": 1, "Standard Plays": 0}.get(res.tier, 0)
        return (1 if visible else 0, tier_bonus, res.ev)

    results_sorted = sorted(results, key=sort_key, reverse=True)

    out: List[Dict] = []
    for r in results_sorted[:limit]:
        p = r.prop
        visible = can_see_tier(subscription_tier, r.tier)
        out.append(
            {
                "id": p.id,
                "sport": p.sport,
                "league": p.league,
                "event_id": p.event_id,
                "event_name": p.event_name,
                "commence_time": p.commence_time.isoformat(),
                "home_team": p.home_team,
                "away_team": p.away_team,
                "player_name": p.player_name,
                "team": p.team,
                "opponent": p.opponent,
                "market_key": p.market_key,
                "line": p.line,
                "side": p.side,
                "bookmaker": p.bookmaker,
                "decimal_odds": p.decimal_odds,
                "implied_prob": r.implied_prob,
                "cover_prob": r.cover_prob,
                "ev": r.ev,
                "tier": r.tier,
                "tier_label": r.tier,
                "avg_stat": r.avg_stat,
                "visible": visible,
                "blurred": not visible,
            }
        )
    return out

def _basic_match(p: NormalizedProp, q: str) -> bool:
    q = q.lower()
    if q in (p.player_name or "").lower():
        return True
    if q in (p.event_name or "").lower():
        return True
    if q in (p.home_team or "").lower():
        return True
    if q in (p.away_team or "").lower():
        return True
    if q in (p.market_key or "").lower():
        return True
    return False


def search_props(
    sport: str,
    query: str,
    limit: int = 15,
    max_events: int = 20,
    cache_max_age_seconds: int = 300,
    subscription_tier: Optional[int] = None,
) -> List[Dict]:
    """Simple text search across props for a sport.

    Respects subscription_tier for visibility/blur logic.
    """
    sport = sport.upper()
    results = _refresh_results_for_sport(
        sport, max_events=max_events, cache_max_age_seconds=cache_max_age_seconds
    )

    q = query.strip().lower()
    filtered: List[PropResult] = []

    for r in results:
        if _basic_match(r.prop, q):
            filtered.append(r)

    # If nothing matches by text, just return top EV
    if not filtered:
        filtered = results

    # Sort primarily by EV, secondarily by tier weight
    def rank_key(res: PropResult):
        tier_bonus = {"Dime Plays": 2, "Nickel Plays": 1, "Standard Plays": 0}.get(res.tier, 0)
        return (res.ev, tier_bonus)

    filtered.sort(key=rank_key, reverse=True)

    # Apply visibility & ensure visible ones appear first in the returned slice
    def sort_with_visibility(res: PropResult):
        visible = can_see_tier(subscription_tier, res.tier)
        tier_bonus = {"Dime Plays": 2, "Nickel Plays": 1, "Standard Plays": 0}.get(res.tier, 0)
        return (1 if visible else 0, tier_bonus, res.ev)

    filtered = sorted(filtered, key=sort_with_visibility, reverse=True)

    out: List[Dict] = []
    for r in filtered[:limit]:
        p = r.prop
        visible = can_see_tier(subscription_tier, r.tier)
        out.append(
            {
                "id": p.id,
                "sport": p.sport,
                "league": p.league,
                "event_id": p.event_id,
                "event_name": p.event_name,
                "commence_time": p.commence_time.isoformat(),
                "home_team": p.home_team,
                "away_team": p.away_team,
                "player_name": p.player_name,
                "team": p.team,
                "opponent": p.opponent,
                "market_key": p.market_key,
                "line": p.line,
                "side": p.side,
                "bookmaker": p.bookmaker,
                "decimal_odds": p.decimal_odds,
                "implied_prob": r.implied_prob,
                "cover_prob": r.cover_prob,
                "ev": r.ev,
                "tier": r.tier,
                "tier_label": r.tier,
                "avg_stat": r.avg_stat,
                "visible": visible,
                "blurred": not visible,
            }
        )
    return out

def _parse_advanced_query(query: str) -> Dict:
    """Very small parser for prompts like:

    - "give me Dime Plays only for a 3 pick power play"
    - "best Nickel Plays nba tonight"
    - "high ev overs only"
    """
    q = query.lower()
    tiers: List[Tier] = []
    min_ev: float = 0.0
    slip_size: Optional[int] = None
    want_power_play: bool = False

    # Tier preferences based on words in the query
    if "dime play" in q or "dime plays" in q or "dime" in q:
        tiers.append("Dime Plays")
    if "nickel play" in q or "nickel plays" in q or "nickel" in q:
        tiers.append("Nickel Plays")
    if "standard play" in q or "standard plays" in q or "standard" in q:
        tiers.append("Standard Plays")

    if "high ev" in q or "best ev" in q or "% ev" in q:
        min_ev = 0.05

    # crude detection of slip size like "3 pick", "3-pick", "3 leg"
    for n in range(2, 7):
        if f"{n} pick" in q or f"{n}-pick" in q or f"{n} leg" in q:
            slip_size = n
            break

    if "power play" in q:
        want_power_play = True

    if not tiers:
        tiers = ["Dime Plays", "Nickel Plays", "Standard Plays"]

    return {
        "tiers": tiers,
        "min_ev": min_ev,
        "slip_size": slip_size,
        "want_power_play": want_power_play,
    }


def search_props_advanced(
    sport: str,
    query: str,
    limit: int = 15,
    max_events: int = 20,
    cache_max_age_seconds: int = 300,
    subscription_tier: Optional[int] = None,
) -> Dict:
    """Advanced prompt-based search.

    Returns both the parsed filters and the matching props so your
    frontend can say "Dime AI interpreted this as: Dime Plays only, 3-pick power play".
    """
    sport = sport.upper()
    parsed = _parse_advanced_query(query)
    tiers: List[Tier] = parsed["tiers"]
    min_ev: float = parsed["min_ev"]
    slip_size: Optional[int] = parsed["slip_size"]

    results = _refresh_results_for_sport(
        sport, max_events=max_events, cache_max_age_seconds=cache_max_age_seconds
    )

    filtered: List[PropResult] = []
    for r in results:
        if r.tier not in tiers:
            continue
        if r.ev < min_ev:
            continue
        filtered.append(r)

    # If still nothing, fall back to best EV regardless of tier
    if not filtered:
        filtered = results

    # Sort by tier priority then EV
    def sort_key(res: PropResult):
        tier_rank_map = {
            "Dime Plays": 2,
            "Nickel Plays": 1,
            "Standard Plays": 0,
        }
        tier_rank = tier_rank_map.get(res.tier, 0)
        return (tier_rank, res.ev)

    filtered.sort(key=sort_key, reverse=True)

    # If user said "3 pick power play", you probably want at least 3 props back.
    target_count = max(limit, slip_size or 0) if slip_size else limit

    # Apply visibility ordering as final pass
    def sort_with_visibility(res: PropResult):
        visible = can_see_tier(subscription_tier, res.tier)
        tier_rank_map = {
            "Dime Plays": 2,
            "Nickel Plays": 1,
            "Standard Plays": 0,
        }
        tier_rank = tier_rank_map.get(res.tier, 0)
        return (1 if visible else 0, tier_rank, res.ev)

    filtered = sorted(filtered, key=sort_with_visibility, reverse=True)

    out_props: List[Dict] = []
    for r in filtered[:target_count]:
        p = r.prop
        visible = can_see_tier(subscription_tier, r.tier)
        out_props.append(
            {
                "id": p.id,
                "sport": p.sport,
                "league": p.league,
                "event_id": p.event_id,
                "event_name": p.event_name,
                "commence_time": p.commence_time.isoformat(),
                "home_team": p.home_team,
                "away_team": p.away_team,
                "player_name": p.player_name,
                "team": p.team,
                "opponent": p.opponent,
                "market_key": p.market_key,
                "line": p.line,
                "side": p.side,
                "bookmaker": p.bookmaker,
                "decimal_odds": p.decimal_odds,
                "implied_prob": r.implied_prob,
                "cover_prob": r.cover_prob,
                "ev": r.ev,
                "tier": r.tier,
                "tier_label": r.tier,
                "avg_stat": r.avg_stat,
                "visible": visible,
                "blurred": not visible,
            }
        )

    return {
        "parsed": parsed,
        "results": out_props,
    }

def get_prop_detail(prop_id: str) -> Optional[Dict]:
    """Return detailed info for a single prop, including best 5 books."""
    base = _PROP_RESULTS_BY_ID.get(prop_id)
    if not base:
        return None

    p = base.prop

    # group key for same underlying bet (ignoring bookmaker)
    group_key = (
        p.sport,
        p.league,
        p.event_id,
        p.market_key,
        p.player_name,
        float(p.line),
        p.side,
    )

    books_seen: Dict[str, PropResult] = {}
    for res in _PROP_RESULTS_BY_ID.values():
        pp = res.prop
        gk = (
            pp.sport,
            pp.league,
            pp.event_id,
            pp.market_key,
            pp.player_name,
            float(pp.line),
            pp.side,
        )
        if gk != group_key:
            continue
        prev = books_seen.get(pp.bookmaker)
        if prev is None or res.ev > prev.ev:
            books_seen[pp.bookmaker] = res

    top_books = sorted(
        [
            {
                "bookmaker": r.prop.bookmaker,
                "decimal_odds": r.prop.decimal_odds,
                "implied_prob": r.implied_prob,
                "cover_prob": r.cover_prob,
                "ev": r.ev,
            }
            for r in books_seen.values()
        ],
        key=lambda x: x["ev"],
        reverse=True,
    )[:5]

    detail = {
        "id": p.id,
        "sport": p.sport,
        "league": p.league,
        "event_id": p.event_id,
        "event_name": p.event_name,
        "commence_time": p.commence_time.isoformat(),
        "home_team": p.home_team,
        "away_team": p.away_team,
        "player_name": p.player_name,
        "team": p.team,
        "opponent": p.opponent,
        "market_key": p.market_key,
        "line": p.line,
        "side": p.side,
        "tier": base.tier,
        "ev": base.ev,
        "cover_prob": base.cover_prob,
        "avg_stat": base.avg_stat,
        "top_books": top_books,
    }
    return detail
