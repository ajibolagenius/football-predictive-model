import requests
import pandas as pd
import streamlit as st
from datetime import datetime

# API Configuration
API_BASE = "https://api.the-odds-api.com/v4/sports"
# Default to EPL, but ideally this should be dynamic or cover multiple leagues
# Common keys: soccer_epl, soccer_uefa_champs_league, soccer_spain_la_liga, etc.
DEFAULT_SPORT = "soccer_epl" 
REGIONS = "uk" # uk, us, eu, au
MARKETS = "h2h" # Head to head

@st.cache_data(ttl=3600) # Cache for 1 hour to save API calls
def fetch_live_odds(api_key, sport_key=DEFAULT_SPORT):
    """
    Fetches live odds from The Odds API.
    Returns a DataFrame with matches and odds.
    """
    if not api_key:
        return None
        
    params = {
        'apiKey': api_key,
        'regions': REGIONS,
        'markets': MARKETS,
        'oddsFormat': 'decimal'
    }
    
    try:
        url = f"{API_BASE}/{sport_key}/odds"
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            st.warning(f"Odds API Error: {response.status_code} - {response.text}")
            return None
            
        data = response.json()
        
        odds_data = []
        for match in data:
            home_team = match['home_team']
            away_team = match['away_team']
            commence_time = match['commence_time']
            
            # We'll take the first available bookmaker for simplicity
            # In a real app, you might want 'pinnacle' or 'betfair' specifically
            if match['bookmakers']:
                bookie = match['bookmakers'][0]
                markets = bookie['markets']
                if markets:
                    outcomes = markets[0]['outcomes']
                    
                    # Initialize odds
                    home_odd = 0.0
                    draw_odd = 0.0
                    away_odd = 0.0
                    
                    for outcome in outcomes:
                        if outcome['name'] == home_team:
                            home_odd = outcome['price']
                        elif outcome['name'] == away_team:
                            away_odd = outcome['price']
                        elif outcome['name'] == 'Draw':
                            draw_odd = outcome['price']
                            
                    odds_data.append({
                        'home_team': home_team,
                        'away_team': away_team,
                        'commence_time': commence_time,
                        'home_odd': home_odd,
                        'draw_odd': draw_odd,
                        'away_odd': away_odd,
                        'bookmaker': bookie['title']
                    })
                    
        return pd.DataFrame(odds_data)
        
    except Exception as e:
        st.error(f"Error fetching odds: {e}")
        return None

def map_teams(local_home, local_away, odds_df):
    """
    Attempts to map dashboard team names to API team names.
    Very basic fuzzy matching (substring).
    """
    if odds_df is None or odds_df.empty:
        return None
        
    if not local_home or not local_away:
        return None

    # 1. Try exact match
    match = odds_df[
        (odds_df['home_team'] == local_home) & 
        (odds_df['away_team'] == local_away)
    ]
    
    if not match.empty:
        return match.iloc[0]
        
    # 2. Try partial match (e.g. "Man City" in "Manchester City")
    # This is a naive implementation. For production, use 'thefuzz' library.
    for _, row in odds_df.iterrows():
        api_home = row['home_team']
        api_away = row['away_team']
        
        # Check if one string is contained in the other
        home_match = (local_home in api_home) or (api_home in local_home)
        away_match = (local_away in api_away) or (api_away in local_away)
        
        if home_match and away_match:
            return row
            
    return None
