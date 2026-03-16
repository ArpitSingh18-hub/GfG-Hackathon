from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from backend.llm.sql_generator import generate_sql
from backend.services.query_executor import execute_query
from backend.llm.chart_selector import select_chart_and_insight
from backend.utils.response_formatter import format_success, format_error
from backend.utils.exceptions import ValidationError, LLMError, DatabaseError

router = APIRouter()


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="The natural language query from the user")
    previous_query: Optional[str] = Field(None, description="The previous natural language query for context")
    previous_sql: Optional[str] = Field(None, description="The previous SQL query for context")


@router.post("/query")
def run_query(req: QueryRequest):
    try:
        # 1. Generate SQL
        try:
            sql = generate_sql(req.query, req.previous_query, req.previous_sql)
        except Exception as e:
            if "No dataset uploaded" in str(e):
                raise ValidationError(str(e))
            raise LLMError(f"Failed to generate SQL: {str(e)}")

        # 2. Execute query
        try:
            result = execute_query(sql)
        except Exception as e:
            raise DatabaseError(f"Database execution failed: {str(e)}")

        # Handle database service specifically returned errors
        if isinstance(result, dict) and "error" in result:
            return format_error(
                error_message=result["error"],
                data={
                    "user_query": req.query,
                    "generated_sql": sql
                }
            )

        # 3. Extract data
        rows = result.get("data", []) if isinstance(result, dict) else result
        columns = list(rows[0].keys()) if rows else []

        # 4. Suggest Chart and Insights
        try:
            chart_info = select_chart_and_insight(req.query, sql, columns, rows)
            chart_info = dict(chart_info) # Clone to prevent mutating cached object
            # Pop the insight from chart_info to keep the same response structure
            insight = chart_info.pop("insight", "No insights available.")
        except Exception:
            # Fallback to table if chart selection fails
            chart_info = {
                "chart_type": "table",
                "x_axis": columns[0] if columns else None,
                "y_axis": [columns[1]] if len(columns) > 1 else []
            }
            insight = "No insights available."

        # 6. Format Final Response
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
        # Re-raise known API exceptions to be caught by global handler
        raise e
    except Exception as e:
        # Catch-all for unexpected internal errors
        return format_error(f"An unexpected error occurred: {str(e)}")