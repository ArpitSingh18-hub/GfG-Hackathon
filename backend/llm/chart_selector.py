import json
import re
from backend.llm.gemini_client import ask_gemini

_chart_cache = {}

def clean_json(text: str):
    text = re.sub(r"```json", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)
    return text.strip()

def select_chart_and_insight(user_query: str, sql: str, columns: list, rows: list):
    cache_key = f"{user_query}_{sql}"
    if cache_key in _chart_cache:
        return _chart_cache[cache_key]

    # Truncate sample data to save input tokens
    truncated_rows = []
    for row in (rows[:5] if rows else []):
        trunc_row = {}
        for k, v in row.items():
            s = str(v)
            trunc_row[k] = s[:50] + "..." if len(s) > 50 else s
        truncated_rows.append(trunc_row)
        
    sample_data = str(truncated_rows) if truncated_rows else "No data returned."
    # Also limit massive column lists natively
    columns_str = ", ".join(columns[:100]) if columns else "none"
    
    prompt = f"""
You are an expert Data Visualization engine and Business Intelligence analyst.
Based on the user query, the generated SQL, the available columns, and the data sample, do TWO things:
1. Select the most appropriate chart type for modern frontend libraries like Recharts or Chart.js.
2. Provide a brief, professional, 1-2 sentence business insight based on the data sample. Do not hallucinate numbers not in the data. Make it sound like an executive summary.

User Query: {user_query}
SQL Query: {sql}
Result Columns: {columns_str}
Data Sample (first 10 rows):
{sample_data}

Available chart types: "bar", "line", "pie", "scatter", "table", "number", "area"

Rules for Selection:
1. If the result is a single number or stat, use "number".
2. If it's time-series (dates/months on x-axis), use "line" or "area".
3. If comparing categories against a metric, use "bar".
4. If showing parts of a whole, use "pie".
5. If there are many columns or no obvious grouping, default to "table".

Return ONLY valid JSON with this exact structure:
{{
    "chart_type": "...",
    "x_axis": "column_name for x axis",
    "y_axis": ["column_name1", "column_name2"],
    "title": "A descriptive title for the chart",
    "description": "A brief explanation of why this chart was chosen",
    "color_palette": ["#8884d8", "#82ca9d", "#ffc658", "#ff8042"],
    "insight": "Your 1-2 sentence business insight goes here"
}}

Note: y_axis should be a list of column names that represent metrics/values.
Do NOT output any markdown, only the raw JSON.
"""
    try:
        response = ask_gemini(prompt, is_json=True)
        cleaned = clean_json(response)
        chart_info = json.loads(cleaned)
        
        # Validation
        if "chart_type" not in chart_info:
            chart_info["chart_type"] = "table"
        if "y_axis" not in chart_info:
            chart_info["y_axis"] = [columns[1]] if len(columns) > 1 else []
        elif isinstance(chart_info["y_axis"], str):
            chart_info["y_axis"] = [chart_info["y_axis"]]

        if "insight" not in chart_info:
            chart_info["insight"] = "No insights could be generated."

    except Exception as e:
        print(f"Chart/insight selection error: {e}")
        chart_info = {
            "chart_type": "table",
            "x_axis": columns[0] if columns else None,
            "y_axis": [columns[1]] if len(columns) > 1 else [],
            "title": "Data Table",
            "description": "Defaulting to table view due to suggestion error.",
            "color_palette": ["#8884d8"],
            "insight": "No insights could be generated."
        }

    _chart_cache[cache_key] = chart_info
    return chart_info
