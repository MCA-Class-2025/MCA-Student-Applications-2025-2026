"""
MovieMind AI
Data Preprocessing Module
"""

import pandas as pd
import ast
from pathlib import Path

# ---------------------------------------------------
# Project Paths
# ---------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "new_movies_full.csv"
OUTPUT_FILE = DATA_DIR / "processed_movies.csv"

# ---------------------------------------------------
# Load Dataset
# ---------------------------------------------------

print("=" * 60)
print("Loading Movie Dataset...")
print("=" * 60)

df = pd.read_csv(INPUT_FILE)

print(f"Movies Loaded : {len(df)}")

# ---------------------------------------------------
# Remove Movies Without Overview
# ---------------------------------------------------

df = df.dropna(subset=["overview"])

print(f"Movies after cleaning : {len(df)}")

# ---------------------------------------------------
# Function to extract names from JSON-like strings
# ---------------------------------------------------

def extract_names(text):
    try:
        data = ast.literal_eval(text)

        if isinstance(data, dict):
            data = data.get("genres", []) or data.get("keywords", [])

        return ", ".join(item["name"] for item in data)

    except:
        return ""

# ---------------------------------------------------
# Extract Genres
# ---------------------------------------------------

print("Extracting Genres...")

df["genres_clean"] = df["genres"].apply(extract_names)

# ---------------------------------------------------
# Extract Keywords
# ---------------------------------------------------

print("Extracting Keywords...")

df["keywords_clean"] = df["keywords"].apply(extract_names)

# ---------------------------------------------------
# Extract Cast & Director
# ---------------------------------------------------

def extract_cast(text):

    try:
        data = ast.literal_eval(text)

        cast = data.get("cast", [])

        names = [actor["name"] for actor in cast[:5]]

        return ", ".join(names)

    except:
        return ""


def extract_director(text):

    try:
        data = ast.literal_eval(text)

        crew = data.get("crew", [])

        for person in crew:

            if person["job"] == "Director":
                return person["name"]

        return ""

    except:
        return ""


print("Extracting Cast...")

df["cast"] = df["credits"].apply(extract_cast)

print("Extracting Directors...")

df["director"] = df["credits"].apply(extract_director)

# ---------------------------------------------------
# Create Search Text
# ---------------------------------------------------

print("Creating Search Text...")

df["search_text"] = (
    "Title: " + df["title"].fillna("") +
    "\nGenres: " + df["genres_clean"].fillna("") +
    "\nOverview: " + df["overview"].fillna("") +
    "\nKeywords: " + df["keywords_clean"].fillna("") +
    "\nCast: " + df["cast"].fillna("") +
    "\nDirector: " + df["director"].fillna("")
)

# ---------------------------------------------------
# Keep Required Columns
# ---------------------------------------------------

final_df = df[
    [
        "title",
        "overview",
        "genres_clean",
        "keywords_clean",
        "cast",
        "director",
        "vote_average",
        "popularity",
        "runtime",
        "release_date",
        "search_text"
    ]
]

# ---------------------------------------------------
# Save Dataset
# ---------------------------------------------------

final_df.to_csv(OUTPUT_FILE, index=False)

print("\nProcessed dataset saved successfully!")

print(f"Location : {OUTPUT_FILE}")

print("\nFinal Shape :", final_df.shape)

print("\nDone!")