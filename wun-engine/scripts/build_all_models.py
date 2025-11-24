import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "markets.json"

def build_spread_model(data_csv: Path, out_json: Path):
    df = pd.read_csv(data_csv)
    df["home_margin"] = df["home_score"] - df["away_score"]

    mean_margin = df["home_margin"].mean()
    std_margin = df["home_margin"].std()
    num_games = len(df)

    model = {
        "mean_margin": float(mean_margin),
        "std_margin": float(std_margin),
        "games": int(num_games),
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w") as f:
        json.dump(model, f, indent=2)

def build_total_model(data_csv: Path, out_json: Path):
    df = pd.read_csv(data_csv)
    df["total_points"] = df["home_score"] + df["away_score"]

    mean_total = df["total_points"].mean()
    std_total = df["total_points"].std()
    num_games = len(df)

    model = {
        "mean_total": float(mean_total),
        "std_total": float(std_total),
        "games": int(num_games),
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w") as f:
        json.dump(model, f, indent=2)

def build_prop_model(data_csv: Path, out_json: Path):
    df = pd.read_csv(data_csv)
    required = ["player", "stat", "stat_value"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{data_csv} missing columns: {missing}")

    df["stat_value"] = df["stat_value"].astype(float)
    grouped = (
        df.groupby(["player", "stat"])["stat_value"]
        .agg(["mean", "std", "count"])
        .reset_index()
    )

    model = {}
    for _, row in grouped.iterrows():
        key = f"{row['player']}|{row['stat']}"
        model[key] = {
            "player": row["player"],
            "stat": row["stat"],
            "mean": float(row["mean"]),
            "std": float(row["std"]) if not pd.isna(row["std"]) else 0.0,
            "samples": int(row["count"]),
        }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w") as f:
        json.dump(model, f, indent=2)

def main():
    with CONFIG_PATH.open() as f:
        markets_cfg = json.load(f)

    for sport, markets in markets_cfg.items():
        for market_name, cfg in markets.items():
            mtype = cfg["type"]
            data_csv = ROOT / cfg["data_file"]
            out_json = ROOT / cfg["model_file"]

            print(f"\nBuilding model for {sport} {market_name} ({mtype})")
            if not data_csv.exists():
                print(f"  SKIP: {data_csv} missing")
                continue

            if mtype == "spread":
                build_spread_model(data_csv, out_json)
            elif mtype == "total":
                build_total_model(data_csv, out_json)
            elif mtype == "prop":
                build_prop_model(data_csv, out_json)
            else:
                print(f"  UNKNOWN type {mtype}, skipping.")
                continue

            print(f"  Saved model to {out_json}")

if __name__ == "__main__":
    main()
