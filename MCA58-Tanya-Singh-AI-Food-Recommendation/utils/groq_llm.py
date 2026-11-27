
from groq import Groq
from config import GROQ_API_KEY


MODEL_NAME = "openai/gpt-oss-20b"

_client = None


def get_client():
    global _client

    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is missing. Check your .env file."
        )

    if _client is None:
        _client = Groq(
            api_key=GROQ_API_KEY,
            timeout=30.0,
            max_retries=1
        )

    return _client


def generate_answer(question, context):

    if not context or not context.strip():
        return (
            "I couldn't find relevant food information "
            "in the knowledge base."
        )

    system_prompt = """
You are Rasoi AI, an Indian food recipe and nutrition assistant.

Your job is to answer questions about:
- Indian recipes
- Ingredients
- Cooking and preparation methods
- Calories
- Protein
- Carbohydrates
- Fat
- Fiber
- Suitable seasons

IMPORTANT RULES:

1. Use only the supplied food knowledge.
2. Never invent ingredients or recipe quantities.
3. Never invent nutrition values.
4. Do not invent cooking steps.
5. Do not display database IDs or technical metadata.
6. If information is missing, say it is not available.
7. Avoid repeating the same food records.
8. Use simple, friendly English.
9. Do not make unsupported medical claims.

Keep answers concise and useful.

Use these headings when relevant:

## Recipe
## Ingredients
## Preparation
## Nutritional Information
## Suitable Season
"""

    user_prompt = f"""
USER QUESTION:
{question}

RETRIEVED FOOD KNOWLEDGE:
{context}

Generate the answer using the system instructions.
"""

    try:
        client = get_client()

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            max_completion_tokens=600
        )

        answer = response.choices[0].message.content

        if answer and answer.strip():
            return answer.strip()

        return "The AI returned an empty response. Please try again."

    except Exception as error:

        print("Groq API Error:", str(error))

        return (
            "Rasoi AI could not generate an answer. "
            "Please check your Groq API key, model access "
            "and API usage limits."
        )


if __name__ == "__main__":

    sample_context = """
    Food: Vegetable Upma
    Ingredients: Semolina, vegetables and peanuts.
    Calories: 350 kcal
    Protein: 25 g
    Carbohydrates: 40 g
    Fat: 12 g
    Fiber: 8 g
    Suitable season: Hot
    """

    answer = generate_answer(
        "Tell me about Vegetable Upma and its nutrition.",
        sample_context
    )

    print("\nRASOI AI RESPONSE\n")
    print(answer)
