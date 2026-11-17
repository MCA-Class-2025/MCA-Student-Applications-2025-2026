import os
import csv
import json
from api_client import get_book_intelligence
from fusion_dataset import create_fusion_dataset


DYNAMIC_FILE = "data/dynamic_books.json"
DYNAMIC_CSV = "data/dynamic_books.csv"
API_CSV = "data/api_records.csv"
FUSION_CSV = "data/fusion_books.csv"


def save_dynamic_book(title: str):
    result = get_book_intelligence(title)

    if not result.get("success"):
        return False, result.get("error", "API failed")

    os.makedirs("data", exist_ok=True)

    # ============================================================
    # 1. SAVE FULL DATA TO dynamic_books.json
    # ============================================================

    if os.path.exists(DYNAMIC_FILE):
        with open(DYNAMIC_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data = [book for book in data if book.get("book", "").lower() != title.lower()]
    data.append(result)

    with open(DYNAMIC_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # ============================================================
    # 2. UPDATE dynamic_books.csv
    # ============================================================

    sources_used = result.get("sources_used", [])

    rows = []

    if os.path.exists(DYNAMIC_CSV):
        with open(DYNAMIC_CSV, "r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))

    # Remove existing copy of this book
    rows = [
        row for row in rows
        if row.get("title", "").lower() != title.lower()
    ]

    rows.append({
        "title": title,
        "sources_used": ", ".join(sources_used),
        "source_count": len(sources_used)
    })

    with open(DYNAMIC_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["title", "sources_used", "source_count"]
        )
        writer.writeheader()
        writer.writerows(rows)

    # ============================================================
    # 3. UPDATE api_records.csv
    # ============================================================

    api_rows = []

    if os.path.exists(API_CSV):
        with open(API_CSV, "r", encoding="utf-8", newline="") as f:
            api_rows = list(csv.DictReader(f))

    # Remove previous records for this book
    api_rows = [
        row for row in api_rows
        if row.get("book", "").lower() != title.lower()
    ]

    api_data = result.get("data", {})

    for api_name in [
        "wikipedia",
        "open_library",
        "gutendex",
        "wikidata",
        "internet_archive",
    ]:
        api_result = api_data.get(api_name, {})

        if not isinstance(api_result, dict):
            continue

        success = api_result.get("success", False)

        api_rows.append({
            "book": title,
            "api": api_name,
            "status": "Success" if success else "Failed",
            "source": api_result.get("source", api_name)
        })

    with open(API_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["book", "api", "status", "source"]
        )
        writer.writeheader()
        writer.writerows(api_rows)

    # ============================================================
    # 4. REBUILD SOURCE-AWARE FUSION DATASET
    # ============================================================

    fusion_success, fusion_result = create_fusion_dataset()

    if not fusion_success:
        return False, fusion_result

    print(f"✅ Dynamic JSON updated: {title}")
    print(f"✅ Dynamic CSV updated: {title}")
    print(f"✅ API records updated: {title}")
    print(f"✅ Source-aware Fusion CSV updated: data/fusion_books.csv")
    print(f"✅ Source-aware Excel updated: data/BookMuse_Data_Fusion.xlsx")

    return True, result


if __name__ == "__main__":
    success, result = save_dynamic_book("The Silent Patient")

    if success:
        print("✅ DYNAMIC DATASETS UPDATED")
        print("Book:", result["book"])
        print("Sources:", result["sources_used"])
        print("Saved to:", DYNAMIC_FILE)
    else:
        print("❌ FAILED:", result)