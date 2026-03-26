import json
import re
from typing import List, Dict, Any
from backend.llm.gemini_client import ask_gemini

_chart_cache = {}

SUPPORTED_CHARTS = ["bar", "line", "pie", "scatter", "table", "number", "area"]


def clean_json(text: str) -> str:
    """Remove markdown wrappers and return clean JSON text"""
    if not text:
        return ""

    text = re.sub(r"```json", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)
    return text.strip()


def is_numeric(value):
    """Check if value is numeric"""
    try:
        float(value)
        return True
    except:
        return False


def detect_numeric_columns(rows: List[Dict]) -> List[str]:
    """Detect numeric columns from sample data"""
    if not rows:
        return []

    numeric_cols = []

    for key in rows[0].keys():
        values = [r.get(key) for r in rows if r.get(key) is not None]

        if values and all(is_numeric(v) for v in values[:5]):
            numeric_cols.append(key)

    return numeric_cols


def rule_based_chart(columns: List[str], rows: List[Dict]) -> str:
    """
    Fallback chart selector when LLM fails
    """

    if not rows:
        return "table"

    numeric_cols = detect_numeric_columns(rows)

    if len(columns) == 1:
        return "number"

    if len(columns) == 2 and numeric_cols:
        return "bar"

    if len(columns) >= 3 and numeric_cols:
        return "scatter"

    return "table"


def validate_axes(chart_info: Dict, columns: List[str], rows: List[Dict]):
    """
    Ensure axes exist and make logical sense
    """

    if not columns:
        chart_info["x_axis"] = None
        chart_info["y_axis"] = []
        return chart_info

    numeric_cols = detect_numeric_columns(rows)

    # Validate X axis
    x_axis = chart_info.get("x_axis")

    if x_axis not in columns:
        chart_info["x_axis"] = columns[0]

    # Validate Y axis
    y_axis = chart_info.get("y_axis", [])

    if isinstance(y_axis, str):
        y_axis = [y_axis]

    valid_y = [col for col in y_axis if col in columns]

    if not valid_y:
        if numeric_cols:
            valid_y = [numeric_cols[0]]
        elif len(columns) > 1:
            valid_y = [columns[1]]

    chart_info["y_axis"] = valid_y

    return chart_info


def generate_title(x_axis, y_axis):
    """Generate a descriptive chart title"""

    if not x_axis and not y_axis:
        return "Data Overview"

    if x_axis and y_axis:
        return f"{y_axis[0].capitalize()} by {x_axis.capitalize()}"

    if y_axis:
        return f"{y_axis[0].capitalize()} Analysis"

    return "Data Visualization"


def select_chart_and_insight(
    user_query: str,
    sql: str,
    columns: List[str],
    rows: List[Dict]
) -> Dict[str, Any]:

    cache_key = f"{user_query}_{sql}"

    if cache_key in _chart_cache:
        return _chart_cache[cache_key]

    # reduce tokens
    truncated_rows = []

    for row in (rows[:5] if rows else []):
        r = {}

        for k, v in row.items():
            s = str(v)
            r[k] = s[:50] + "..." if len(s) > 50 else s

        truncated_rows.append(r)

    sample_data = str(truncated_rows) if truncated_rows else "No rows returned."

    columns_str = ", ".join(columns[:50]) if columns else "none"

    prompt = f"""
You are a Business Intelligence visualization expert.

Analyze the query results and determine:

1. Best chart type
2. Clear business insight
3. Descriptive chart title

User Query:
{user_query}

SQL Query:
{sql}

Columns:
{columns_str}

Sample Data:
{sample_data}

Supported charts:
bar, line, pie, scatter, table, number, area

Rules:

Single numeric value → number

Time trend → line

Category comparison → bar

Part of whole → pie

Multiple metrics → scatter

Ambiguous data → table

Return ONLY JSON:

{{
"chart_type": "",
"x_axis": "",
"y_axis": [],
"title": "",
"description": "",
"color_palette": ["#636EFA","#EF553B","#00CC96","#AB63FA","#FFA15A"],
"insight": ""
}}
"""

    try:

        response = ask_gemini(prompt, is_json=True)

        cleaned = clean_json(response)

        chart_info = json.loads(cleaned)

        if chart_info.get("chart_type") not in SUPPORTED_CHARTS:
            chart_info["chart_type"] = rule_based_chart(columns, rows)

        chart_info = validate_axes(chart_info, columns, rows)

        if not chart_info.get("title"):
            chart_info["title"] = generate_title(
                chart_info.get("x_axis"),
                chart_info.get("y_axis")
            )

        if not chart_info.get("description"):
            chart_info["description"] = (
                "This visualization was automatically generated "
                "to best represent the query results."
            )

        if not chart_info.get("insight"):
            chart_info["insight"] = (
                "This chart summarizes the relationship between the selected variables."
            )

    except Exception as e:

        print("Chart selection failed:", e)

        chart_type = rule_based_chart(columns, rows)

        fallback_x = columns[0] if columns else None
        fallback_y = [columns[1]] if len(columns) > 1 else []

        chart_info = {
            "chart_type": chart_type,
            "x_axis": fallback_x,
            "y_axis": fallback_y,
            "title": generate_title(fallback_x, fallback_y),
            "description": "Fallback visualization due to AI response failure.",
            "color_palette": [
                "#636EFA",
                "#EF553B",
                "#00CC96",
                "#AB63FA",
                "#FFA15A"
            ],
            "insight": "Visualization generated using rule-based analysis."
        }

    _chart_cache[cache_key] = chart_info

    return chart_info