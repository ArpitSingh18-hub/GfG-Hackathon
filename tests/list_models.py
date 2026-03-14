import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

print("Listing available models...")
try:
    for model in client.models.list():
        print(f"Name: {model.name}, Supported Actions: {model.supported_actions}")
except Exception as e:
    print(f"Error: {e}")
