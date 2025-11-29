from sqlalchemy import create_engine, text
import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

def init_db():
    print(f"🔌 Connecting to {config.DB_CONNECTION}...")
    engine = create_engine(config.DB_CONNECTION)
    
    schemas = [
        "sql/schema.sql",
        "sql/schema_v2.sql",
        "sql/schema_v3.sql",
        "sql/schema_v4.sql",
        "sql/schema_v5.sql"
    ]
    
    with engine.connect() as conn:
        for schema_file in schemas:
            print(f"📜 Applying {schema_file}...")
            try:
                with open(schema_file, "r") as f:
                    sql = f.read()
                    # Split by ; to execute statements separately
                    statements = sql.split(';')
                    for stmt in statements:
                        if stmt.strip():
                            conn.execute(text(stmt))
                    conn.commit()
            except Exception as e:
                print(f"❌ Error applying {schema_file}: {e}")
                # Don't exit, might be partial failure or already exists
                
    print("✅ Database Initialization Complete!")

if __name__ == "__main__":
    init_db()
