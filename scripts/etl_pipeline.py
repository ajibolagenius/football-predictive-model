import requests
import pandas as pd
import json
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import time
import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from utils import fetch_url, logger

# --- CONFIGURATION ---
DB_CONNECTION = config.DB_CONNECTION
API_KEY = config.RAPIDAPI_KEY
API_HOST = "api-football-v1.p.rapidapi.com"
BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

LEAGUES = {
    "EPL": 39,
    "La_Liga": 140,
    "Bundesliga": 78
}
SEASON = 2025

# --- 1. DATABASE CONNECTION ---
def get_db_engine():
    return create_engine(DB_CONNECTION)

# --- 2. API FETCHER ---
def fetch_api_fixtures(league_id, date_from, date_to):
    url = f"{BASE_URL}/fixtures"
    
    querystring = {
        "league": str(league_id),
        "season": str(SEASON),
        "from": date_from,
        "to": date_to
    }
    
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": API_HOST
    }

    logger.info(f"📡 Fetching matches from {date_from} to {date_to}...")
    try:
        response = fetch_url(url, headers=headers, params=querystring)
        data = response.json()
        
        if data.get('errors'):
            logger.error(f"❌ API Internal Error: {data['errors']}")
            return []
            
        results = data.get('response', [])
        logger.info(f"✅ Found {len(results)} matches.")
        return results
        
    except Exception as e:
        logger.error(f"❌ Network/Parsing Error: {e}")
        return []

# --- 3. WEB SCRAPER ---
def scrape_understat_xg(league="EPL", season="2025"):
    base_url = f"https://understat.com/league/{league}/{season}"
    logger.info(f"🕵️  Scraping xG data from {base_url}...")
    
    try:
        response = fetch_url(base_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        scripts = soup.find_all('script')
        strings = [script.string for script in scripts if script.string and 'datesData' in script.string]
        
        if not strings:
            logger.warning("⚠️  Could not find data on Understat.")
            return []

        json_data = strings[0].split("('")[1].split("')")[0]
        decoded_data = json.loads(json_data.encode('utf8').decode('unicode_escape'))
        
        logger.info(f"✅ Scraped xG data for {len(decoded_data)} matches.")
        return decoded_data
    except Exception as e:
        logger.error(f"❌ Scraping Error: {e}")
        return []

# --- 4. DATA STORAGE ENGINE ---
def process_and_store(api_data, scraped_data, league_name):
    engine = get_db_engine()
    
    scraped_map = {}
    for match in scraped_data:
        key = f"{match['h']['title']} - {match['a']['title']}"
        scraped_map[key] = match

    with engine.connect() as conn:
        for fixture in api_data:
            fix = fixture['fixture']
            teams = fixture['teams']
            goals = fixture['goals']
            
            if fix['status']['short'] not in ['FT', 'AET', 'PEN']:
                continue

            match_date = fix['date'].split('T')[0]
            
            # Insert Teams
            for side in ['home', 'away']:
                t_id = teams[side]['id']
                t_name = teams[side]['name']
                conn.execute(text("""
                    INSERT INTO teams (team_id, name, league) VALUES (:id, :name, :league)
                    ON CONFLICT (team_id) DO UPDATE SET league = EXCLUDED.league
                """), {'id': t_id, 'name': t_name, 'league': league_name})

            # Match Mapping
            home_name = teams['home']['name']
            away_name = teams['away']['name']
            
            scrape_key = f"{home_name} - {away_name}"
            xg_stats = scraped_map.get(scrape_key)
            
            if not xg_stats:
                for k, v in scraped_map.items():
                    if home_name in k and away_name in k:
                        xg_stats = v
                        break
            
            home_xg = float(xg_stats['xG']['h']) if xg_stats else None
            away_xg = float(xg_stats['xG']['a']) if xg_stats else None

            match_uid = f"{match_date}-{teams['home']['id']}-{teams['away']['id']}"

            conn.execute(text("""
                INSERT INTO matches (match_id, date, season, home_team_id, away_team_id, home_goals, away_goals, status, league)
                VALUES (:mid, :date, :season, :hid, :aid, :hg, :ag, :status, :league)
                ON CONFLICT (match_id) DO UPDATE SET 
                    home_goals = EXCLUDED.home_goals,
                    away_goals = EXCLUDED.away_goals,
                    status = EXCLUDED.status,
                    league = EXCLUDED.league
            """), {
                'mid': match_uid,
                'date': match_date,
                'season': str(SEASON),
                'hid': teams['home']['id'],
                'aid': teams['away']['id'],
                'hg': goals['home'],
                'ag': goals['away'],
                'status': fix['status']['short'],
                'league': league_name
            })

            if home_xg is not None:
                conn.execute(text("""
                    INSERT INTO match_stats (match_id, home_xg, away_xg)
                    VALUES (:mid, :hxg, :axg)
                    ON CONFLICT (match_id) DO UPDATE SET
                        home_xg = EXCLUDED.home_xg,
                        away_xg = EXCLUDED.away_xg
                """), {
                    'mid': match_uid,
                    'hxg': home_xg,
                    'axg': away_xg
                })

            conn.commit()

if __name__ == "__main__":
    start_date = "2025-08-11" 
    end_date = "2026-05-20"
    
    logger.info("🚀 Starting Data Pipeline...")
    
    for league_name, league_id in LEAGUES.items():
        logger.info(f"\n🌍 Processing {league_name}...")
        
        api_matches = fetch_api_fixtures(league_id, start_date, end_date)
        scraped_matches = scrape_understat_xg(league=league_name, season=str(SEASON))
        
        if api_matches:
            process_and_store(api_matches, scraped_matches, league_name)
        else:
            logger.warning(f"⚠️ No API data found for {league_name}.")
