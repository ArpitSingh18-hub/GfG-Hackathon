import re
from backend.llm.gemini_client import ask_gemini
from backend.services.schema_service import get_schema
from backend.services.table_context import get_table

# Cache structure: { cache_key: sql }
_cache: dict[str, str] = {}
_last_table: str | None = None


def clean_sql(sql: str) -> str:
    sql = re.sub(r"```sql", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"```", "", sql)
    # Strip any leading/trailing whitespace or stray semicolons from LLM output
    return sql.strip().rstrip(";").strip()


def _invalidate_cache_if_table_changed(table_name: str):
    """Clear cache whenever the active table changes (new CSV uploaded)."""
    global _last_table
    if _last_table != table_name:
        _cache.clear()
        _last_table = table_name


def generate_sql(
    user_query: str,
    previous_query: str = None,
    previous_sql: str = None,
) -> str:

    table_name = get_table()

    if not table_name:
        raise ValueError("No dataset uploaded. Please upload a CSV first.")

    if not user_query or not user_query.strip():
        raise ValueError("User query cannot be empty.")

    # Invalidate stale cache if the dataset has changed
    _invalidate_cache_if_table_changed(table_name)

    user_query_norm = user_query.strip().lower()
    prev_query_norm = previous_query.strip().lower() if previous_query else "none"
    cache_key = f"{table_name}__{user_query_norm}__{prev_query_norm}"

    if cache_key in _cache:
        return _cache[cache_key]

    schema = get_schema()

    prompt = f"""
You are an expert DuckDB SQL engineer and BI Data Analyst.

Table name: {table_name}
Schema (column name → data type):
{schema}

Your task: Write a single valid DuckDB SQL SELECT query that answers the user's request.

Strict Rules:
1. Return ONLY raw SQL — no markdown, no backticks, no explanation, no comments.
2. Use ONLY column names listed in the schema above. Never invent columns.
3. DuckDB syntax only — do NOT use MySQL or PostgreSQL-specific functions.
4. For date/time operations:
   - Always CAST text columns to TIMESTAMP before using date functions.
   - Use strftime('%Y', CAST(col AS TIMESTAMP)) for year extraction.
   - Use strftime('%m', CAST(col AS TIMESTAMP)) for month extraction.
5. For aggregations (SUM, COUNT, AVG, etc.):
   - Every non-aggregated column in SELECT must appear in GROUP BY.
6. For text comparisons, use ILIKE for case-insensitive matching.
7. Always alias aggregated columns with meaningful names (e.g., COUNT(*) AS total_count).
8. Do NOT add a trailing semicolon.
9. If the request is ambiguous, make the most reasonable assumption and write the query.
"""

    if previous_query and previous_sql:
        prompt += f"""
--- Conversation Context (Follow-up Query) ---
The user's new request is a follow-up to a previous question.

Previous Question: {previous_query}
Previous SQL:
{previous_sql}

Adapt or extend the previous SQL to answer the new request where applicable.
---
"""

    prompt += f"\nUser Request: {user_query}"

    sql = ask_gemini(prompt)
    sql = clean_sql(sql)

    if not sql.upper().startswith("SELECT"):
        # Safety guard: if LLM returns something other than a SELECT, don't cache it
        raise ValueError(f"LLM returned non-SELECT SQL, refusing to execute: {sql[:100]}")

    _cache[cache_key] = sql
    return sql