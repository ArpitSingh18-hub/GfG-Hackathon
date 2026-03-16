import os
import pandas as pd
from fastapi import APIRouter, File, UploadFile, status
from backend.database.db import get_connection
from backend.services.table_context import set_table
from backend.utils.response_formatter import format_success, format_error
from backend.utils.exceptions import ValidationError, DatabaseError

router = APIRouter()

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename:
        raise ValidationError("No filename provided.")

    if not file.filename.endswith(".csv"):
        raise ValidationError("Only CSV files are supported.")

    os.makedirs("data", exist_ok=True)
    file_location = f"data/temp_{file.filename}"

    try:
        # Save uploaded file temporarily
        content = await file.read()
        if not content:
            raise ValidationError("The uploaded file is empty.")

        with open(file_location, "wb+") as file_object:
            file_object.write(content)

        # Read CSV
        try:
            df = pd.read_csv(file_location)
        except Exception as e:
            raise ValidationError(f"Failed to parse CSV: {str(e)}")

        if df.empty:
            raise ValidationError("The CSV file contains no data.")

        # Clean column names
        df.columns = (
            df.columns
            .str.strip()
            .str.replace('"', '')
            .str.replace(" ", "_")
            .str.replace(r'[^\w]', '', regex=True) # Remove non-alphanumeric chars
            .str.lower()
        )

        # Create table name from file name
        table_base_name = os.path.splitext(file.filename)[0]
        table_name = "".join(e for e in table_base_name if e.isalnum() or e == "_").lower()
        
        if not table_name:
            table_name = "uploaded_data"

        try:
            conn = get_connection()
            # Register dataframe
            conn.register("df_view", df)
            
            # Drop old table if exists
            conn.execute(f"DROP TABLE IF EXISTS {table_name}")

            # Create new table
            conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df_view")
            conn.close()
        except Exception as e:
            raise DatabaseError(f"Failed to store data in database: {str(e)}")

        # Store table context globally
        set_table(table_name)

        # Cleanup temp file
        if os.path.exists(file_location):
            os.remove(file_location)

        return format_success({
            "message": f"Successfully uploaded {file.filename}",
            "table_name": table_name,
            "rows_loaded": len(df),
            "columns": list(df.columns)
        })

    except (ValidationError, DatabaseError) as e:
        if os.path.exists(file_location):
            os.remove(file_location)
        raise e
    except Exception as e:
        if os.path.exists(file_location):
            os.remove(file_location)
        return format_error(f"Upload failed: {str(e)}")