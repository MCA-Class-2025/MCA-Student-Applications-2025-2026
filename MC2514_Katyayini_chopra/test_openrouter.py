import os
import requests

from dotenv import load_dotenv

load_dotenv()

key = os.getenv("OPENROUTER_API_KEY")

response = requests.post(

    "https://openrouter.ai/api/v1/chat/completions",

    headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    },

    json={

        "model":
            "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",

        "messages": [
            {
                "role": "user",

                "content":
                    "Reply with exactly: FixAI backup working"
            }
        ]
    },

    timeout=60
)

print("Status:", response.status_code)
print(response.text)