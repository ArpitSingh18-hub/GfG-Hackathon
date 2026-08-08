from backend.llm.gemini_client import ask_gemini
import math

_insight_cache = {}


def sanitize_value(val):
    """Convert non-serializable values to safe strings."""
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return val


def summarize_data(data: list[dict]) -> str:
    """
    Instead of passing only 10 rows, build a full statistical summary
    of ALL rows so Gemini can generate insights over the entire dataset.
    """
    if not data:
        return "No data."

    total_rows = len(data)
    columns = list(data[0].keys())

    numeric_cols = {}
    categorical_cols = {}

    for col in columns:
        values = [sanitize_value(row.get(col)) for row in data]
        values = [v for v in values if v is not None]

        # Detect numeric columns
        numeric_values = []
        for v in values:
            try:
                numeric_values.append(float(v))
            except (TypeError, ValueError):
                pass

        if len(numeric_values) >= len(values) * 0.7:
            # Treat as numeric — compute stats
            sorted_vals = sorted(numeric_values)
            n = len(sorted_vals)
            mean = sum(sorted_vals) / n if n else 0
            median = sorted_vals[n // 2] if n else 0
            numeric_cols[col] = {
                "count": n,
                "min": round(sorted_vals[0], 4) if n else None,
                "max": round(sorted_vals[-1], 4) if n else None,
                "mean": round(mean, 4),
                "median": round(median, 4),
                "sum": round(sum(sorted_vals), 4),
            }
        else:
            # Treat as categorical — compute top values by frequency
            freq: dict = {}
            for v in values:
                key = str(v)
                freq[key] = freq.get(key, 0) + 1

            top_5 = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
            categorical_cols[col] = {
                "unique_count": len(freq),
                "top_5": [{"value": k, "count": v} for k, v in top_5],
            }

    # Build a readable summary string
    lines = [f"Total rows: {total_rows}", f"Columns: {', '.join(columns)}", ""]

    if numeric_cols:
        lines.append("Numeric Column Statistics:")
        for col, stats in numeric_cols.items():
            lines.append(
                f"  {col}: min={stats['min']}, max={stats['max']}, "
                f"mean={stats['mean']}, median={stats['median']}, sum={stats['sum']}"
            )
        lines.append("")

    if categorical_cols:
        lines.append("Categorical Column Summaries:")
        for col, stats in categorical_cols.items():
            top = ", ".join(
                f"{item['value']} ({item['count']})" for item in stats["top_5"]
            )
            lines.append(
                f"  {col}: {stats['unique_count']} unique values | Top: {top}"
            )

    return "\n".join(lines)


def generate_insights(user_query: str, data: list) -> str:
    if not data:
        return "No data returned for this query."

    # Cache key based on query + full data length + first+last row fingerprint
    # (avoids re-generating for identical results without hashing all rows)
    fingerprint = f"{len(data)}_{str(data[0])}_{str(data[-1])}"
    cache_key = f"{user_query}_{fingerprint}"

    if cache_key in _insight_cache:
        return _insight_cache[cache_key]

    # Build full statistical summary over ALL rows
    summary = summarize_data(data)

    prompt = f"""
You are an expert Business Intelligence analyst.
Based on the user's query and the FULL dataset summary below, provide a concise, professional 2-3 sentence business insight.

Rules:
- Only reference numbers that are present in the summary.
- Sound like an executive summary — highlight trends, outliers, or key takeaways.
- Do NOT use markdown, bullet points, or labels. Return plain text only.

User Query:
{user_query}

Full Dataset Summary ({len(data)} rows analyzed):
{summary}
"""

    try:
        insight = ask_gemini(prompt)
    except Exception:
        insight = "Could not generate insight at this time."

    _insight_cache[cache_key] = insight
    return insight