from PIL.Image import item
import requests
from typing import Dict

from streamlit import title


class WikipediaAPI:
    BASE_URL = "https://en.wikipedia.org/api/rest_v1"

    def get_book_info(self, title: str) -> Dict:
        try:
            url = f"{self.BASE_URL}/page/summary/{title.replace(' ', '_')}"

            headers = {"User-Agent": "BookMuse/2.0 (bookmuse-college-project)"}

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                returned_title = data.get("title", "").lower()

                if title.lower() == "1984" and returned_title != "1984 (novel)":
                    return {
                        "success": False,
                        "error": "Wikipedia returned the year 1984 instead of the novel",
                    }

                return {
                    "success": True,
                    "title": data.get("title", ""),
                    "summary": data.get("extract", ""),
                    "url": data.get("content_urls", {})
                    .get("desktop", {})
                    .get("page", ""),
                    "source": "Wikipedia",
                }

            return {
                "success": False,
                "error": f"Wikipedia returned status {response.status_code}",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


class OpenLibraryAPI:
    BASE_URL = "https://openlibrary.org"

    def search_book(self, title: str, expected_author: str = "") -> Dict:
        try:
            url = f"{self.BASE_URL}/search.json"
            params = {
                "q": f'title:"{title}"',
                "limit": 20,
            }
            headers = {"User-Agent": "BookMuse/2.0 (bookmuse-college-project)"}

            response = requests.get(url, params=params, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data.get("docs"):
                    docs = data["docs"]

                    candidates = []

                    for item in docs:
                        item_title = item.get("title", "")
                        authors = item.get("author_name", [])

                        if not item_title or not authors:
                            continue

                        title_match = title.lower() in item_title.lower()

                        if not title_match:
                            continue

                        author_match = (
                            not expected_author
                            or any(
                                expected_author.lower() in author.lower()
                                or author.lower() in expected_author.lower()
                                for author in authors
                            )
                        )

                        if not author_match:
                            continue

                        item_title_lower = item_title.lower()

                        penalty_words = [
                            "adaptation",
                            "poster",
                            "sparknotes",
                            "notes",
                            "guide",
                            "summary",
                            "movie",
                            "film",
                            "comic",
                            "special",
                        ]

                        penalty = sum(
                            1
                            for word in penalty_words
                            if word in item_title_lower
                        )

                        year = item.get("first_publish_year") or 9999

                        candidates.append(
                            (
                                penalty,
                                year,
                                item,
                            )
                        )

                    if not candidates:
                        return {
                            "success": False,
                            "error": "No relevant Open Library book found",
                        }

                    candidates.sort(key=lambda x: (x[0], x[1]))

                    book = candidates[0][2]

                if book is None:
                        return {
                            "success": False,
                            "error": "No relevant Open Library book found",
                }

                return {
                        "success": True,
                        "title": book.get("title", ""),
                        "author": ", ".join(book.get("author_name", [])),
                        "first_publish_year": book.get("first_publish_year", ""),
                        "isbn": book.get("isbn", [])[:3],
                        "source": "Open Library",
                    }

                return {"success": False, "error": "Book not found"}

            return {
                "success": False,
                "error": f"Open Library returned status {response.status_code}",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


class GutendexAPI:
    BASE_URL = "https://gutendex.com/books"

    def search_book(self, title: str) -> Dict:
        try:
            response = requests.get(self.BASE_URL, params={"search": title}, timeout=20)

            if response.status_code == 200:
                data = response.json()

                if data.get("results"):
                    # Find a result whose title matches the searched book
                    searched_title = title.lower().strip()

                    matching_book = None

                    for book in data["results"]:
                        returned_title = book.get("title", "").lower().strip()

                        if (
                            returned_title == searched_title
                            or searched_title in returned_title
                            or returned_title in searched_title
                        ):
                            matching_book = book
                            break

                    # Do not use unrelated Gutendex results
                    if not matching_book:
                        return {
                            "success": False,
                            "error": "No matching Gutendex book found",
                        }

                    authors = ", ".join(
                        author.get("name", "")
                        for author in matching_book.get("authors", [])
                    )

                    return {
                        "success": True,
                        "id": matching_book.get("id"),
                        "title": matching_book.get("title", ""),
                        "author": authors,
                        "subjects": matching_book.get("subjects", [])[:5],
                        "languages": matching_book.get("languages", []),
                        "download_count": matching_book.get("download_count", 0),
                        "source": "Gutendex",
                    }

                return {"success": False, "error": "Book not found"}

            return {
                "success": False,
                "error": (f"Gutendex returned status {response.status_code}"),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


class WikidataAPI:
    BASE_URL = "https://query.wikidata.org/sparql"

    def search_book(self, title: str) -> Dict:
        try:
            query = f"""
            SELECT ?book ?bookLabel ?authorLabel ?publicationDate WHERE {{
              ?book rdfs:label "{title}"@en .
              OPTIONAL {{ ?book wdt:P50 ?author . }}
              OPTIONAL {{ ?book wdt:P577 ?publicationDate . }}
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
            }}
            LIMIT 1
            """

            headers = {
                "User-Agent": "BookMuse/2.0 (bookmuse-college-project)",
                "Accept": "application/sparql-results+json",
            }

            response = requests.get(
                self.BASE_URL,
                params={"query": query, "format": "json"},
                headers=headers,
                timeout=20,
            )

            if response.status_code == 200:
                data = response.json()
                bindings = data.get("results", {}).get("bindings", [])

                if bindings:
                    item = bindings[0]

                    return {
                        "success": True,
                        "title": item.get("bookLabel", {}).get("value", ""),
                        "author": item.get("authorLabel", {}).get("value", ""),
                        "publication_date": item.get("publicationDate", {}).get(
                            "value", ""
                        ),
                        "source": "Wikidata",
                    }

                return {"success": False, "error": "Book not found in Wikidata"}

            return {
                "success": False,
                "error": f"Wikidata returned status {response.status_code}",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


class InternetArchiveAPI:
    BASE_URL = "https://archive.org/advancedsearch.php"

    def search_book(self, title: str) -> Dict:
        try:
            params = {
                "q": f'title:"{title}" AND mediatype:texts',
                "fl[]": ["identifier", "title", "creator", "date", "language"],
                "rows": 5,
                "output": "json",
            }

            response = requests.get(self.BASE_URL, params=params, timeout=20)

            if response.status_code == 200:
                data = response.json()
                docs = data.get("response", {}).get("docs", [])

                if docs:
                    book = docs[0]

                    if title.lower() == "1984" and (
                        "gazzetta" in book.get("title", "").lower()
                        or book.get("language", "").lower() == "italian"
                    ):
                        return {
                            "success": False,
                            "error": "Internet Archive returned an unrelated 1984 record",
                        }

                return {
                    "success": True,
                    "identifier": book.get("identifier", ""),
                    "title": book.get("title", ""),
                    "author": book.get("creator", ""),
                    "publication_date": book.get("date", ""),
                    "language": book.get("language", ""),
                    "source": "Internet Archive",
                }

                return {"success": False, "error": "Book not found"}

            return {
                "success": False,
                "error": f"Internet Archive returned status {response.status_code}",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


class BookMuseFusion:
    def __init__(self):
        self.wikipedia = WikipediaAPI()
        self.open_library = OpenLibraryAPI()
        self.gutendex = GutendexAPI()
        self.wikidata = WikidataAPI()
        self.internet_archive = InternetArchiveAPI()

    def get_book_intelligence(self, title: str, expected_author: str = "") -> Dict:

        wikipedia = self.wikipedia.get_book_info(title)
        open_library = self.open_library.search_book(title, expected_author)
        gutendex = self.gutendex.search_book(title)
        wikidata = self.wikidata.search_book(title)
        internet_archive = self.internet_archive.search_book(title)

        return {
            "title": title,
            "wikipedia": wikipedia,
            "open_library": open_library,
            "gutendex": gutendex,
            "wikidata": wikidata,
            "internet_archive": internet_archive,
            "source_count": sum(
                1
                for source in [
                    wikipedia,
                    open_library,
                    gutendex,
                    wikidata,
                    internet_archive
                ]
                if source.get("success")
            )
        }


if __name__ == "__main__":
    print("\n===== WIKIPEDIA API TEST =====")

    wiki = WikipediaAPI()
    result = wiki.get_book_info("The Great Gatsby")

    if result["success"]:
        print("✅ API 1 WORKING")
        print("Title:", result["title"])
    else:
        print("❌ API 1 FAILED:", result["error"])

    print("\n===== OPEN LIBRARY API TEST =====")

    open_library = OpenLibraryAPI()
    result = open_library.search_book("The Great Gatsby")

    if result["success"]:
        print("✅ API 2 WORKING")
        print("Title:", result["title"])
        print("Author:", result["author"])
        print("Year:", result["first_publish_year"])
        print("Source:", result["source"])
    else:
        print("❌ API 2 FAILED")
        print("Error:", result["error"])

    print("\n===== GUTENDEX API TEST =====")

    gutendex = GutendexAPI()
    result = gutendex.search_book("Pride and Prejudice")

    if result["success"]:
        print("✅ API 3 WORKING")
        print("Title:", result["title"])
        print("Author:", result["author"])
        print("Languages:", result["languages"])
        print("Downloads:", result["download_count"])
        print("Source:", result["source"])
    else:
        print("❌ API 3 FAILED")
        print("Error:", result["error"])

    print("\n===== WIKIDATA API TEST =====")

    wikidata = WikidataAPI()
    result = wikidata.search_book("Pride and Prejudice")

    if result["success"]:
        print("✅ API 4 WORKING")
        print("Title:", result["title"])
        print("Author:", result["author"])
        print("Publication:", result["publication_date"])
        print("Source:", result["source"])
    else:
        print("❌ API 4 FAILED")
        print("Error:", result["error"])

    print("\n===== BOOKMUSE FUSION TEST =====")

    fusion = BookMuseFusion()
    result = fusion.get_book_intelligence("Pride and Prejudice")

    print("✅ FUSION COMPLETED")
    print("Book:", result["title"])
    print("Sources combined:", result["source_count"])

    for source in ["wikipedia", "open_library", "gutendex", "wikidata"]:
        print(source, "→", "✅" if result[source].get("success") else "❌")
