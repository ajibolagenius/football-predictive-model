import requests
import pandas as pd
import streamlit as st
import config

ODDS_API_KEY = config.ODDS_API_KEY
SPORT = 'soccer_epl' # We can make this dynamic later
REGIONS = 'uk'
MARKETS = 'h2h'

def fetch_live_odds(api_key, sport_key='soccer_epl'):
    """
    Fetches live odds from The Odds API.
    """
    if not api_key:
        return None

    url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'
    params = {
        'api_key': api_key,
        'regions': REGIONS,
        'markets': MARKETS,
        'oddsFormat': 'decimal'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        odds_data = []
        for event in data:
            home_team = event['home_team']
            away_team = event['away_team']
            commence_time = event['commence_time']
            
            # Get best odds (using first bookmaker for simplicity, e.g., Betfair or William Hill)
            # In a real app, we'd compare bookies.
            bookmakers = event.get('bookmakers', [])
            if not bookmakers:
                continue
                
            # Try to find a major bookie
            bookie = bookmakers[0]
            for b in bookmakers:
                if b['key'] in ['williamhill', 'betfair', 'bet365']:
                    bookie = b
                    break
            
            markets = bookie.get('markets', [])
            if not markets:
                continue
                
            outcomes = markets[0]['outcomes']
            
            home_odd = next((x['price'] for x in outcomes if x['name'] == home_team), None)
            away_odd = next((x['price'] for x in outcomes if x['name'] == away_team), None)
            draw_odd = next((x['price'] for x in outcomes if x['name'] == 'Draw'), None)
            
            if home_odd and away_odd and draw_odd:
                odds_data.append({
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_odd': home_odd,
                    'away_odd': away_odd,
                    'draw_odd': draw_odd,
                    'bookmaker': bookie['title'],
                    'commence_time': commence_time
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

    for index, row in odds_df.iterrows():
        api_home = row['home_team']
        api_away = row['away_team']
        
        if not api_home or not api_away:
            continue
        
        # Check if one string contains the other (e.g. "Man Utd" in "Manchester United")
        home_match = (local_home in api_home) or (api_home in local_home)
        away_match = (local_away in api_away) or (api_away in local_away)
        
        if home_match and away_match:
            return row
            
    return None
