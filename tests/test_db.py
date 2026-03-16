import os
import sys
import duckdb

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.db import get_connection

def test_db_connection():
    print("Testing Database Connection...")
    try:
        conn = get_connection()
        res = conn.execute("SELECT 1").fetchone()
        if res[0] == 1:
            print("[PASS] DuckDB connection successful!")
        
        # Check if table exists
        tables = conn.execute("SHOW TABLES").fetchall()
        table_names = [t[0] for t in tables]
        if "youtube_data" in table_names:
            count = conn.execute("SELECT count(*) FROM youtube_data").fetchone()[0]
            print(f"[PASS] Found youtube_data table with {count} records.")
        else:
            print("[WARN] Table 'youtube_data' not found. Run 'python -m backend.database.load_data' first.")
            
        conn.close()
    except Exception as e:
        print(f"[FAIL] Database test failed: {e}")

if __name__ == "__main__":
    test_db_connection()
