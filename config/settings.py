import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    ODDS_API_KEY=os.getenv("ODDS_API_KEY","demo")
settings=Settings()