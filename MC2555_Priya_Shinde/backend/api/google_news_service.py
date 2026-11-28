import requests
import urllib.parse
import xml.etree.ElementTree as ET


# ============================================================
# GOOGLE NEWS RSS
# ============================================================

GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"


# ============================================================
# SEARCH NEWS
# ============================================================

def search_news(
    query,
    language="en",
    country="IN",
    max_results=10
):

    if not query or not query.strip():

        return {
            "success": False,
            "error": "Search query cannot be empty.",
            "articles": []
        }


    # --------------------------------------------------------
    # LANGUAGE / COUNTRY
    # --------------------------------------------------------

    language_config = {

        "en": {
            "hl": "en-IN",
            "gl": "IN",
            "ceid": "IN:en"
        },

        "hi": {
            "hl": "hi-IN",
            "gl": "IN",
            "ceid": "IN:hi"
        },

        "mr": {
            "hl": "mr-IN",
            "gl": "IN",
            "ceid": "IN:mr"
        }
    }


    config = language_config.get(
        language,
        language_config["en"]
    )


    # --------------------------------------------------------
    # URL PARAMETERS
    # --------------------------------------------------------

    params = {

        "q": query,

        "hl": config["hl"],

        "gl": country,

        "ceid": config["ceid"]
    }


    # --------------------------------------------------------
    # REQUEST
    # --------------------------------------------------------

    try:

        response = requests.get(

            GOOGLE_NEWS_RSS_URL,

            params=params,

            timeout=20,

            headers={
                "User-Agent":
                    "Mozilla/5.0"
            }

        )


        print(
            "\nGoogle News RSS response:"
        )

        print(
            "HTTP Status:",
            response.status_code
        )


        if response.status_code != 200:

            return {

                "success": False,

                "status_code":
                    response.status_code,

                "error":
                    f"Google News returned HTTP {response.status_code}",

                "articles": []

            }


        # ----------------------------------------------------
        # PARSE XML
        # ----------------------------------------------------

        root = ET.fromstring(
            response.content
        )


        articles = []


        for item in root.findall(
            ".//item"
        ):

            title_element = item.find(
                "title"
            )

            link_element = item.find(
                "link"
            )

            pubdate_element = item.find(
                "pubDate"
            )

            source_element = item.find(
                "source"
            )

            description_element = item.find(
                "description"
            )


            title = (
                title_element.text
                if title_element is not None
                else ""
            )


            url = (
                link_element.text
                if link_element is not None
                else ""
            )


            published_at = (
                pubdate_element.text
                if pubdate_element is not None
                else ""
            )


            source_name = (
                source_element.text
                if source_element is not None
                else ""
            )


            description = (
                description_element.text
                if description_element is not None
                else ""
            )


            articles.append({

                "title":
                    title or "",

                "description":
                    description or "",

                "content":
                    description or "",

                "url":
                    url or "",

                "publishedAt":
                    published_at or "",

                "language":
                    language,

                "source_name":
                    source_name or "",

                "source_url":
                    "",

                "source_country":
                    country,

                "api_source":
                    "Google News RSS"

            })


            if len(articles) >= max_results:

                break


        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        print(
            "Articles returned:",
            len(articles)
        )


        return {

            "success": True,

            "total_articles":
                len(articles),

            "articles":
                articles

        }


    except requests.exceptions.Timeout:

        return {

            "success": False,

            "error":
                "Google News RSS request timed out.",

            "articles": []

        }


    except requests.exceptions.RequestException as e:

        return {

            "success": False,

            "error":
                str(e),

            "articles": []

        }


    except ET.ParseError:

        return {

            "success": False,

            "error":
                "Could not parse Google News RSS response.",

            "articles": []

        }


    except Exception as e:

        return {

            "success": False,

            "error":
                str(e),

            "articles": []

        }


# ============================================================
# GET NEWS EVIDENCE
# ============================================================

def get_news_evidence(
    claim,
    language="en",
    max_results=10
):

    result = search_news(

        query=claim,

        language=language,

        country="IN",

        max_results=max_results

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
                    "Unknown Google News error"
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
            " GOOGLE NEWS RSS ERROR"
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

        return


    print(
        "\n========================================"
    )

    print(
        " GOOGLE NEWS RSS SUCCESS"
    )

    print(
        "========================================"
    )


    print(
        "\nArticles returned:",
        len(
            result.get(
                "articles",
                []
            )
        )
    )


    articles = result.get(
        "articles",
        []
    )


    if not articles:

        print(
            "\nNo articles found."
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
                "Google News RSS"
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
        " GOOGLE NEWS RSS TEST"
    )

    print(
        "========================================"
    )


    query = input(
        "\nEnter news search query:\n"
    ).strip()


    print(
        "\nSearching Google News..."
    )


    result = search_news(

        query=query,

        language="en",

        country="IN",

        max_results=10

    )


    display_articles(
        result
    )