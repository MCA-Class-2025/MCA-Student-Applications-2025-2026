import os
from pathlib import Path

import requests
from dotenv import load_dotenv


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


# ============================================================
# API CONFIGURATION
# ============================================================

CURRENTS_API_KEY = os.getenv(
    "CURRENTS_API_KEY"
)

CURRENTS_SEARCH_URL = (
    "https://api.currentsapi.services/v1/search"
)


# ============================================================
# LANGUAGE MAPPING
# ============================================================

LANGUAGE_CODES = {

    "English": "en",

    "Hindi": "hi",

    "Marathi": "mr"

}


# ============================================================
# SEARCH NEWS
# ============================================================

def search_news(
    query,
    language="English",
    country="IN",
    max_results=10,
    category=None
):

    # ========================================================
    # CHECK API KEY
    # ========================================================

    if not CURRENTS_API_KEY:

        return {

            "success": False,

            "error": (
                "CURRENTS_API_KEY not found in .env"
            ),

            "articles": []

        }


    # ========================================================
    # LANGUAGE
    # ========================================================

    language_code = LANGUAGE_CODES.get(
        language
    )


    if not language_code:

        return {

            "success": False,

            "error": (
                f"Unsupported language: {language}"
            ),

            "articles": []

        }


    # ========================================================
    # PARAMETERS
    # ========================================================

    params = {

        # Boolean search query
        "query": query,

        "language": language_code,

        "country": country,

        "page_number": 1,

        "page_size": max_results

    }


    # ========================================================
    # OPTIONAL CATEGORY
    # ========================================================

    if category:

        params["category"] = category


    # ========================================================
    # HEADERS
    # ========================================================

    headers = {

        "Authorization": (
            f"Bearer {CURRENTS_API_KEY}"
        )

    }


    # ========================================================
    # API REQUEST
    # ========================================================

    try:

        response = requests.get(

            CURRENTS_SEARCH_URL,

            params=params,

            headers=headers,

            timeout=20

        )


        # ====================================================
        # HTTP ERROR
        # ====================================================

        if response.status_code != 200:

            try:

                error_data = response.json()

            except Exception:

                error_data = response.text


            return {

                "success": False,

                "status_code": (
                    response.status_code
                ),

                "error": error_data,

                "articles": []

            }


        # ====================================================
        # JSON
        # ====================================================

        data = response.json()


        # ====================================================
        # API STATUS
        # ====================================================

        if data.get("status") == "error":

            return {

                "success": False,

                "status_code": response.status_code,

                "error": data,

                "articles": []

            }


        # ====================================================
        # ARTICLES
        # ====================================================

        raw_articles = data.get(
            "news",
            []
        )


        articles = []


        # ====================================================
        # NORMALIZE
        # ====================================================

        for article in raw_articles:

            if not isinstance(
                article,
                dict
            ):

                continue


            articles.append({

                "title": article.get(
                    "title",
                    ""
                ),

                "description": article.get(
                    "description",
                    ""
                ),

                "content": article.get(
                    "description",
                    ""
                ),

                "url": article.get(
                    "url",
                    ""
                ),

                "publishedAt": article.get(
                    "published",
                    ""
                ),

                "language": article.get(
                    "language",
                    language_code
                ),

                "source_name": article.get(
                    "author",
                    ""
                ),

                "source_url": "",

                "source_country": country,

                "category": article.get(
                    "category",
                    []
                )

            })


        # ====================================================
        # RETURN
        # ====================================================

        return {

            "success": True,

            "total_articles": len(
                articles
            ),

            "articles": articles

        }


    # ========================================================
    # TIMEOUT
    # ========================================================

    except requests.exceptions.Timeout:

        return {

            "success": False,

            "error": (
                "Currents API request timed out."
            ),

            "articles": []

        }


    # ========================================================
    # REQUEST ERROR
    # ========================================================

    except requests.exceptions.RequestException as e:

        return {

            "success": False,

            "error": str(e),

            "articles": []

        }


    # ========================================================
    # OTHER ERROR
    # ========================================================

    except Exception as e:

        return {

            "success": False,

            "error": str(e),

            "articles": []

        }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n========================================"
    )

    print(
        " CURRENTS API TEST"
    )

    print(
        "========================================"
    )


    query = input(
        "\nEnter news search query:\n"
    )


    print(
        "\nSearching current news..."
    )


    result = search_news(

        query=query,

        language="English",

        country="IN",

        max_results=10

    )


    # ========================================================
    # SUCCESS
    # ========================================================

    if result["success"]:

        print(
            "\n========================================"
        )

        print(
            " API SUCCESS"
        )

        print(
            "========================================"
        )


        print(
            "\nArticles returned:",
            len(
                result["articles"]
            )
        )


        for index, article in enumerate(

            result["articles"],

            start=1

        ):

            print(
                "\n----------------------------------------"
            )

            print(
                f"Article {index}"
            )

            print(
                "Title:",
                article["title"]
            )

            print(
                "Author:",
                article["source_name"]
            )

            print(
                "Published:",
                article["publishedAt"]
            )

            print(
                "Category:",
                article["category"]
            )

            print(
                "URL:",
                article["url"]
            )


    # ========================================================
    # ERROR
    # ========================================================

    else:

        print(
            "\n========================================"
        )

        print(
            " API ERROR"
        )

        print(
            "========================================"
        )


        print(
            "\nStatus:",
            result.get(
                "status_code",
                "N/A"
            )
        )


        print(
            "Error:",
            result.get(
                "error",
                "Unknown error"
            )
        )