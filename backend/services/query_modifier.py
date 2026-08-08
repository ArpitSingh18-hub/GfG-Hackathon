from backend.llm.gemini_client import ask_gemini
import re


def clean_sql(sql: str):
    sql = re.sub(r"```sql", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"```", "", sql)
    return sql.strip()


def modify_query(user_query, previous_query, previous_sql, schema, table):

    prompt = f"""
You are an expert SQL assistant.

Table name: {table}

Columns:
{schema}

Previous user query:
{previous_query}

Previous SQL query:
{previous_sql}

The user now wants to modify the query.

User request:
{user_query}

Rules:
- Return ONLY raw SQL, no markdown, no backticks, no explanation.
- Use DuckDB syntax.
- Preserve the logic of the previous query where applicable.
- Only use columns that exist in the schema above.
"""

    sql = ask_gemini(prompt)
    return clean_sql(sql)