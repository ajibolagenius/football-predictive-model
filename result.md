# Codebase Analysis Result

## 1. Remaining Refactoring & Enhancements

### `dashboard.py`
- **Configuration:** Move database connection strings and API keys to a `.env` file or a `config.py` module to avoid hardcoding.

### `etl_pipeline.py` & `scraper_pipeline.py`
- **Enhancements:**
  - **Robustness:** Add retry logic for network requests and better logging for scraping failures.
  - **Data Validation:** Implement checks to ensure scraped data is within expected ranges before saving to the database.

## 2. Additional Features to Add

- **League Standings Table:** Auto-generate a live league table from the match history in the database.
- **Live Odds Integration:** Instead of manual input, integrate with a free/freemium Odds API to fetch real-time bookmaker odds.
- **Player-Level Analytics:** If data permits, add a section for top scorers, assist leaders, and player xG performance.

## 3. Next Recommended Task

**👉 League Standings Table**
- **Why:** It provides immediate visual context for the teams' performance this season.
- **How:** Query the match history, calculate points, goal difference, and goals scored for all teams, and display it in a sortable table.
