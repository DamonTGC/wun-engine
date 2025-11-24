import os
import requests
from dotenv import load_dotenv

# Load .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

def test_odds_api():
    if not ODDS_API_KEY:
        print("[ERROR] ODDS_API_KEY missing in .env")
        return

    url = f"https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "h2h,spreads,totals"
    }

    print("→ Sending request:", url)
    resp = requests.get(url, params=params)

    print("\nSTATUS:", resp.status_code)

    if resp.status_code != 200:
        print("ERROR BODY:", resp.text)
        return

    data = resp.json()
    print("\nSUCCESS: Received", len(data), "events")
    if len(data) > 0:
        print("\nSample event:")
        print(data[0])

if __name__ == "__main__":
    test_odds_api()

