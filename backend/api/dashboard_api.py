from fastapi import APIRouter
from backend.llm.sql_generator import generate_sql
from backend.services.query_executor import execute_query

router = APIRouter()

@router.post("/query")

def run_query(query: str):

    sql = generate_sql(query)

    data = execute_query(sql)

    return {
        "user_query": query,
        "generated_sql": sql,
        "data": data
    }