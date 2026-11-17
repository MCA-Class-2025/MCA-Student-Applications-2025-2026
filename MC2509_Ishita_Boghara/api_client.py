import json
import os
import requests

API_BASE_URL = "http://127.0.0.1:8000"


def get_expected_author(title: str):
    path = os.path.join("data", "books_database.json")

    try:
        with open(path, "r", encoding="utf-8") as f:
            books = json.load(f)

        for book in books:
            if book.get("title", "").strip().lower() == title.strip().lower():
                return book.get("author", "")

    except Exception:
        pass

    return ""


def get_book_intelligence(title: str):
    try:
        author = get_expected_author(title)

        response = requests.get(
            f"{API_BASE_URL}/api/book/{title}", params={"author": author}, timeout=30
        )

        if response.status_code == 200:
            return response.json()

        return {"success": False, "error": f"API returned {response.status_code}"}

    except Exception as e:
        return {"success": False, "error": str(e)}
