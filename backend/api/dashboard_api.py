from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from backend.llm.sql_generator import generate_sql
from backend.services.query_executor import execute_query
from backend.llm.chart_selector import select_chart_and_insight
from backend.utils.response_formatter import format_success, format_error
from backend.utils.exceptions import ValidationError, LLMError, DatabaseError

router = APIRouter()


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    previous_query: Optional[str] = None
    previous_sql: Optional[str] = None


def safe_extract_columns(rows):
    """Safely extract column names from query result"""
    if not rows:
        return []

    if isinstance(rows, list) and isinstance(rows[0], dict):
        return list(rows[0].keys())

    return []


def build_safe_chart(columns, rows):
    """Fallback chart if AI chart generation fails"""

    x_axis = columns[0] if columns else None
    y_axis = [columns[1]] if len(columns) > 1 else []

    return {
        "chart_type": "table",
        "x_axis": x_axis,
        "y_axis": y_axis,
        "title": "Data Table",
        "description": "Default visualization due to chart generation failure.",
        "color_palette": [
            "#636EFA",
            "#EF553B",
            "#00CC96",
            "#AB63FA",
            "#FFA15A"
        ]
    }


@router.post("/query")
def run_query(req: QueryRequest):

    try:

        # ---------------------------
        # 1️⃣ Generate SQL
        # ---------------------------

        try:
            sql = generate_sql(req.query, req.previous_query, req.previous_sql)

        except Exception as e:

            if "No dataset uploaded" in str(e):
                raise ValidationError(str(e))

            raise LLMError(f"Failed to generate SQL: {str(e)}")

        # ---------------------------
        # 2️⃣ Execute SQL
        # ---------------------------

        try:
            result = execute_query(sql)

        except Exception as e:
            raise DatabaseError(f"Database execution failed: {str(e)}")

        # Database service may return error dict
        if isinstance(result, dict) and "error" in result:

            return format_error(
                error_message=result["error"],
                data={
                    "user_query": req.query,
                    "generated_sql": sql
                }
            )

        # ---------------------------
        # 3️⃣ Extract data safely
        # ---------------------------

        rows = result.get("data", []) if isinstance(result, dict) else result
        columns = safe_extract_columns(rows)

        # ---------------------------
        # 4️⃣ Chart Selection
        # ---------------------------

        try:

            chart_info = select_chart_and_insight(
                req.query,
                sql,
                columns,
                rows
            )

            chart_info = dict(chart_info)

            insight = chart_info.get(
                "insight",
                "No insights could be generated."
            )

            chart_info.pop("insight", None)

        except Exception:

            chart_info = build_safe_chart(columns, rows)

            insight = "No insights could be generated."

        # ---------------------------
        # 5️⃣ Validate chart fields
        # ---------------------------

        chart_info.setdefault("chart_type", "table")
        chart_info.setdefault("x_axis", columns[0] if columns else None)
        chart_info.setdefault("y_axis", [columns[1]] if len(columns) > 1 else [])
        chart_info.setdefault("title", "Data Visualization")
        chart_info.setdefault("description", "Auto generated visualization.")
        chart_info.setdefault(
            "color_palette",
            ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"]
        )

        # ---------------------------
        # 6️⃣ Build Response
        # ---------------------------

        response_data = {

            "user_query": req.query,

            "generated_sql": sql,

            "data": rows,

            "chart_info": chart_info,

            "insight": insight,

            "summary": {
                "row_count": len(rows),
                "column_count": len(columns),
                "columns": columns
            }

        }

        return format_success(response_data)

    except (ValidationError, LLMError, DatabaseError) as e:
        raise e

    except Exception as e:
        return format_error(f"Unexpected server error: {str(e)}")