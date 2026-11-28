import os
from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()

api_key = os.getenv("MISTRAL_API_KEY")

if not api_key:
    print("MISTRAL_API_KEY not found")
    exit()

client = Mistral(
    api_key=api_key
)

response = client.chat.complete(
    model="mistral-large-latest",
    messages=[
        {
            "role": "user",
            "content": "Give me one short interior design idea."
        }
    ]
)

print("\nSUCCESS!")
print(response.choices[0].message.content)