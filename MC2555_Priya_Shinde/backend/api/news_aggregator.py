import sys
import re
import unicodedata
import requests
import time

from pathlib import Path
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORT NEWS SERVICES
# ============================================================

from backend.api.gnews_service import search_news as gnews_search
from backend.api.currents_service import search_news as currents_search
from backend.api.newsapi_service import search_news as newsapi_search
from backend.api.newsdata_service import search_news as newsdata_search
from backend.api.thenewsapi_service import search_news as thenewsapi_search
from backend.api.google_news_service import search_news as google_news_search


# ============================================================
# SETTINGS
# ============================================================

MAX_RESULTS_PER_API = 10
MAX_FINAL_RESULTS = 15

# Keep only news from the last 7 days
RECENT_DAYS = 7

# Normal relevance threshold
MIN_RELEVANCE_SCORE = 35.0

# Entity bonus
CRITICAL_ENTITY_BONUS = 20.0

# Require critical entities when detected
REQUIRE_CRITICAL_ENTITY = True

# IMPORTANT:
# If the query contains a known topic such as weather,
# an article must also contain that topic.
REQUIRE_TOPIC_MATCH = True

# Minimum number of query terms that should match when
# a topic/entity based query is being evaluated.
MIN_QUERY_TERM_MATCHES = 1


# ============================================================
# OLLAMA / LLAMA SETTINGS
# ============================================================

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "llama3.2:latest"
OLLAMA_TIMEOUT = 20

# ============================================================
# NEW — NEWSDATA.IO RATE-LIMIT PROTECTION
# ============================================================
#
# NewsData.io can return HTTP 429 when too many requests are
# made in a short period. Once that happens, temporarily stop
# sending additional requests to NewsData.io for this process.
#
# This prevents the remaining search queries from repeatedly
# hitting the same rate limit.
# ============================================================

NEWSDATA_COOLDOWN_SECONDS = 60
newsdata_disabled_until = 0.0


# ============================================================
# MULTILINGUAL STOPWORDS
# ============================================================

RELEVANCE_STOPWORDS = {

    # --------------------------------------------------------
    # ENGLISH
    # --------------------------------------------------------

    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "being",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "there",
    "this",
    "to",
    "was",
    "were",
    "will",
    "with",

    "today",
    "yesterday",
    "tomorrow",
    "latest",
    "news",
    "current",
    "breaking",
    "update",
    "updates",

    "what",
    "when",
    "where",
    "why",
    "how",

    # --------------------------------------------------------
    # HINDI
    # --------------------------------------------------------

    "और",
    "का",
    "के",
    "की",
    "को",
    "में",
    "से",
    "पर",
    "यह",
    "है",
    "हैं",
    "था",
    "थे",
    "एक",
    "आज",
    "कल",
    "ने",
    "लिए",
    "समाचार",
    "खबर",
    "खबरें",
    "ताजा",
    "लेटेस्ट",

    # --------------------------------------------------------
    # MARATHI
    # --------------------------------------------------------

    "आणि",
    "चा",
    "ची",
    "चे",
    "च्या",
    "ला",
    "मध्ये",
    "मधून",
    "वर",
    "हे",
    "आहे",
    "आहेत",
    "होते",
    "एक",
    "आज",
    "उद्या",
    "काल",
    "ने",
    "साठी",
    "बातम्या",
    "बातमी",
    "ताज्या"
}


# ============================================================
# TOPIC ALIASES
# ============================================================

RELEVANCE_ALIASES = {

    "weather": {

        # English
        "weather",
        "forecast",
        "rain",
        "rainfall",
        "rains",
        "heavy rain",
        "heavy rainfall",
        "heavy rains",
        "rain warning",
        "rainfall warning",
        "heavy rainfall warning",
        "storm",
        "storms",
        "thunderstorm",
        "thunderstorms",
        "monsoon",
        "imd",
        "temperature",
        "climate",
        "heatwave",
        "heat",
        "flood",
        "flooding",
        "cyclone",
        "cloudy",
        "humidity",
        "wind",
        "winds",
        "warning",

        # Hindi
        "मौसम",
        "बारिश",
        "बरसात",
        "वर्षा",
        "तेज बारिश",
        "भारी बारिश",
        "मूसलाधार बारिश",
        "तूफान",
        "बाढ़",
        "आंधी",
        "मानसून",
        "मॉनसून",
        "तापमान",
        "चेतावनी",

        # Marathi
        "हवामान",
        "पाऊस",
        "पावसाचा",
        "पावसाची",
        "पावसाचे",
        "मुसळधार",
        "मुसळधार पाऊस",
        "मुसळधार पावसाचा",
        "मुसळधार पावसाची",
        "मुसळधार पावसाचे",
        "वृष्टी",
        "वादळ",
        "पूर",
        "मान्सून",
        "तापमान",
        "इशारा"
    },

    "education": {

        "education",
        "student",
        "students",
        "school",
        "schools",
        "college",
        "colleges",
        "university",
        "universities",
        "exam",
        "exams",
        "examination",
        "admission",
        "result",

        "शिक्षण",
        "विद्यार्थी",
        "विद्यार्थ्यांना",
        "शाळा",
        "महाविद्यालय",
        "विद्यापीठ",

        "शिक्षा",
        "छात्र",
        "छात्रों",
        "स्कूल",
        "कॉलेज",
        "विश्वविद्यालय",
        "परीक्षा",
        "प्रवेश",
        "निकाल"
    },

    "scholarship": {

        "scholarship",
        "scholarships",
        "stipend",
        "fellowship",
        "grant",
        "financial aid",

        "शिष्यवृत्ती",
        "शिष्यवृत्त्या",
        "छात्रवृत्ति",
        "वजीफा",
        "फेलोशिप",
        "अनुदान"
    },

    "government": {

        "government",
        "govt",
        "ministry",
        "minister",
        "official",
        "policy",
        "scheme",

        "सरकार",
        "सरकारी",
        "मंत्रालय",
        "मंत्री",
        "योजना",

        "शासन",
        "शासकीय"
    },

    "politics": {

        "politics",
        "political",
        "election",
        "elections",
        "vote",
        "voting",
        "poll",
        "polls",
        "candidate",
        "party",
        "politician",

        "राजकारण",
        "राजकीय",
        "निवडणूक",
        "निवडणुका",
        "मतदान",
        "उमेदवार",
        "पक्ष",
        "नेता",

        "राजनीति",
        "राजनीतिक",
        "चुनाव",
        "वोट"
    },

    "health": {

        "health",
        "hospital",
        "doctor",
        "disease",
        "medical",
        "healthcare",
        "patient",
        "medicine",

        "स्वास्थ्य",
        "अस्पताल",
        "डॉक्टर",
        "बीमारी",
        "चिकित्सा",

        "आरोग्य",
        "रुग्णालय"
    }
}


# ============================================================
# COMMON INDIAN LOCATION ALIASES
# ============================================================

LOCATION_ALIASES = {

    "maharashtra": {
        "maharashtra",
        "महाराष्ट्र",
        "महाराष्ट्रात",
        "महाराष्ट्राचा",
        "महाराष्ट्राची",
        "महाराष्ट्राचे",
        "महाराष्ट्रातील"
    },

    "mumbai": {
        "mumbai",
        "मुंबई",
        "मुंबईत",
        "मुंबईचा",
        "मुंबईची",
        "मुंबईचे"
    },

    "pune": {
        "pune",
        "पुणे",
        "पुण्यात",
        "पुण्याचा",
        "पुण्याची",
        "पुण्याचे"
    },

    "nagpur": {
        "nagpur",
        "नागपूर",
        "नागपुर",
        "नागपुरात"
    },

    "delhi": {
        "delhi",
        "new delhi",
        "दिल्ली",
        "नई दिल्ली"
    },

    "gujarat": {
        "gujarat",
        "गुजरात",
        "गुजरातमध्ये",
        "गुजरातात"
    },

    "odisha": {
        "odisha",
        "odissa",
        "ओडिशा",
        "उड़ीसा"
    },

    "karnataka": {
        "karnataka",
        "कर्नाटक",
        "कर्नाटकात"
    },

    "kerala": {
        "kerala",
        "केरळ",
        "केरल"
    },

    "tamil_nadu": {
        "tamil nadu",
        "तमिळनाडू",
        "तमिलनाडु"
    },

    "west_bengal": {
        "west bengal",
        "पश्चिम बंगाल"
    },

    "assam": {
        "assam",
        "आसाम",
        "असम"
    },

    "bihar": {
        "bihar",
        "बिहार"
    },

    "rajasthan": {
        "rajasthan",
        "राजस्थान"
    },

    "madhya_pradesh": {
        "madhya pradesh",
        "मध्य प्रदेश"
    },

    "uttar_pradesh": {
        "uttar pradesh",
        "उत्तर प्रदेश"
    }
}


# ============================================================
# ENGLISH CANONICAL TOPIC SEARCH TERMS
# ============================================================

CANONICAL_TOPIC_QUERIES = {

    "weather": [
        "heavy rainfall warning",
        "heavy rain warning",
        "rainfall warning",
        "weather warning"
    ],

    "education": [
        "education news"
    ],

    "scholarship": [
        "scholarship news"
    ],

    "government": [
        "government news"
    ],

    "politics": [
        "politics news"
    ],

    "health": [
        "health news"
    ]
}


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_relevance_text(value):

    if value is None:
        return ""

    value = unicodedata.normalize(
        "NFC",
        str(value).lower()
    )

    chars = []

    for character in value:

        category = unicodedata.category(character)

        if (
            character.isalnum()
            or character.isspace()
            or category.startswith("M")
        ):
            chars.append(character)

        else:
            chars.append(" ")

    normalized = "".join(chars)

    normalized = re.sub(
        r"\s+",
        " ",
        normalized
    ).strip()

    return normalized


# ============================================================
# GET WORDS
# ============================================================

def get_words(value):

    normalized = normalize_relevance_text(value)

    if not normalized:
        return []

    return normalized.split()


# ============================================================
# TEXT CONTAINS ALIAS
# ============================================================

def text_contains_alias(value, aliases):

    normalized = normalize_relevance_text(value)

    if not normalized:
        return False

    words = set(normalized.split())

    for alias in aliases:

        alias_normalized = normalize_relevance_text(alias)

        if not alias_normalized:
            continue

        if " " in alias_normalized:

            if alias_normalized in normalized:
                return True

        else:

            if alias_normalized in words:
                return True

    return False


# ============================================================
# COUNT ALIAS MATCHES
# ============================================================

def count_alias_matches(value, aliases):

    normalized = normalize_relevance_text(value)

    if not normalized:
        return 0

    words = set(normalized.split())

    count = 0

    for alias in aliases:

        alias_normalized = normalize_relevance_text(alias)

        if not alias_normalized:
            continue

        if " " in alias_normalized:

            if alias_normalized in normalized:
                count += 1

        else:

            if alias_normalized in words:
                count += 1

    return count


# ============================================================
# EXTRACT IMPORTANT QUERY TERMS
# ============================================================

def extract_query_terms(query):

    normalized_query = normalize_relevance_text(query)

    words = normalized_query.split()

    important_terms = []

    for word in words:

        if not word:
            continue

        if word in RELEVANCE_STOPWORDS:
            continue

        if len(word.strip()) < 2:
            continue

        important_terms.append(word)

    return list(
        dict.fromkeys(
            important_terms
        )
    )


# ============================================================
# DETECT TOPICS
# ============================================================

def detect_topic_groups(query):

    topic_groups = []

    for topic_name, aliases in RELEVANCE_ALIASES.items():

        if text_contains_alias(
            query,
            aliases
        ):

            topic_groups.append(
                (
                    topic_name,
                    aliases
                )
            )

    return topic_groups


# ============================================================
# DETECT CRITICAL ENTITIES
# ============================================================

def detect_critical_entities(query):

    normalized_query = normalize_relevance_text(query)

    detected = []

    for entity_name, aliases in LOCATION_ALIASES.items():

        if text_contains_alias(
            normalized_query,
            aliases
        ):

            detected.append(
                entity_name
            )

    return list(
        dict.fromkeys(
            detected
        )
    )


# ============================================================
# GET ENTITY MATCHES IN ARTICLE
# ============================================================

def get_article_entity_matches(
    article,
    critical_entities
):

    title = str(
        article.get(
            "title",
            ""
        )
    )

    description = str(
        article.get(
            "description",
            ""
        )
    )

    combined = (
        title
        + " "
        + description
    )

    matched_entities = []
    missing_entities = []

    for entity_name in critical_entities:

        aliases = LOCATION_ALIASES.get(
            entity_name,
            set()
        )

        if text_contains_alias(
            combined,
            aliases
        ):

            matched_entities.append(
                entity_name
            )

        else:

            missing_entities.append(
                entity_name
            )

    return (
        matched_entities,
        missing_entities
    )


# ============================================================
# GET TOPIC MATCHES IN ARTICLE
# ============================================================

def get_article_topic_matches(
    article,
    topic_groups
):

    title = str(
        article.get(
            "title",
            ""
        )
    )

    description = str(
        article.get(
            "description",
            ""
        )
    )

    combined = (
        title
        + " "
        + description
    )

    matched_topics = []

    for topic_name, aliases in topic_groups:

        if text_contains_alias(
            combined,
            aliases
        ):

            matched_topics.append(
                topic_name
            )

    return matched_topics


# ============================================================
# LLAMA SEARCH QUERY TRANSLATION
# ============================================================

def translate_query_for_search(
    query,
    language
):

    language_normalized = (
        language or "English"
    ).strip().lower()

    if language_normalized == "english":
        return ""

    if language_normalized not in {
        "hindi",
        "marathi"
    }:
        return ""

    if not query.strip():
        return ""

    prompt = f"""
Translate this {language} news claim into ONE concise English
search query for finding current news articles.

VERY IMPORTANT:

- Preserve the exact main meaning.
- Preserve the exact location.
- Preserve the exact event/topic.
- Do NOT replace "heavy rain/rainfall" with only "flood".
- If the claim says heavy rain, use "heavy rain" or "heavy rainfall".
- If the claim says a warning, keep "warning".
- Keep important people.
- Keep places.
- Keep organizations.
- Keep important numbers.
- Do not add facts.
- Do not explain anything.
- Return ONLY the English search query.
- Prefer 3 to 7 important words.

Examples:

Marathi:
महाराष्ट्रात मुसळधार पावसाचा इशारा देण्यात आला आहे.
Correct:
Maharashtra heavy rainfall warning

Hindi:
मुंबई में भारी बारिश की चेतावनी जारी
Correct:
Mumbai heavy rainfall warning

Claim:
{query}
"""

    try:

        response = requests.post(

            OLLAMA_URL,

            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0
                }
            },

            timeout=OLLAMA_TIMEOUT
        )

        if response.status_code != 200:

            print(
                "Llama search translation HTTP:",
                response.status_code
            )

            return ""

        data = response.json()

        translated = str(
            data.get(
                "response",
                ""
            )
        ).strip()

        translated = translated.strip(
            " \t\r\n\"'`"
        )

        translated = re.sub(
            r"^(english\s+search\s+query|search\s+query)\s*:\s*",
            "",
            translated,
            flags=re.IGNORECASE
        ).strip()

        # Remove accidental explanation lines
        translated = translated.split("\n")[0].strip()

        if not translated:
            return ""

        if len(translated) > 250:

            translated = (
                translated[:250]
                .rsplit(
                    " ",
                    1
                )[0]
            )

        print()
        print(
            "Llama English search query:"
        )

        print(
            translated
        )

        return translated

    except Exception as e:

        print(
            "Llama search translation unavailable:",
            e
        )

        return ""


# ============================================================
# BUILD CANONICAL QUERY
#
# This is the important new part.
#
# Example:
#
# Marathi claim
#       ↓
# Maharashtra + weather
#       ↓
# Maharashtra heavy rainfall warning
# ============================================================

def build_canonical_search_query(
    query
):

    entities = detect_critical_entities(query)
    topics = detect_topic_groups(query)

    if not entities or not topics:
        return ""

    entity_terms = []

    for entity in entities:

        if entity == "maharashtra":
            entity_terms.append("Maharashtra")

        elif entity == "mumbai":
            entity_terms.append("Mumbai")

        elif entity == "pune":
            entity_terms.append("Pune")

        elif entity == "nagpur":
            entity_terms.append("Nagpur")

        elif entity == "delhi":
            entity_terms.append("Delhi")

        elif entity == "gujarat":
            entity_terms.append("Gujarat")

        elif entity == "odisha":
            entity_terms.append("Odisha")

        elif entity == "karnataka":
            entity_terms.append("Karnataka")

        elif entity == "kerala":
            entity_terms.append("Kerala")

        elif entity == "tamil_nadu":
            entity_terms.append("Tamil Nadu")

        elif entity == "west_bengal":
            entity_terms.append("West Bengal")

        elif entity == "assam":
            entity_terms.append("Assam")

        elif entity == "bihar":
            entity_terms.append("Bihar")

        elif entity == "rajasthan":
            entity_terms.append("Rajasthan")

        elif entity == "madhya_pradesh":
            entity_terms.append("Madhya Pradesh")

        elif entity == "uttar_pradesh":
            entity_terms.append("Uttar Pradesh")

    topic_terms = []

    for topic_name, _ in topics:

        canonical = CANONICAL_TOPIC_QUERIES.get(
            topic_name,
            []
        )

        if canonical:
            topic_terms.append(
                canonical[0]
            )

    if not entity_terms or not topic_terms:
        return ""

    return (
        " ".join(entity_terms)
        + " "
        + " ".join(topic_terms)
    ).strip()


# ============================================================
# GENERATE MULTILINGUAL SEARCH QUERIES
# ============================================================

def generate_search_queries(
    query,
    language
):

    """
    Generate a small, high-quality set of multilingual search
    queries.

    For Hindi/Marathi we intentionally keep only:
        1. Original-language query
        2. Llama English translation
        3. Canonical entity + topic query

    The previous implementation also generated:
        - translated important terms
        - translated important terms + "news"

    Those extra variants were often duplicates of the Llama
    translation/canonical query and caused unnecessary API calls.

    Maximum search queries:
        English       -> up to 3
        Hindi/Marathi -> up to 3
    """

    language_normalized = (
        language or "English"
    ).strip().lower()

    queries = []

    original_query = str(
        query
    ).strip()

    # --------------------------------------------------------
    # 1. ORIGINAL QUERY
    # --------------------------------------------------------

    if original_query:

        queries.append(
            original_query
        )

    # --------------------------------------------------------
    # DETECT TOPIC / ENTITY FROM ORIGINAL CLAIM
    # --------------------------------------------------------

    original_topics = detect_topic_groups(
        query
    )

    original_entities = detect_critical_entities(
        query
    )

    # --------------------------------------------------------
    # 2. LLAMA TRANSLATION
    # --------------------------------------------------------

    translated_query = ""

    if language_normalized in {
        "hindi",
        "marathi"
    }:

        translated_query = (
            translate_query_for_search(
                query,
                language
            )
        )

        if translated_query:

            queries.append(
                translated_query
            )

    # --------------------------------------------------------
    # 3. CANONICAL ENTITY + TOPIC QUERY
    # --------------------------------------------------------

    canonical_query = (
        build_canonical_search_query(
            query
        )
    )

    if canonical_query:

        queries.append(
            canonical_query
        )

    # --------------------------------------------------------
    # ENGLISH
    # --------------------------------------------------------
    #
    # English claims do not need Llama translation.
    # Keep a concise original/important-term/news set.
    # --------------------------------------------------------

    if language_normalized == "english":

        query_terms = extract_query_terms(
            query
        )

        if query_terms:

            important_query = " ".join(
                query_terms
            )

            queries.append(
                important_query
            )

            # Add "news" only when it creates a genuinely
            # different query from the existing ones.
            queries.append(
                f"{important_query} news"
            )

    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    unique_queries = []

    seen = set()

    for item in queries:

        item = str(
            item
        ).strip()

        normalized = (
            normalize_relevance_text(
                item
            )
        )

        if not normalized:
            continue

        if normalized in seen:
            continue

        seen.add(
            normalized
        )

        unique_queries.append(
            item
        )

    # --------------------------------------------------------
    # HARD SAFETY LIMIT
    # --------------------------------------------------------
    #
    # This guarantees that one claim cannot unexpectedly
    # expand into a large number of API requests.
    # --------------------------------------------------------

    unique_queries = unique_queries[:3]

    # --------------------------------------------------------
    # LOGGING
    # --------------------------------------------------------

    print()
    print(
        "Detected original topics:",
        [
            topic
            for topic, _ in original_topics
        ]
    )

    print(
        "Detected original entities:",
        original_entities
    )

    if canonical_query:

        print(
            "Canonical search query:",
            canonical_query
        )

    print(
        "Total search queries:",
        len(unique_queries)
    )

    return unique_queries


# ============================================================
# DATE PARSER
# ============================================================

def parse_published_date(value):

    if not value:
        return None

    value = str(
        value
    ).strip()

    if not value:
        return None

    # ISO format
    try:

        normalized_value = value.replace(
            "Z",
            "+00:00"
        )

        dt = datetime.fromisoformat(
            normalized_value
        )

        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt.astimezone(
            timezone.utc
        )

    except Exception:
        pass

    # RFC date format
    try:

        dt = parsedate_to_datetime(
            value
        )

        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt.astimezone(
            timezone.utc
        )

    except Exception:
        pass

    return None


# ============================================================
# GET ARTICLE DATE
# ============================================================

def get_article_date(article):

    possible_fields = [

        "publishedAt",
        "published_at",
        "published",
        "pubDate",
        "date",
        "publication_date",
        "publishedDate"
    ]

    for field in possible_fields:

        value = article.get(
            field
        )

        parsed = parse_published_date(
            value
        )

        if parsed is not None:
            return parsed

    return None


# ============================================================
# ADD ARTICLES
# ============================================================

def add_articles(
    all_articles,
    result,
    api_name
):

    if not isinstance(
        result,
        dict
    ):

        print(
            f"{api_name} returned invalid response."
        )

        return

    if not result.get(
        "success",
        False
    ):

        print(
            f"{api_name} returned an error:"
        )

        print(
            result.get(
                "error",
                "Unknown error"
            )
        )

        return

    articles = result.get(
        "articles",
        []
    )

    print(
        f"{api_name} articles:",
        len(articles)
    )

    for article in articles:

        if not isinstance(
            article,
            dict
        ):
            continue

        article_copy = article.copy()

        article_copy[
            "api_source"
        ] = api_name

        article_copy.setdefault(
            "title",
            ""
        )

        article_copy.setdefault(
            "description",
            ""
        )

        article_copy.setdefault(
            "url",
            ""
        )

        all_articles.append(
            article_copy
        )


# ============================================================
# RECENCY FILTER
# ============================================================

def filter_recent_articles(
    articles,
    recent_days=RECENT_DAYS
):

    now = datetime.now(
        timezone.utc
    )

    cutoff = (
        now
        - timedelta(
            days=recent_days
        )
    )

    recent_articles = []

    rejected_old = 0
    rejected_undated = 0

    today_count = 0
    yesterday_count = 0
    current_week_count = 0

    today = now.date()

    yesterday = (
        now
        - timedelta(
            days=1
        )
    ).date()

    for article in articles:

        if not isinstance(
            article,
            dict
        ):
            continue

        published_date = (
            get_article_date(
                article
            )
        )

        if published_date is None:

            rejected_undated += 1

            continue

        if published_date < cutoff:

            rejected_old += 1

            continue

        article = article.copy()

        article[
            "publishedAt"
        ] = published_date.isoformat()

        article_date = (
            published_date.date()
        )

        if article_date == today:

            article[
                "recency"
            ] = "Today"

            article[
                "recency_score"
            ] = 100.0

            today_count += 1

        elif article_date == yesterday:

            article[
                "recency"
            ] = "Yesterday"

            article[
                "recency_score"
            ] = 90.0

            yesterday_count += 1

        else:

            article[
                "recency"
            ] = "This Week"

            age_hours = (

                now
                - published_date

            ).total_seconds() / 3600

            if age_hours <= 72:

                article[
                    "recency_score"
                ] = 80.0

            else:

                article[
                    "recency_score"
                ] = 65.0

            current_week_count += 1

        recent_articles.append(
            article
        )

    recent_articles.sort(

        key=lambda article:

            get_article_date(
                article
            )

            or datetime.min.replace(
                tzinfo=timezone.utc
            ),

        reverse=True
    )

    print()
    print("=" * 60)
    print(
        " REAL-TIME RECENCY FILTER"
    )
    print("=" * 60)

    print(
        "Input articles:",
        len(articles)
    )

    print(
        "Recent articles kept:",
        len(recent_articles)
    )

    print(
        "Today:",
        today_count
    )

    print(
        "Yesterday:",
        yesterday_count
    )

    print(
        "Current week:",
        current_week_count
    )

    print(
        "Old articles rejected:",
        rejected_old
    )

    print(
        "Undated articles rejected:",
        rejected_undated
    )

    print(
        "Recent window:",
        f"Last {recent_days} days"
    )

    print("=" * 60)

    return recent_articles


# ============================================================
# CALCULATE RELEVANCE FOR ONE QUERY
# ============================================================

def calculate_relevance_score_for_query(
    article,
    query
):

    query_terms = extract_query_terms(
        query
    )

    topic_groups = detect_topic_groups(
        query
    )

    critical_entities = detect_critical_entities(
        query
    )

    title = str(
        article.get(
            "title",
            ""
        )
    )

    description = str(
        article.get(
            "description",
            ""
        )
    )

    normalized_title = (
        normalize_relevance_text(
            title
        )
    )

    normalized_description = (
        normalize_relevance_text(
            description
        )
    )

    normalized_combined = (
        normalized_title
        + " "
        + normalized_description
    ).strip()

    title_words = set(
        normalized_title.split()
    )

    description_words = set(
        normalized_description.split()
    )

    title_matches = []
    description_matches = []
    all_matches = []

    # ========================================================
    # QUERY TERM MATCHING
    # ========================================================

    for term in query_terms:

        if term in title_words:

            title_matches.append(
                term
            )

            all_matches.append(
                term
            )

        elif term in description_words:

            description_matches.append(
                term
            )

            all_matches.append(
                term
            )

    all_matches = list(
        dict.fromkeys(
            all_matches
        )
    )

    # ========================================================
    # ENTITY MATCHING
    # ========================================================

    (
        matched_entities,
        missing_entities
    ) = get_article_entity_matches(

        article,

        critical_entities
    )

    # ========================================================
    # TOPIC MATCHING
    # ========================================================

    topic_matches = (
        get_article_topic_matches(
            article,
            topic_groups
        )
    )

    # ========================================================
    # QUERY COVERAGE
    # ========================================================

    if query_terms:

        coverage_ratio = (
            len(all_matches)
            /
            len(query_terms)
        )

    else:

        coverage_ratio = 0.0

    # ========================================================
    # BASE SCORE
    # ========================================================

    score = 0.0

    # Query coverage
    score += (
        coverage_ratio
        * 50.0
    )

    # Title matches
    score += min(
        len(title_matches)
        * 15.0,
        30.0
    )

    # Description matches
    score += min(
        len(description_matches)
        * 5.0,
        15.0
    )

    # ========================================================
    # EXACT PHRASE
    # ========================================================

    normalized_query = (
        normalize_relevance_text(
            query
        )
    )

    if (
        len(
            normalized_query.split()
        ) >= 2

        and

        normalized_query
        in normalized_combined
    ):

        score += 15.0

    # ========================================================
    # TOPIC SIGNAL
    # ========================================================

    if topic_matches:

        score += 10.0 * len(
            topic_matches
        )

    # ========================================================
    # MULTIPLE TERM BONUS
    # ========================================================

    if len(all_matches) >= 2:

        score += 10.0

    # ========================================================
    # STRONG TITLE COVERAGE
    # ========================================================

    if query_terms:

        title_coverage = (
            len(title_matches)
            /
            len(query_terms)
        )

        if title_coverage >= 0.75:

            score += 10.0

    # ========================================================
    # CRITICAL ENTITY SCORE
    # ========================================================

    entity_required = (
        len(critical_entities) > 0
    )

    entity_match = (
        len(matched_entities) ==
        len(critical_entities)
    )

    if entity_match and entity_required:

        score += CRITICAL_ENTITY_BONUS

    # ========================================================
    # ENTITY PENALTY
    # ========================================================

    if (
        REQUIRE_CRITICAL_ENTITY
        and entity_required
        and not entity_match
    ):

        score -= 45.0

    # ========================================================
    # SCORE CAP
    # ========================================================

    score = max(
        0.0,
        min(
            score,
            100.0
        )
    )

    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    valid = (
        score >= MIN_RELEVANCE_SCORE
    )

    # --------------------------------------------------------
    # REQUIRED ENTITY
    # --------------------------------------------------------

    if (
        REQUIRE_CRITICAL_ENTITY
        and entity_required
        and not entity_match
    ):

        valid = False

    # --------------------------------------------------------
    # REQUIRED TOPIC
    #
    # THIS FIXES YOUR CURRENT PROBLEM.
    #
    # Example:
    #
    # Query:
    # Maharashtra heavy rainfall warning
    #
    # Article:
    # Maharashtra Maratha reservation
    #
    # Entity = YES
    # Weather topic = NO
    #
    # Therefore:
    # REJECT
    # --------------------------------------------------------

    topic_required = (
        REQUIRE_TOPIC_MATCH
        and len(topic_groups) > 0
    )

    if (
        topic_required
        and len(topic_matches) == 0
    ):

        valid = False

    # --------------------------------------------------------
    # QUERY TERM REQUIREMENT
    # --------------------------------------------------------

    if (
        query_terms
        and len(all_matches) < MIN_QUERY_TERM_MATCHES
    ):

        valid = False

    return {

        "score":
            round(
                score,
                2
            ),

        "valid":
            valid,

        "query":
            query,

        "query_terms":
            query_terms,

        "matched_terms":
            all_matches,

        "title_matches":
            title_matches,

        "description_matches":
            description_matches,

        "topic_matches":
            topic_matches,

        "critical_entities":
            critical_entities,

        "matched_entities":
            matched_entities,

        "missing_entities":
            missing_entities
    }


# ============================================================
# MULTILINGUAL RELEVANCE FILTER
# ============================================================

def filter_relevant_articles(
    articles,
    query,
    search_queries=None
):

    relevant_articles = []

    rejected_irrelevant = 0

    if not search_queries:

        search_queries = [
            query
        ]

    print()
    print("=" * 60)

    print(
        " MULTILINGUAL ENTITY + TOPIC RELEVANCE FILTER"
    )

    print("=" * 60)

    print(
        "Original Query:",
        query
    )

    print()
    print(
        "Query variants used:"
    )

    for item in search_queries:

        print(
            "-",
            item
        )

    # ========================================================
    # ORIGINAL CLAIM REQUIREMENTS
    # ========================================================

    original_entities = (
        detect_critical_entities(
            query
        )
    )

    original_topics = (
        detect_topic_groups(
            query
        )
    )

    original_topic_names = [
        topic_name
        for topic_name, _ in original_topics
    ]

    print()
    print(
        "Critical entities from original query:"
    )

    if original_entities:

        for entity in original_entities:

            print(
                "✓",
                entity
            )

    else:

        print(
            "None detected"
        )

    print()
    print(
        "Required topics from original query:"
    )

    if original_topic_names:

        for topic in original_topic_names:

            print(
                "✓",
                topic
            )

    else:

        print(
            "None detected"
        )

    # ========================================================
    # PROCESS ARTICLES
    # ========================================================

    for article in articles:

        if not isinstance(
            article,
            dict
        ):
            continue

        article = article.copy()

        best_result = None

        # ----------------------------------------------------
        # SCORE AGAINST EVERY QUERY VARIANT
        # ----------------------------------------------------

        for candidate_query in search_queries:

            current_result = (
                calculate_relevance_score_for_query(

                    article,

                    candidate_query

                )
            )

            if (
                best_result is None

                or

                current_result["score"]
                >
                best_result["score"]
            ):

                best_result = (
                    current_result
                )

        if best_result is None:

            rejected_irrelevant += 1

            continue

        # ====================================================
        # ORIGINAL ENTITY CHECK
        # ====================================================

        original_matched_entities = []
        original_missing_entities = []

        original_entity_match = True

        if original_entities:

            (
                original_matched_entities,
                original_missing_entities
            ) = get_article_entity_matches(

                article,

                original_entities

            )

            original_entity_match = (
                len(original_matched_entities)
                ==
                len(original_entities)
            )

            if not original_entity_match:

                best_result["valid"] = False

        # ====================================================
        # ORIGINAL TOPIC CHECK
        #
        # This is the other important fix.
        #
        # We don't trust only the translated query.
        # The original claim decides the topic.
        # ====================================================

        original_topic_matches = (
            get_article_topic_matches(
                article,
                original_topics
            )
        )

        if (
            REQUIRE_TOPIC_MATCH
            and original_topics
            and not original_topic_matches
        ):

            best_result["valid"] = False

        # ====================================================
        # SAVE RELEVANCE DATA
        # ====================================================

        article[
            "relevance_score"
        ] = best_result[
            "score"
        ]

        article[
            "matched_search_query"
        ] = best_result[
            "query"
        ]

        article[
            "matched_query_terms"
        ] = ", ".join(
            best_result[
                "matched_terms"
            ]
        )

        article[
            "matched_title_terms"
        ] = ", ".join(
            best_result[
                "title_matches"
            ]
        )

        article[
            "matched_description_terms"
        ] = ", ".join(
            best_result[
                "description_matches"
            ]
        )

        article[
            "matched_topics"
        ] = ", ".join(
            original_topic_matches
        )

        article[
            "critical_entities"
        ] = ", ".join(
            original_entities
        )

        article[
            "matched_entities"
        ] = ", ".join(
            original_matched_entities
        )

        article[
            "missing_entities"
        ] = ", ".join(
            original_missing_entities
        )

        # ====================================================
        # FINAL DECISION
        # ====================================================

        if not best_result["valid"]:

            rejected_irrelevant += 1

            continue

        relevant_articles.append(
            article
        )

    # ========================================================
    # SORT
    # ========================================================

    relevant_articles.sort(

        key=lambda article: (

            float(
                article.get(
                    "relevance_score",
                    0
                )
            ),

            float(
                article.get(
                    "recency_score",
                    0
                )
            ),

            get_article_date(
                article
            )

            or datetime.min.replace(
                tzinfo=timezone.utc
            )
        ),

        reverse=True
    )

    print()

    print(
        "Input recent articles:",
        len(articles)
    )

    print(
        "Relevant articles kept:",
        len(relevant_articles)
    )

    print(
        "Irrelevant/entity/topic-mismatched articles rejected:",
        rejected_irrelevant
    )

    print("=" * 60)

    return relevant_articles


# ============================================================
# SEARCH ONE QUERY ACROSS ALL SOURCES
# ============================================================

def search_one_query(
    search_query,
    all_articles
):

    print()
    print("=" * 60)

    print(
        "SEARCH QUERY:",
        search_query
    )

    print("=" * 60)

    # ========================================================
    # GNEWS
    # ========================================================

    try:

        result = gnews_search(

            query=search_query,

            language="English",

            country="in",

            max_results=MAX_RESULTS_PER_API

        )

        add_articles(

            all_articles,

            result,

            f"GNews ({search_query})"

        )

    except Exception as e:

        print(
            "GNews exception:",
            e
        )

    # ========================================================
    # CURRENTS
    # ========================================================

    try:

        result = currents_search(
            query=search_query
        )

        add_articles(

            all_articles,

            result,

            f"Currents ({search_query})"

        )

    except Exception as e:

        print(
            "Currents exception:",
            e
        )

    # ========================================================
    # NEWSAPI
    # ========================================================

    try:

        result = newsapi_search(
            query=search_query
        )

        add_articles(

            all_articles,

            result,

            f"NewsAPI ({search_query})"

        )

    except Exception as e:

        print(
            "NewsAPI exception:",
            e
        )

    # ========================================================
    # NEWSDATA.IO
    # ========================================================
    #
    # Rate-limit protection:
    # If NewsData.io has recently returned HTTP 429, skip it
    # temporarily instead of repeatedly sending requests.
    # ========================================================

    global newsdata_disabled_until

    current_time = time.time()

    if current_time < newsdata_disabled_until:

        remaining = int(
            max(
                1,
                newsdata_disabled_until - current_time
            )
        )

        print(
            f"NewsData.io temporarily skipped "
            f"(rate-limit cooldown: {remaining}s remaining)."
        )

    else:

        try:

            result = newsdata_search(
                query=search_query
            )

            # ------------------------------------------------
            # Detect a rate-limit response returned by the
            # service wrapper.
            # ------------------------------------------------

            result_error = str(
                result.get(
                    "error",
                    ""
                )
            ).lower() if isinstance(
                result,
                dict
            ) else ""

            if (
                "429" in result_error
                or "rate limit" in result_error
                or "ratelimit" in result_error
            ):

                newsdata_disabled_until = (
                    time.time()
                    + NEWSDATA_COOLDOWN_SECONDS
                )

                print(
                    "NewsData.io rate limit detected."
                )

                print(
                    f"NewsData.io disabled for "
                    f"{NEWSDATA_COOLDOWN_SECONDS}s."
                )

            else:

                add_articles(

                    all_articles,

                    result,

                    f"NewsData.io ({search_query})"

                )

        except Exception as e:

            error_text = str(
                e
            ).lower()

            if (
                "429" in error_text
                or "rate limit" in error_text
                or "ratelimit" in error_text
            ):

                newsdata_disabled_until = (
                    time.time()
                    + NEWSDATA_COOLDOWN_SECONDS
                )

                print(
                    "NewsData.io rate limit detected."
                )

                print(
                    f"NewsData.io disabled for "
                    f"{NEWSDATA_COOLDOWN_SECONDS}s."
                )

            else:

                print(
                    "NewsData.io exception:",
                    e
                )

    # ========================================================
    # THENEWSAPI
    # ========================================================

    try:

        result = thenewsapi_search(
            query=search_query
        )

        add_articles(

            all_articles,

            result,

            f"TheNewsAPI ({search_query})"

        )

    except Exception as e:

        print(
            "TheNewsAPI exception:",
            e
        )

    # ========================================================
    # GOOGLE NEWS RSS
    # ========================================================

    try:

        result = google_news_search(
            query=search_query
        )

        add_articles(

            all_articles,

            result,

            f"Google News RSS ({search_query})"

        )

    except Exception as e:

        print(
            "Google News RSS exception:",
            e
        )


# ============================================================
# SEARCH ALL SOURCES
# ============================================================

def search_all_sources(
    query,
    language="English"
):

    print()
    print("=" * 60)

    print(
        " MULTI-API MULTILINGUAL NEWS SEARCH"
    )

    print("=" * 60)

    print()
    print(
        "Original Query:"
    )

    print(
        query
    )

    print()
    print(
        "Language:"
    )

    print(
        language
    )

    # ========================================================
    # GENERATE SEARCH QUERIES
    # ========================================================

    search_queries = generate_search_queries(

        query,

        language

    )

    print()
    print(
        "Generated search queries:"
    )

    for item in search_queries:

        print(
            "-",
            item
        )

    all_articles = []

    # ========================================================
    # SEARCH
    # ========================================================

    for index, search_query in enumerate(
        search_queries,
        start=1
    ):

        search_one_query(

            search_query,

            all_articles

        )

        # ----------------------------------------------------
        # Small delay between query batches.
        #
        # This helps avoid burst traffic when multiple
        # search queries are generated for one claim.
        # ----------------------------------------------------

        if index < len(search_queries):

            time.sleep(
                1
            )

    # ========================================================
    # COLLECTION COMPLETE
    # ========================================================

    print()
    print("=" * 60)

    print(
        " COLLECTION COMPLETE"
    )

    print("=" * 60)

    print(
        "Total articles collected:",
        len(all_articles)
    )

    # ========================================================
    # RECENCY
    # ========================================================

    recent_articles = filter_recent_articles(

        all_articles,

        recent_days=RECENT_DAYS

    )

    print()

    print(
        "Articles after real-time filtering:",
        len(recent_articles)
    )

    # ========================================================
    # RELEVANCE
    # ========================================================

    relevant_articles = filter_relevant_articles(

        recent_articles,

        query,

        search_queries=search_queries

    )

    print()

    print(
        "Articles after relevance filtering:",
        len(relevant_articles)
    )

    return relevant_articles


# ============================================================
# TITLE SIMILARITY
# ============================================================

def get_title_similarity(
    title1,
    title2
):

    words1 = set(

        normalize_relevance_text(
            title1
        ).split()

    )

    words2 = set(

        normalize_relevance_text(
            title2
        ).split()

    )

    if not words1 or not words2:

        return 0.0

    intersection = len(

        words1.intersection(
            words2
        )

    )

    union = len(

        words1.union(
            words2
        )

    )

    if union == 0:

        return 0.0

    return (
        intersection
        /
        union
    )


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def remove_duplicates(
    articles
):

    unique_articles = []

    seen_urls = set()

    for article in articles:

        url = str(

            article.get(
                "url",
                ""
            )

        ).strip().lower()

        title = normalize_relevance_text(

            article.get(
                "title",
                ""
            )

        )

        # ----------------------------------------------------
        # URL DUPLICATE
        # ----------------------------------------------------

        if url and url in seen_urls:

            continue

        duplicate_found = False

        # ----------------------------------------------------
        # TITLE DUPLICATE
        # ----------------------------------------------------

        for existing_article in unique_articles:

            existing_title = (
                existing_article.get(
                    "title",
                    ""
                )
            )

            similarity = (
                get_title_similarity(

                    title,

                    existing_title

                )
            )

            if similarity >= 0.85:

                duplicate_found = True

                break

        if duplicate_found:

            continue

        if url:

            seen_urls.add(
                url
            )

        unique_articles.append(
            article
        )

    return unique_articles


# ============================================================
# FINAL SORT
# ============================================================

def sort_articles(
    articles
):

    articles.sort(

        key=lambda article: (

            float(
                article.get(
                    "relevance_score",
                    0
                )
            ),

            float(
                article.get(
                    "recency_score",
                    0
                )
            ),

            get_article_date(
                article
            )

            or datetime.min.replace(
                tzinfo=timezone.utc
            )
        ),

        reverse=True
    )

    return articles


# ============================================================
# AGGREGATE NEWS
# ============================================================

def aggregate_news(
    query,
    language="English"
):

    articles = search_all_sources(

        query=query,

        language=language

    )

    unique_articles = remove_duplicates(
        articles
    )

    unique_articles = sort_articles(
        unique_articles
    )

    unique_articles = unique_articles[
        :MAX_FINAL_RESULTS
    ]

    print()
    print("=" * 60)

    print(
        " FINAL RECENT NEWS RESULT"
    )

    print("=" * 60)

    print(
        "Before deduplication:",
        len(articles)
    )

    print(
        "Unique recent articles:",
        len(unique_articles)
    )

    return {

        "success":
            True,

        "query":
            query,

        "language":
            language,

        "total_before_deduplication":
            len(articles),

        "total_unique_articles":
            len(unique_articles),

        "articles":
            unique_articles
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print()

    print("=" * 60)

    print(
        " MULTI-API MULTILINGUAL NEWS AGGREGATOR TEST"
    )

    print("=" * 60)

    query = input(
        "\nEnter news search query:\n"
    ).strip()

    if not query:

        print(
            "\nQuery cannot be empty."
        )

        sys.exit(1)

    language_input = input(
        "\nEnter language (English/Hindi/Marathi):\n"
    ).strip()

    if not language_input:

        language_input = "English"

    result = aggregate_news(

        query=query,

        language=language_input

    )

    print()

    print("=" * 60)

    print(
        " FINAL AGGREGATED RESULT"
    )

    print("=" * 60)

    print(
        "\nQuery:",
        result[
            "query"
        ]
    )

    print(
        "Language:",
        result[
            "language"
        ]
    )

    print(
        "Total before deduplication:",
        result[
            "total_before_deduplication"
        ]
    )

    print(
        "Total unique recent articles:",
        result[
            "total_unique_articles"
        ]
    )

    articles = result[
        "articles"
    ]

    if not articles:

        print(
            "\nNo recent relevant articles collected."
        )

    else:

        print(
            "\nCollected recent relevant articles:"
        )

        for index, article in enumerate(

            articles,

            start=1

        ):

            print()

            print(
                "-" * 60
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
                "Description:",
                article.get(
                    "description",
                    ""
                )
            )

            print(
                "Source:",
                article.get(
                    "source_name",
                    article.get(
                        "source",
                        ""
                    )
                )
            )

            print(
                "API:",
                article.get(
                    "api_source",
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
                "Recency:",
                article.get(
                    "recency",
                    ""
                )
            )

            print(
                "Recency Score:",
                article.get(
                    "recency_score",
                    ""
                )
            )

            print(
                "Relevance Score:",
                article.get(
                    "relevance_score",
                    ""
                )
            )

            print(
                "Matched Search Query:",
                article.get(
                    "matched_search_query",
                    ""
                )
            )

            print(
                "Matched Query Terms:",
                article.get(
                    "matched_query_terms",
                    ""
                )
            )

            print(
                "Matched Title Terms:",
                article.get(
                    "matched_title_terms",
                    ""
                )
            )

            print(
                "Matched Description Terms:",
                article.get(
                    "matched_description_terms",
                    ""
                )
            )

            print(
                "Matched Topics:",
                article.get(
                    "matched_topics",
                    ""
                )
            )

            print(
                "Critical Entities:",
                article.get(
                    "critical_entities",
                    ""
                )
            )

            print(
                "Matched Entities:",
                article.get(
                    "matched_entities",
                    ""
                )
            )

            print(
                "Missing Entities:",
                article.get(
                    "missing_entities",
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