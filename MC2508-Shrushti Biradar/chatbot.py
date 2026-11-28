import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY was not found in .env")

client = genai.Client(api_key=api_key)

# If the first model is busy, we try the next one.
MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-2.5-flash",
]

TRIES_PER_MODEL = 2


def generate_response(user_message):
    last_error = ""

    for model_name in MODELS:

        for attempt in range(TRIES_PER_MODEL):

            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=user_message
                )

                if response and response.text:
                    return response.text

                last_error = f"{model_name}: empty answer"
                break

            except Exception as e:
                last_error = f"{model_name}: {e}"
                error_message = str(e).lower()

                # This prints the REAL error in your terminal.
                print(f"[Gemini] {last_error}")

                # Busy model: wait a little, then try again.
                if (
                    "503" in error_message
                    or "unavailable" in error_message
                    or "overloaded" in error_message
                ):
                    time.sleep(2 * (attempt + 1))
                    continue

                # Quota or wrong name: skip to the next model.
                break

    return (
        "⚠️ Gemini could not answer right now.\n\n"
        "Please try again in a minute.\n\n"
        f"Details: {last_error}"
    )