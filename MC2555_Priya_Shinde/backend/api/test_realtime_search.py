import time

from query_builder import build_search_queries
from gnews_service import search_news


# ============================================================
# REAL-TIME MULTI-QUERY SEARCH
# ============================================================

print("\n========================================")
print(" REAL-TIME NEWS VERIFICATION TEST")
print("========================================")


# ============================================================
# GET USER CLAIM
# ============================================================

claim = input(
    "\nEnter news claim:\n"
)


# ============================================================
# BUILD SEARCH QUERIES
# ============================================================

queries = build_search_queries(
    claim
)


print(
    "\nGenerated search queries:"
)

for index, query in enumerate(
    queries,
    start=1
):

    print(
        f"{index}. {query}"
    )


# ============================================================
# SEARCH GNEWS USING ALL QUERIES
# ============================================================

all_articles = []

seen_urls = set()


for index, query in enumerate(queries):

    # --------------------------------------------------------
    # WAIT BETWEEN API REQUESTS
    # --------------------------------------------------------

    if index > 0:

        print(
            "\nWaiting before next API request..."
        )

        time.sleep(2)


    print(
        f"\nSearching GNews for:"
        f"\n{query}"
    )


    result = search_news(
        query=query,
        language="English",
        country="in",
        max_results=5
    )


    if not result["success"]:

        print(
            "API error:",
            result.get(
                "error",
                "Unknown error"
            )
        )

        continue


    articles = result.get(
        "articles",
        []
    )


    print(
        "Articles received:",
        len(articles)
    )


    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    for article in articles:

        url = article.get(
            "url",
            ""
        )


        if url and url in seen_urls:

            continue


        if url:

            seen_urls.add(
                url
            )


        all_articles.append(
            article
        )


# ============================================================
# DISPLAY COMBINED RESULTS
# ============================================================

print(
    "\n========================================"
)

print(
    " COMBINED REAL-TIME EVIDENCE"
)

print(
    "========================================"
)


print(
    "\nUnique articles found:",
    len(all_articles)
)


if not all_articles:

    print(
        "\nNo current articles found."
    )


else:

    for index, article in enumerate(
        all_articles,
        start=1
    ):

        print(
            "\n----------------------------------------"
        )

        print(
            f"ARTICLE {index}"
        )

        print(
            "----------------------------------------"
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