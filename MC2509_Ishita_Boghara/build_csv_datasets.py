import csv
import json
import os
import requests

DATA_DIR = "data"
API_URL = "http://127.0.0.1:8000/api/book"


def load_json(filename):
    path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        return data.get("books", data.get("data", []))

    return []

BOOKS = load_json("books_database.json")

def write_csv(filename, rows, fieldnames):
    path = os.path.join(DATA_DIR, filename)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ {filename}: {len(rows)} records")


os.makedirs(DATA_DIR, exist_ok=True)


# ============================================================
# 1. STATIC DATASET
# ============================================================

static = load_json("books_database.json")

static_rows = []

for book in static:
    static_rows.append({
        "title": book.get("title", ""),
        "author": book.get("author", ""),
        "genre": book.get("genre", ""),
        "year": book.get("year", book.get("publication_year", "")),
        "description": book.get("description", "")
    })

write_csv(
    "static_books.csv",
    static_rows,
    ["title", "author", "genre", "year", "description"]
)


# ============================================================
# 2. DYNAMIC DATASET
# ============================================================

dynamic_rows = []
dynamic_json = []

for book in BOOKS:
    title = book.get("title", "")
    author = book.get("author", "")
    try:
        response = requests.get(
            f"{API_URL}/{title}", 
            params={"author": author}, 
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()

            if result.get("success"):
                dynamic_json.append(result)

                dynamic_rows.append({
                    "title": result.get("book", title),
                    "sources_used": ", ".join(
                        result.get("sources_used", [])
                    ),
                    "source_count": result.get("source_count", 0)
                })

                print(f"🌐 Dynamic: {title} → SUCCESS")

    except Exception as e:
        print(f"⚠️ Dynamic failed: {title} → {e}")


with open(
    os.path.join(DATA_DIR, "dynamic_books.json"),
    "w",
    encoding="utf-8"
) as f:
    json.dump(dynamic_json, f, indent=2, ensure_ascii=False)

write_csv(
    "dynamic_books.csv",
    dynamic_rows,
    ["title", "sources_used", "source_count"]
)


# ============================================================
# 3. FUSION DATASET
# ============================================================

fusion_rows = []

static_by_title = {book.get("title", "").strip().lower(): book for book in static}

for item in dynamic_json:
    title = item.get("book", "")
    data = item.get("data", {})

    static_book = static_by_title.get(title.strip().lower(), {})

    wiki = data.get("wikipedia", {})
    ol = data.get("open_library", {})
    gut = data.get("gutendex", {})
    wd = data.get("wikidata", {})
    ia = data.get("internet_archive", {})

    fusion_rows.append(
        {
            "title": title,
            # Static dataset is the trusted identity baseline.
            "author": static_book.get("author", ""),
            "year": static_book.get("year", static_book.get("publication_year", "")),
            # Use external API data only for enrichment.
            "publication_date": wd.get("publication_date", ""),
            "summary": (
                wiki.get("summary", "")
                if wiki.get("success")
                else static_book.get("description", "")
            ),
            "languages": ", ".join(gut.get("languages", []))
            if gut.get("success")
            else "",
            "downloads": (gut.get("download_count", 0) if gut.get("success") else 0),
            "sources": ", ".join(item.get("sources_used", [])),
            "source_count": item.get("source_count", 0),
            "internet_archive_author": ia.get("author", ""),
            "internet_archive_date": ia.get("publication_date", ""),
            "internet_archive_language": ia.get("language", ""),
            "internet_archive_id": ia.get("identifier", ""),
        }
    )


write_csv(
    "fusion_books.csv",
    fusion_rows,
    [
        "title",
        "author",
        "year",
        "publication_date",
        "summary",
        "languages",
        "downloads",
        "internet_archive_author",
        "internet_archive_date",
        "internet_archive_language",
        "internet_archive_id",
        "sources",
        "source_count",
    ],
)


# ============================================================
# 4. API RECORDS DATASET
# ============================================================

api_rows = []

for item in dynamic_json:

    title = item.get("book", "")
    data = item.get("data", {})

    for api_name in [
    "wikipedia",
    "open_library",
    "gutendex",
    "wikidata",
    "internet_archive"
]:

        api_data = data.get(api_name, {})

        api_rows.append({
            "book": title,
            "api": api_name,
            "status": "Success" if api_data.get("success") else "Failed",
            "source": api_data.get("source", api_name)
        })

write_csv(
    "api_records.csv",
    api_rows,
    ["book", "api", "status", "source"]
)


# ============================================================
# 5. BOOK FEATURES DATASET
# ============================================================

feature_rows = []

for row in fusion_rows:

    feature_rows.append({
        "title": row["title"],
        "author": row["author"],
        "publication_year": row["year"],
        "language": row["languages"],
        "download_count": row["downloads"],
        "api_source_count": row["source_count"],
        "has_summary": "Yes" if row["summary"] else "No"
    })

write_csv(
    "book_features.csv",
    feature_rows,
    [
        "title",
        "author",
        "publication_year",
        "language",
        "download_count",
        "api_source_count",
        "has_summary"
    ]
)


print("\n======================================")
print("🎉 ALL CSV DATASETS CREATED")
print("======================================")

for filename in [
    "static_books.csv",
    "dynamic_books.csv",
    "fusion_books.csv",
    "api_records.csv",
    "book_features.csv"
]:
    print("📄 data/" + filename)