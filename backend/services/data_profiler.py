import math
import json
import re
from typing import Any
import pandas as pd
import numpy as np
from backend.llm.gemini_client import ask_gemini


# ─────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────

def _safe(val):
    """Convert any non-JSON-safe value to a Python native type."""
    if val is None:
        return None
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        v = float(val)
        return None if (math.isnan(v) or math.isinf(v)) else v
    if isinstance(val, (np.bool_,)):
        return bool(val)
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    if isinstance(val, (pd.Timestamp,)):
        return str(val)
    if hasattr(val, "item"):          # catch-all for numpy scalars
        return val.item()
    return val


def _clean_json(text: str) -> str:
    text = re.sub(r"```json", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)
    return text.strip()


# ─────────────────────────────────────────────────────────────
# Column-level profiling
# ─────────────────────────────────────────────────────────────

def _profile_column(series: pd.Series) -> dict:
    """Return a rich profile dict for a single DataFrame column."""
    col = series.dropna()
    total = len(series)
    non_null = len(col)
    null_count = total - non_null
    null_pct = round(null_count / total * 100, 2) if total else 0.0
    unique_count = int(col.nunique())
    dtype_str = str(series.dtype)

    # ── Infer semantic type ──────────────────────────────────
    name_lower = series.name.lower()
    if pd.api.types.is_datetime64_any_dtype(series):
        semantic = "datetime"
    elif pd.api.types.is_numeric_dtype(series):
        semantic = "numeric"
    elif unique_count <= 20 and pd.api.types.is_object_dtype(series):
        semantic = "categorical"
    elif any(kw in name_lower for kw in ["text", "description", "title", "content", "body", "review", "comment", "name"]):
        semantic = "text"
    elif any(kw in name_lower for kw in ["url", "link", "href", "uri"]):
        semantic = "url"
    elif any(kw in name_lower for kw in ["email", "mail"]):
        semantic = "email"
    elif any(kw in name_lower for kw in ["id", "_id", "uuid", "key"]):
        semantic = "identifier"
    else:
        semantic = "categorical" if pd.api.types.is_object_dtype(series) else "other"

    base = {
        "column": series.name,
        "dtype": dtype_str,
        "semantic_type": semantic,
        "total_rows": total,
        "non_null_count": non_null,
        "null_count": null_count,
        "null_pct": null_pct,
        "unique_count": unique_count,
        "is_unique": unique_count == non_null and non_null > 0,
    }

    # ── Numeric stats ────────────────────────────────────────
    if semantic == "numeric":
        base.update({
            "min": _safe(col.min()),
            "max": _safe(col.max()),
            "mean": _safe(round(col.mean(), 4)),
            "median": _safe(col.median()),
            "std": _safe(round(col.std(), 4)),
            "sum": _safe(col.sum()),
            "q25": _safe(col.quantile(0.25)),
            "q75": _safe(col.quantile(0.75)),
            "has_negatives": bool((col < 0).any()),
            "is_integer_like": bool((col % 1 == 0).all()),
        })

    # ── Categorical / text top values ───────────────────────
    if semantic in ("categorical", "text", "identifier", "url", "email", "other"):
        top5 = col.value_counts().head(5)
        base["top_values"] = [
            {"value": str(k), "count": int(v)}
            for k, v in top5.items()
        ]

    # ── Datetime range ───────────────────────────────────────
    if semantic == "datetime":
        base.update({
            "min_date": str(col.min()),
            "max_date": str(col.max()),
            "date_range_days": _safe((col.max() - col.min()).days) if non_null >= 2 else None,
        })

    return base


# ─────────────────────────────────────────────────────────────
# Dataset-level summary
# ─────────────────────────────────────────────────────────────

def _dataset_summary(df: pd.DataFrame, column_profiles: list[dict]) -> dict:
    """High-level dataset facts."""
    numeric_cols   = [p["column"] for p in column_profiles if p["semantic_type"] == "numeric"]
    categorical_cols = [p["column"] for p in column_profiles if p["semantic_type"] == "categorical"]
    datetime_cols  = [p["column"] for p in column_profiles if p["semantic_type"] == "datetime"]
    text_cols      = [p["column"] for p in column_profiles if p["semantic_type"] == "text"]
    id_cols        = [p["column"] for p in column_profiles if p["semantic_type"] == "identifier"]

    # duplicate row detection
    duplicate_rows = int(df.duplicated().sum())

    # memory
    memory_kb = round(df.memory_usage(deep=True).sum() / 1024, 2)

    return {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "duplicate_rows": duplicate_rows,
        "duplicate_pct": round(duplicate_rows / len(df) * 100, 2) if len(df) else 0,
        "memory_kb": memory_kb,
        "numeric_column_count": len(numeric_cols),
        "categorical_column_count": len(categorical_cols),
        "datetime_column_count": len(datetime_cols),
        "text_column_count": len(text_cols),
        "identifier_column_count": len(id_cols),
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "datetime_columns": datetime_cols,
        "text_columns": text_cols,
        "identifier_columns": id_cols,
        "columns_with_nulls": [
            p["column"] for p in column_profiles if p["null_count"] > 0
        ],
        "fully_unique_columns": [
            p["column"] for p in column_profiles if p["is_unique"]
        ],
    }


# ─────────────────────────────────────────────────────────────
# Sentiment detection (text columns only)
# ─────────────────────────────────────────────────────────────

def _detect_sentiment(df: pd.DataFrame, text_cols: list[str]) -> dict:
    """
    Lightweight keyword-based sentiment for text columns.
    Returns per-column sentiment distribution without calling an LLM.
    """
    positive_kw = {"good","great","excellent","amazing","love","best","awesome",
                   "fantastic","wonderful","perfect","happy","positive","nice","top"}
    negative_kw = {"bad","worst","terrible","awful","hate","poor","horrible",
                   "disappointing","negative","slow","broken","ugly","failed","error"}

    result = {}
    for col in text_cols:
        pos = neg = neu = 0
        for val in df[col].dropna().astype(str):
            words = set(val.lower().split())
            if words & positive_kw:
                pos += 1
            elif words & negative_kw:
                neg += 1
            else:
                neu += 1
        total = pos + neg + neu
        result[col] = {
            "positive": pos,
            "negative": neg,
            "neutral": neu,
            "positive_pct": round(pos / total * 100, 2) if total else 0,
            "negative_pct": round(neg / total * 100, 2) if total else 0,
            "neutral_pct":  round(neu / total * 100, 2) if total else 0,
        }
    return result


# ─────────────────────────────────────────────────────────────
# LLM: Dataset description + 10 questions
# ─────────────────────────────────────────────────────────────

def _llm_analysis(
    table_name: str,
    summary: dict,
    column_profiles: list[dict],
) -> dict:
    """
    Ask Gemini to:
      1. Describe what the dataset is about
      2. Generate 10 meaningful analysis questions
    Returns {"description": str, "suggested_questions": [str x 10]}
    """

    # Compact profile for the prompt (avoid token explosion)
    compact_cols = []
    for p in column_profiles:
        entry: dict[str, Any] = {
            "column": p["column"],
            "type": p["semantic_type"],
            "dtype": p["dtype"],
            "unique": p["unique_count"],
            "nulls_pct": p["null_pct"],
        }
        if p["semantic_type"] == "numeric":
            entry.update({
                "min": p.get("min"), "max": p.get("max"),
                "mean": p.get("mean"), "sum": p.get("sum"),
            })
        if "top_values" in p:
            entry["sample_values"] = [t["value"] for t in p["top_values"][:3]]
        compact_cols.append(entry)

    prompt = f"""
You are an expert data analyst.

You have been given a dataset named "{table_name}" with the following profile:

Total rows: {summary["total_rows"]}
Total columns: {summary["total_columns"]}
Numeric columns: {summary["numeric_columns"]}
Categorical columns: {summary["categorical_columns"]}
Datetime columns: {summary["datetime_columns"]}
Text columns: {summary["text_columns"]}

Column details:
{json.dumps(compact_cols, indent=2)}

Your tasks:
1. Write a 2-3 sentence plain-English description of what this dataset is about,
   what domain it comes from, and what kind of analysis it supports.
2. Generate exactly 10 insightful analytical questions a business user could ask
   about this dataset. Questions should be diverse — cover trends, comparisons,
   top/bottom rankings, distributions, correlations, and anomalies.
   Every question must be answerable from the columns that actually exist.

Return ONLY valid JSON, no markdown:
{{
  "description": "...",
  "suggested_questions": [
    "Question 1?",
    "Question 2?",
    ...
    "Question 10?"
  ]
}}
"""

    try:
        response = ask_gemini(prompt, is_json=True)
        cleaned = _clean_json(response)
        parsed = json.loads(cleaned)
        # Validate structure
        if "description" not in parsed or "suggested_questions" not in parsed:
            raise ValueError("Missing keys in LLM response")
        # Ensure exactly 10 questions
        questions = parsed["suggested_questions"][:10]
        while len(questions) < 10:
            questions.append("What are the key trends in this dataset?")
        parsed["suggested_questions"] = questions
        return parsed
    except Exception as e:
        print("LLM analysis failed:", e)
        return {
            "description": f"This dataset contains {summary['total_rows']} rows and {summary['total_columns']} columns covering {', '.join(summary['numeric_columns'][:3])} and other fields.",
            "suggested_questions": [
                f"What is the total {col}?" for col in summary["numeric_columns"][:3]
            ] + [
                f"What are the top values in {col}?" for col in summary["categorical_columns"][:3]
            ] + [
                "What is the overall distribution of the data?",
                "Are there any outliers in the dataset?",
                "What are the trends over time?",
                "Which category has the highest value?",
            ]
        }


# ─────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────

def profile_dataset(df: pd.DataFrame, table_name: str) -> dict:
    """
    Full dataset profiling pipeline.
    Returns a single dict with everything the frontend needs:
      - dataset summary
      - per-column profiles
      - sentiment analysis (text columns)
      - LLM-generated description + 10 suggested questions
    """

    # 1. Per-column profiles
    column_profiles = [_profile_column(df[col]) for col in df.columns]

    # 2. Dataset summary
    summary = _dataset_summary(df, column_profiles)

    # 3. Sentiment (only if text columns exist)
    sentiment = {}
    if summary["text_columns"]:
        sentiment = _detect_sentiment(df, summary["text_columns"])

    # 4. LLM description + questions
    llm_result = _llm_analysis(table_name, summary, column_profiles)

    return {
        "table_name": table_name,
        "summary": summary,
        "column_profiles": column_profiles,
        "sentiment": sentiment,
        "description": llm_result["description"],
        "suggested_questions": llm_result["suggested_questions"],
    }