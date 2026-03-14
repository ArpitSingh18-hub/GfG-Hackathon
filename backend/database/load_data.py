import pandas as pd
from backend.database.db import get_connection


def load_youtube_data():

    file_path = "data/YouTube Content Creation_clean.csv"

    # Read dataset
    df = pd.read_csv(file_path)

    # Clean column names (important for SQL generation later)
    df.columns = (
        df.columns
        .str.strip()           # remove extra spaces
        .str.replace('"', '')  # remove quotes if present
        .str.replace(" ", "_") # replace spaces with underscore
        .str.lower()           # lowercase column names
    )

    # Connect to DuckDB
    conn = get_connection()

    # Remove old table if it exists
    conn.execute("DROP TABLE IF EXISTS youtube_data")

    # Register dataframe as DuckDB view
    conn.register("df_view", df)

    # Create table from dataframe
    conn.execute("""
        CREATE TABLE youtube_data AS
        SELECT * FROM df_view
    """)

    conn.close()

    print("✅ Dataset loaded successfully into DuckDB")


if __name__ == "__main__":
    load_youtube_data()