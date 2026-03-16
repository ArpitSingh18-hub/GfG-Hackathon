from backend.llm.gemini_client import ask_gemini

_insight_cache = {}

def generate_insights(user_query: str, data: list):
    if not data:
        return "No data returned for this query."
    
    # We serialize first few rows to avoid giant contexts
    sample_data = str(data[:10])
    
    cache_key = f"{user_query}_{sample_data}"
    if cache_key in _insight_cache:
        return _insight_cache[cache_key]

    prompt = f"""
You are an expert Business Intelligence analyst analyzing data from YouTube.
Based on the user's query and the data results, provide a brief, professional, 1-2 sentence business insight.
Do not hallucinate numbers not in the data. Make it sound like an executive summary.
Return ONLY the text of the insight without markdown or labels.

User Query: {user_query}
Data Sample (first 10 rows):
{sample_data}
"""
    try:
        insight = ask_gemini(prompt)
    except Exception as e:
        insight = "Could not generate insight at this time."

    _insight_cache[cache_key] = insight
    return insight
