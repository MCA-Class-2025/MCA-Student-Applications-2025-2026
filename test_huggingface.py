import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

print("=" * 70)
print("TESTING HUGGING FACE")
print("=" * 70)

if not HF_TOKEN:
    print("✗ HF_TOKEN missing")
    raise SystemExit

print("✓ HF_TOKEN found")

try:
    client = InferenceClient(
        api_key=HF_TOKEN,
        provider="auto"
    )

    response = client.chat.completions.create(
        model="meta-llama/Llama-3.1-8B-Instruct",
        messages=[
            {
                "role": "user",
                "content": "Give one short interior design tip."
            }
        ],
        max_tokens=100
    )

    result = response.choices[0].message.content

    print("\nHugging Face response:")
    print(result)

    print("\n✓ HUGGING FACE WORKING")

except Exception as e:
    print("\n✗ HUGGING FACE FAILED")
    print(e)