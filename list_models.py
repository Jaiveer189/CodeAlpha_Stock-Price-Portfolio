from google import genai
import os

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("ERROR: GOOGLE_API_KEY not set. See instructions below.")
else:
    client = genai.Client(api_key=api_key)
    print("Available models:\n")
    for model in client.models.list():
        print(f"  {model.name}")