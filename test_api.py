from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

try:
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents="Say hello in one sentence."
    )

    print(response.text)

except Exception as e:
    print(e)