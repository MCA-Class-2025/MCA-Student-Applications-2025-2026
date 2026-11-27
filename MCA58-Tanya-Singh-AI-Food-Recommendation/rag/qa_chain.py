
import statistics

from rag.retriever import retrieve_food
from utils.gemini_llm import generate_answer
from utils.response_cache import ttl_cache


def clean_value(value):
    if value is None:
        return "Not available"

    value = str(value).strip()

    if value.lower() in ("", "nan", "none", "null"):
        return "Not available"

    return value


def get_median(records, column):
    values = []

    for record in records:
        try:
            value = float(record.get(column))

            if value == value:
                values.append(value)

        except (TypeError, ValueError):
            continue

    if not values:
        return "Not available"

    return round(statistics.median(values), 1)


def build_food_context(documents):

    pdf_documents = []
    excel_groups = {}

    for doc in documents:

        source_type = str(
            doc.get("source_type", "")
        ).upper()

        if source_type == "PDF":
            pdf_documents.append(doc)

        elif source_type == "EXCEL":
            food_name = clean_value(
                doc.get("food_name")
            )

            if food_name != "Not available":
                excel_groups.setdefault(
                    food_name.lower(), []
                ).append(doc)

    context_parts = []

    # Keep only the three most relevant PDF chunks
    if pdf_documents:
        context_parts.append(
            "RECIPE BOOK INFORMATION:"
        )

        for doc in pdf_documents[:3]:

            text = clean_value(doc.get("text"))

            # Limit each PDF chunk
            text = text[:1400]

            context_parts.append(
                f"""
Recipe information:
{text}
"""
            )

    # Keep at most three distinct foods
    if excel_groups:
        context_parts.append(
            "FOOD AND NUTRITION INFORMATION:"
        )

        for records in list(excel_groups.values())[:3]:

            first = records[0]

            context_parts.append(
                f"""
Food: {clean_value(first.get('food_name'))}
Cuisine: {clean_value(first.get('cuisine'))}
Meal type: {clean_value(first.get('meal_type'))}
Diet: {clean_value(first.get('diet'))}
Ingredients: {clean_value(first.get('ingredients'))}

Calories: {get_median(records, 'calories')} kcal
Protein: {get_median(records, 'protein_g')} g
Carbohydrates: {get_median(records, 'carbs_g')} g
Fat: {get_median(records, 'fat_g')} g
Fiber: {get_median(records, 'fiber_g')} g

Suitable season: {clean_value(first.get('weather_suitable'))}
"""
            )

    return "\n\n".join(context_parts)


@ttl_cache(ttl_seconds=600, maxsize=100)
def ask_food_question(question, top_k=6):
    """Retrieve information and generate a cached AI response."""

    if not question or not question.strip():
        return {
            "answer": "Please enter a food-related question."
        }

    try:
        documents = retrieve_food(
            question,
            top_k=top_k
        )

        if not documents:
            return {
                "answer": (
                    "I couldn't find relevant food information. "
                    "Please try another recipe or food question."
                )
            }

        context = build_food_context(documents)

        answer = generate_answer(
            question=question,
            context=context
        )

        return {"answer": answer}

    except Exception as error:
        print("Food QA Error:", error)

        return {
            "answer": (
                "Sorry, I couldn't process your question. "
                "Please try again."
            )
        }


if __name__ == "__main__":

    result = ask_food_question(
        "Tell me about Rajma Masala and its nutrition."
    )

    print("\nRASOI AI ANSWER\n")
    print(result["answer"])
