import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("--- HESABINIZA AÇIK GEMINI MODELLERİ ---")
try:
    for model in client.models.list():
        print(model.name)
except Exception as e:
    print(f"Hata oluştu: {e}")