from backend.database.db import get_connection
from backend.llm.gemini_client import ask_gemini
from backend.services.schema_service import get_schema
from backend.services.table_context import get_table


def execute_query(sql):

    conn = get_connection()

    try:

        df = conn.execute(sql).fetchdf()

        # Clean NaN / Infinity values
        df = df.replace([float("inf"), float("-inf")], None)
        df = df.where(df.notnull(), None)

        data = df.to_dict(orient="records")

        return {
            "generated_sql": sql,
            "data": data
        }

    except Exception as error:

        error_message = str(error)

        print("SQL execution error:", error_message)

        try:

            table = get_table()
            schema = get_schema()

            repair_prompt = f"""
The following SQL query failed.

Table: {table}

Schema:
{schema}

SQL:
{sql}

Error:
{error_message}

Fix the SQL query.

Return ONLY corrected SQL.
"""

            fixed_sql = ask_gemini(repair_prompt)

            df = conn.execute(fixed_sql).fetchdf()

            df = df.replace([float("inf"), float("-inf")], None)
            df = df.where(df.notnull(), None)

            return {
                "generated_sql": sql,
                "fixed_sql": fixed_sql,
                "data": df.to_dict(orient="records")
            }

        except Exception as repair_error:

            return {
                "generated_sql": sql,
                "error": f"Query failed after repair attempt: {repair_error}"
            }

    finally:
        conn.close()