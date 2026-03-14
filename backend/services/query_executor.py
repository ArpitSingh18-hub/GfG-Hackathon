from backend.database.db import get_connection


def execute_query(sql: str):

    conn = get_connection()

    try:
        result = conn.execute(sql).fetchdf()
        return result.to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}

    finally:
        conn.close()