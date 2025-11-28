import requests
import json
import time
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text

DB_CONNECTION = "postgresql://postgres@localhost:5432/football_prediction_db"
SEASONS = ["2023", "2024", "2025"] # Reduced list to get you started faster

def get_db_engine():
    return create_engine(DB_CONNECTION)

def get_team_slugs(season):
    url = f"https://understat.com/league/EPL/{season}"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'teamsData' in script.string:
                json_string = script.string.split("('")[1].split("')")[0]
                data = json.loads(json_string.encode('utf8').decode('unicode_escape'))
                slugs = {}
                for t_id, t_data in data.items():
                    slugs[t_data['title']] = t_data['title'].replace(' ', '_')
                return slugs
    except Exception as e:
        print(f"❌ Error fetching team list: {e}")
    return {}

def scrape_team_tactics(team_slug, season):
    url = f"https://understat.com/team/{team_slug}/{season}"
    print(f"   🕵️‍♀️ Parsing tactics for {team_slug}...")
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'datesData' in script.string:
                json_string = script.string.split("('")[1].split("')")[0]
                return json.loads(json_string.encode('utf8').decode('unicode_escape'))
    except Exception as e:
        print(f"   ⚠️ Could not scrape {team_slug} (Skipping)")
    return []

def update_database_tactics():
    engine = get_db_engine()
    
    for season in SEASONS:
        print(f"\n📅 Processing Season {season}...")
        teams_map = get_team_slugs(season)
        
        for team_name, team_slug in teams_map.items():
            matches = scrape_team_tactics(team_slug, season)
            
            with engine.connect() as conn:
                for m in matches:
                    # SAFETY CHECK: Only process if 'ppda' exists and is valid
                    try:
                        if 'ppda' in m and m['ppda'] and 'att' in m['ppda'] and 'def' in m['ppda']:
                            if m['ppda']['def'] != 0:
                                ppda_val = m['ppda']['att'] / m['ppda']['def']
                            else:
                                ppda_val = 0
                        else:
                            ppda_val = None # No data available

                        deep_val = m.get('deep', 0)
                        date = m['datetime'].split(' ')[0]
                        side = m['side']
                        
                        # SQL Logic
                        if side == 'h':
                            sql = """
                            UPDATE match_stats SET home_ppda = :ppda, home_deep = :deep
                            FROM matches, teams
                            WHERE match_stats.match_id = matches.match_id
                            AND matches.home_team_id = teams.team_id
                            AND matches.date = :date
                            AND teams.name = :team_name
                            """
                        else:
                            sql = """
                            UPDATE match_stats SET away_ppda = :ppda, away_deep = :deep
                            FROM matches, teams
                            WHERE match_stats.match_id = matches.match_id
                            AND matches.away_team_id = teams.team_id
                            AND matches.date = :date
                            AND teams.name = :team_name
                            """
                        
                        conn.execute(text(sql), {
                            'ppda': ppda_val,
                            'deep': deep_val,
                            'date': date,
                            'team_name': team_name
                        })
                    except Exception as e:
                        # Skip this single match if it fails, don't crash the script
                        continue
                        
                conn.commit()
            time.sleep(0.5)

    print("\n✅ Tactical Data Import Complete!")

if __name__ == "__main__":
    update_database_tactics()