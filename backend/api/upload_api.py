import os
import pandas as pd
from fastapi import APIRouter, File, UploadFile, HTTPException
from backend.database.db import get_connection

router = APIRouter()

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
        
    os.makedirs("data", exist_ok=True)
    file_location = f"data/temp_{file.filename}"
    
    try:
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())
            
        # load into duckdb
        df = pd.read_csv(file_location)
        
        # Clean column names
        df.columns = (
            df.columns
            .str.strip()
            .str.replace('"', '')
            .str.replace(" ", "_")
            .str.lower()
        )
        
        conn = get_connection()
        conn.execute("DROP TABLE IF EXISTS youtube_data")
        conn.register("df_view", df)
        conn.execute("""
            CREATE TABLE youtube_data AS
            SELECT * FROM df_view
        """)
        conn.close()
        
        # Cleanup
        os.remove(file_location)
        
        return {
            "message": f"Successfully uploaded {file.filename} and updated the database schema. You can now prompt against your new data!"
        }
        
    except Exception as e:
        if os.path.exists(file_location):
            os.remove(file_location)
        raise HTTPException(status_code=500, detail=str(e))
