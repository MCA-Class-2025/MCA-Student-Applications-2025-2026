import os
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL = "openrouter/free"

df = pd.read_csv(
    "data/building_defect_knowledge.csv"
)

original_data = df[
    [
        "work_type",
        "location",
        "element",
        "defect",
        "example_description"
    ]
].to_json(
    orient="records",
    indent=2
)

questions = [
    "How many Water leak records are present in the original dataset?",
    "Which building element occurs most frequently in the original dataset?",
    "How many records have work_type = RC?",
    "Which location category occurs most frequently in the original dataset?",
    "How many Broken defect records are present in the original dataset?"
]

expected = [
    "6",
    "Wall (13 records)",
    "6",
    "Exterior (10 records)",
    "1"
]

for i, question in enumerate(questions):

    prompt = f"""
You are testing the BEFORE-FUSION version of FixAI.

Use ONLY the original dataset below.

Do not use external knowledge.
Do not use weather.
Do not use air quality.
Do not use professional information.
Do not use service_type.
Do not use any fused/API data.

ORIGINAL DATASET:
{original_data}

QUESTION:
{question}

Answer concisely.
"""

    response = requests.post(
        URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        },
        timeout=60
    )

    print("\n" + "=" * 70)
    print(f"QUESTION {i + 1}")
    print(question)
    print("EXPECTED:")
    print(expected[i])

    if response.ok:
        data = response.json()

        try:
            answer = (
                data["choices"][0]["message"]["content"]
            )
        except Exception:
            answer = str(data)

        print("LLM RESPONSE:")
        print(answer)

    else:
        print("LLM ERROR:")
        print(response.text)