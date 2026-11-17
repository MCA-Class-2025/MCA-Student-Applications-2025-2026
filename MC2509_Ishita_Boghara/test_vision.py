import base64
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

image_path = "test_cover.jpg"

with open(image_path, "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode("utf-8")

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """
Look carefully at this book cover.

Read the text directly from the image.

Return ONLY:

Title: ...
Author: ...

Do not guess.
Do not use outside knowledge.
If text is unclear, say UNKNOWN.
"""
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                }
            ]
        }
    ],
    max_tokens=100
)

print("\n===== VISION TEST =====")
print(response.choices[0].message.content)