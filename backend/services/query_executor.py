from backend.database.db import get_connection
from backend.llm.gemini_client import ask_gemini
from backend.services.schema_service import get_schema
from backend.services.table_context import get_table
import re

def clean_sql(sql: str):
    sql = re.sub(r"```sql", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"```", "", sql)
    return sql.strip()

def execute_query(sql, limit=5000):
    conn = get_connection()
    try:
        # Basic SQL cleaning
        sql = sql.strip()
        if not sql.endswith(';') and sql:
            sql += ';'

        df = conn.execute(sql).fetchdf()

        # Limit result set
        if len(df) > limit:
            df = df.head(limit)

        # Clean NaN / Infinity values
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

            repair_prompt = f"""
The following SQL query failed in DuckDB.

Table: {table}
Schema:
{schema}

Failed SQL:
{sql}

Error:
{error_message}

Fix the SQL query to be valid DuckDB syntax. Ensure column names are correct as per schema.
Return ONLY corrected SQL without any markdown or explanation.
"""
            fixed_sql = ask_gemini(repair_prompt)
            fixed_sql = clean_sql(fixed_sql)

            if not fixed_sql:
                raise ValueError("LLM returned empty SQL for repair.")

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