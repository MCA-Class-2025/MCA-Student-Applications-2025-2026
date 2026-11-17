import base64

from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

image_path = "test_cover.jpg"

with open(image_path, "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode("utf-8")

response = client.chat.completions.create(
    model="qwen/qwen3.6-27b",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """
Read this book cover carefully.

Return ONLY:

Title: ...
Author: ...

Read the exact visible text.
Do not guess.
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
    temperature=0,
    max_tokens=100
)

print("\n===== GROQ VISION TEST =====")
print(response.choices[0].message.content)