from sqlalchemy import create_engine, text

DB_CONNECTION = "postgresql://postgres@localhost:5432/football_prediction_db"

def upgrade_schema_v4():
    engine = create_engine(DB_CONNECTION)
    
    # We need to ensure these columns exist in 'match_stats'
    commands = [
        "ALTER TABLE match_stats ADD COLUMN IF NOT EXISTS home_ppda FLOAT;",
        "ALTER TABLE match_stats ADD COLUMN IF NOT EXISTS away_ppda FLOAT;",
        "ALTER TABLE match_stats ADD COLUMN IF NOT EXISTS home_deep INT;",
        "ALTER TABLE match_stats ADD COLUMN IF NOT EXISTS away_deep INT;"
    ]
    
    print("🔧 Upgrading Database Schema to V4...")
    with engine.connect() as conn:
        for sql in commands:
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"✅ Success: {sql}")
            except Exception as e:
                print(f"⚠️ Note: {e}")
                
    print("✨ Database is ready for Tactics.")

if __name__ == "__main__":
    upgrade_schema_v4()