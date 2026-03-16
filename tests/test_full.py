import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.api.dashboard_api import run_query, QueryRequest

def test_full_flow():
    req1 = QueryRequest(query="Show total views and likes for each category.")
    out1 = run_query(req1)
    
    print("\n\n--- FIRST QUERY ---")
    print("User Query:", out1.get("user_query"))
    print("SQL:", out1.get("generated_sql"))
    
    req2 = QueryRequest(
        query="Now filter this to only show Vlogs and Education",
        previous_query=out1.get("user_query"),
        previous_sql=out1.get("generated_sql")
    )
    out2 = run_query(req2)
    
    print("\n\n--- SECOND QUERY (FOLLOW UP) ---")
    print("User Query:", out2.get("user_query"))
    print("SQL:", out2.get("generated_sql"))
    
if __name__ == "__main__":
    test_full_flow()
