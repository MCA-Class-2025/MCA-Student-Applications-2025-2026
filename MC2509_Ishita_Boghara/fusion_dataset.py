import json
import os
import pandas as pd

DYNAMIC_FILE = "data/dynamic_books.json"
FUSION_JSON = "data/fusion_books.json"
FUSION_CSV = "data/fusion_books.csv"
FUSION_EXCEL = "data/BookMuse_Data_Fusion.xlsx"


def get_value(data, api, field, default=""):
    """Safely get a value from an API response."""
    return data.get(api, {}).get(field, default)


def create_fusion_dataset():

    if not os.path.exists(DYNAMIC_FILE):
        return False, "Dynamic dataset not found"

    with open(DYNAMIC_FILE, "r", encoding="utf-8") as f:
        dynamic_books = json.load(f)

    fusion_books = []

    for item in dynamic_books:
        data = item.get("data", {})

        # ----------------------------
        # GET DATA FROM EACH API
        # ----------------------------

        # Wikipedia
        wikipedia_summary = get_value(data, "wikipedia", "summary")

        # Open Library
        openlibrary_author = get_value(data, "open_library", "author")

        openlibrary_year = get_value(data, "open_library", "first_publish_year")

        openlibrary_isbn = get_value(data, "open_library", "isbn", [])

        if isinstance(openlibrary_isbn, list):
            openlibrary_isbn = ", ".join(openlibrary_isbn)

        # Gutendex
        gutendex_languages = get_value(data, "gutendex", "languages", [])

        if isinstance(gutendex_languages, list):
            gutendex_languages = ", ".join(gutendex_languages)

        gutendex_downloads = get_value(data, "gutendex", "download_count")

        gutendex_subjects = get_value(data, "gutendex", "subjects", [])

        if isinstance(gutendex_subjects, list):
            gutendex_subjects = ", ".join(gutendex_subjects)

        # Wikidata
        wikidata_publication_date = get_value(data, "wikidata", "publication_date")

        # Internet Archive
        archive_id = get_value(data, "internet_archive", "identifier")

        archive_author = get_value(data, "internet_archive", "author")

        archive_date = get_value(data, "internet_archive", "publication_date")

        archive_language = get_value(data, "internet_archive", "language")

        # ----------------------------
        # CREATE ONE FUSED ROW
        # ----------------------------

        fused_book = {
            "title": item.get("book", ""),
            "title_source": "Application Search",
            # Wikipedia
            "summary": wikipedia_summary,
            "summary_source": "Wikipedia",
            # Open Library
            "author": openlibrary_author,
            "author_source": "Open Library",
            "first_publish_year": openlibrary_year,
            "first_publish_year_source": "Open Library",
            "isbn": openlibrary_isbn,
            "isbn_source": "Open Library",
            # Gutendex
            "languages": gutendex_languages,
            "languages_source": "Gutendex",
            "download_count": gutendex_downloads,
            "download_count_source": "Gutendex",
            "subjects": gutendex_subjects,
            "subjects_source": "Gutendex",
            # Wikidata
            "publication_date": wikidata_publication_date,
            "publication_date_source": "Wikidata",
            # Internet Archive
            "internet_archive_id": archive_id,
            "internet_archive_id_source": "Internet Archive",
            "archive_author": archive_author,
            "archive_author_source": "Internet Archive",
            "archive_publication_date": archive_date,
            "archive_publication_date_source": "Internet Archive",
            "archive_language": archive_language,
            "archive_language_source": "Internet Archive",
            # Overall source information
            "successful_sources": ", ".join(item.get("sources_used", [])),
            "source_count": item.get("source_count", 0),
        }

        fusion_books.append(fused_book)

    # ----------------------------
    # SAVE JSON
    # ----------------------------

    os.makedirs("data", exist_ok=True)

    with open(FUSION_JSON, "w", encoding="utf-8") as f:
        json.dump(fusion_books, f, indent=2, ensure_ascii=False)

    # ----------------------------
    # SAVE CSV
    # ----------------------------

    df = pd.DataFrame(fusion_books)

    df.to_csv(FUSION_CSV, index=False, encoding="utf-8-sig")

    # ----------------------------
    # SAVE EXCEL
    # ----------------------------

    df.to_excel(FUSION_EXCEL, index=False, sheet_name="Fused Dataset")

    return True, fusion_books


if __name__ == "__main__":
    success, result = create_fusion_dataset()

    if success:
        print("FUSION DATASET CREATED")
        print("BOOKS:", len(result))
        print("COLUMNS:", len(result[0]) if result else 0)
        print("JSON:", FUSION_JSON)
        print("CSV:", FUSION_CSV)
        print("EXCEL:", FUSION_EXCEL)
    else:
        print("FAILED")
        print(result)
