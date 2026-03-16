import json
import re
from backend.llm.gemini_client import ask_gemini

_chart_cache = {}

def clean_json(text: str):
    text = re.sub(r"```json", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)
    return text.strip()

def select_chart(user_query: str, sql: str, columns: list):
    cache_key = f"{user_query}_{sql}"
    if cache_key in _chart_cache:
        return _chart_cache[cache_key]

    columns_str = ", ".join(columns) if columns else "none"
    
    prompt = f"""
You are an expert Data Visualization engine.
Based on the user query, the generated SQL, and the available columns, select the most appropriate chart type.

User Query: {user_query}
SQL Query: {sql}
Result Columns: {columns_str}

Available chart types: "bar", "line", "pie", "scatter", "table", "number"

Rules for Selection:
1. If the result is a single number or stat, use "number".
2. If it's time-series (dates/months), use "line".
3. If comparing categories against a metric, use "bar" or "pie".
4. If there are many columns or no obvious grouping, default to "table".

Return ONLY valid JSON with this exact structure:
{{
    "chart_type": "...",
    "x_axis": "column_name for x axis (or null)",
    "y_axis": "column_name for y axis (or null)"
}}
Do NOT output any markdown, only the raw JSON.
"""
    try:
        response = ask_gemini(prompt)
        cleaned = clean_json(response)
        chart_info = json.loads(cleaned)
    except Exception as e:
        chart_info = {
            "chart_type": "table",
            "x_axis": columns[0] if columns else None,
            "y_axis": columns[1] if len(columns) > 1 else None
        }

    _chart_cache[cache_key] = chart_info
    return chart_info
