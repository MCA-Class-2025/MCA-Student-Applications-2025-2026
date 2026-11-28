
from config import GROQ_API_KEY
from utils.groq_llm import generate_answer


print("=" * 45)
print("RASOI AI - GROQ CONNECTION TEST")
print("=" * 45)

if not GROQ_API_KEY:
    print("ERROR: Groq API key not found.")
    print("Please add GROQ_API_KEY to your .env file.")

else:
    print("Groq API key loaded successfully.")

    context = """
    Food: Vegetable Upma

    Ingredients:
    Semolina, vegetables, peanuts and spices.

    Calories: 350 kcal
    Protein: 25 g
    Carbohydrates: 40 g
    Fat: 12 g
    Fiber: 8 g

    Suitable season: Hot
    """

    question = (
        "Tell me about Vegetable Upma, "
        "its ingredients, nutrition and suitable season."
    )

    print("\nSending question to Groq...\n")

    answer = generate_answer(
        question,
        context
    )

    print("=" * 45)
    print("AI GENERATED ANSWER")
    print("=" * 45)

    print(answer)
