import requests
from config.settings import settings

BASE_URL="https://api.the-odds-api.com/v4"
SPORT="basketball_nba"

def get_events(sport):
    url=f"{BASE_URL}/sports/{'basketball_nba'}/events"
    r=requests.get(url, params={"apiKey":settings.ODDS_API_KEY})
    return r.json() if r.status_code==200 else []

def get_player_props(event_id, sport):
    url=f"{BASE_URL}/sports/basketball_nba/events/{event_id}/odds"
    r=requests.get(url, params={"apiKey":settings.ODDS_API_KEY,"markets":"player_points"})
    return r.json() if r.status_code==200 else []