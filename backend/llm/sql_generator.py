import re
from backend.llm.gemini_client import ask_gemini
from backend.services.schema_service import get_schema

_cache = {}

def clean_sql(sql: str):
    sql = re.sub(r"```sql", "", sql)
    sql = re.sub(r"```", "", sql)
    return sql.strip()

def generate_sql(user_query: str):

    # simple cache so repeated runs don't call Gemini again
    if user_query in _cache:
        return _cache[user_query]

    schema = get_schema()

    prompt = f"""
You are a BI analyst.

Table name: youtube_data

Columns:
{schema}

Convert the user request into SQL.

Rules:
- Return only SQL
- No markdown
- DuckDB syntax
"""

    sql = ask_gemini(prompt + "\nUser query:\n" + user_query)

    sql = clean_sql(sql)

    _cache[user_query] = sql

    return sql