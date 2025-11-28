import requests
import os
import sys
from sqlalchemy import create_engine, text

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

API_KEY = config.RAPIDAPI_KEY
API_HOST = "api-football-v1.p.rapidapi.com"
BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

def test_fetch():
    url = f"{BASE_URL}/leagues"
    querystring = {
        "id": "39",
        "current": "true"
    }
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": API_HOST
    }
    
    print(f"Checking Bundesliga (78) info...")
    try:
        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()
        print(data)
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_fetch()
