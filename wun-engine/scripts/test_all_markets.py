from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.tiles import generate_tiles
import json

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "markets.json"

def quick_summary_tile(t):
    return (
        f"{t.get('sport')} | {t.get('game')} | {t.get('market')} | "
        f"{t.get('line_text')} @ {t.get('book')} | "
        f"EV={t.get('ev')} | Win={t.get('modelWin')}% | {t.get('avgResult')}"
    )

def main():
    with CONFIG_PATH.open() as f:
        markets_cfg = json.load(f)

    review_log = []

    for sport, markets in markets_cfg.items():
        for page_name in markets.keys():
            print("\n" + "=" * 60)
            print(f"Testing {sport} - {page_name}")
            print("=" * 60)

            # page_name here maps to your engine page; adjust if needed
            page = "straights" if page_name in ("spreads", "totals") else "props"

            tiles = generate_tiles(sport, page, "top 5", "free")

            if not tiles:
                print("No tiles generated.")
                review_log.append((sport, page_name, "NO_TILES"))
                input("Press Enter to continue...")
                continue

            for t in tiles[:5]:
                print("  " + quick_summary_tile(t))

            resp = input("\nLooks good? [Enter = yes, any text = flag]: ").strip()
            status = "OK" if resp == "" else "FLAG"
            review_log.append((sport, page_name, status))

    print("\nReview Summary:")
    for sport, page_name, status in review_log:
        print(f"  {sport} {page_name}: {status}")

    # Optionally save to file:
    out = ROOT / "data" / "market_review_log.txt"
    with out.open("w") as f:
        for sport, page_name, status in review_log:
            f.write(f"{sport},{page_name},{status}\n")

    print(f"\nSaved review log to {out}")

if __name__ == "__main__":
    main()
