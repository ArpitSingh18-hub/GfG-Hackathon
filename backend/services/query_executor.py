from backend.database.db import get_connection
from backend.llm.gemini_client import ask_gemini
from backend.services.schema_service import get_schema
from backend.services.table_context import get_table
import re


def clean_sql(sql: str):
    sql = re.sub(r"```sql", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"```", "", sql)
    return sql.strip()


def fix_time_functions(sql: str):
    """
    Automatically fix common LLM mistakes with time functions
    """

    # Fix strftime('%m', timestamp)
    sql = re.sub(
        r"strftime\(([^,]+),\s*(\w+)\)",
        r"strftime(\1, CAST(\2 AS TIMESTAMP))",
        sql,
        flags=re.IGNORECASE
    )

    # Fix EXTRACT(MONTH FROM timestamp)
    sql = re.sub(
        r"EXTRACT\((.*?) FROM (\w+)\)",
        r"EXTRACT(\1 FROM CAST(\2 AS TIMESTAMP))",
        sql,
        flags=re.IGNORECASE
    )

    # Fix date_part('month', timestamp)
    sql = re.sub(
        r"date_part\(([^,]+),\s*(\w+)\)",
        r"date_part(\1, CAST(\2 AS TIMESTAMP))",
        sql,
        flags=re.IGNORECASE
    )

    return sql


def execute_query(sql, limit=5000):

    conn = get_connection()

    try:

        # -----------------------------
        # Clean SQL
        # -----------------------------

        sql = clean_sql(sql)

        # Auto fix common timestamp errors
        sql = fix_time_functions(sql)

        # Ensure semicolon
        if not sql.endswith(";") and sql:
            sql += ";"

        # -----------------------------
        # Execute query
        # -----------------------------

        df = conn.execute(sql).fetchdf()

        # Limit results
        if len(df) > limit:
            df = df.head(limit)

        # Clean NaN / Inf
        df = df.replace([float("inf"), float("-inf")], None)
        df = df.where(df.notnull(), None)

        data = df.to_dict(orient="records")

        return {
            "generated_sql": sql,
            "data": data,
            "row_count": len(data)
        }

    except Exception as error:

        error_message = str(error)
        print("SQL execution error:", error_message)

        try:

            table = get_table()
            schema = get_schema()

            # -----------------------------
            # Ask LLM to repair SQL
            # -----------------------------

            repair_prompt = f"""
You are an expert DuckDB SQL engineer.

The following SQL query failed.

Table: {table}

Schema:
{schema}

Failed SQL:
{sql}

Error:
{error_message}

Fix the SQL query to valid DuckDB syntax.

Rules:
1. Use only columns present in schema
2. Fix timestamp / date casting issues
3. Ensure valid GROUP BY rules
4. Return ONLY SQL without markdown or explanation
"""

            fixed_sql = ask_gemini(repair_prompt)
            fixed_sql = clean_sql(fixed_sql)

            if not fixed_sql:
                raise ValueError("LLM returned empty SQL for repair.")

            # Apply time fix again
            fixed_sql = fix_time_functions(fixed_sql)

            if not fixed_sql.endswith(";"):
                fixed_sql += ";"

            df = conn.execute(fixed_sql).fetchdf()

            if len(df) > limit:
                df = df.head(limit)

            df = df.replace([float("inf"), float("-inf")], None)
            df = df.where(df.notnull(), None)

            return {
                "generated_sql": sql,
                "fixed_sql": fixed_sql,
                "data": df.to_dict(orient="records"),
                "repaired": True,
                "row_count": len(df)
            }

        except Exception as repair_error:

            return {
                "generated_sql": sql,
                "error": f"Query failed. Attempted repair also failed: {str(repair_error)}"
            }

    finally:
        conn.close()