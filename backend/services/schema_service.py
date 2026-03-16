from backend.database.db import get_connection
from backend.services.table_context import get_table


def get_schema():

    table_name = get_table()

    if not table_name:
        return "No dataset uploaded yet."

    conn = get_connection()

    schema_info = conn.execute(f"DESCRIBE {table_name}").fetchall()

    conn.close()

    schema = []

    for column in schema_info:
        schema.append(column[0])

    return schema