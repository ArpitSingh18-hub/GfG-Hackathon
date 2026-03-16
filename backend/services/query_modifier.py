from backend.llm.gemini_client import ask_gemini


def modify_query(user_query, previous_query, previous_sql, schema, table):

    prompt = f"""
You are an expert SQL assistant.

The user already created a query.

Table name: {table}

Columns:
{schema}

Previous user query:
{previous_query}

Previous SQL query:
{previous_sql}

Now the user wants to modify the query.

User request:
{user_query}

Modify the SQL accordingly.

Rules:
- Return ONLY SQL
- Use DuckDB syntax
- Preserve the logic of the previous query
"""

    return ask_gemini(prompt)