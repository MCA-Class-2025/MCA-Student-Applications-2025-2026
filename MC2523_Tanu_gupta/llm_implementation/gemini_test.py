import os

from dotenv import load_dotenv
from google import genai


# Load .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY not found in .env"
    )


# Create Gemini client
client = genai.Client(
    api_key=api_key
)


# Send test request
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Explain weather forecasting in two simple sentences."
)


print("\nGemini Response:")
print("==========================")
print(response.text)