import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestClassifier

# --- CONFIGURATION ---
st.set_page_config(page_title="Football AI Oracle", layout="wide")
DB_CONNECTION = "postgresql://postgres@localhost:5432/football_prediction_db"

# --- CACHED FUNCTIONS (Speed up the app) ---
@st.cache_resource
def get_db_engine():
    return create_engine(DB_CONNECTION)

@st.cache_data
def load_data():
    """Loads all match data and calculates current stats."""
    engine = get_db_engine()
    
    # 1. Load History
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
    
    # 2. Calculate Elo & Form
    current_elo = {}
    elo_history = []
    
    # Form dictionaries
    team_goals = {}
    team_xg = {}
    team_points = {}
    
    K_FACTOR = 20
    
    for index, row in df.iterrows():
        h = row['home_name']
        a = row['away_name']
        date = row['date']
        
        h_rating = current_elo.get(h, 1500)
        a_rating = current_elo.get(a, 1500)
        
        # Determine Outcome
        if row['home_goals'] > row['away_goals']: actual = 1.0
        elif row['home_goals'] == row['away_goals']: actual = 0.5
        else: actual = 0.0
        
        expected_h = 1 / (1 + 10 ** ((a_rating - h_rating) / 400))
        
        new_h = h_rating + K_FACTOR * (actual - expected_h)
        new_a = a_rating + K_FACTOR * ((1 - actual) - (1 - expected_h))
        
        current_elo[h] = new_h
        current_elo[a] = new_a
        
        elo_history.append({'date': date, 'team': h, 'elo': new_h})
        elo_history.append({'date': date, 'team': a, 'elo': new_a})

    # Calculate Rolling Stats for "Form"
    # We reconstruct a simple DF for this
    form_df = pd.concat([
        df[['date', 'home_name', 'home_goals', 'home_xg', 'home_points']].rename(columns={'home_name':'team', 'home_goals':'goals', 'home_xg':'xg', 'home_points':'points'}),
        df[['date', 'away_name', 'away_goals', 'away_xg', 'away_points']].rename(columns={'away_name':'team', 'away_goals':'goals', 'away_xg':'xg', 'away_points':'points'})
    ]).sort_values('date')
    
    stats_dict = {}
    for team in form_df['team'].unique():
        last_5 = form_df[form_df['team'] == team].tail(5)
        stats_dict[team] = {
            'goals': last_5['goals'].mean(),
            'xg': last_5['xg'].mean(),
            'points': last_5['points'].mean()
        }
        
    return df, current_elo, stats_dict, pd.DataFrame(elo_history)

@st.cache_resource
def train_model():
    engine = get_db_engine()
    df = pd.read_sql("SELECT * FROM model_features", engine)
    
    features = ['elo_diff', 'home_elo', 'away_elo', 'home_xg_last_5', 'away_xg_last_5', 'home_points_last_5', 'away_points_last_5']
    target = 'target_home_win'
    
    model = RandomForestClassifier(n_estimators=200, random_state=42, max_depth=5)
    model.fit(df[features], df[target])
    return model

# --- MAIN UI ---
st.title("⚽ Football AI Oracle")

# Load Data
df, elo_dict, form_dict, elo_hist_df = load_data()
model = train_model()

# Sidebar
st.sidebar.header("Match Configuration")
teams = sorted(list(elo_dict.keys()))
home_team = st.sidebar.selectbox("Home Team", teams, index=0)
away_team = st.sidebar.selectbox("Away Team", teams, index=1)

if home_team == away_team:
    st.error("Select two different teams!")
else:
    # --- PREDICTION ---
    h_elo = elo_dict[home_team]
    a_elo = elo_dict[away_team]
    h_form = form_dict[home_team]
    a_form = form_dict[away_team]
    
    # Input Vector
    input_data = pd.DataFrame([{
        'elo_diff': h_elo - a_elo,
        'home_elo': h_elo,
        'away_elo': a_elo,
        'home_xg_last_5': h_form['xg'],
        'away_xg_last_5': a_form['xg'],
        'home_points_last_5': h_form['points'],
        'away_points_last_5': a_form['points']
    }])
    
    prob = model.predict_proba(input_data)[0][1]
    
    # --- DISPLAY METRICS ---
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.subheader(home_team)
        st.metric("Elo Rating", int(h_elo), delta=int(h_elo - 1500))
        st.write(f"**xG Form:** {h_form['xg']:.2f}")
        st.write(f"**Goals Form:** {h_form['goals']:.2f}")

    with col2:
        st.markdown("<h1 style='text-align: center;'>VS</h1>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align: center; color: {'green' if prob > 0.55 else 'orange'};'>{prob:.1%} Home Win Prob</h2>", unsafe_allow_html=True)
        
        if prob > 0.55:
            st.success(f"✅ Prediction: **{home_team}** is the Value Pick")
        elif prob < 0.35:
            st.warning(f"⚠️ Prediction: Lean towards **{away_team}** (Draw/Win)")
        else:
            st.info("⚖️ Prediction: Too Close to Call")

    with col3:
        st.subheader(away_team)
        st.metric("Elo Rating", int(a_elo), delta=int(a_elo - 1500))
        st.write(f"**xG Form:** {a_form['xg']:.2f}")
        st.write(f"**Goals Form:** {a_form['goals']:.2f}")

    # --- CHARTS ---
    st.divider()
    
    # Elo Chart
    st.subheader("📈 Elo History (Last 5 Years)")
    chart_data = elo_hist_df[elo_hist_df['team'].isin([home_team, away_team])]
    
    fig = go.Figure()
    for team in [home_team, away_team]:
        team_data = chart_data[chart_data['team'] == team]
        fig.add_trace(go.Scatter(x=team_data['date'], y=team_data['elo'], mode='lines', name=team))
    
    fig.update_layout(height=400, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
    
    # --- STATS COMPARISON ---
    st.subheader("📊 Tale of the Tape (Last 5 Games)")
    
    comparison_df = pd.DataFrame({
        'Metric': ['Points (Avg)', 'Expected Goals (xG)', 'Actual Goals'],
        home_team: [h_form['points'], h_form['xg'], h_form['goals']],
        away_team: [a_form['points'], a_form['xg'], a_form['goals']]
    }).set_index('Metric')
    
    st.bar_chart(comparison_df)