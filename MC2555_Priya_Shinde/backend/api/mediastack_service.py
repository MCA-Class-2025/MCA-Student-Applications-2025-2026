import os
from pathlib import Path

import requests
from dotenv import load_dotenv


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


# ============================================================
# API CONFIGURATION
# ============================================================

MEDIASTACK_API_KEY = os.getenv("MEDIASTACK_API_KEY")

MEDIASTACK_URL = "https://api.mediastack.com/v1/news"


# ============================================================
# SEARCH NEWS
# ============================================================

def search_news(
    query,
    countries="in",
    languages="en",
    limit=10
):

    # --------------------------------------------------------
    # CHECK API KEY
    # --------------------------------------------------------

    if not MEDIASTACK_API_KEY:

        return {
            "success": False,
            "error": "MEDIASTACK_API_KEY not found in .env",
            "articles": []
        }


    # --------------------------------------------------------
    # CHECK QUERY
    # --------------------------------------------------------

    if not query or not query.strip():

        return {
            "success": False,
            "error": "Search query cannot be empty.",
            "articles": []
        }


    # --------------------------------------------------------
    # API PARAMETERS
    # --------------------------------------------------------

    params = {

        "access_key": MEDIASTACK_API_KEY,

        "keywords": query,

        "countries": countries,

        "languages": languages,

        "limit": limit
    }


    # --------------------------------------------------------
    # API REQUEST
    # --------------------------------------------------------

    try:

        response = requests.get(
            MEDIASTACK_URL,
            params=params,
            timeout=20
        )


        # ----------------------------------------------------
        # DEBUG INFORMATION
        # ----------------------------------------------------

        print("\nMediastack response:")
        print("HTTP Status:", response.status_code)


        # ----------------------------------------------------
        # HTTP ERROR
        # ----------------------------------------------------

        if response.status_code != 200:

            try:

                error_data = response.json()

            except Exception:

                error_data = response.text


            return {

                "success": False,

                "status_code": response.status_code,

                "error": error_data,

                "articles": []
            }


        # ----------------------------------------------------
        # PARSE JSON
        # ----------------------------------------------------

        data = response.json()


        # ----------------------------------------------------
        # MEDIstack API ERROR
        # ----------------------------------------------------

        if data.get("error"):

            return {

                "success": False,

                "status_code": response.status_code,

                "error": data.get("error"),

                "articles": []
            }


        # ----------------------------------------------------
        # GET ARTICLES
        # ----------------------------------------------------

        raw_articles = data.get(
            "data",
            []
        )


        print(
            "Total matching articles:",
            data.get(
                "pagination",
                {}
            ).get(
                "total",
                0
            )
        )

        print(
            "Articles returned:",
            len(raw_articles)
        )


        # ----------------------------------------------------
        # NORMALIZE ARTICLES
        # ----------------------------------------------------

        articles = []


        for article in raw_articles:

            if not isinstance(article, dict):

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
                    "published_at",
                    ""
                ),

                "source_name": article.get(
                    "source",
                    ""
                ),

                "source_url": "",

                "source_country": article.get(
                    "country",
                    ""
                ),

                "language": article.get(
                    "language",
                    languages
                ),

                "api": "Mediastack"
            })


        # ----------------------------------------------------
        # RETURN RESULT
        # ----------------------------------------------------

        return {

            "success": True,

            "total_articles": data.get(
                "pagination",
                {}
            ).get(
                "total",
                len(articles)
            ),

            "articles": articles
        }


    # --------------------------------------------------------
    # TIMEOUT
    # --------------------------------------------------------

    except requests.exceptions.Timeout:

        return {

            "success": False,

            "error": "Mediastack API request timed out.",

            "articles": []
        }


    # --------------------------------------------------------
    # REQUEST ERROR
    # --------------------------------------------------------

    except requests.exceptions.RequestException as e:

        return {

            "success": False,

            "error": str(e),

            "articles": []
        }


    # --------------------------------------------------------
    # GENERAL ERROR
    # --------------------------------------------------------

    except Exception as e:

        return {

            "success": False,

            "error": str(e),

            "articles": []
        }


# ============================================================
# GET NEWS EVIDENCE
# ============================================================

def get_news_evidence(
    claim,
    limit=10
):

    result = search_news(
        query=claim,
        countries="in",
        languages="en",
        limit=limit
    )


    if not result["success"]:

        return {

            "success": False,

            "claim": claim,

            "articles": [],

            "error": result.get(
                "error",
                "Unknown Mediastack error"
            )
        }


    return {

        "success": True,

        "claim": claim,

        "total_articles": result.get(
            "total_articles",
            0
        ),

        "articles": result.get(
            "articles",
            []
        )
    }


# ============================================================
# DISPLAY ARTICLES
# ============================================================

def display_articles(result):

    if not result["success"]:

        print("\n========================================")
        print(" MEDIASTACK API ERROR")
        print("========================================")

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

        return


    print("\n========================================")
    print(" MEDIASTACK API SUCCESS")
    print("========================================")


    print(
        "\nTotal matching articles:",
        result.get(
            "total_articles",
            0
        )
    )


    articles = result.get(
        "articles",
        []
    )


    print(
        "Articles returned:",
        len(articles)
    )


    if not articles:

        print(
            "\nNo article objects returned."
        )

        return


    print(
        f"\nShowing {len(articles)} articles:\n"
    )


    for index, article in enumerate(
        articles,
        start=1
    ):

        print("----------------------------------------")

        print(
            f"Article {index}"
        )

        print(
            "Title:",
            article.get(
                "title",
                ""
            )
        )

        print(
            "Source:",
            article.get(
                "source_name",
                ""
            )
        )

        print(
            "Published:",
            article.get(
                "publishedAt",
                ""
            )
        )

        print(
            "URL:",
            article.get(
                "url",
                ""
            )
        )

        print(
            "API:",
            article.get(
                "api",
                "Mediastack"
            )
        )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n========================================"
    )

    print(
        " MEDIASTACK API TEST"
    )

    print(
        "========================================"
    )


    print(
        "\nAPI key loaded:",
        bool(MEDIASTACK_API_KEY)
    )


    query = input(
        "\nEnter news search query:\n"
    ).strip()


    print(
        "\nSearching Mediastack..."
    )


    result = search_news(
        query=query,
        countries="in",
        languages="en",
        limit=10
    )


    display_articles(
        result
    )