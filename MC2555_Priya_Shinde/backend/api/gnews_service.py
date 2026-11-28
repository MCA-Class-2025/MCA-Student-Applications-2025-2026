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

GNEWS_API_KEY = os.getenv(
    "GNEWS_API_KEY"
)

GNEWS_URL = (
    "https://gnews.io/api/v4/search"
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
    country="in",
    max_results=10
):

    # ========================================================
    # CHECK API KEY
    # ========================================================

    if not GNEWS_API_KEY:

        return {

            "success": False,

            "error": (
                "GNEWS_API_KEY not found in .env"
            ),

            "articles": []

        }


    # ========================================================
    # CHECK LANGUAGE
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
    # API PARAMETERS
    # ========================================================

    params = {

        "q": query,

        "lang": language_code,

        "country": country,

        "max": max_results,

        "sortby": "relevance",

        "apikey": GNEWS_API_KEY

    }


    # ========================================================
    # API REQUEST
    # ========================================================

    try:

        response = requests.get(

            GNEWS_URL,

            params=params,

            timeout=15

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
        # PARSE RESPONSE
        # ====================================================

        data = response.json()


        # ====================================================
        # RAW RESPONSE INFORMATION
        # ====================================================

        total_articles = data.get(
            "totalArticles",
            0
        )


        raw_articles = data.get(
            "articles",
            []
        )


        # ====================================================
        # DEBUG INFORMATION
        # ====================================================

        print(
            "\nGNews response:"
        )

        print(
            "Total matching articles:",
            total_articles
        )

        print(
            "Articles returned:",
            len(raw_articles)
        )


        # ====================================================
        # EXTRACT ARTICLES
        # ====================================================

        articles = []


        for article in raw_articles:

            if not isinstance(
                article,
                dict
            ):

                continue


            source = article.get(
                "source",
                {}
            )


            if not isinstance(
                source,
                dict
            ):

                source = {}


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
                    "content",
                    ""
                ),

                "url": article.get(
                    "url",
                    ""
                ),

                "publishedAt": article.get(
                    "publishedAt",
                    ""
                ),

                "language": article.get(
                    "lang",
                    language_code
                ),

                "source_name": source.get(
                    "name",
                    ""
                ),

                "source_url": source.get(
                    "url",
                    ""
                ),

                "source_country": source.get(
                    "country",
                    ""
                )

            })


        # ====================================================
        # RETURN RESULT
        # ====================================================

        return {

            "success": True,

            "total_articles": total_articles,

            "articles": articles

        }


    # ========================================================
    # TIMEOUT
    # ========================================================

    except requests.exceptions.Timeout:

        return {

            "success": False,

            "error": (
                "GNews API request timed out."
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
    # JSON / OTHER ERROR
    # ========================================================

    except Exception as e:

        return {

            "success": False,

            "error": str(e),

            "articles": []

        }


# ============================================================
# GET EVIDENCE FOR NEWS CLAIM
# ============================================================

def get_news_evidence(
    claim,
    language="English",
    max_results=5
):

    result = search_news(

        query=claim,

        language=language,

        country="in",

        max_results=max_results

    )


    if not result["success"]:

        return {

            "success": False,

            "claim": claim,

            "language": language,

            "articles": [],

            "error": result.get(

                "error",

                "Unknown API error"

            )

        }


    return {

        "success": True,

        "claim": claim,

        "language": language,

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
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n========================================"
    )

    print(
        " GNEWS API TEST"
    )

    print(
        "========================================"
    )


    query = input(

        "\nEnter news topic/claim to search:\n"

    )


    print(
        "\nSearching current news..."
    )


    result = search_news(

        query=query,

        language="English",

        country="in",

        max_results=5

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

            "\nTotal matching articles:",

            result["total_articles"]

        )


        articles = result[
            "articles"
        ]


        # ----------------------------------------------------
        # NO ARTICLES RETURNED
        # ----------------------------------------------------

        if not articles:

            print(
                "\nGNews returned no article objects."
            )

            print(
                "The API may report matching articles "
                "but remove them from the response."
            )


        # ----------------------------------------------------
        # ARTICLES FOUND
        # ----------------------------------------------------

        else:

            print(

                f"\nShowing {len(articles)} articles:\n"

            )


            for index, article in enumerate(

                articles,

                start=1

            ):

                print(
                    "----------------------------------------"
                )

                print(
                    f"Article {index}"
                )

                print(
                    "Title:",
                    article["title"]
                )

                print(
                    "Source:",
                    article["source_name"]
                )

                print(
                    "Published:",
                    article["publishedAt"]
                )

                print(
                    "URL:",
                    article["url"]
                )


    # ========================================================
    # API ERROR
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