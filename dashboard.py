import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestClassifier

# --- CONFIGURATION ---
st.set_page_config(page_title="Football AI Oracle", layout="wide", page_icon="⚽")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
        
        /* Global Settings */
        html, body, .stApp, [data-testid="stAppViewContainer"] {
            font-family: 'Poppins', sans-serif !important;
        }
        
        /* Headers */
        h1, h2, h3 {
            font-family: 'Poppins', sans-serif !important;
        }

        h1 {
            font-weight: 500 !important;
        }
        

        h2, h3 {
            font-weight: 300 !important;
        }

        /* Metrics */
        [data-testid="stMetricValue"] {
            font-size: 2rem !important;
        }
        
        /* Custom Card for Kelly Recommendation */
        .kelly-card {
            background-color: #1e2329; /* Darker card background */
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #30363d;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            margin-top: 20px;
        }
        .kelly-title {
            font-size: 1.0rem;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        .kelly-value {
            font-size: 1.4rem;
            font-weight: bold;
            color: #2ea043; /* Success green */
            margin-top: 10px;
            display: block;
        }
        .kelly-no-bet {
            font-size: 1.4rem;
            font-weight: bold;
            color: #da3633; /* Danger red */
            margin-top: 10px;
            display: block;
        }
        
        /* Footer */
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #0e1117;
            color: #8b949e;
            text-align: center;
            padding: 10px;
            font-size: 0.8rem;
            border-top: 1px solid #30363d;
            z-index: 100;
        }

        /* VS Text */
        .vs-text {
            font-size: 4rem;
            font-weight: 900;
            background: -webkit-linear-gradient(45deg, #ff6b6b, #f06595);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            line-height: 1;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

DB_CONNECTION = "postgresql://postgres@localhost:5432/football_prediction_db"

# --- CACHED FUNCTIONS ---
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
        t_home.name as home_name, t_away.name as away_name
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

    # Calculate Last 5 Stats (Aggregates)
    # We reconstruct a simple DF for this
    # Determine points for each row
    df['home_points'] = df.apply(lambda x: 3 if x['home_goals'] > x['away_goals'] else (1 if x['home_goals'] == x['away_goals'] else 0), axis=1)
    df['away_points'] = df.apply(lambda x: 3 if x['away_goals'] > x['home_goals'] else (1 if x['home_goals'] == x['away_goals'] else 0), axis=1)

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
    # We reload model_features to ensure we train on the engineered features
    df = pd.read_sql("SELECT * FROM model_features", engine)
    
    features = ['elo_diff', 'home_elo', 'away_elo', 'home_xg_last_5', 'away_xg_last_5', 'home_points_last_5', 'away_points_last_5']
    target = 'target_home_win'
    
    model = RandomForestClassifier(n_estimators=200, random_state=42, max_depth=5)
    model.fit(df[features], df[target])
    return model

def get_last_5_matches(team_name, full_df):
    """
    Extracts the last 5 matches for a specific team to display in the UI.
    """
    # Filter where team is either home or away
    team_matches = full_df[(full_df['home_name'] == team_name) | (full_df['away_name'] == team_name)].copy()
    team_matches = team_matches.sort_values('date', ascending=False).head(5)
    
    display_data = []
    for _, row in team_matches.iterrows():
        if row['home_name'] == team_name:
            opponent = row['away_name']
            location = "(H)"
            goals_for = row['home_goals']
            goals_against = row['away_goals']
            xg_for = row['home_xg']
            xg_against = row['away_xg']
        else:
            opponent = row['home_name']
            location = "(A)"
            goals_for = row['away_goals']
            goals_against = row['home_goals']
            xg_for = row['away_xg']
            xg_against = row['home_xg']
            
        # Determine Result string
        if goals_for > goals_against: result = "W"
        elif goals_for == goals_against: result = "D"
        else: result = "L"
        
        display_data.append({
            "Date": row['date'],
            "Opponent": f"{opponent} {location}",
            "Result": f"{result} {goals_for}-{goals_against}",
            "xG": f"{xg_for:.2f} - {xg_against:.2f}"
        })
    
    return pd.DataFrame(display_data)

# --- MAIN UI ---
st.title("⚽ Football AI Oracle")

# Load Data
df, elo_dict, form_dict, elo_hist_df = load_data()
model = train_model()

# --- SIDEBAR: CONFIG & CALCULATOR ---
st.sidebar.header("1. Match Configuration")
teams = sorted(list(elo_dict.keys()))
home_team = st.sidebar.selectbox("Home Team", teams, index=0)
away_team = st.sidebar.selectbox("Away Team", teams, index=1)

st.sidebar.markdown("---")
st.sidebar.header("2. Betting Calculator (Kelly)")
st.sidebar.info("Enter your bankroll and the bookie's odds to see the optimal stake.")

bankroll = st.sidebar.number_input("Total Bankroll ($)", value=1000, step=100)
odds = st.sidebar.number_input("Bookmaker Odds (Decimal)", value=2.00, step=0.01)

# --- PREDICTION LOGIC ---
if home_team == away_team:
    st.error("Select two different teams!")
else:
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
    
    # --- KELLY CRITERION CALCULATION ---
    # Formula: f = (bp - q) / b
    # b = decimal_odds - 1
    # p = probability of winning (prob)
    # q = probability of losing (1 - prob)
    
    decimal_odds = odds
    b = decimal_odds - 1
    p = prob
    q = 1 - p
    
    kelly_fraction = (b * p - q) / b
    
    # Safety: Many bettors use "Half Kelly" or "Quarter Kelly" to reduce volatility
    # We will show Full Kelly but capped at 0 (no negative bets)
    if kelly_fraction < 0:
        kelly_stake = 0
        kelly_msg = "⛔ No Bet (Negative Value)"
    else:
        kelly_stake = bankroll * kelly_fraction
        kelly_msg = f"💰 Bet ${kelly_stake:.2f} ({kelly_fraction*100:.1f}%)"

    # --- MAIN DISPLAY ---
    col1, col2, col3 = st.columns([1.2, 1.5, 1.2])
    
    with col1:
        st.subheader(home_team)
        st.metric("Elo Rating", int(h_elo), delta=int(h_elo - 1500))
        st.write(f"**Avg xG:** {h_form['xg']:.2f}")
    
    with col2:
        st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
        
        # Probability Display
        prob_color = '#2ea043' if prob > 0.55 else ('#d29922' if prob > 0.40 else '#da3633')
        st.markdown(f"""
            <div style="text-align: center; margin-bottom: 20px;">
                <div style="font-size: 3rem; font-weight: 700; color: {prob_color};">{prob:.1%}</div>
                <div style="color: #8b949e; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;">Home Win Probability</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Kelly Recommendation Box
        kelly_class = "kelly-value" if kelly_fraction >= 0 else "kelly-no-bet"
        st.markdown(f"""
        <div class="kelly-card">
            <div class="kelly-title">Kelly Recommendation (@ {odds})</div>
            <div class="{kelly_class}">{kelly_msg}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.subheader(away_team)
        st.metric("Elo Rating", int(a_elo), delta=int(a_elo - 1500))
        st.write(f"**Avg xG:** {a_form['xg']:.2f}")

    st.divider()

    # --- RECENT FORM TABLES ---
    st.subheader("📅 Recent Match History (Last 5)")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown(f"**{home_team} Form**")
        df_home_last_5 = get_last_5_matches(home_team, df)
        st.dataframe(df_home_last_5, use_container_width=True, hide_index=True)

    with c2:
        st.markdown(f"**{away_team} Form**")
        df_away_last_5 = get_last_5_matches(away_team, df)
        st.dataframe(df_away_last_5, use_container_width=True, hide_index=True)

    # --- CHARTS ---
    st.divider()
    st.subheader("📈 Elo History (5 Years)")
    chart_data = elo_hist_df[elo_hist_df['team'].isin([home_team, away_team])]
    
    fig = go.Figure()
    colors = ['#58a6ff', '#ff6b6b'] # Blue and Red/Pinkish to match theme
    for team, color in zip([home_team, away_team], colors):
        team_data = chart_data[chart_data['team'] == team]
        fig.add_trace(go.Scatter(x=team_data['date'], y=team_data['elo'], mode='lines', name=team, line=dict(color=color, width=3)))
    
    fig.update_layout(
        height=350, 
        margin=dict(l=20, r=20, t=20, b=20), 
        hovermode="x unified",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0'),
        xaxis=dict(showgrid=False, linecolor='#30363d'),
        yaxis=dict(showgrid=True, gridcolor='#30363d', linecolor='#30363d')
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- FOOTER ---
    st.markdown('<div class="footer">(c) 2025 DON_GENIUS</div>', unsafe_allow_html=True)