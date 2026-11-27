
import os
import pandas as pd

from config import ORIGINAL_DATA, FUSED_DATA_DIR


FUSED_FILE = os.path.join(
    FUSED_DATA_DIR,
    "fused_food_dataset.csv"
)


def load_excel_documents():
    """Convert food dataset rows into RAG documents."""

    if os.path.exists(FUSED_FILE):
        file_path = FUSED_FILE
        print("Loading fused food dataset...")

        df = pd.read_csv(file_path)

    elif os.path.exists(ORIGINAL_DATA):
        file_path = ORIGINAL_DATA
        print("Loading original food dataset...")

        df = pd.read_excel(file_path)

    else:
        print("Food Excel dataset not found.")
        return []

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    df = df.where(pd.notna(df), None)

    documents = []

    for _, row in df.iterrows():

        food_name = row.get("food_name")

        if not food_name:
            continue

        text = f"""
Food Name: {row.get('food_name', 'Not available')}
Cuisine: {row.get('cuisine', 'Not available')}
Meal Type: {row.get('meal_type', 'Not available')}
Diet: {row.get('diet', 'Not available')}
Ingredients: {row.get('ingredients', 'Not available')}

Calories: {row.get('calories', 'Not available')} kcal
Protein: {row.get('protein_g', 'Not available')} g
Carbohydrates: {row.get('carbs_g', 'Not available')} g
Fat: {row.get('fat_g', 'Not available')} g
Fiber: {row.get('fiber_g', 'Not available')} g

Spice Level: {row.get('spice_level', 'Not available')}
Cooking Time: {row.get('cooking_time_min', 'Not available')} minutes
Difficulty: {row.get('difficulty', 'Not available')}
Health Category: {row.get('health_category', 'Not available')}
Suitable Season: {row.get('weather_suitable', 'Not available')}
"""

        metadata = {
            "text": text.strip(),
            "source_type": "EXCEL",
            "source_file": os.path.basename(file_path),
            "page": None,
            "chunk": None,
            "food_id": str(row.get("food_id", "")),
            "food_name": str(food_name),
            "cuisine": row.get("cuisine"),
            "meal_type": row.get("meal_type"),
            "diet": row.get("diet"),
            "ingredients": row.get("ingredients"),
            "calories": row.get("calories"),
            "protein_g": row.get("protein_g"),
            "carbs_g": row.get("carbs_g"),
            "fat_g": row.get("fat_g"),
            "fiber_g": row.get("fiber_g"),
            "weather_suitable": row.get("weather_suitable"),
            "cooking_time_min": row.get("cooking_time_min"),
            "difficulty": row.get("difficulty")
        }

        documents.append(metadata)

    print("Excel documents loaded:", len(documents))

    return documents


if __name__ == "__main__":
    docs = load_excel_documents()

    print("\nTotal food documents:", len(docs))

    if docs:
        print("\nSample document:")
        print(docs[0]["text"])
