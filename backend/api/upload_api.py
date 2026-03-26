import os
import pandas as pd
from fastapi import APIRouter, File, UploadFile
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

        content = await file.read()

        if not content:
            raise ValidationError("Uploaded file is empty.")

        with open(file_location, "wb+") as f:
            f.write(content)

        # safer CSV loading
        df = pd.read_csv(file_location, low_memory=False)

        if df.empty:
            raise ValidationError("CSV contains no data.")

        # ----------------------------
        # CLEAN COLUMN NAMES
        # ----------------------------

        df.columns = (
            df.columns
            .str.strip()
            .str.replace('"', '')
            .str.replace(" ", "_")
            .str.replace(r"[^\w]", "", regex=True)
            .str.lower()
        )

        # ----------------------------
        # AUTO DATA TYPE FIXES
        # ----------------------------

        for col in df.columns:

            # detect datetime columns
            if "date" in col or "time" in col or "timestamp" in col:

                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                except:
                    pass

            # numeric conversion
            try:
                df[col] = pd.to_numeric(df[col])
            except:
                pass

        # ----------------------------
        # CREATE TABLE NAME
        # ----------------------------

        table_base = os.path.splitext(file.filename)[0]

        table_name = "".join(
            e for e in table_base if e.isalnum() or e == "_"
        ).lower()

        if not table_name:
            table_name = "uploaded_data"

        # ----------------------------
        # STORE IN DUCKDB
        # ----------------------------

        try:

            conn = get_connection()

            conn.register("df_view", df)

            conn.execute(f"DROP TABLE IF EXISTS {table_name}")

            conn.execute(
                f"CREATE TABLE {table_name} AS SELECT * FROM df_view"
            )

            conn.close()

        except Exception as e:
            raise DatabaseError(f"Database error: {str(e)}")

        set_table(table_name)

        if os.path.exists(file_location):
            os.remove(file_location)

        return format_success({
            "message": "Dataset uploaded successfully",
            "table": table_name,
            "rows": len(df),
            "columns": list(df.columns)
        })

    except Exception as e:

        if os.path.exists(file_location):
            os.remove(file_location)

        return format_error(str(e))