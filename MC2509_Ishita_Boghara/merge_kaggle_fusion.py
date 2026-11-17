import pandas as pd
import shutil
import os

base = "data/books.csv"
old_fusion = "data/fusion_books.csv"
backup = "data/fusion_books_30_backup.csv"
output = "data/fusion_books.csv"

books = pd.read_csv(base)

if os.path.exists(old_fusion):
    shutil.copy2(old_fusion, backup)
    fusion = pd.read_csv(old_fusion)
else:
    fusion = pd.DataFrame()

books["_key"] = books["title"].astype(str).str.strip().str.lower()

if not fusion.empty and "title" in fusion.columns:
    fusion["_key"] = fusion["title"].astype(str).str.strip().str.lower()

    api_cols = [
        "author", "year", "publication_date", "summary",
        "languages", "downloads", "sources", "source_count",
        "internet_archive_author", "internet_archive_date",
        "internet_archive_language", "internet_archive_id"
    ]

    available = [c for c in api_cols if c in fusion.columns]

    fusion_api = fusion[["_key"] + available].drop_duplicates("_key")

    final = books.merge(fusion_api, on="_key", how="left")

else:
    final = books.copy()

final.drop(columns=["_key"], inplace=True, errors="ignore")

final.to_csv(output, index=False, encoding="utf-8-sig")

print("DONE")
print("FINAL ROWS:", len(final))
print("FINAL COLUMNS:", len(final.columns))
print("FILE:", output)
print("BACKUP:", backup)

