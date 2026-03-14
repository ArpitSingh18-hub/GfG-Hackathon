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
    sql = generate_sql(req.query, req.previous_query, req.previous_sql)
    data = execute_query(sql)

    if isinstance(data, dict) and "error" in data:
        return {
            "user_query": req.query,
            "generated_sql": sql,
            "error": data["error"]
        }

    columns = list(data[0].keys()) if isinstance(data, list) and data else []

    chart_info = select_chart(req.query, sql, columns)
    insight = generate_insights(req.query, data)

    return {
        "user_query": req.query,
        "generated_sql": sql,
        "data": data,
        "chart_info": chart_info,
        "insight": insight
    }