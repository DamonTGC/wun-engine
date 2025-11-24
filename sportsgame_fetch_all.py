import requests
import json

API_KEY = "9ecdbb494f465c1924e26d6afdfd5469"
BASE_URL = "https://api.sportsgameodds.com/v2"

# What YOU want to support in Dime AI
TARGET_LEAGUES = {
    "NFL":   ("FOOTBALL",  "NFL"),
    "NCAAF": ("FOOTBALL",  "NCAAF"),
    "NBA":   ("BASKETBALL","NBA"),
    "NCAAB": ("BASKETBALL","NCAAB"),
    "NHL":   ("HOCKEY",    "NHL"),
    "MLB":   ("BASEBALL",  "MLB"),
}


def call_sports_endpoint():
    """
    Ask SportsGameOdds: which sportID / leagueID combos does my key support?
    """
    print("🔵 Calling /sports to see what this API key can access...")
    url = f"{BASE_URL}/sports"

    try:
        resp = requests.get(url, headers={"x-api-key": API_KEY}, timeout=10)
        print("SPORTS STATUS:", resp.status_code)

        # Print first part of body so you can see errors/details
        print("SPORTS BODY (first 800 chars):")
        print(resp.text[:800])

        if resp.status_code != 200:
            return []

        payload = resp.json()
        if not payload.get("success", True):
            print("SPORTS API ERROR:", payload.get("error"))
            return []

        return payload.get("data", [])

    except Exception as e:
        print("EXCEPTION calling /sports:", e)
        return []


def get_supported_pairs():
    """
    Build a set of (sportID, leagueID) pairs your key actually has.
    """
    data = call_sports_endpoint()
    supported = set()

    for sport in data:
        sport_id = sport.get("sportID")
        for lg in sport.get("leagues", []):
            league_id = lg.get("leagueID")
            supported.add((sport_id, league_id))

    print("\n✅ Supported sportID/leagueID pairs for this key:")
    for s, l in sorted(supported):
        print(f"  {s} / {l}")

    return supported


def fetch_events_for_league(label: str, sport_id: str, league_id: str):
    """
    Fetch Events for a single (sportID, leagueID) combo.
    Minimal params to avoid 400 errors.
    """
    print(f"\n🔵 Fetching {label} events (sportID={sport_id}, leagueID={league_id})")

    params = {
        "sportID": sport_id,
        "leagueID": league_id,
        "limit": 50,
    }

    url = f"{BASE_URL}/events/"

    try:
        resp = requests.get(
            url,
            params=params,
            headers={"x-api-key": API_KEY},
            timeout=10,
        )

        print("EVENTS STATUS:", resp.status_code)
        if resp.status_code != 200:
            # Show the error text so we see exactly why it's 400
            print("EVENTS BODY (first 400 chars):")
            print(resp.text[:400])
            return []

        payload = resp.json()
        if not payload.get("success", True):
            print("EVENTS API ERROR:", payload.get("error"))
            return []

        events = payload.get("data", [])
        print(f"✅ {label}: {len(events)} events returned")
        return events

    except Exception as e:
        print(f"EXCEPTION for {label}:", e)
        return []


def main():
    # 1) See what this key can actually access
    supported_pairs = get_supported_pairs()

    all_results = {}

    # 2) Loop through your 6 target leagues, but only hit ones the key supports
    for label, (sport_id, league_id) in TARGET_LEAGUES.items():
        if (sport_id, league_id) not in supported_pairs:
            print(f"\n⚠️ Skipping {label}: ({sport_id}, {league_id}) not in your plan / /sports list")
            all_results[label] = []
            continue

        events = fetch_events_for_league(label, sport_id, league_id)
        all_results[label] = events

    print("\n=======================================")
    print("            ALL SPORTS DONE")
    print("=======================================")
    print("Preview of combined results:")
    print(json.dumps(all_results, indent=2)[:2000])


if __name__ == "__main__":
    main()
