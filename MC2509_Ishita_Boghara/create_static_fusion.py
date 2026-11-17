import pandas as pd
import os

INPUT_FILE = "data/books.csv"
OUTPUT_FILE = "data/fusion_data.csv"

# Read Kaggle dataset
df = pd.read_csv(INPUT_FILE)

# Create source-aware fusion dataset
fusion = pd.DataFrame(
    {
        "title": df["title"],
        "title_source": "Kaggle 7K Books with Metadata",
        "author": df["authors"],
        "author_source": "Kaggle 7K Books with Metadata",
        "year": df["published_year"],
        "year_source": "Kaggle 7K Books with Metadata",
        "description": df["description"],
        "description_source": "Kaggle 7K Books with Metadata",
        "genre": df["categories"],
        "genre_source": "Kaggle 7K Books with Metadata",
        "rating": df["average_rating"],
        "rating_source": "Kaggle 7K Books with Metadata",
        "pages": df["num_pages"],
        "pages_source": "Kaggle 7K Books with Metadata",
        "ratings_count": df["ratings_count"],
        "ratings_count_source": "Kaggle 7K Books with Metadata",
        "isbn13": df["isbn13"],
        "isbn13_source": "Kaggle 7K Books with Metadata",
        "isbn10": df["isbn10"],
        "isbn10_source": "Kaggle 7K Books with Metadata",
        "subtitle": df["subtitle"],
        "subtitle_source": "Kaggle 7K Books with Metadata",
        "thumbnail": df["thumbnail"],
        "thumbnail_source": "Kaggle 7K Books with Metadata",
    }
)

os.makedirs("data", exist_ok=True)

fusion.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print("STATIC FUSION DATASET CREATED")
print("ROWS:", len(fusion))
print("COLUMNS:", len(fusion.columns))
print("FILE:", OUTPUT_FILE)
