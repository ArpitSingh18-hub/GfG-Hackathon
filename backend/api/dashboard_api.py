from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from backend.llm.sql_generator import generate_sql
from backend.services.query_executor import execute_query
from backend.llm.chart_selector import select_chart
from backend.services.insight_generator import generate_insights

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    previous_query: Optional[str] = None
    previous_sql: Optional[str] = None


@router.post("/query")
def run_query(req: QueryRequest):

    # Generate SQL
    sql = generate_sql(req.query, req.previous_query, req.previous_sql)

    # Execute query
    result = execute_query(sql)

    # Handle query errors
    if isinstance(result, dict) and "error" in result:
        return {
            "user_query": req.query,
            "generated_sql": sql,
            "error": result["error"]
        }

    # Extract rows safely
    rows = result.get("data", []) if isinstance(result, dict) else result

    # Extract column names
    columns = list(rows[0].keys()) if rows else []

    # Generate chart suggestion
    chart_info = select_chart(req.query, sql, columns)

    # Use only sample rows for insight generation
    sample_rows = rows[:10]

    insight = generate_insights(req.query, sample_rows)

    return {
        "user_query": req.query,
        "generated_sql": sql,
        "data": rows,
        "chart_info": chart_info,
        "insight": insight
    }