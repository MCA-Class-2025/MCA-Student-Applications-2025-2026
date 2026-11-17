import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


def generate_food_recommendation(prompt):

    if not GOOGLE_API_KEY:
        return {
            "success": False,
            "error": "GOOGLE_API_KEY is missing from .env"
        }

    try:

        model = genai.GenerativeModel(
            "gemini-flash-latest"
        )

        response = model.generate_content(prompt)

        return {
            "success": True,
            "answer": response.text
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":

    print("=" * 60)
    print("GEMINI API TEST")
    print("=" * 60)

    result = generate_food_recommendation(
        "Suggest one healthy Indian vegetarian dinner."
    )

    if result["success"]:

        print("\nGemini Response:")
        print(result["answer"])

    else:

        print("\nERROR:")
        print(result["error"])