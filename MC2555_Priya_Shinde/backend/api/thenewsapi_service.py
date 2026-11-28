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

THENEWSAPI_KEY = os.getenv("THENEWSAPI_KEY")

THENEWSAPI_URL = "https://api.thenewsapi.com/v1/news/all"


# ============================================================
# SEARCH NEWS
# ============================================================

def search_news(
    query,
    language="en",
    limit=10
):

    # --------------------------------------------------------
    # CHECK API KEY
    # --------------------------------------------------------

    if not THENEWSAPI_KEY:

        return {
            "success": False,
            "error": "THENEWSAPI_KEY not found in .env",
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
    # LIMIT
    # --------------------------------------------------------

    try:

        limit = int(limit)

    except (ValueError, TypeError):

        limit = 10


    limit = max(
        1,
        min(limit, 50)
    )


    # --------------------------------------------------------
    # API PARAMETERS
    # --------------------------------------------------------

    params = {

        "api_token": THENEWSAPI_KEY,

        "search": query,

        "language": language,

        "limit": limit

    }


    # --------------------------------------------------------
    # REQUEST
    # --------------------------------------------------------

    try:

        response = requests.get(

            THENEWSAPI_URL,

            params=params,

            timeout=20

        )


        print(
            "\nTheNewsAPI response:"
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

        except ValueError:

            return {

                "success": False,

                "status_code":
                    response.status_code,

                "error":
                    "TheNewsAPI returned invalid JSON.",

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
                    extract_error(data),

                "articles": []

            }


        # ----------------------------------------------------
        # API ERROR
        # ----------------------------------------------------

        if data.get("error"):

            return {

                "success": False,

                "status_code":
                    response.status_code,

                "error":
                    extract_error(data),

                "articles": []

            }


        # ----------------------------------------------------
        # ARTICLES
        # ----------------------------------------------------

        raw_articles = data.get(
            "data",
            []
        )


        # Some API responses can use articles instead.
        if not raw_articles:

            raw_articles = data.get(
                "articles",
                []
            )


        # ----------------------------------------------------
        # TOTAL
        # ----------------------------------------------------

        meta = data.get(
            "meta",
            {}
        )


        total_articles = meta.get(
            "found",
            data.get(
                "total",
                len(raw_articles)
            )
        )


        print(
            "Total matching articles:",
            total_articles
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

            if not isinstance(
                article,
                dict
            ):

                continue


            # ------------------------------------------------
            # TITLE
            # ------------------------------------------------

            title = (

                article.get(
                    "title"
                )

                or ""

            ).strip()


            # ------------------------------------------------
            # DESCRIPTION
            # ------------------------------------------------

            description = (

                article.get(
                    "description"
                )

                or ""

            ).strip()


            # ------------------------------------------------
            # CONTENT
            # ------------------------------------------------

            content = (

                article.get(
                    "snippet"
                )

                or article.get(
                    "content"
                )

                or ""

            ).strip()


            # ------------------------------------------------
            # URL
            # ------------------------------------------------

            url = (

                article.get(
                    "url"
                )

                or ""

            ).strip()


            # ------------------------------------------------
            # DATE
            # ------------------------------------------------

            published_at = (

                article.get(
                    "published_at"
                )

                or article.get(
                    "publishedAt"
                )

                or ""

            )


            # ------------------------------------------------
            # SOURCE
            # ------------------------------------------------

            source_name = ""


            source = article.get(
                "source"
            )


            if isinstance(
                source,
                dict
            ):

                source_name = (

                    source.get(
                        "name"
                    )

                    or source.get(
                        "title"
                    )

                    or ""

                )


            elif isinstance(
                source,
                str
            ):

                source_name = source


            # Fallback source field

            if not source_name:

                source_name = (

                    article.get(
                        "source_name"
                    )

                    or ""

                )


            # ------------------------------------------------
            # SOURCE URL
            # ------------------------------------------------

            source_url = (

                article.get(
                    "source_url"
                )

                or ""

            )


            # ------------------------------------------------
            # COUNTRY
            # ------------------------------------------------

            source_country = (

                article.get(
                    "locale"
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

            normalized_article = {

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
                    language,

                "source_name":
                    source_name,

                "source_url":
                    source_url,

                "source_country":
                    source_country,

                "api_source":
                    "TheNewsAPI"

            }


            articles.append(
                normalized_article
            )


        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        return {

            "success": True,

            "total_articles":
                total_articles,

            "articles":
                articles

        }


    # --------------------------------------------------------
    # TIMEOUT
    # --------------------------------------------------------

    except requests.exceptions.Timeout:

        return {

            "success": False,

            "error":
                "TheNewsAPI request timed out.",

            "articles": []

        }


    # --------------------------------------------------------
    # CONNECTION ERROR
    # --------------------------------------------------------

    except requests.exceptions.ConnectionError:

        return {

            "success": False,

            "error":
                "Could not connect to TheNewsAPI.",

            "articles": []

        }


    # --------------------------------------------------------
    # REQUEST ERROR
    # --------------------------------------------------------

    except requests.exceptions.RequestException as e:

        return {

            "success": False,

            "error":
                str(e),

            "articles": []

        }


    # --------------------------------------------------------
    # GENERAL ERROR
    # --------------------------------------------------------

    except Exception as e:

        return {

            "success": False,

            "error":
                str(e),

            "articles": []

        }


# ============================================================
# ERROR EXTRACTION
# ============================================================

def extract_error(data):

    if not isinstance(
        data,
        dict
    ):

        return "Unknown TheNewsAPI error."


    if data.get(
        "message"
    ):

        return str(
            data["message"]
        )


    if data.get(
        "error"
    ):

        error = data["error"]

        if isinstance(
            error,
            dict
        ):

            return str(
                error.get(
                    "message",
                    error
                )
            )

        return str(error)


    return "Unknown TheNewsAPI error."


# ============================================================
# GET EVIDENCE
# ============================================================

def get_news_evidence(

    claim,

    language="en",

    limit=10

):

    result = search_news(

        query=claim,

        language=language,

        limit=limit

    )


    if not result["success"]:

        return {

            "success": False,

            "claim":
                claim,

            "articles": [],

            "error":
                result.get(
                    "error",
                    "Unknown TheNewsAPI error"
                )

        }


    return {

        "success": True,

        "claim":
            claim,

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
# DISPLAY ARTICLES
# ============================================================

def display_articles(
    result
):

    if not result["success"]:

        print(
            "\n========================================"
        )

        print(
            " THENEWSAPI ERROR"
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

        return


    print(
        "\n========================================"
    )

    print(
        " THENEWSAPI SUCCESS"
    )

    print(
        "========================================"
    )


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

        print(
            "----------------------------------------"
        )

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
                "api_source",
                "TheNewsAPI"
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
        " THENEWSAPI TEST"
    )

    print(
        "========================================"
    )


    # --------------------------------------------------------
    # KEY CHECK
    # --------------------------------------------------------

    print(
        "\nAPI key loaded:",
        bool(THENEWSAPI_KEY)
    )


    if not THENEWSAPI_KEY:

        print(
            "\nERROR:"
        )

        print(
            "Add THENEWSAPI_KEY to your .env file."
        )

        raise SystemExit(1)


    # --------------------------------------------------------
    # QUERY
    # --------------------------------------------------------

    query = input(
        "\nEnter news search query:\n"
    ).strip()


    print(
        "\nSearching TheNewsAPI..."
    )


    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    result = search_news(

        query=query,

        language="en",

        limit=10

    )


    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    display_articles(
        result
    )