# ⚽ The Culture AI Oracle V4

**An AI-powered football analytics platform featuring a sleek Streamlit dashboard, advanced xG & tactical metrics, and machine learning models to forecast match outcomes and identify value bets.**

The **Culture AI Oracle** is an end-to-end data science project that scrapes football match data, engineers advanced features (Elo, Rolling xG, PPDA, Deep Completions), and uses XGBoost classifiers to predict game results. It visualizes these insights through a modern, glassmorphism-styled interface designed for strategic betting analysis.

---

## 🚀 Features

### 🏟️ Interactive Dashboard
- **Modern Glassmorphism UI**: A sleek, dark-themed interface with glass cards, neon accents, and responsive design.
- **Multi-League Support**: Analyze matches from **EPL**, **La Liga**, and **Bundesliga**.
- **Real-time Predictions**: Instant win probabilities for Home vs Away teams.
- **Live Odds Integration**: Automatically fetches live betting odds from **The Odds API** to identify value bets.
- **Kelly Criterion Calculator**: Built-in betting calculator that suggests optimal stake sizes.

### 🧠 Machine Learning Core (V4)
- **XGBoost Classifier**: Trained on historical match data, Elo ratings, and advanced tactical metrics.
- **Tactical Features**:
    - **PPDA (Passes Per Defensive Action)**: Measures pressing intensity.
    - **Deep Completions**: Measures ability to penetrate the danger zone.
    - **Rest Days**: Accounts for fatigue.
- **Feature Engineering**:
    - **Elo Ratings**: Dynamic rating system updating after every match.
    - **Rolling xG (Expected Goals)**: Tracks team performance trends.

### 📊 Advanced Analytics
- **Player-Level Analytics**: "Top Players" tab showing goals, assists, xG, and xA for the current season.
- **Live League Standings**: Up-to-date league tables filtered by season.
- **Tactical Radar Charts**: Visual comparison of team playing styles.
- **Rolling xG Trends**: Line charts visualizing offensive and defensive performance.

---

## 🛠️ Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/) (Python-based web framework), `streamlit-extras`
- **Visualization**: [Plotly](https://plotly.com/) (Interactive charts), HTML/CSS (Custom styling)
- **Machine Learning**: [XGBoost](https://xgboost.readthedocs.io/), [Scikit-Learn](https://scikit-learn.org/)
- **Data Processing**: [Pandas](https://pandas.pydata.org/), [SQLAlchemy](https://www.sqlalchemy.org/)
- **Database**: [PostgreSQL](https://www.postgresql.org/)
- **Data Sources**: API-Football (RapidAPI), Understat (Scraping), The Odds API
- **Automation**: `schedule`, `tenacity` for robust ETL pipelines.

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.9+
- PostgreSQL installed and running

### 1. Clone the Repository
```bash
git clone https://github.com/ajibolagenius/football-predictive-model.git
cd football-predictive-model
```

### 2. Set Up Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration
Create a `.env` file in the root directory (copy from `env.example` if available, or use the template below):
```env
DB_CONNECTION=postgresql://postgres@localhost:5432/football_prediction_db
ODDS_API_KEY=your_odds_api_key
RAPIDAPI_KEY=your_rapidapi_key
```

### 5. Database Setup
Create a PostgreSQL database and apply the schemas:
```bash
createdb football_prediction_db
# Apply schemas from the sql/ directory
psql -d football_prediction_db -f sql/schema.sql
psql -d football_prediction_db -f sql/schema_v2.sql
psql -d football_prediction_db -f sql/schema_v3.sql
```

### 6. Data Pipeline (ETL)
Populate the database with match, tactical, and player data:
```bash
# 1. Fetch Matches (API-Football)
python3 scripts/etl_pipeline.py

# 2. Scrape Tactical Data (Understat)
python3 scripts/scraper_pipeline.py

# 3. Scrape Player Data (Understat)
python3 scripts/scraper_players.py
```

---

## 🖥️ Usage

### Run the Dashboard
```bash
streamlit run dashboard.py
```
The app will open in your browser at `http://localhost:8501`.

### Automated Scheduler
To keep data fresh, run the scheduler in the background:
```bash
python3 scripts/scheduler.py
```
This will run the scrapers daily at 02:00 AM.

---

## 📂 Project Structure

```
├── dashboard.py           # Main Streamlit application
├── config.py              # Configuration loader
├── utils.py               # Shared utilities (logging, requests)
├── scripts/               # ETL and Scraper scripts
│   ├── etl_pipeline.py    # Fetches match data from API
│   ├── scraper_pipeline.py# Scrapes tactical data
│   ├── scraper_players.py # Scrapes player stats
│   ├── scheduler.py       # Automated job scheduler
│   └── apply_schema_v3.py # Schema migration utility
├── sql/                   # Database schemas
├── src/                   # (Optional) Core logic modules
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

---

## 🔮 Future Improvements

-   **Advanced Metrics**: Expected Threat (xT), Passing Networks.
-   **Cloud Deployment**: Deploy the app to Streamlit Cloud or AWS.
-   **User Accounts**: Save betting history and preferences.

---

*(c) 2025 DON_GENIUS*