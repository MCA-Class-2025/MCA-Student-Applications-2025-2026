import os
import csv
from datetime import datetime

DATA_DIR = "data"


def save_book_search(api_result):
    """Append a newly searched/fused book to dynamic CSV datasets."""

    if not api_result or not api_result.get("success"):
        return

    book = api_result.get("book") or api_result.get("book_title", "")
    fusion = api_result.get("api_fusion", {}).get("data", {})

    if not book:
        return

    os.makedirs(DATA_DIR, exist_ok=True)

    # -----------------------------
    # 1. Dynamic Books
    # -----------------------------
    sources = []

    for name, data in fusion.items():
        if isinstance(data, dict) and data.get("success"):
            sources.append(name)

    dynamic_file = os.path.join(DATA_DIR, "dynamic_books.csv")

    existing = set()
    if os.path.exists(dynamic_file):
        with open(dynamic_file, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existing.add(row.get("title", "").strip().lower())

    if book.strip().lower() not in existing:
        with open(dynamic_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            if os.path.getsize(dynamic_file) == 0:
                writer.writerow(["title", "sources_used", "source_count"])

            writer.writerow([
                book,
                ", ".join(sources),
                len(sources)
            ])

    # -----------------------------
    # 2. API Records
    # -----------------------------
    api_file = os.path.join(DATA_DIR, "api_records.csv")

    with open(api_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if os.path.getsize(api_file) == 0:
            writer.writerow(["book", "api", "status", "source"])

        for api_name, data in fusion.items():
            if not isinstance(data, dict):
                continue

            success = data.get("success", False)

            writer.writerow([
                book,
                api_name,
                "Success" if success else "Failed",
                data.get("source", api_name)
            ])

    # -----------------------------
    # 3. Fusion Books
    # -----------------------------
    fusion_file = os.path.join(DATA_DIR, "fusion_books.csv")

    successful = [
        (name, data)
        for name, data in fusion.items()
        if isinstance(data, dict) and data.get("success")
    ]

    author = ""
    year = ""
    publication_date = ""
    summary = ""
    language = ""
    downloads = 0

    for name, data in successful:
        if not author:
            author = data.get("author", "") or data.get("authors", "")
        if not year:
            year = data.get("first_publish_year", "")
        if not publication_date:
            publication_date = data.get("publication_date", "")
        if not summary:
            summary = data.get("summary", "")
        if not language:
            languages = data.get("languages", [])
            language = ", ".join(languages) if isinstance(languages, list) else languages
        if not downloads:
            downloads = data.get("download_count", 0)

    existing_fusion = set()

    if os.path.exists(fusion_file):
        with open(fusion_file, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existing_fusion.add(row.get("title", "").strip().lower())

    if book.strip().lower() not in existing_fusion:
        with open(fusion_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            if os.path.getsize(fusion_file) == 0:
                writer.writerow([
                    "title",
                    "author",
                    "year",
                    "publication_date",
                    "summary",
                    "languages",
                    "downloads",
                    "sources",
                    "source_count"
                ])

            writer.writerow([
                book,
                author,
                year,
                publication_date,
                summary,
                language,
                downloads,
                ", ".join(name for name, _ in successful),
                len(successful)
            ])

    print(f"✅ Dataset updated: {book}")