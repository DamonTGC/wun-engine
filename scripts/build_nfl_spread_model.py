import pandas as pd
import json
from pathlib import Path

# Paths
ROOT = Path(__file__).resolve().parents[1]
DATA_CSV = ROOT / "data" / "nfl_games.csv"
OUT_JSON = ROOT / "data" / "nfl_spread_model.json"

print(f"Loading data from: {DATA_CSV}")

df = pd.read_csv(DATA_CSV)

required_cols = [
    "date",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "closing_spread",
]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    raise ValueError(f"CSV is missing required columns: {missing}")

# margin from HOME team perspective
df["home_margin"] = df["home_score"] - df["away_score"]

# Global stats (fallback)
global_mean = df["home_margin"].mean()
global_std = df["home_margin"].std()

# Per-team stats
home_stats = (
    df.groupby("home_team")["home_margin"]
    .agg(["mean", "count"])
    .reset_index()
    .rename(columns={"mean": "home_margin_mean", "count": "home_games"})
)

away_stats = (
    df.assign(away_margin=-df["home_margin"])  # away margin = -home margin
    .groupby("away_team")["away_margin"]
    .agg(["mean", "count"])
    .reset_index()
    .rename(columns={"mean": "away_margin_mean", "count": "away_games"})
)

team_df = pd.merge(
    home_stats,
    away_stats,
    left_on="home_team",
    right_on="away_team",
    how="outer",
)

# Normalize team name column
team_df["team"] = team_df["home_team"].combine_first(team_df["away_team"])
team_df = team_df.drop(columns=["home_team", "away_team"])

# Fill NaNs with zeros for counts, and 0.0 for means if missing
for col in ["home_margin_mean", "away_margin_mean"]:
    team_df[col] = team_df[col].fillna(0.0)

for col in ["home_games", "away_games"]:
    team_df[col] = team_df[col].fillna(0).astype(int)

teams_model = {}
for _, row in team_df.iterrows():
    name = row["team"]
    teams_model[name] = {
        "home_margin_mean": float(row["home_margin_mean"]),
        "away_margin_mean": float(row["away_margin_mean"]),
        "home_games": int(row["home_games"]),
        "away_games": int(row["away_games"]),
    }

model = {
    "global": {
        "mean_margin": float(global_mean),
        "std_margin": float(global_std),
        "games": int(len(df)),
    },
    "teams": teams_model,
}

print("\nNFL spread team model:")
print(json.dumps(model, indent=2)[:800], "...\n")  # print first part

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
with OUT_JSON.open("w") as f:
    json.dump(model, f, indent=2)

print(f"Saved model to: {OUT_JSON}")
