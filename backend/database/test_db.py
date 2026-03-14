from backend.database.db import get_connection

conn = get_connection()

rows = conn.execute(
    "SELECT * FROM youtube_data LIMIT 5"
).fetchall()

for r in rows:
    print(r)

conn.close()