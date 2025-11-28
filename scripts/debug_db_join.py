from sqlalchemy import create_engine, text
import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

def debug_join():
    engine = create_engine(config.DB_CONNECTION)
    
    print("🔍 Checking Matches...")
    matches = pd.read_sql("SELECT league, count(*) FROM matches GROUP BY league", engine)
    print(matches)
    
    print("\n🔍 Checking Teams...")
    teams = pd.read_sql("SELECT league, count(*) FROM teams GROUP BY league", engine)
    print(teams)
    
    print("\n🔍 Testing Dashboard Query (Bundesliga) with Stats...")
    query = """
    SELECT 
        m.date, m.home_team_id
    FROM matches m
    JOIN match_stats s ON m.match_id = s.match_id
    WHERE m.league = 'Bundesliga'
    LIMIT 5;
    """
    df = pd.read_sql(query, engine)
    print(df)
    
    if df.empty:
        print("\n❌ Query returned no rows!")
    else:
        print("\n✅ Query returned rows. Check for NULL names:")
        print(df)
    print(f"Rows: {len(df)}")

if __name__ == "__main__":
    debug_join()
