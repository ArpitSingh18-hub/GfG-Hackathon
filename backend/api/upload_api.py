import os
import pandas as pd
from fastapi import APIRouter, File, UploadFile, HTTPException
from backend.database.db import get_connection
from backend.services.table_context import set_table

router = APIRouter()

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    os.makedirs("data", exist_ok=True)

    file_location = f"data/temp_{file.filename}"

    try:

        # Save uploaded file temporarily
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())

        # Read CSV
        df = pd.read_csv(file_location)

        # Clean column names
        df.columns = (
            df.columns
            .str.strip()
            .str.replace('"', '')
            .str.replace(" ", "_")
            .str.lower()
        )

        # Create table name from file name
        table_name = os.path.splitext(file.filename)[0]
        table_name = table_name.lower().replace(" ", "_")

        conn = get_connection()

        # Drop old table if exists
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")

        # Register dataframe
        conn.register("df_view", df)

        # Create new table
        conn.execute(f"""
            CREATE TABLE {table_name} AS
            SELECT * FROM df_view
        """)

        conn.close()

        # Store table context globally
        set_table(table_name)

        # Cleanup temp file
        os.remove(file_location)

        return {
            "message": f"Successfully uploaded {file.filename}",
            "table_name": table_name,
            "rows_loaded": len(df),
            "columns": list(df.columns)
        }

    except Exception as e:

        if os.path.exists(file_location):
            os.remove(file_location)

        raise HTTPException(status_code=500, detail=str(e))