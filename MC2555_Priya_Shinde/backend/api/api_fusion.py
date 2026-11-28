import os
import requests
import feedparser
import pandas as pd
from dotenv import load_dotenv
from urllib.parse import quote, urlparse

load_dotenv()


# ============================================================
# API KEYS
# ============================================================

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
CURRENTS_API_KEY = os.getenv("CURRENTS_API_KEY")
NEWSAPI_API_KEY = os.getenv("NEWSAPI_API_KEY")
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
THENEWSAPI_API_KEY = os.getenv("THENEWSAPI_KEY")


# ============================================================
# OUTPUT
# ============================================================

OUTPUT_FILE = "data/processed/realtime_api_fusion.csv"


# ============================================================
# COMMON ARTICLE FORMAT
# ============================================================

def normalize_article(
    api,
    query,
    title="",
    description="",
    source="",
    published="",
    url="",
    image="",
):
    return {
        "api": api,
        "query": query,
        "title": title or "",
        "description": description or "",
        "source": source or "",
        "published": published or "",
        "url": url or "",
        "image": image or "",
    }


# ============================================================
# 1. GNEWS
# ============================================================

def search_gnews(query):

    articles = []

    if not GNEWS_API_KEY:
        print("GNews API key missing")
        return articles

    url = "https://gnews.io/api/v4/search"

    params = {
        "q": query,
        "lang": "en",
        "max": 10,
        "apikey": GNEWS_API_KEY
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        data = response.json()

        if response.status_code != 200:

            print("GNews error:", data)
            return articles

        for item in data.get("articles", []):

            articles.append(
                normalize_article(
                    api="GNews",
                    query=query,
                    title=item.get("title"),
                    description=item.get("description"),
                    source=item.get("source", {}).get("name"),
                    published=item.get("publishedAt"),
                    url=item.get("url"),
                    image=item.get("image")
                )
            )

    except Exception as e:
        print("GNews exception:", e)

    return articles


# ============================================================
# 2. CURRENTS
# ============================================================

def search_currents(query):

    articles = []

    if not CURRENTS_API_KEY:
        print("Currents API key missing")
        return articles

    url = "https://api.currentsapi.services/v1/search"

    headers = {
        "Authorization": CURRENTS_API_KEY
    }

    params = {
        "keywords": query,
        "language": "en",
        "page_size": 10
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=15
        )

        data = response.json()

        if response.status_code != 200:
            print("Currents error:", data)
            return articles

        for item in data.get("news", []):

            articles.append(
                normalize_article(
                    api="Currents",
                    query=query,
                    title=item.get("title"),
                    description=item.get("description"),
                    source=item.get("author"),
                    published=item.get("published"),
                    url=item.get("url"),
                    image=item.get("image")
                )
            )

    except Exception as e:
        print("Currents exception:", e)

    return articles


# ============================================================
# 3. NEWSAPI
# ============================================================

def search_newsapi(query):

    articles = []

    if not NEWSAPI_API_KEY:
        print("NewsAPI key missing")
        return articles

    url = "https://newsapi.org/v2/everything"

    params = {
        "q": query,
        "language": "en",
        "pageSize": 10,
        "apiKey": NEWSAPI_API_KEY
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        data = response.json()

        if response.status_code != 200:
            print("NewsAPI error:", data)
            return articles

        for item in data.get("articles", []):

            articles.append(
                normalize_article(
                    api="NewsAPI",
                    query=query,
                    title=item.get("title"),
                    description=item.get("description"),
                    source=item.get("source", {}).get("name"),
                    published=item.get("publishedAt"),
                    url=item.get("url"),
                    image=item.get("urlToImage")
                )
            )

    except Exception as e:
        print("NewsAPI exception:", e)

    return articles


# ============================================================
# 4. NEWSDATA.IO
# ============================================================

def search_newsdata(query):

    articles = []

    if not NEWSDATA_API_KEY:
        print("NewsData API key missing")
        return articles

    url = "https://newsdata.io/api/1/latest"

    params = {
        "apikey": NEWSDATA_API_KEY,
        "q": query,
        "language": "en",
        "size": 10
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        data = response.json()

        if response.status_code != 200:

            print("NewsData error:", data)
            return articles

        for item in data.get("results", []):

            articles.append(
                normalize_article(
                    api="NewsData.io",
                    query=query,
                    title=item.get("title"),
                    description=item.get("description"),
                    source=item.get("source_name"),
                    published=item.get("pubDate"),
                    url=item.get("link"),
                    image=item.get("image_url")
                )
            )

    except Exception as e:
        print("NewsData exception:", e)

    return articles


# ============================================================
# 5. THENEWSAPI
# ============================================================

def search_thenewsapi(query):

    articles = []

    if not THENEWSAPI_API_KEY:
        print("TheNewsAPI key missing")
        return articles

    url = "https://api.thenewsapi.com/v1/news/all"

    params = {
        "api_token": THENEWSAPI_API_KEY,
        "search": query,
        "language": "en",
        "limit": 10
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        data = response.json()

        if response.status_code != 200:

            print("TheNewsAPI error:", data)
            return articles

        for item in data.get("data", []):

            articles.append(
                normalize_article(
                    api="TheNewsAPI",
                    query=query,
                    title=item.get("title"),
                    description=item.get("description"),
                    source=item.get("source"),
                    published=item.get("published_at"),
                    url=item.get("url"),
                    image=item.get("image_url")
                )
            )

    except Exception as e:
        print("TheNewsAPI exception:", e)

    return articles


# ============================================================
# 6. GOOGLE NEWS RSS
# ============================================================

def search_google_news(query):

    articles = []

    try:

        encoded_query = quote(query)

        url = (
            "https://news.google.com/rss/search"
            f"?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
        )

        feed = feedparser.parse(url)

        for item in feed.entries[:10]:

            source = ""

            if hasattr(item, "source"):
                source = item.source.get("title", "")

            articles.append(
                normalize_article(
                    api="Google News RSS",
                    query=query,
                    title=item.get("title"),
                    description=item.get("summary"),
                    source=source,
                    published=item.get("published"),
                    url=item.get("link")
                )
            )

    except Exception as e:
        print("Google News RSS exception:", e)

    return articles


# ============================================================
# API FUSION
# ============================================================

def search_all_apis(query):

    print("\n========================================")
    print("MULTI-API NEWS SEARCH")
    print("========================================")
    print("Query:", query)

    all_articles = []

    # --------------------------------------------------------
    # GNEWS
    # --------------------------------------------------------

    print("\nSearching GNews...")

    gnews_articles = search_gnews(query)

    print("GNews articles:", len(gnews_articles))

    all_articles.extend(gnews_articles)


    # --------------------------------------------------------
    # CURRENTS
    # --------------------------------------------------------

    print("\nSearching Currents...")

    currents_articles = search_currents(query)

    print("Currents articles:", len(currents_articles))

    all_articles.extend(currents_articles)


    # --------------------------------------------------------
    # NEWSAPI
    # --------------------------------------------------------

    print("\nSearching NewsAPI...")

    newsapi_articles = search_newsapi(query)

    print("NewsAPI articles:", len(newsapi_articles))

    all_articles.extend(newsapi_articles)


    # --------------------------------------------------------
    # NEWSDATA
    # --------------------------------------------------------

    print("\nSearching NewsData.io...")

    newsdata_articles = search_newsdata(query)

    print("NewsData.io articles:", len(newsdata_articles))

    all_articles.extend(newsdata_articles)


    # --------------------------------------------------------
    # THENEWSAPI
    # --------------------------------------------------------

    print("\nSearching TheNewsAPI...")

    thenews_articles = search_thenewsapi(query)

    print("TheNewsAPI articles:", len(thenews_articles))

    all_articles.extend(thenews_articles)


    # --------------------------------------------------------
    # GOOGLE NEWS
    # --------------------------------------------------------

    print("\nSearching Google News RSS...")

    google_articles = search_google_news(query)

    print("Google News RSS articles:", len(google_articles))

    all_articles.extend(google_articles)


    print("\n========================================")
    print("COLLECTION COMPLETE")
    print("========================================")

    print(
        "Total articles collected:",
        len(all_articles)
    )

    return all_articles


# ============================================================
# VALIDATE AND CLEAN ARTICLES
# ============================================================

def validate_articles(articles):

    # These fields are required for the research dataset.
    required_fields = [
        "api",
        "query",
        "title",
        "published",
        "url"
    ]

    valid_articles = []
    rejected_articles = []

    for article in articles:

        is_valid = True

        # --------------------------------------------------------
        # REQUIRED FIELD CHECK
        # --------------------------------------------------------

        for field in required_fields:

            value = article.get(field)

            if value is None:
                is_valid = False
                break

            if str(value).strip() == "":
                is_valid = False
                break

        if not is_valid:

            rejected_articles.append(article)
            continue


        # --------------------------------------------------------
        # SOURCE CLEANUP
        # --------------------------------------------------------
        #
        # Source is important for research reporting.
        # If an API does not provide it, derive it from the URL.
        #

        source = str(
            article.get("source") or ""
        ).strip()

        if not source:

            try:

                hostname = urlparse(
                    article["url"]
                ).netloc.lower()

                hostname = hostname.replace(
                    "www.",
                    ""
                )

                source = hostname

            except Exception:

                source = "Unknown Source"


        article["source"] = source


        # --------------------------------------------------------
        # OPTIONAL DESCRIPTION
        # --------------------------------------------------------
        #
        # Description is not required for evidence matching.
        # Keep the record instead of deleting it.
        #

        description = str(
            article.get("description") or ""
        ).strip()

        if not description:

            article["description"] = (
                "No description available."
            )


        # --------------------------------------------------------
        # OPTIONAL IMAGE
        # --------------------------------------------------------
        #
        # Image is only a presentation field and is not required
        # for news verification.
        #

        image = str(
            article.get("image") or ""
        ).strip()

        article["image"] = image


        valid_articles.append(article)


    print("\n========================================")
    print("DATA VALIDATION")
    print("========================================")

    print(
        "Input records:",
        len(articles)
    )

    print(
        "Valid records:",
        len(valid_articles)
    )

    print(
        "Rejected records:",
        len(rejected_articles)
    )

    print(
        "Required fields:",
        ", ".join(required_fields)
    )

    return valid_articles


# ============================================================
# DATASET QUALITY CHECK
# ============================================================

def print_dataset_quality(df):

    print("\n========================================")
    print("FINAL DATASET QUALITY CHECK")
    print("========================================")

    print(
        "Rows:",
        len(df)
    )

    print("\nNull values:")

    print(
        df.isnull().sum()
    )

    print("\nEmpty string values:")

    empty_counts = (
        df.fillna("")
        .astype(str)
        .apply(
            lambda column:
            column.str.strip().eq("").sum()
        )
    )

    print(empty_counts)

    print(
        "\nDuplicate rows:",
        df.duplicated().sum()
    )


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def remove_duplicates(articles):

    unique = []
    seen = set()

    for article in articles:

        title = article.get("title", "").strip().lower()

        url = article.get("url", "").strip().lower()

        # URL is the strongest duplicate key
        if url:

            key = url

        else:

            key = title

        if not key:
            continue

        if key not in seen:

            seen.add(key)
            unique.append(article)

    return unique


# ============================================================
# SAVE FUSED DATA
# ============================================================

def save_fused_data(articles):

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    df = pd.DataFrame(articles)

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n========================================")
    print("API FUSION COMPLETE")
    print("========================================")

    print("Unique articles:", len(df))

    print("CSV saved at:")
    print(OUTPUT_FILE)

    return df


# ============================================================
# MAIN FUSION FUNCTION
# ============================================================

def run_api_fusion(search_queries):

    all_articles = []

    for query in search_queries:

        articles = search_all_apis(
            query
        )

        all_articles.extend(
            articles
        )


    # --------------------------------------------------------
    # VALIDATE AND CLEAN RECORDS
    # --------------------------------------------------------

    validated_articles = validate_articles(
        all_articles
    )


    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    print("\nRemoving duplicate articles...")

    unique_articles = remove_duplicates(
        validated_articles
    )

    print(
        "Before duplicate removal:",
        len(validated_articles)
    )

    print(
        "After duplicate removal:",
        len(unique_articles)
    )


    # --------------------------------------------------------
    # SAVE CSV
    # --------------------------------------------------------

    df = save_fused_data(
        unique_articles
    )


    # --------------------------------------------------------
    # FINAL QUALITY CHECK
    # --------------------------------------------------------

    print_dataset_quality(
        df
    )


    return df


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    queries = [
        '"scholarship" AND ("students" OR "education")',
        '"scholarship" AND "India"',
        "government AND scholarship AND students",
        "government AND scheme AND students"
    ]

    run_api_fusion(queries)