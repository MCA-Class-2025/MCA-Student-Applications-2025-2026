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

NEWSDATA_API_KEY = os.getenv(
    "NEWSDATA_API_KEY"
)

NEWSDATA_URL = (
    "https://newsdata.io/api/1/latest"
)


# ============================================================
# LANGUAGE MAPPING
# ============================================================

LANGUAGE_CODES = {

    "English": "en",

    # NewsData search will use English as the
    # common evidence language for multilingual claims.
    "Hindi": "en",

    "Marathi": "en"

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

    # --------------------------------------------------------
    # API KEY CHECK
    # --------------------------------------------------------

    if not NEWSDATA_API_KEY:

        return {

            "success": False,

            "error":
                "NEWSDATA_API_KEY not found in .env",

            "articles": []

        }


    # --------------------------------------------------------
    # QUERY CHECK
    # --------------------------------------------------------

    if not query or not query.strip():

        return {

            "success": False,

            "error":
                "Search query cannot be empty.",

            "articles": []

        }


    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    language_code = LANGUAGE_CODES.get(

        language,

        "en"

    )


    # --------------------------------------------------------
    # LIMIT
    # --------------------------------------------------------

    try:

        max_results = int(
            max_results
        )

    except Exception:

        max_results = 10


    max_results = max(

        1,

        min(
            max_results,
            10
        )

    )


    # --------------------------------------------------------
    # PARAMETERS
    # --------------------------------------------------------

    params = {

        "apikey":
            NEWSDATA_API_KEY,

        "q":
            query,

        "language":
            language_code,

        "country":
            country,

        "size":
            max_results

    }


    # --------------------------------------------------------
    # REQUEST
    # --------------------------------------------------------

    try:

        response = requests.get(

            NEWSDATA_URL,

            params=params,

            timeout=20

        )


        print(
            "\nNewsData.io response:"
        )

        print(
            "HTTP Status:",
            response.status_code
        )


        # ----------------------------------------------------
        # JSON
        # ----------------------------------------------------

        try:

            data = response.json()

        except Exception:

            return {

                "success": False,

                "status_code":
                    response.status_code,

                "error":
                    "NewsData.io returned invalid JSON.",

                "articles": []

            }


        # ----------------------------------------------------
        # HTTP ERROR
        # ----------------------------------------------------

        if response.status_code != 200:

            return {

                "success": False,

                "status_code":
                    response.status_code,

                "error":
                    data.get(

                        "message",

                        data.get(

                            "results",

                            "NewsData.io API error."

                        )

                    ),

                "articles": []

            }


        # ----------------------------------------------------
        # API STATUS
        # ----------------------------------------------------

        if data.get("status") != "success":

            return {

                "success": False,

                "status_code":
                    response.status_code,

                "error":
                    data.get(

                        "message",

                        "NewsData.io returned an error."

                    ),

                "articles": []

            }


        # ----------------------------------------------------
        # RESULTS
        # ----------------------------------------------------

        raw_articles = data.get(

            "results",

            []

        )


        print(

            "Articles returned:",

            len(raw_articles)

        )


        articles = []


        # ====================================================
        # NORMALIZE ARTICLES
        # ====================================================

        for article in raw_articles:

            title = (

                article.get(
                    "title",
                    ""
                )

                or ""

            )


            description = (

                article.get(
                    "description",
                    ""
                )

                or ""

            )


            content = (

                article.get(
                    "content",
                    ""
                )

                or ""

            )


            url = (

                article.get(
                    "link",
                    ""
                )

                or ""

            )


            published_at = (

                article.get(
                    "pubDate",
                    ""
                )

                or ""

            )


            source_name = (

                article.get(
                    "source_name",
                    ""
                )

                or ""

            )


            source_url = (

                article.get(
                    "source_url",
                    ""
                )

                or ""

            )


            # ------------------------------------------------
            # SKIP INVALID ARTICLES
            # ------------------------------------------------

            if not title or not url:

                continue


            # ------------------------------------------------
            # NORMALIZED FORMAT
            # ------------------------------------------------

            articles.append({

                "title":
                    title,

                "description":
                    description,

                "content":
                    content,

                "url":
                    url,

                "publishedAt":
                    published_at,

                "language":
                    language_code,

                "source_name":
                    source_name,

                "source_url":
                    source_url,

                "source_country":
                    country,

                "api_source":
                    "NewsData.io"

            })


        # ====================================================
        # RETURN
        # ====================================================

        return {

            "success": True,

            "total_articles":
                len(articles),

            "articles":
                articles

        }


    # ========================================================
    # TIMEOUT
    # ========================================================

    except requests.exceptions.Timeout:

        return {

            "success": False,

            "error":
                "NewsData.io request timed out.",

            "articles": []

        }


    # ========================================================
    # CONNECTION ERROR
    # ========================================================

    except requests.exceptions.ConnectionError:

        return {

            "success": False,

            "error":
                "Could not connect to NewsData.io.",

            "articles": []

        }


    # ========================================================
    # OTHER ERROR
    # ========================================================

    except requests.exceptions.RequestException as e:

        return {

            "success": False,

            "error":
                str(e),

            "articles": []

        }


# ============================================================
# GET EVIDENCE
# ============================================================

def get_news_evidence(

    claim,

    language="English",

    max_results=10

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

            "claim":
                claim,

            "language":
                language,

            "articles": [],

            "error":
                result.get(

                    "error",

                    "Unknown NewsData.io error"

                )

        }


    return {

        "success": True,

        "claim":
            claim,

        "language":
            language,

        "total_articles":
            result.get(

                "total_articles",

                0

            ),

        "articles":
            result.get(

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
        " NEWSDATA.IO TEST"
    )

    print(
        "========================================"
    )


    query = input(
        "\nEnter news search query:\n"
    )


    print(
        "\nSearching NewsData.io..."
    )


    result = search_news(

        query=query,

        language="English",

        country="in",

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
            " NEWSDATA.IO SUCCESS"
        )

        print(
            "========================================"
        )


        print(
            "\nTotal articles:",
            result.get(
                "total_articles",
                0
            )
        )


        articles = result.get(
            "articles",
            []
        )


        if not articles:

            print(
                "\nNo article objects returned."
            )


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

                print(
                    "API:",
                    article["api_source"]
                )


    # ========================================================
    # ERROR
    # ========================================================

    else:

        print(
            "\n========================================"
        )

        print(
            " NEWSDATA.IO ERROR"
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