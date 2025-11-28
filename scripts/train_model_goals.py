import pandas as pd
import xgboost as xgb
import sys
import os
from sqlalchemy import create_engine
from sklearn.metrics import accuracy_score, classification_report

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

DB_CONNECTION = config.DB_CONNECTION

def train_goals_models():
    engine = create_engine(DB_CONNECTION)
    print("📥 Loading V5 Data for Goals Models...")
    
    try:
        df = pd.read_sql("SELECT * FROM model_features_v5 ORDER BY date ASC", engine)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
        
    if df.empty:
        print("❌ Error: Table is empty!")
        sys.exit(1)

    # Clean
    cols = [
        'home_ppda_5', 'away_ppda_5', 'home_deep_5', 'away_deep_5', 'home_xg_5', 'away_xg_5',
        'home_goals_scored_5', 'home_goals_conceded_5', 'away_goals_scored_5', 'away_goals_conceded_5',
        'home_squad_xg_chain', 'home_squad_xg_buildup', 'away_squad_xg_chain', 'away_squad_xg_buildup'
    ]
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    features = [
        'elo_diff', 
        'home_ppda_5', 'away_ppda_5',
        'home_deep_5', 'away_deep_5',
        'home_xg_5', 'away_xg_5',
        'home_goals_scored_5', 'home_goals_conceded_5',
        'away_goals_scored_5', 'away_goals_conceded_5',
        'home_squad_xg_chain', 'home_squad_xg_buildup',
        'away_squad_xg_chain', 'away_squad_xg_buildup'
    ]
    
    split = int(len(df) * 0.85)
    X_train = df[features].iloc[:split]
    X_test = df[features].iloc[split:]
    
    # --- TRAIN OVER 2.5 ---
    print("\n⚽ Training Over 2.5 Goals Model...")
    y_train_ou = df['target_over_2_5'].iloc[:split]
    y_test_ou = df['target_over_2_5'].iloc[split:]
    
    model_ou = xgb.XGBClassifier(
        n_estimators=200, learning_rate=0.05, max_depth=3,
        objective='binary:logistic', eval_metric='logloss', random_state=42
    )
    model_ou.fit(X_train, y_train_ou)
    
    preds_ou = model_ou.predict(X_test)
    acc_ou = accuracy_score(y_test_ou, preds_ou)
    print(f"✅ Over 2.5 Accuracy: {acc_ou:.2%}")
    print(classification_report(y_test_ou, preds_ou, target_names=['Under', 'Over']))
    
    model_ou.save_model("football_v5_over_2_5.json")
    print("💾 Saved football_v5_over_2_5.json")

    # --- TRAIN BTTS ---
    print("\n🤝 Training BTTS Model...")
    y_train_btts = df['target_btts'].iloc[:split]
    y_test_btts = df['target_btts'].iloc[split:]
    
    model_btts = xgb.XGBClassifier(
        n_estimators=200, learning_rate=0.05, max_depth=3,
        objective='binary:logistic', eval_metric='logloss', random_state=42
    )
    model_btts.fit(X_train, y_train_btts)
    
    preds_btts = model_btts.predict(X_test)
    acc_btts = accuracy_score(y_test_btts, preds_btts)
    print(f"✅ BTTS Accuracy: {acc_btts:.2%}")
    print(classification_report(y_test_btts, preds_btts, target_names=['No', 'Yes']))
    
    model_btts.save_model("football_v5_btts.json")
    print("💾 Saved football_v5_btts.json")

if __name__ == "__main__":
    train_goals_models()
