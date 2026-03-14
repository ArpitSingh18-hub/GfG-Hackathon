import duckdb

DB_PATH = "sales.db"

def get_connection():
    return duckdb.connect(DB_PATH)