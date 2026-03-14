import os
import sys
from dotenv import load_dotenv

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.llm.gemini_client import ask_gemini

load_dotenv()

def test_gemini_connection():
    print("Testing Gemini Client...")
    prompt = "Hello Gemini, this is a test from the GfG-Hackathon backend. Reply with 'Success' if you can hear me."
    
    try:
        response = ask_gemini(prompt)
        print(f"Response: {response}")
        if "Success" in response:
            print("[PASS] Gemini Client test passed!")
        else:
            print("[WARN] Received unexpected response, but connection worked.")
    except Exception as e:
        print(f"[FAIL] Gemini Client test failed: {e}")

if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY not found in environment. Please check your .env file.")
    else:
        test_gemini_connection()
