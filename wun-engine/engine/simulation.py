# engine/simulation.py

from typing import Dict, Any, List
import random
import math


def american_to_implied(odds: int | float) -> float:
    """
    Convert American odds to implied probability (0–1).
    """
    try:
        o = float(odds)
    except Exception:
        return 0.5

    if o == 0:
        return 0.5

    if o > 0:
        # +150 -> 100/(150+100)
        return 100.0 / (o + 100.0)
    else:
        # -150 -> 150/(150+100)
        return (-o) / ((-o) + 100.0)


def ev_from_prob_and_odds(p: float, odds: int | float) -> float:
    """
    Expected value per 1 unit stake with true prob p and American odds.
    """
    try:
        o = float(odds)
    except Exception:
        return 0.0

    if o == 0:
        return 0.0

    # payout if you win (net profit on 1 unit staked)
    if o > 0:
        win_return = o / 100.0
    else:
        win_return = 100.0 / (-o)

    lose_amount = 1.0
    return p * win_return - (1.0 - p) * lose_amount


# ---------- Core simulation primitives (50,000 sims) ----------

def simulate_spread_50000(mu_diff: float, sigma_diff: float, n: int = 50000) -> Dict[str, Any]:
    """
    Your custom model:
      - 50% of sims: average vs average
      - 25%: home at worst, away at best (diff shifts against home)
      - 25%: home at best, away at worst (diff shifts toward home)

    We approximate this by using 3 different means:
      mu_avg       = mu_diff             (baseline)
      mu_home_bad  = mu_diff - delta
      mu_home_good = mu_diff + delta
    """
    # how far extremes are from average
    delta = max(3.0, abs(mu_diff) * 0.5)

    mu_avg = mu_diff
    mu_home_bad = mu_diff - delta
    mu_home_good = mu_diff + delta

    samples: List[float] = []

    for _ in range(n):
        r = random.random()
        if r < 0.5:
            # 50% average
            s = random.gauss(mu_avg, sigma_diff)
        elif r < 0.75:
            # 25% home worst, away best
            s = random.gauss(mu_home_bad, sigma_diff)
        else:
            # 25% home best, away worst
            s = random.gauss(mu_home_good, sigma_diff)

        samples.append(s)

    avg_diff = sum(samples) / float(n)
    return {"samples": samples, "avg_diff": avg_diff}



def simulate_total_50000(mu_total: float, sigma_total: float, n: int = 50000) -> Dict[str, Any]:
    """
    Your custom model for TOTAL points:
      - 50% of sims: average vs average (mu_total)
      - 25%: worst scoring game (low total)
      - 25%: best scoring game (high total)

    Implemented as a 3-mean Gaussian mixture.
    """
    # How far extremes are from average
    delta = max(5.0, abs(mu_total) * 0.10)

    mu_avg = mu_total
    mu_low = mu_total - delta   # ugly / low scoring game
    mu_high = mu_total + delta  # shootout / high scoring game

    samples: List[float] = []

    for _ in range(n):
        r = random.random()
        if r < 0.5:
            # 50% average
            s = random.gauss(mu_avg, sigma_total)
        elif r < 0.75:
            # 25% low scoring
            s = random.gauss(mu_low, sigma_total)
        else:
            # 25% high scoring
            s = random.gauss(mu_high, sigma_total)

        samples.append(s)

    avg_total = sum(samples) / float(n)
    return {"samples": samples, "avg_total": avg_total}



def simulate_prop_50000(mu_stat: float, sigma_stat: float, n: int = 50000) -> Dict[str, Any]:
    """
    Simulate player stat n times.
    """
    samples: List[float] = []
    for _ in range(n):
        samples.append(max(0.0, random.gauss(mu_stat, sigma_stat)))
    avg_stat = sum(samples) / float(n)
    return {"samples": samples, "avg_stat": avg_stat}


# ---------- TEMP param models (later: replace w/ real models) ----------

def model_params_for_spread(market: Dict[str, Any]) -> Dict[str, float]:
    """
    TEMP: simple model params for spreads.
    Later: load from nfl_spread_model.json etc.
    """
    line = market.get("line") or 0.0
    sigma = 13.0  # rough NFL score spread stdev placeholder
    return {"mu_diff": line, "sigma_diff": sigma}


def model_params_for_total(market: Dict[str, Any]) -> Dict[str, float]:
    """
    TEMP: simple model params for totals.
    Later we can make this per-sport and learned from history.
    """
    line = float(market.get("line") or 0.0)
    sport = (market.get("sport") or "").upper()

    # Rough defaults per sport – tweak later
    if sport in ("NFL", "CFB"):
        sigma = 10.0
    elif sport in ("NBA", "NCAAM"):
        sigma = 15.0
    else:
        sigma = 12.0

    return {"mu_total": line, "sigma_total": sigma}



def model_params_for_prop(market: Dict[str, Any]) -> Dict[str, float]:
    """
    TEMP: simple params for props.
    Later: load from nba_player_prop_model.json, nfl_prop_model.json, etc.
    """
    line = market.get("line") or 20.0
    sigma = max(3.0, abs(line) * 0.25)
    return {"mu_stat": line, "sigma_stat": sigma}


# ---------- EV engines for each market type ----------

def simulate_spread_ev(market: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use 50k sims on point-diff to estimate p_cover and EV for a spread bet.
    Assumes simulated diff = home_score - away_score.
    market['team'] = team you are betting on.
    market['line']  = spread from that team's perspective (like -9.5).
    """
    params = model_params_for_spread(market)
    mu_diff = params["mu_diff"]
    sigma_diff = params["sigma_diff"]

    sim = simulate_spread_50000(mu_diff, sigma_diff)
    diffs = sim["samples"]

    line = market.get("line") or 0.0
    odds = market.get("odds")
    team = market.get("team")
    home_team = market.get("home_team")
    away_team = market.get("away_team")

    covers = 0
    total = float(len(diffs))

    # If team == home, cover when (home - away - line > 0) => diff - line > 0
    # If team == away, cover when (away - home - line > 0) => -diff - line > 0
    if team == home_team:
        for d in diffs:
            if d - line > 0:
                covers += 1
    else:
        for d in diffs:
            if -d - line > 0:
                covers += 1

    if total == 0:
        p_cover = 0.5
    else:
        p_cover = covers / total

    ev = ev_from_prob_and_odds(p_cover, odds)

    return {
        "p_cover": p_cover,
        "ev": ev,
        "avg_diff": sim["avg_diff"],
    }


def simulate_total_ev(market: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use 50k sims on TOTAL points to estimate p_cover and EV for an Over/Under bet.

    Assumes:
      - market['type'] == 'total'
      - market['side'] is 'Over' or 'Under' (case-insensitive)
      - simulated value is the combined score (home + away).
    """
    params = model_params_for_total(market)
    mu_total = params["mu_total"]
    sigma_total = params["sigma_total"]

    sim = simulate_total_50000(mu_total, sigma_total)
    totals = sim["samples"]

    line = float(market.get("line") or 0.0)
    odds = market.get("odds")
    side = (market.get("side") or "").lower()

    covers = 0
    total_n = float(len(totals) or 1)

    if side.startswith("over"):
        for t in totals:
            if t > line:
                covers += 1
    else:
        # default to "Under" if side is missing or not Over
        for t in totals:
            if t < line:
                covers += 1

    p_cover = covers / total_n
    ev = ev_from_prob_and_odds(p_cover, odds)

    return {
        "p_cover": p_cover,
        "ev": ev,
        "avg_total": sim["avg_total"],
    }



def simulate_prop_ev(market: Dict[str, Any]) -> Dict[str, Any]:
    """
    50k sims for a player prop: over/under on a stat.
    Expects:
      market['direction'] = 'over'/'under'
      market['line']
      market['odds']
    """
    params = model_params_for_prop(market)
    mu_stat = params["mu_stat"]
    sigma_stat = params["sigma_stat"]

    sim = simulate_prop_50000(mu_stat, sigma_stat)
    stats = sim["samples"]

    line = market.get("line") or 20.0
    odds = market.get("odds")
    direction = (market.get("direction") or "").lower()

    covers = 0
    total = float(len(stats))

    if direction == "over":
        for s in stats:
            if s > line:
                covers += 1
    else:
        for s in stats:
            if s < line:
                covers += 1

    if total == 0:
        p_cover = 0.5
    else:
        p_cover = covers / total

    ev = ev_from_prob_and_odds(p_cover, odds)

    return {
        "p_cover": p_cover,
        "ev": ev,
        "avg_stat": sim["avg_stat"],
    }


# ---------- Bridge functions used by tiles.py ----------

def best_line_for_straight_market(market: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    Attach EV and model info to a single straight market:
      - spread  -> uses simulate_spread_ev (50/25/25 on diff)
      - total   -> uses simulate_total_ev  (50/25/25 on total)
      - others  -> simple implied prob from the odds
    """
    odds = market.get("odds")
    if odds is None:
        return None

    mtype = market.get("type")

    # --- Spread: your 50/25/25 difference model ---
    if mtype == "spread":
        sim_result = simulate_spread_ev(market)
        avg_metric = sim_result["avg_diff"]

    # --- Total: your 50/25/25 total model ---
    elif mtype == "total":
        sim_result = simulate_total_ev(market)
        avg_metric = sim_result["avg_total"]

    # --- Moneyline or unknown type: fallback EV from implied probability ---
    else:
        p_impl = american_to_implied(odds)
        ev = ev_from_prob_and_odds(p_impl, odds)
        sim_result = {"p_cover": p_impl, "ev": ev}
        avg_metric = None

    return {
        "sport": market.get("sport"),
        "gameId": market.get("game_id"),
        "book": market.get("book"),
        "marketType": mtype,
        "team": market.get("team"),
        "line": market.get("line"),
        "odds": odds,
        "pCover": sim_result["p_cover"],
        "ev": sim_result["ev"],
        "avgMetric": avg_metric,        # diff for spreads, total for O/U, None for ML
        "homeTeam": market.get("home_team"),
        "awayTeam": market.get("away_team"),
    }



def best_line_for_prop_market(market: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    Attach EV + p_cover + avgStat to a prop market.
    Expects prop-like fields on market.
    """
    odds = market.get("odds")
    if odds is None:
        return None

    # Normalize direction / stat type naming
    direction = (market.get("direction") or market.get("side") or "over").lower()
    market["direction"] = direction

    sim_res = simulate_prop_ev(market)
    p_cover = sim_res["p_cover"]
    ev = sim_res["ev"]
    avg_stat = sim_res["avg_stat"]

    return {
        "sport": market.get("sport"),
        "gameId": market.get("game_id"),
        "book": market.get("book"),
        "marketType": market.get("type") or "prop",
        "team": market.get("team"),
        "player": market.get("player"),
        "statType": market.get("stat_type"),
        "direction": direction,
        "line": market.get("line"),
        "odds": odds,
        "pCover": round(p_cover, 4),
        "ev": round(ev, 4),
        "avgStat": avg_stat,
        "homeTeam": market.get("home_team"),
        "awayTeam": market.get("away_team"),
    }
