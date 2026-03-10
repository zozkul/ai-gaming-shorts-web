import os
from dotenv import load_dotenv
import google.genai as genai

load_dotenv()
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

print("📋 Mevcut modeller:")
for model in client.models.list():
    if 'video' in model.name.lower() or 'veo' in model.name.lower():
        print(f"  🎬 {model.name}")
