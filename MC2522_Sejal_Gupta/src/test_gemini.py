import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not set in the .env file")

client = genai.Client(api_key=api_key)


def test_gemini():
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents="Say hello in one short sentence."
    )

    print("\n===== GEMINI API TEST =====")
    print(response.text)
    print("===========================\n")


if __name__ == "__main__":
    test_gemini()