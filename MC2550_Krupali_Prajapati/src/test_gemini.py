
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY not found in .env")
    raise SystemExit

client = genai.Client(api_key=api_key)

print("\nChecking Gemini models available to your API key...\n")

try:
    available = list(client.models.list())

    candidates = []

    for model in available:
        name = getattr(model, "name", "") or ""
        actions = getattr(model, "supported_actions", []) or []

        if "generateContent" in actions:
            model_id = name.replace("models/", "")

            if "flash" in model_id.lower():
                candidates.append(model_id)

    # Try lighter Flash models first.
    candidates.sort(
        key=lambda x: (
            "lite" not in x.lower(),
            x
        )
    )

    if not candidates:
        print("No Flash models supporting generateContent were listed.")
        raise SystemExit

    print("Available Flash models:")
    for model in candidates:
        print("-", model)

    print("\nTesting models...\n")

    for model in candidates:
        try:
            print("Testing:", model)

            response = client.models.generate_content(
                model=model,
                contents="Reply with exactly: GEMINI_CONNECTION_OK"
            )

            print("\nSUCCESS!")
            print("Working model:", model)
            print("Response:", response.text)
            print("\nSave this model name. We will use it in the app.")
            break

        except Exception as error:
            print("This model did not work:")
            print(str(error)[:350])
            print("\nTrying the next available model...\n")

    else:
        print("\nNo listed Flash model completed the test.")
        print("We will use a different LLM approach if necessary.")

except Exception as error:
    print("Could not retrieve Gemini models.")
    print(str(error))
