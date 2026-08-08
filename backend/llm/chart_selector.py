import json
import re
import math
from typing import List, Dict, Any
import numpy as np
from backend.llm.gemini_client import ask_gemini

_chart_cache: dict[str, Any] = {}

SUPPORTED_CHARTS = ["bar", "line", "pie", "scatter", "table", "number", "area"]
DEFAULT_PALETTE  = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"]


# ─────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────

def clean_json(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"```json", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)
    return text.strip()


def sanitize_value(val):
    """Replace nan/inf/numpy scalars so they never crash JSON serialization."""
    if val is None:
        return None
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        v = float(val)
        return None if (math.isnan(v) or math.isinf(v)) else v
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return val


def is_numeric(value) -> bool:
    try:
        f = float(value)
        return not (math.isnan(f) or math.isinf(f))
    except Exception:
        return False


def detect_numeric_columns(rows: List[Dict]) -> List[str]:
    if not rows:
        return []
    return [
        key for key in rows[0].keys()
        if all(is_numeric(r.get(key)) for r in rows[:10] if r.get(key) is not None)
    ]


def detect_time_columns(rows: List[Dict]) -> List[str]:
    if not rows:
        return []
    kws = ["date", "time", "year", "month", "day", "week", "period", "quarter", "hour"]
    return [col for col in rows[0].keys() if any(k in col.lower() for k in kws)]


def rule_based_chart(columns: List[str], rows: List[Dict]) -> str:
    if not rows:
        return "table"
    numeric_cols = detect_numeric_columns(rows)
    time_cols    = detect_time_columns(rows)
    if len(columns) == 1:
        return "number"
    if time_cols and numeric_cols:
        return "line"
    if len(columns) == 2 and numeric_cols:
        return "bar"
    if len(columns) >= 3 and numeric_cols:
        return "scatter"
    return "table"


def validate_axes(chart_info: Dict, columns: List[str], rows: List[Dict]) -> Dict:
    if not columns:
        chart_info["x_axis"] = None
        chart_info["y_axis"] = []
        return chart_info

    numeric_cols = detect_numeric_columns(rows)

    x_axis = chart_info.get("x_axis")
    if x_axis not in columns:
        chart_info["x_axis"] = columns[0]

    y_axis = chart_info.get("y_axis", [])
    if isinstance(y_axis, str):
        y_axis = [y_axis]
    valid_y = [col for col in y_axis if col in columns]
    if not valid_y:
        valid_y = [numeric_cols[0]] if numeric_cols else ([columns[1]] if len(columns) > 1 else [])
    chart_info["y_axis"] = valid_y

    return chart_info


def generate_title(x_axis, y_axis) -> str:
    if x_axis and y_axis:
        return f"{y_axis[0].replace('_',' ').title()} by {x_axis.replace('_',' ').title()}"
    if y_axis:
        return f"{y_axis[0].replace('_',' ').title()} Analysis"
    return "Data Overview"


# ─────────────────────────────────────────────
# Data profile (compact, full-dataset stats)
# ─────────────────────────────────────────────

def profile_data(rows: List[Dict]) -> str:
    """
    Build a compact statistical summary string of ALL rows.
    Used in the LLM prompt so insights are grounded in real data,
    not just 5 sample rows.
    """
    if not rows:
        return "No data."

    total = len(rows)
    columns = list(rows[0].keys())
    numeric_cols = detect_numeric_columns(rows)
    lines = [f"Total rows: {total}", f"Columns: {', '.join(columns)}", ""]

    for col in columns:
        values = [sanitize_value(r.get(col)) for r in rows if r.get(col) is not None]

        if col in numeric_cols:
            nums = [float(v) for v in values if v is not None]
            if nums:
                nums_sorted = sorted(nums)
                n = len(nums_sorted)
                mean = sum(nums_sorted) / n
                lines.append(
                    f"  {col} [numeric]: min={round(nums_sorted[0],2)}, "
                    f"max={round(nums_sorted[-1],2)}, mean={round(mean,2)}, "
                    f"sum={round(sum(nums_sorted),2)}"
                )
        else:
            freq: dict = {}
            for v in values:
                k = str(v)
                freq[k] = freq.get(k, 0) + 1
            top3 = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:3]
            top_str = ", ".join(f"{k}({c})" for k, c in top3)
            lines.append(f"  {col} [categorical]: {len(freq)} unique | top: {top_str}")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# Single-query chart selector
# ─────────────────────────────────────────────

def select_chart_and_insight(
    user_query: str,
    sql: str,
    columns: List[str],
    rows: List[Dict],
) -> Dict[str, Any]:
    """Pick the best chart for a specific user query and generate a targeted insight."""

    # Short cache key — hash of query + row count + first/last row
    fingerprint = f"{len(rows)}_{str(rows[0]) if rows else ''}_{str(rows[-1]) if rows else ''}"
    cache_key = f"{user_query[:80]}_{fingerprint}"

    if cache_key in _chart_cache:
        return _chart_cache[cache_key]

    # Full-dataset stats summary for the LLM (not just 5 rows)
    data_summary = profile_data(rows)
    columns_str  = ", ".join(columns[:50]) if columns else "none"

    prompt = f"""
You are a Business Intelligence visualization expert.

Pick the SINGLE best chart type for this user query and generate a targeted insight.

User Query: {user_query}

SQL: {sql}

Columns: {columns_str}

Full Dataset Summary ({len(rows)} rows):
{data_summary}

Supported charts: bar, line, pie, scatter, table, number, area

Selection guide:
- Single numeric result            → number
- Trend over time                  → line or area
- Category comparison (< 15 cats)  → bar
- Part of whole / proportions      → pie
- Two numeric metrics              → scatter
- Complex / wide data              → table

Return ONLY valid JSON, no markdown:
{{
  "chart_type": "",
  "x_axis": "",
  "y_axis": [],
  "title": "",
  "description": "",
  "color_palette": {json.dumps(DEFAULT_PALETTE)},
  "insight": ""
}}
"""

    try:
        response  = ask_gemini(prompt, is_json=True)
        cleaned   = clean_json(response)
        chart_info = json.loads(cleaned)

        if chart_info.get("chart_type") not in SUPPORTED_CHARTS:
            chart_info["chart_type"] = rule_based_chart(columns, rows)

        chart_info = validate_axes(chart_info, columns, rows)

        chart_info.setdefault("title",       generate_title(chart_info.get("x_axis"), chart_info.get("y_axis")))
        chart_info.setdefault("description", "Visualization automatically generated for your query.")
        chart_info.setdefault("insight",     "Chart summarizes the key relationship in your data.")
        chart_info.setdefault("color_palette", DEFAULT_PALETTE)

    except Exception as e:
        print("Chart selection failed:", e)
        fallback_x = columns[0] if columns else None
        fallback_y = [columns[1]] if len(columns) > 1 else []
        chart_info = {
            "chart_type":    rule_based_chart(columns, rows),
            "x_axis":        fallback_x,
            "y_axis":        fallback_y,
            "title":         generate_title(fallback_x, fallback_y),
            "description":   "Fallback visualization due to AI response error.",
            "color_palette": DEFAULT_PALETTE,
            "insight":       "Visualization generated using rule-based fallback.",
        }

    _chart_cache[cache_key] = chart_info
    return chart_info


# ─────────────────────────────────────────────
# Auto dashboard generator
# ─────────────────────────────────────────────

def generate_dashboard(rows: List[Dict]) -> List[Dict[str, Any]]:
    """
    Auto-generates 4-8 chart configs covering different analytical
    angles of the dataset. Called once on upload, no user query needed.
    """
    if not rows:
        return []

    columns      = list(rows[0].keys())
    numeric_cols = detect_numeric_columns(rows)
    time_cols    = detect_time_columns(rows)
    cat_cols     = [c for c in columns if c not in numeric_cols]
    data_summary = profile_data(rows)

    fingerprint = f"dash_{len(rows)}_{columns}"
    if fingerprint in _chart_cache:
        return _chart_cache[fingerprint]

    prompt = f"""
You are an expert BI dashboard designer.

Design a multi-chart dashboard covering as many meaningful analytical
angles as possible for the dataset below.

Dataset profile:
{data_summary}

Available columns: {columns}
Numeric columns:   {numeric_cols}
Time columns:      {time_cols}
Categorical cols:  {cat_cols}

Supported chart types: bar, line, pie, scatter, table, number, area

Rules:
1. Generate between 4 and 8 charts.
2. Each chart must cover a DIFFERENT angle:
   - KPI totals          → number
   - Trends over time    → line or area  (only if time columns exist)
   - Category comparison → bar
   - Proportions         → pie
   - Correlation         → scatter
   - Full data view      → table
3. x_axis and y_axis MUST use only columns from: {columns}
4. y_axis must always be a JSON array, even for one metric.
5. Each chart needs a clear title and a 1-sentence insight.
6. Return ONLY a valid JSON array, no markdown.

Format:
[
  {{
    "chart_type": "number",
    "x_axis": null,
    "y_axis": ["col_name"],
    "title": "Total X",
    "description": "...",
    "color_palette": {json.dumps(DEFAULT_PALETTE)},
    "insight": "..."
  }}
]
"""

    try:
        response = ask_gemini(prompt, is_json=True)
        charts   = json.loads(clean_json(response))

        validated = []
        for chart in charts:
            if chart.get("chart_type") not in SUPPORTED_CHARTS:
                chart["chart_type"] = "bar"
            chart = validate_axes(chart, columns, rows)
            chart.setdefault("title",         generate_title(chart.get("x_axis"), chart.get("y_axis")))
            chart.setdefault("color_palette", DEFAULT_PALETTE)
            chart.setdefault("insight",       "Auto-generated insight.")
            chart.setdefault("description",   "Auto-generated chart.")
            validated.append(chart)

        _chart_cache[fingerprint] = validated
        return validated

    except Exception as e:
        print("Dashboard generation failed, using rule-based fallback:", e)
        return _fallback_dashboard(columns, numeric_cols, cat_cols, time_cols)


def _fallback_dashboard(columns, numeric_cols, cat_cols, time_cols) -> List[Dict]:
    charts = []

    for col in numeric_cols[:3]:
        charts.append({
            "chart_type": "number", "x_axis": None, "y_axis": [col],
            "title": f"Total {col.replace('_',' ').title()}",
            "description": f"Sum of {col}.", "color_palette": DEFAULT_PALETTE,
            "insight": f"Aggregate KPI for {col}.",
        })

    if time_cols and numeric_cols:
        charts.append({
            "chart_type": "line", "x_axis": time_cols[0], "y_axis": [numeric_cols[0]],
            "title": f"{numeric_cols[0].replace('_',' ').title()} Over Time",
            "description": "Trend over time.", "color_palette": DEFAULT_PALETTE,
            "insight": "Shows primary metric trend over time.",
        })

    if cat_cols and numeric_cols:
        charts.append({
            "chart_type": "bar", "x_axis": cat_cols[0], "y_axis": [numeric_cols[0]],
            "title": f"{numeric_cols[0].replace('_',' ').title()} by {cat_cols[0].replace('_',' ').title()}",
            "description": "Category comparison.", "color_palette": DEFAULT_PALETTE,
            "insight": "Compares primary metric across categories.",
        })

    if len(cat_cols) > 1 and numeric_cols:
        charts.append({
            "chart_type": "pie", "x_axis": cat_cols[1], "y_axis": [numeric_cols[0]],
            "title": f"Distribution by {cat_cols[1].replace('_',' ').title()}",
            "description": "Proportional breakdown.", "color_palette": DEFAULT_PALETTE,
            "insight": "Shows share of each category.",
        })

    charts.append({
        "chart_type": "table",
        "x_axis": columns[0] if columns else None,
        "y_axis": columns[1:4] if len(columns) > 1 else [],
        "title": "Full Data Table", "description": "Complete dataset view.",
        "color_palette": DEFAULT_PALETTE, "insight": "Raw data for inspection.",
    })

    return charts