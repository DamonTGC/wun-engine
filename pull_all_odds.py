import requests
import json

API_KEY = "9ecdbb494f465c1924e26d6afdfd5469"
BASE_URL = "https://api.sportsgameodds.com/v2/events/"

# sportName -> (sportID, leagueID)
SPORT_CONFIG = {
    "NFL":   ("FOOTBALL",  "NFL"),
    "NCAAF": ("FOOTBALL",  "NCAAF"),
    "NBA":   ("BASKETBALL","NBA"),
    "NCAAB": ("BASKETBALL","NCAAB"),
    "NHL":   ("HOCKEY",    "NHL"),
    "MLB":   ("BASEBALL",  "MLB"),
}

def fetch_events_for_league(label: str, sport_id: str, league_id: str):
    """
    Fetch events for a single (sportID, leagueID) combo.
    Keeps params minimal to avoid 400 'invalid param' errors.
    """
    print(f"\n🔵 Fetching {label} (sportID={sport_id}, leagueID={league_id})")

    params = {
        "sportID": sport_id,     # e.g. FOOTBALL
        "leagueID": league_id,   # e.g. NFL
        "limit": 50,
        # We intentionally leave out optional filters like oddsPresent for now
    }

    try:
        resp = requests.get(
            BASE_URL,
            params=params,
            headers={"x-api-key": API_KEY},
            timeout=10,
        )

        print("STATUS:", resp.status_code)

        # If not 200, log body and give up on this league
        if resp.status_code != 200:
            print("BODY:", resp.text[:400])
            return []

        payload = resp.json()

        # SportsGameOdds uses { success: bool, error?: string, data?: [] }
        if not payload.get("success", True):
            print("API ERROR:", payload.get("error"))
            return []

        data = payload.get("data", [])
        print(f"✅ {label}: {len(data)} events returned")
        return data

    except Exception as e:
        print(f"EXCEPTION for {label}:", e)
        return []


def main():
    all_results = {}

    for label, (sport_id, league_id) in SPORT_CONFIG.items():
        events = fetch_events_for_league(label, sport_id, league_id)
        all_results[label] = events

    print("\n=======================================")
    print("            ALL SPORTS DONE")
    print("=======================================")

    # Preview only, so you don't get spammed
    print(json.dumps(all_results, indent=2)[:2000])


if __name__ == "__main__":
    main()
