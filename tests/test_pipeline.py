import os
import sys
from dotenv import load_dotenv

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.llm.sql_generator import generate_sql

load_dotenv()

def test_sql_generation():
    print("Testing SQL Generation...")
    user_query = "Show me the top 5 videos by views"
    
    try:
        sql = generate_sql(user_query)
        print(f"User Query: {user_query}")
        print(f"Generated SQL: {sql}")
        
        if "SELECT" in sql.upper() and "FROM youtube_data" in sql:
            print("[PASS] SQL Generation appears valid!")
        else:
            print("[WARN] SQL format might be unexpected.")
            
    except Exception as e:
        print(f"[FAIL] SQL Generation test failed: {e}")

if __name__ == "__main__":
    test_sql_generation()
