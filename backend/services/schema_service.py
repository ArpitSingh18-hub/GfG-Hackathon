from backend.database.db import get_connection

def get_schema():

    conn = get_connection()

    columns = conn.execute(
        "DESCRIBE youtube_data"
    ).fetchall()

    conn.close()

    return [c[0] for c in columns]