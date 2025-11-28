import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestClassifier

# --- CONFIGURATION ---
DB_CONNECTION = "postgresql://postgres@localhost:5432/football_prediction_db"

def get_db_engine():
    return create_engine(DB_CONNECTION)

def get_latest_team_stats():
    """
    Re-runs the entire history to get the CURRENT state (Elo + Form) of every team.
    """
    engine = get_db_engine()
    
    # 1. Load All History
    query = """
    SELECT 
        m.date, m.home_team_id, m.away_team_id,
        m.home_goals, m.away_goals,
        s.home_xg, s.away_xg,
        t_home.name as home_name, t_away.name as away_name,
        CASE WHEN m.home_goals > m.away_goals THEN 3 WHEN m.home_goals = m.away_goals THEN 1 ELSE 0 END as home_points,
        CASE WHEN m.away_goals > m.home_goals THEN 3 WHEN m.home_goals = m.away_goals THEN 1 ELSE 0 END as away_points
    FROM matches m
    JOIN match_stats s ON m.match_id = s.match_id
    JOIN teams t_home ON m.home_team_id = t_home.team_id
    JOIN teams t_away ON m.away_team_id = t_away.team_id
    ORDER BY m.date ASC;
    """
    df = pd.read_sql(query, engine)
    
    # 2. Re-Calculate Elo State
    current_elo = {} # {team_name: 1500}
    K_FACTOR = 20
    
    for index, row in df.iterrows():
        h = row['home_name']
        a = row['away_name']
        
        h_rating = current_elo.get(h, 1500)
        a_rating = current_elo.get(a, 1500)
        
        # Calculate Outcome
        if row['home_goals'] > row['away_goals']: actual = 1.0
        elif row['home_goals'] == row['away_goals']: actual = 0.5
        else: actual = 0.0
        
        expected_h = 1 / (1 + 10 ** ((a_rating - h_rating) / 400))
        
        current_elo[h] = h_rating + K_FACTOR * (actual - expected_h)
        current_elo[a] = a_rating + K_FACTOR * ((1 - actual) - (1 - expected_h))

    # 3. Re-Calculate Form (Last 5 Games)
    # We do this by creating a massive list of every team's performances
    team_performances = {} # {team_name: DataFrame}
    
    # Prepare data for rolling calc
    h_df = df[['date', 'home_name', 'home_xg', 'home_goals', 'home_points']].copy()
    h_df.columns = ['date', 'team', 'xg', 'goals', 'points']
    
    a_df = df[['date', 'away_name', 'away_xg', 'away_goals', 'away_points']].copy()
    a_df.columns = ['date', 'team', 'xg', 'goals', 'points']
    
    all_games = pd.concat([h_df, a_df]).sort_values('date')
    
    # Calculate last 5 averages for every team
    current_form = {}
    for team in all_games['team'].unique():
        last_5 = all_games[all_games['team'] == team].tail(5)
        current_form[team] = {
            'goals': last_5['goals'].mean(),
            'xg': last_5['xg'].mean(),
            'points': last_5['points'].mean()
        }

    return current_elo, current_form

def train_final_model():
    """Trains the model on ALL available data (no test split) for maximum power."""
    engine = get_db_engine()
    df = pd.read_sql("SELECT * FROM model_features", engine)
    
    features = [
        'elo_diff', 'home_elo', 'away_elo',
        'home_xg_last_5', 'away_xg_last_5',
        'home_points_last_5', 'away_points_last_5'
    ]
    target = 'target_home_win'
    
    model = RandomForestClassifier(n_estimators=200, random_state=42, max_depth=5)
    model.fit(df[features], df[target])
    return model

def predict_match(home_team, away_team):
    print(f"\n🔮 Analyzing Matchup: {home_team} vs {away_team}...")
    
    # 1. Get Data
    elo_dict, form_dict = get_latest_team_stats()
    
    # Check if teams exist
    if home_team not in elo_dict or away_team not in elo_dict:
        print(f"❌ Error: Could not find one of the teams. Check spelling.")
        print(f"Available teams: {list(elo_dict.keys())[:5]}...")
        return

    # 2. Build Feature Vector
    h_elo = elo_dict[home_team]
    a_elo = elo_dict[away_team]
    
    features = pd.DataFrame([{
        'elo_diff': h_elo - a_elo,
        'home_elo': h_elo,
        'away_elo': a_elo,
        'home_xg_last_5': form_dict[home_team]['xg'],
        'away_xg_last_5': form_dict[away_team]['xg'],
        'home_points_last_5': form_dict[home_team]['points'],
        'away_points_last_5': form_dict[away_team]['points']
    }])
    
    # 3. Load Brain
    model = train_final_model()
    
    # 4. Predict
    prob = model.predict_proba(features)[0][1] # Probability of Class 1 (Home Win)
    
    print("\n" + "="*40)
    print(f"📊 PREDICTION REPORT")
    print("="*40)
    print(f"🏠 {home_team} (Elo: {int(h_elo)})")
    print(f"✈️  {away_team} (Elo: {int(a_elo)})")
    print("-" * 40)
    print(f"🤖 Model Confidence (Home Win): {prob:.1%}")
    
    if prob > 0.55:
        print("✅ VERDICT: VALUE BET (HOME WIN)")
    elif prob < 0.30:
         print("⚠️ VERDICT: LIKELY AWAY RESULT (WIN/DRAW)")
    else:
        print("⚖️ VERDICT: TOO CLOSE TO CALL (NO BET)")
    print("="*40)

if __name__ == "__main__":
    # YOU CAN CHANGE THESE NAMES TO TEST DIFFERENT MATCHES
    # Use the names exactly as they appear in Understat (e.g. "Man Utd", "Newcastle United")
    predict_match("Chelsea", "Arsenal")