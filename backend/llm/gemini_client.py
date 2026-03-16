import os
import time
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Initialize the Gemini Client
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("[ERROR] GEMINI_API_KEY not found in environment variables.")

client = genai.Client(api_key=api_key)

# gemini-2.0-flash-lite has ~3x higher free-tier RPM quota than gemini-2.0-flash
# Free tier limits: Flash = 10 RPM, Flash-Lite = 30 RPM
# Switch back to "gemini-2.0-flash" if you upgrade to a paid plan
MODEL_NAME = "gemini-2.5-flash"

def ask_gemini(prompt: str, max_retries: int = 5, is_json: bool = False):
    """
    Sends a prompt to Gemini using the google-genai SDK with exponential
    backoff to handle 429 Quota/Rate limit errors.
    """
    delay = 5  # Start with 5 seconds to give the API breathing room

    for attempt in range(max_retries):
        try:
            config = {"temperature": 0.1}
            if is_json:
                config["response_mime_type"] = "application/json"

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=config,
            )

            if not response.text:
                return "Error: Empty response from AI"

            return response.text.strip()

        except Exception as e:
            error_msg = str(e).lower()

            # Check for rate limit (429) or Quota errors
            if "exhausted" in error_msg or "429" in error_msg or "quota" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = delay
                    # Honour the Retry-After hint the API sends back
                    retry_match = re.search(r"retry in (\d+(?:\.\d+)?)s", error_msg)
                    if retry_match:
                        wait_time = float(retry_match.group(1)) + 2.0  # 2s buffer

                    print(
                        f"[WARN] Gemini quota hit. Retrying in {wait_time:.1f}s..."
                        f" (Attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                    delay = max(delay * 2, wait_time)  # True exponential backoff
                    continue

            # For auth errors, non-quota errors, or exhausted retries
            print(f"[FAIL] Gemini Error: {e}")
            raise

    raise RuntimeError(
        f"Gemini API failed after {max_retries} retries due to quota limits."
    )
