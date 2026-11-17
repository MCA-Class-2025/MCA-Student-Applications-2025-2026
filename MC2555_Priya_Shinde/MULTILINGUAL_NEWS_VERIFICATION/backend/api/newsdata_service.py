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

NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")

NEWSDATA_URL = "https://newsdata.io/api/1/latest"


# ============================================================
# SEARCH NEWS
# ============================================================

def search_news(
    query,
    country="in",
    language="en",
    max_results=10
):

    # --------------------------------------------------------
    # CHECK API KEY
    # --------------------------------------------------------

    if not NEWSDATA_API_KEY:

        return {
            "success": False,
            "error": "NEWSDATA_API_KEY not found in .env",
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
        max_results = int(max_results)
    except (ValueError, TypeError):
        max_results = 10

    # Free plans normally return up to 10 articles.
    max_results = max(
        1,
        min(max_results, 10)
    )


    # --------------------------------------------------------
    # API PARAMETERS
    # --------------------------------------------------------

    params = {

        "apikey": NEWSDATA_API_KEY,

        "q": query,

        "country": country,

        "language": language,

        "size": max_results,

        "removeduplicate": 1

    }


    # --------------------------------------------------------
    # API REQUEST
    # --------------------------------------------------------

    try:

        response = requests.get(
            NEWSDATA_URL,
            params=params,
            timeout=20
        )


        print("\nNewsData.io response:")
        print(
            "HTTP Status:",
            response.status_code
        )


        # ----------------------------------------------------
        # PARSE JSON
        # ----------------------------------------------------

        try:

            data = response.json()

        except ValueError:

            return {
                "success": False,
                "status_code": response.status_code,
                "error": "NewsData.io returned invalid JSON.",
                "articles": []
            }


        # ----------------------------------------------------
        # HTTP ERROR
        # ----------------------------------------------------

        if response.status_code != 200:

            return {
                "success": False,
                "status_code": response.status_code,
                "error": extract_error(data),
                "articles": []
            }


        # ----------------------------------------------------
        # API ERROR
        # ----------------------------------------------------

        if data.get("status") != "success":

            return {
                "success": False,
                "status_code": response.status_code,
                "error": extract_error(data),
                "articles": []
            }


        # ----------------------------------------------------
        # RAW ARTICLES
        # ----------------------------------------------------

        raw_articles = data.get(
            "results",
            []
        )


        print(
            "Total matching articles:",
            data.get(
                "totalResults",
                len(raw_articles)
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

            title = (
                article.get("title")
                or ""
            ).strip()


            description = (
                article.get("description")
                or ""
            ).strip()


            content = (
                article.get("content")
                or ""
            ).strip()


            url = (
                article.get("link")
                or ""
            ).strip()


            published_at = (
                article.get("pubDate")
                or ""
            )


            source_name = (
                article.get("source_name")
                or ""
            )


            source_url = (
                article.get("source_url")
                or ""
            )


            source_id = (
                article.get("source_id")
                or ""
            )


            article_id = (
                article.get("article_id")
                or ""
            )


            image_url = (
                article.get("image_url")
                or ""
            )


            # ------------------------------------------------
            # IGNORE INVALID ARTICLES
            # ------------------------------------------------

            if not title or not url:
                continue


            # ------------------------------------------------
            # NORMALIZED ARTICLE
            # ------------------------------------------------

            normalized_article = {

                "title": title,

                "description": description,

                "content": content,

                "url": url,

                "publishedAt": published_at,

                "language": language,

                "source_name": source_name,

                "source_url": source_url,

                "source_country": country,

                "source_id": source_id,

                "article_id": article_id,

                "image_url": image_url,

                "api_source": "NewsData.io"

            }


            articles.append(
                normalized_article
            )


        # ----------------------------------------------------
        # RETURN
        # ----------------------------------------------------

        return {

            "success": True,

            "total_articles": data.get(
                "totalResults",
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

            "error":
                "NewsData.io request timed out.",

            "articles": []

        }


    # --------------------------------------------------------
    # CONNECTION ERROR
    # --------------------------------------------------------

    except requests.exceptions.ConnectionError:

        return {

            "success": False,

            "error":
                "Could not connect to NewsData.io.",

            "articles": []

        }


    # --------------------------------------------------------
    # GENERAL REQUEST ERROR
    # --------------------------------------------------------

    except requests.exceptions.RequestException as e:

        return {

            "success": False,

            "error": str(e),

            "articles": []

        }


# ============================================================
# ERROR EXTRACTION
# ============================================================

def extract_error(data):

    if not isinstance(data, dict):
        return "Unknown NewsData.io error."


    # Try common error fields

    if data.get("message"):
        return str(data["message"])


    if data.get("results"):

        results = data["results"]

        if isinstance(results, dict):

            if results.get("message"):
                return str(results["message"])

            if results.get("error"):
                return str(results["error"])


        if isinstance(results, str):
            return results


    return "Unknown NewsData.io API error."


# ============================================================
# GET NEWS EVIDENCE
# ============================================================

def get_news_evidence(
    claim,
    country="in",
    language="en",
    max_results=10
):

    result = search_news(
        query=claim,
        country=country,
        language=language,
        max_results=max_results
    )


    if not result["success"]:

        return {

            "success": False,

            "claim": claim,

            "articles": [],

            "error": result.get(
                "error",
                "Unknown NewsData.io error"
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
# PRINT ARTICLES
# ============================================================

def print_articles(articles):

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


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n========================================"
    )

    print(
        " NEWSDATA.IO API TEST"
    )

    print(
        "========================================"
    )


    # --------------------------------------------------------
    # KEY CHECK
    # --------------------------------------------------------

    print(
        "\nAPI key loaded:",
        bool(NEWSDATA_API_KEY)
    )


    if not NEWSDATA_API_KEY:

        print(
            "\nERROR:"
        )

        print(
            "Add NEWSDATA_API_KEY to your .env file."
        )

        raise SystemExit(1)


    # --------------------------------------------------------
    # USER QUERY
    # --------------------------------------------------------

    query = input(
        "\nEnter news search query:\n"
    ).strip()


    print(
        "\nSearching NewsData.io..."
    )


    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    result = search_news(

        query=query,

        country="in",

        language="en",

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
            "\nTotal matching articles:",
            result["total_articles"]
        )


        articles = result["articles"]


        print(
            "Valid articles:",
            len(articles)
        )


        print_articles(
            articles
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
            "\nError:",
            result.get(
                "error",
                "Unknown error"
            )
        )
