import os
import re
import pandas as pd
from fastapi import APIRouter, File, UploadFile

from backend.database.db import get_connection
from backend.services.table_context import set_table
from backend.services.data_profiler import profile_dataset
from backend.utils.response_formatter import format_success, format_error
from backend.utils.exceptions import ValidationError, DatabaseError

router = APIRouter()


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):

    if not file.filename:
        raise ValidationError("No filename provided.")

    if not file.filename.lower().endswith(".csv"):
        raise ValidationError("Only CSV files are supported.")

    os.makedirs("data", exist_ok=True)

    file_location = os.path.join(
        "data",
        f"temp_{os.path.basename(file.filename)}"
    )

    try:

        # -------------------------------------------------------
        # Save uploaded file
        # -------------------------------------------------------
        content = await file.read()

        if not content:
            raise ValidationError("Uploaded file is empty.")

        with open(file_location, "wb") as f:
            f.write(content)

        # -------------------------------------------------------
        # Read CSV
        # -------------------------------------------------------
        df = pd.read_csv(file_location, low_memory=False)

        if df.empty:
            raise ValidationError("CSV contains no data.")

        # -------------------------------------------------------
        # Clean Column Names
        # -------------------------------------------------------
        df.columns = (
            df.columns
            .str.strip()
            .str.replace('"', "", regex=False)
            .str.replace(" ", "_", regex=False)
            .str.replace(r"[^\w]", "", regex=True)
            .str.lower()
        )

        # -------------------------------------------------------
        # Auto Detect Types
        # -------------------------------------------------------
        for col in df.columns:

            if any(
                x in col
                for x in [
                    "date",
                    "time",
                    "timestamp",
                    "created",
                    "updated",
                ]
            ):
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                    continue
                except Exception:
                    pass

            try:
                df[col] = pd.to_numeric(df[col])
            except Exception:
                pass

        # -------------------------------------------------------
        # Generate Safe Table Name
        # -------------------------------------------------------
        table_base = os.path.splitext(file.filename)[0].strip().lower()

        table_name = re.sub(
            r"[^a-zA-Z0-9_]",
            "_",
            table_base,
        )

        table_name = re.sub(
            r"_+",
            "_",
            table_name,
        )

        table_name = table_name.strip("_")

        if not table_name:
            table_name = "uploaded_data"

        # Cannot start with number
        if table_name[0].isdigit():
            table_name = "tbl_" + table_name

        # Maximum identifier length
        table_name = table_name[:63]

        quoted_table = f'"{table_name}"'

        print("=" * 60)
        print("Original filename :", file.filename)
        print("Generated table   :", table_name)
        print("=" * 60)

        # -------------------------------------------------------
        # Store into DuckDB
        # -------------------------------------------------------
        try:

            conn = get_connection()

            conn.register("df_view", df)

            conn.execute(
                f"DROP TABLE IF EXISTS {quoted_table}"
            )

            conn.execute(
                f"""
                CREATE TABLE {quoted_table}
                AS
                SELECT *
                FROM df_view
                """
            )

            conn.unregister("df_view")

            conn.close()

        except Exception as e:
            raise DatabaseError(
                f"Database error: {str(e)}"
            )

        # -------------------------------------------------------
        # Save Active Table
        # -------------------------------------------------------
        set_table(table_name)

        # -------------------------------------------------------
        # Profile Dataset
        # -------------------------------------------------------
        try:
            profile = profile_dataset(df, table_name)

        except Exception as e:

            print("Profiler Error:", e)

            profile = {}

        # -------------------------------------------------------
        # Delete Temp File
        # -------------------------------------------------------
        if os.path.exists(file_location):
            os.remove(file_location)

        return format_success(
            {
                "message": "Dataset uploaded successfully",
                "table": table_name,
                "rows": len(df),
                "columns": list(df.columns),
                "profile": profile,
            }
        )

    except Exception as e:

        if os.path.exists(file_location):
            os.remove(file_location)

        return format_error(str(e))