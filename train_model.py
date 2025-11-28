import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score
from sklearn.model_selection import TimeSeriesSplit

DB_CONNECTION = "postgresql://postgres@localhost:5432/football_prediction_db"

def train_football_model():
    engine = create_engine(DB_CONNECTION)
    
    print("📥 Loading feature data...")
    df = pd.read_sql("SELECT * FROM model_features ORDER BY date ASC", engine)
    
    # ADDED: 'elo_diff', 'home_elo', 'away_elo'
    features = [
        'elo_diff', 'home_elo', 'away_elo',
        'home_xg_last_5', 'away_xg_last_5',
        'home_points_last_5', 'away_points_last_5'
    ]
    target = 'target_home_win'
    
    X = df[features]
    y = df[target]
    
    split_index = int(len(df) * 0.85) # Training on 85% now to give it more recent data
    
    X_train = X.iloc[:split_index]
    y_train = y.iloc[:split_index]
    X_test = X.iloc[split_index:]
    y_test = y.iloc[split_index:]
    
    print(f"🧠 Training on {len(X_train)} matches...")

    # Increased trees to 200 for better stability
    model = RandomForestClassifier(n_estimators=200, random_state=42, max_depth=5)
    model.fit(X_train, y_train)
    
    predictions = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]
    
    acc = accuracy_score(y_test, predictions)
    prec = precision_score(y_test, predictions)
    
    print("\n" + "="*30)
    print(f"🏆 NEW MODEL RESULTS (With Elo)")
    print("="*30)
    print(f"✅ Accuracy:  {acc:.2%}")
    print(f"🎯 Precision: {prec:.2%}")
    print("-" * 30)
    
    importances = model.feature_importances_
    feature_imp = pd.DataFrame({'Feature': features, 'Importance': importances}).sort_values('Importance', ascending=False)
    
    print("\n🧐 Feature Importance:")
    print(feature_imp)

if __name__ == "__main__":
    train_football_model()