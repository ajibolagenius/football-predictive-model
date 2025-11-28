import pandas as pd
import xgboost as xgb
from sqlalchemy import create_engine
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit

DB_CONNECTION = "postgresql://postgres@localhost:5432/football_prediction_db"

def tune_xgboost():
    engine = create_engine(DB_CONNECTION)
    print("📥 Loading V3 Data...")
    df = pd.read_sql("SELECT * FROM model_features_v3 ORDER BY date ASC", engine)
    
    features = ['home_rest', 'away_rest', 'home_xg_last_3_at_home', 'away_xg_last_3_at_away', 'home_goals_last_3_at_home', 'away_goals_last_3_at_away']
    target = 'match_result'
    
    # Use recent 85% of data
    split = int(len(df) * 0.85)
    X_train = df[features].iloc[:split]
    y_train = df[target].iloc[:split]
    
    # Define the "Search Space"
    param_grid = {
        'n_estimators': [100, 300, 500],
        'learning_rate': [0.01, 0.05, 0.1],
        'max_depth': [3, 4, 5, 6],
        'subsample': [0.8, 0.9, 1.0],
        'colsample_bytree': [0.8, 0.9, 1.0]
    }
    
    xgb_model = xgb.XGBClassifier(objective='multi:softprob', num_class=3, random_state=42)
    
    # Cross Validation optimized for Time Series
    tscv = TimeSeriesSplit(n_splits=3)
    
    print("🐢 Starting Grid Search (This might take a minute)...")
    search = RandomizedSearchCV(
        xgb_model, 
        param_grid, 
        n_iter=15, # Try 15 random combinations
        scoring='accuracy', 
        cv=tscv, 
        verbose=1,
        n_jobs=-1 # Use all CPU cores
    )
    
    search.fit(X_train, y_train)
    
    print("\n" + "="*30)
    print("🎉 BEST PARAMETERS FOUND")
    print("="*30)
    print(search.best_params_)
    print(f"Best CV Accuracy: {search.best_score_:.2%}")

if __name__ == "__main__":
    tune_xgboost()