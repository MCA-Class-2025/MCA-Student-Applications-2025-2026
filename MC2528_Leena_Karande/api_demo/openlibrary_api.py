"""
Open Library API Demo
DanceCompass AI

Purpose:
Find books and literature related to a dance form.
The results can later be used as additional
knowledge sources for the DanceCompass RAG system.
"""

import requests


OPEN_LIBRARY_URL = "https://openlibrary.org/search.json"


def search_openlibrary(dance_name: str) -> dict:
    """
    Search Open Library for books related to a dance form.
    """

    params = {
        "q": f"{dance_name} dance",
        "fields": "key,title,author_name,first_publish_year,edition_count,cover_i",
        "limit": 5,
    }

    headers = {
        "User-Agent": "DanceCompass-AI/1.0"
    }

    try:
        response = requests.get(
            OPEN_LIBRARY_URL,
            params=params,
            headers=headers,
            timeout=10,
        )

        if response.status_code != 200:
            return {
                "dance": dance_name,
                "found": False,
                "error": f"HTTP {response.status_code}",
            }

        data = response.json()

        books = []

        for book in data.get("docs", []):
            books.append({
                "title": book.get("title"),
                "authors": book.get("author_name", []),
                "first_publish_year": book.get("first_publish_year"),
                "edition_count": book.get("edition_count"),
                "cover_id": book.get("cover_i"),
                "openlibrary_key": book.get("key"),
            })

        return {
            "dance": dance_name,
            "found": len(books) > 0,
            "total_results": data.get("numFound", 0),
            "books": books,
        }

    except requests.RequestException as e:
        return {
            "dance": dance_name,
            "found": False,
            "error": str(e),
        }


def enrich_dance_with_literature(dance_name: str) -> dict:
    """
    Find literature related to the dance form.
    """

    return search_openlibrary(dance_name)


if __name__ == "__main__":

    dance_name = input("Enter dance name: ")

    result = enrich_dance_with_literature(dance_name)

    print("\n--- Open Library API Result ---")

    print(f"Dance: {result.get('dance')}")
    print(f"Found: {result.get('found')}")
    print(f"Total results: {result.get('total_results')}")

    print("\nRelated Books:")

    for index, book in enumerate(result.get("books", []), start=1):

        print(f"\nBook {index}")
        print(f"Title: {book.get('title')}")
        print(f"Authors: {', '.join(book.get('authors', []))}")
        print(f"First Published: {book.get('first_publish_year')}")
        print(f"Editions: {book.get('edition_count')}")
        print(f"Open Library ID: {book.get('openlibrary_key')}")