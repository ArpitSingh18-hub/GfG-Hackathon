import re
from backend.llm.gemini_client import ask_gemini
from backend.services.schema_service import get_schema
from backend.services.table_context import get_table

_cache = {}

def clean_sql(sql: str):
    sql = re.sub(r"```sql", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"```", "", sql)
    return sql.strip()

def generate_sql(user_query: str, previous_query: str = None, previous_sql: str = None):
    # get dynamic table name
    table_name = get_table()

    if not table_name:
        raise ValueError("No dataset uploaded. Please upload a CSV first.")

    user_query_norm = user_query.strip().lower() if user_query else "none"
    prev_query_norm = previous_query.strip().lower() if previous_query else "none"
    cache_key = f"{table_name}_{user_query_norm}_{prev_query_norm}"
    
    if cache_key in _cache:
        return _cache[cache_key]

    schema = get_schema()

    prompt = f"""
You are an expert BI Data Analyst.



Table name: {table_name}
Columns available:
{schema}

Task: Convert the user request into a SQL query.
Rules:
- Give me ONLY the SQL code, no formatting, no markdown (no ```sql).
- Use DuckDB syntax.
"""

    if previous_query and previous_sql:
        prompt += f"""
Context of the conversation (Follow-up):
Previous Question: {previous_query}
Previous SQL Query: 
{previous_sql}

The user's new request is likely a follow-up or modification of the previous question. Base your new query on the previous SQL context if applicable.
"""

    prompt += f"\nUser Request:\n{user_query}"

    sql = ask_gemini(prompt)
    sql = clean_sql(sql)

    _cache[cache_key] = sql
    return sql