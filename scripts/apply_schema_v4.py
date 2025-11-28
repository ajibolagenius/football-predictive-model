from sqlalchemy import create_engine, text
import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

def apply_schema():
    engine = create_engine(config.DB_CONNECTION)
    with engine.connect() as conn:
        with open("sql/schema_v4.sql", "r") as f:
            sql = f.read()
            # Split by ; to execute statements separately
            statements = sql.split(';')
            for stmt in statements:
                if stmt.strip():
                    print(f"Executing: {stmt.strip()[:50]}...")
                    conn.execute(text(stmt))
            conn.commit()
    print("✅ Schema V4 Applied Successfully!")

if __name__ == "__main__":
    apply_schema()
