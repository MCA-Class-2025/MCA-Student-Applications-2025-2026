import requests
import streamlit as st

OPEN_LIBRARY_URL = "https://openlibrary.org/search.json"


@st.cache_data(ttl=600)
def search_books(query, max_results=10):

    params = {
        "q": query,
        "limit": max_results
    }

    try:

        response = requests.get(
            OPEN_LIBRARY_URL,
            params=params,
            timeout=15
        )

        if response.status_code != 200:

            return {
                "success": False,
                "message": f"Open Library API error: {response.status_code}",
                "books": []
            }

        data = response.json()

        books = []

        for item in data.get("docs", []):

            title = item.get(
                "title",
                "Unknown Title"
            )

            authors = item.get(
                "author_name",
                ["Unknown Author"]
            )

            cover_id = item.get("cover_i")

            if cover_id:

                thumbnail = (
                    "https://covers.openlibrary.org/b/id/"
                    + str(cover_id)
                    + "-M.jpg"
                )

            else:

                thumbnail = None

            key = item.get("key", "")

            link = ""

            if key:

                link = (
                    "https://openlibrary.org"
                    + key
                )

            books.append({

                "title": title,

                "authors": authors,

                "description": "Technical or career-related book",

                "thumbnail": thumbnail,

                "published": item.get(
                    "first_publish_year",
                    "Unknown"
                ),

                "rating": "Not available",

                "link": link
            })

        return {
            "success": True,
            "message": "Books found successfully.",
            "books": books
        }

    except requests.exceptions.RequestException as e:

        return {
            "success": False,
            "message": str(e),
            "books": []
        }