from backend.database.db import get_connection
from backend.llm.gemini_client import ask_gemini
from backend.services.schema_service import get_schema
from backend.services.table_context import get_table
import re
import math
import numpy as np


def clean_sql(sql: str):
    sql = re.sub(r"```sql", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"```", "", sql)
    return sql.strip()


def fix_time_functions(sql: str):
    """Automatically fix common LLM mistakes with time functions."""

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


def sanitize_value(val):
    """
    Converts any non-JSON-compliant float (nan, inf, -inf) to None.
    Also handles numpy scalar types that json.dumps can't serialize.
    """
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    # Convert numpy scalars → native Python types
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        v = float(val)
        return None if (math.isnan(v) or math.isinf(v)) else v
    if isinstance(val, (np.bool_,)):
        return bool(val)
    # numpy NaT or pandas NaT
    if val is not None and not isinstance(val, (str, int, float, bool, list, dict)):
        try:
            if math.isnan(float(val)):
                return None
        except Exception:
            pass
    return val


def sanitize_records(records: list[dict]) -> list[dict]:
    """Walk every value in every row and sanitize it."""
    return [
        {k: sanitize_value(v) for k, v in row.items()}
        for row in records
    ]


def clean_df(df):
    """
    Full DataFrame cleanup before converting to records:
    1. Replace inf/-inf with NaN
    2. Replace NaN with None (via object dtype conversion)
    """
    # Replace inf values with NaN first
    df = df.replace([float("inf"), float("-inf")], float("nan"))

    # Convert to object dtype so NaN → None works cleanly
    df = df.astype(object).where(df.notnull(), None)

    return df


def execute_query(sql, limit=5000):

    conn = get_connection()

    try:

        # Clean SQL
        sql = clean_sql(sql)
        sql = fix_time_functions(sql)

        if not sql.endswith(";") and sql:
            sql += ";"

        # Execute
        df = conn.execute(sql).fetchdf()

        if len(df) > limit:
            df = df.head(limit)

        df = clean_df(df)
        data = sanitize_records(df.to_dict(orient="records"))

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

            fixed_sql = fix_time_functions(fixed_sql)

            if not fixed_sql.endswith(";"):
                fixed_sql += ";"

            df = conn.execute(fixed_sql).fetchdf()

            if len(df) > limit:
                df = df.head(limit)

            df = clean_df(df)
            data = sanitize_records(df.to_dict(orient="records"))

            return {
                "generated_sql": sql,
                "fixed_sql": fixed_sql,
                "data": data,
                "repaired": True,
                "row_count": len(data)
            }

        except Exception as repair_error:
            return {
                "generated_sql": sql,
                "error": f"Query failed. Attempted repair also failed: {str(repair_error)}"
            }

    finally:
        conn.close()