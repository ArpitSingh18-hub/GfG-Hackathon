import os
import time
import sys
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Initialize the Gemini Client
# By default, it looks for GOOGLE_API_KEY, but we explicitly pass GEMINI_API_KEY
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Use the latest cost-efficient model gemini-2.5-flash-lite
MODEL_NAME = "gemini-2.5-flash-lite"

def ask_gemini(prompt: str, max_retries: int = 5):
    """
    Sends a prompt to Gemini using the google-genai SDK with exponential 
    backoff to handle 429 Quota/Rate limit errors.
    """
    delay = 2  # Start with 2 seconds

    for attempt in range(max_retries):
        try:
            # Using the suggested client structure
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={
                    'temperature': 0.1,  # Low temperature for reliable SQL
                }
            )
            
            if not response.text:
                return "Error: Empty response from AI"
                
            return response.text.strip()

        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for rate limit (429) or Quota errors
            if "exhausted" in error_msg or "429" in error_msg or "quota" in error_msg:
                if attempt < max_retries - 1:
                    print(f"[WARN] Gemini quota hit. Retrying in {delay}s... (Attempt {attempt + 1})")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                    continue
            
            # For other errors or if retries are exhausted
            print(f"[FAIL] Gemini Error: {e}")
            raise

    raise RuntimeError(f"Gemini API failed after {max_retries} retries due to quota limits.")