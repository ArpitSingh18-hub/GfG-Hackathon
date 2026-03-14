import os
import time
import genkit
from genkit.plugins import google_ai
from dotenv import load_dotenv

load_dotenv()

# Initialize Genkit with the Google AI plugin
# The plugin will automatically use the GEMINI_API_KEY from your .env
ai = genkit.Genkit(plugins=[google_ai.google_ai()])

def ask_gemini(prompt: str, max_retries: int = 5):
    """
    Sends a prompt to Gemini using Genkit with exponential backoff 
    to handle the 429 Quota errors.
    """
    delay = 2  # Start with 2 seconds

    for attempt in range(max_retries):
        try:
            # Using Genkit's generate method
            response = ai.generate(
                model=google_ai.gemini_2_0_flash,
                prompt=prompt,
                config=genkit.GenerationConfig(
                    temperature=0.1, # Low temperature for reliable SQL
                )
            )
            return response.text.strip()

        except Exception as e:
            error_msg = str(e).lower()
            # If we hit a rate limit (429) or Quota error
            if "429" in error_msg or "quota" in error_msg or "rate" in error_msg:
                if attempt < max_retries - 1:
                    print(f"⚠️ Gemini quota hit. Retrying in {delay}s... (Attempt {attempt + 1})")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                    continue
            
            # If it's a different error or we ran out of retries, raise it
            print(f"❌ Gemini Error: {e}")
            raise

    raise RuntimeError("Gemini API failed after maximum retries due to quota limits.")