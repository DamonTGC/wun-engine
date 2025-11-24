# test_simulation.py
from props_fetch import fetch_player_props_for_sport
from simulation import simulate_props
from tiers import assign_tier


if __name__ == "__main__":
    sport = "americanfootball_nfl"
    print(f"Fetching player props for {sport}...")

    props = fetch_player_props_for_sport(sport)
    print(f"Got {len(props)} normalized props")

    sims = simulate_props(props)
    print(f"Simulated {len(sims)} props")

    # Rank by EV, highest first
    ranked = sorted(sims, key=lambda s: s.best_ev, reverse=True)
    top = ranked[:10]

    for s in top:
        tier = assign_tier(s)
        p = s.cover_prob * 100.0
        line_str = f"{s.prop.line}" if s.prop.line is not None else "N/A"
        print(
            f"[{tier.upper()}] {s.prop.player} | {s.prop.market} "
            f"{s.best_side} {line_str} | "
            f"cover={p:.1f}% ev={s.best_ev:.3f} "
            f"book={s.prop.bookmaker}"
        )
