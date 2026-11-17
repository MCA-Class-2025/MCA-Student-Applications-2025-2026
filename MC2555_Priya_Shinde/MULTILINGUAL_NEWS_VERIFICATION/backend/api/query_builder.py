import re


# ============================================================
# STOP WORDS
# ============================================================

STOP_WORDS = {

    # --------------------------------------------------------
    # English
    # --------------------------------------------------------

    "the",
    "is",
    "a",
    "an",
    "has",
    "have",
    "had",
    "been",
    "being",
    "was",
    "were",

    "to",
    "of",
    "for",
    "from",
    "in",
    "on",
    "at",
    "by",
    "with",

    "and",
    "or",
    "but",
    "as",
    "into",
    "about",
    "after",
    "before",
    "during",

    "that",
    "this",
    "these",
    "those",

    "it",
    "its",
    "he",
    "she",
    "they",
    "them",
    "his",
    "her",
    "their",

    # Search noise
    "important",
    "latest",
    "recent",
    "current",

    # Event words
    "wins",
    "won",
    "win",
    "announced",
    "announcement",
    "announce",

    # --------------------------------------------------------
    # Hindi
    # --------------------------------------------------------

    "ने",
    "के",
    "की",
    "का",
    "है",
    "हैं",
    "और",
    "लिए",
    "से",
    "में",
    "पर",
    "को",
    "एक",

    # --------------------------------------------------------
    # Marathi
    # --------------------------------------------------------

    "ने",
    "चा",
    "ची",
    "चे",
    "च्या",
    "आहे",
    "आहेत",
    "आणि",
    "साठी",
    "मध्ये",
    "वर",
    "ला",
    "एक",

    "नवीन",
    "सुरू",
    "करण्याची",
    "घोषणा",
    "केलीआहे",
}


# ============================================================
# IMPORTANT CONCEPT WORDS
# ============================================================

CONCEPT_MAP = {

    # --------------------------------------------------------
    # Scholarship
    # --------------------------------------------------------

    "scholarship": [
        "scholarship",
        "students",
        "education"
    ],

    "scholarships": [
        "scholarship",
        "students",
        "education"
    ],

    "छात्रवृत्ति": [
        "scholarship",
        "students",
        "education"
    ],

    "शिष्यवृत्ती": [
        "scholarship",
        "students",
        "education"
    ],

    # --------------------------------------------------------
    # Students
    # --------------------------------------------------------

    "student": [
        "students",
        "education"
    ],

    "students": [
        "students",
        "education"
    ],

    "विद्यार्थी": [
        "students",
        "education"
    ],

    "विद्यार्थ्यांसाठी": [
        "students",
        "education"
    ],

    "छात्र": [
        "students",
        "education"
    ],

    "छात्रों": [
        "students",
        "education"
    ],

    # --------------------------------------------------------
    # Government
    # --------------------------------------------------------

    "government": [
        "government"
    ],

    "सरकार": [
        "government"
    ],

    "सरकारने": [
        "government"
    ],

    "शासन": [
        "government"
    ],

    # --------------------------------------------------------
    # Scheme / Program
    # --------------------------------------------------------

    "scheme": [
        "scheme"
    ],

    "schemes": [
        "scheme"
    ],

    "program": [
        "program"
    ],

    "programme": [
        "programme"
    ],

    "योजना": [
        "scheme"
    ],

    # --------------------------------------------------------
    # Sports
    # --------------------------------------------------------

    "cricket": [
        "cricket",
        "sports"
    ],

    "football": [
        "football",
        "sports"
    ],

    "soccer": [
        "soccer",
        "sports"
    ],

    "tennis": [
        "tennis",
        "sports"
    ],

    "basketball": [
        "basketball",
        "sports"
    ],

    "baseball": [
        "baseball",
        "sports"
    ],

    "hockey": [
        "hockey",
        "sports"
    ],

    "match": [
        "match",
        "sports"
    ],

    "tournament": [
        "tournament",
        "sports"
    ],

    "league": [
        "league",
        "sports"
    ],

    "championship": [
        "championship",
        "sports"
    ],

    "cup": [
        "cup",
        "sports"
    ],

    "मैच": [
        "match",
        "sports"
    ],

    "क्रिकेट": [
        "cricket",
        "sports"
    ],

    # --------------------------------------------------------
    # Politics
    # --------------------------------------------------------

    "election": [
        "election",
        "politics"
    ],

    "elections": [
        "election",
        "politics"
    ],

    "politics": [
        "politics"
    ],

    "political": [
        "politics"
    ],

    "चुनाव": [
        "election",
        "politics"
    ],

    # --------------------------------------------------------
    # Technology
    # --------------------------------------------------------

    "technology": [
        "technology"
    ],

    "artificial": [
        "AI",
        "technology"
    ],

    "intelligence": [
        "AI",
        "technology"
    ],

    # IMPORTANT:
    # "ai" is handled as an exact word.
    # It must NOT match inside "against", "said", etc.

    "ai": [
        "AI",
        "technology"
    ],

    # --------------------------------------------------------
    # Business / Economy
    # --------------------------------------------------------

    "business": [
        "business"
    ],

    "economy": [
        "economy"
    ],

    "economic": [
        "economy"
    ],

    "market": [
        "market",
        "business"
    ],

    "company": [
        "company",
        "business"
    ],

    # --------------------------------------------------------
    # Health
    # --------------------------------------------------------

    "health": [
        "health"
    ],

    "disease": [
        "health"
    ],

    "hospital": [
        "health"
    ],

    "medical": [
        "health"
    ],

    # --------------------------------------------------------
    # Accident / Disaster
    # --------------------------------------------------------

    "accident": [
        "accident"
    ],

    "earthquake": [
        "earthquake",
        "disaster"
    ],

    "flood": [
        "flood",
        "disaster"
    ],

    "cyclone": [
        "cyclone",
        "disaster"
    ],

    "fire": [
        "fire",
        "disaster"
    ],
}


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(text):

    if not text:
        return ""

    text = str(text).lower()

    text = re.sub(
        r"[^\w\s\u0900-\u097F]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# EXTRACT KEYWORDS
# ============================================================

def extract_keywords(text):

    cleaned = clean_text(
        text
    )

    words = cleaned.split()

    keywords = []

    for word in words:

        if word in STOP_WORDS:
            continue

        if len(word) < 2:
            continue

        if word not in keywords:

            keywords.append(
                word
            )

    return keywords


# ============================================================
# DETECT CONCEPTS
# ============================================================

def detect_concepts(text):

    cleaned = clean_text(
        text
    )

    words = set(
        cleaned.split()
    )

    concepts = []

    for word, mapped_concepts in CONCEPT_MAP.items():

        normalized_word = clean_text(
            word
        )

        if not normalized_word:
            continue

        # ----------------------------------------------------
        # Single-word concept
        #
        # Exact word matching prevents:
        #
        # "ai" -> matching "against"
        #
        # ----------------------------------------------------

        if " " not in normalized_word:

            if normalized_word in words:

                for concept in mapped_concepts:

                    if concept not in concepts:

                        concepts.append(
                            concept
                        )

        # ----------------------------------------------------
        # Multi-word concept
        # ----------------------------------------------------

        else:

            if normalized_word in cleaned:

                for concept in mapped_concepts:

                    if concept not in concepts:

                        concepts.append(
                            concept
                        )

    return concepts


# ============================================================
# GET SEARCH KEYWORDS
# ============================================================

def get_search_keywords(
    claim,
    maximum=8
):

    keywords = extract_keywords(
        claim
    )

    return keywords[:maximum]


# ============================================================
# ADD QUERY SAFELY
# ============================================================

def add_query(
    queries,
    query
):

    if not query:
        return

    query = query.strip()

    if not query:
        return

    if query not in queries:

        queries.append(
            query
        )


# ============================================================
# SCHOLARSHIP QUERY BUILDER
# ============================================================

def build_scholarship_queries(
    cleaned,
    queries
):

    scholarship_found = any(

        word in cleaned

        for word in [

            "scholarship",
            "scholarships",
            "छात्रवृत्ति",
            "शिष्यवृत्ती"

        ]
    )


    student_found = any(

        word in cleaned

        for word in [

            "student",
            "students",
            "विद्यार्थी",
            "विद्यार्थ्यांसाठी",
            "छात्र",
            "छात्रों"

        ]
    )


    government_found = any(

        word in cleaned

        for word in [

            "government",
            "सरकार",
            "सरकारने",
            "शासन"

        ]
    )


    scheme_found = any(

        word in cleaned

        for word in [

            "scheme",
            "program",
            "programme",
            "योजना"

        ]
    )


    # --------------------------------------------------------
    # Scholarship
    # --------------------------------------------------------

    if scholarship_found:

        add_query(
            queries,
            '"scholarship" AND ("students" OR "education")'
        )

        add_query(
            queries,
            '"scholarship" AND "India"'
        )


    # --------------------------------------------------------
    # Government + Scholarship
    # --------------------------------------------------------

    if (
        scholarship_found
        and government_found
    ):

        add_query(
            queries,
            'government AND scholarship AND students'
        )


    # --------------------------------------------------------
    # Government + Scheme
    # --------------------------------------------------------

    if (
        government_found
        and scheme_found
    ):

        add_query(
            queries,
            'government AND scheme AND students'
        )


# ============================================================
# SPORTS QUERY BUILDER
# ============================================================

def build_sports_queries(
    cleaned,
    keywords,
    queries
):

    sports_words = {

        "cricket",
        "football",
        "soccer",
        "tennis",
        "basketball",
        "baseball",
        "hockey",
        "match",
        "tournament",
        "league",
        "cup",
        "championship",
        "sports",

        "क्रिकेट",
        "मैच"
    }


    sports_found = any(

        word in cleaned

        for word in sports_words
    )


    if not sports_found:
        return


    # --------------------------------------------------------
    # Sports keyword
    # --------------------------------------------------------

    sports_keyword = None

    for word in keywords:

        if word in sports_words:

            sports_keyword = word

            break


    # --------------------------------------------------------
    # Main sports query
    # --------------------------------------------------------

    if len(keywords) >= 2:

        add_query(

            queries,

            " ".join(
                keywords[:6]
            )
        )


    # --------------------------------------------------------
    # Sports-focused query
    # --------------------------------------------------------

    if sports_keyword:

        remaining = [

            word

            for word in keywords

            if word != sports_keyword
        ]


        if remaining:

            add_query(

                queries,

                sports_keyword
                + " "
                + " ".join(
                    remaining[:5]
                )
            )


    # --------------------------------------------------------
    # Quoted query
    # --------------------------------------------------------

    if len(keywords) >= 2:

        quoted_query = " ".join(

            f'"{word}"'

            for word in keywords[:5]
        )


        add_query(
            queries,
            quoted_query
        )


# ============================================================
# LOCATION QUERY
# ============================================================

def build_location_query(
    cleaned,
    keywords,
    queries
):

    india_found = any(

        word in cleaned

        for word in [

            "india",
            "indian",
            "भारत",
            "भारतीय"

        ]
    )


    if not india_found:
        return


    if len(keywords) < 2:
        return


    location_keywords = [

        word

        for word in keywords

        if word not in {

            "india",
            "indian",
            "भारत",
            "भारतीय"

        }
    ]


    if location_keywords:

        add_query(

            queries,

            " ".join(
                location_keywords[:5]
            )
            + " India"
        )


# ============================================================
# GENERAL QUERY BUILDER
# ============================================================

def build_general_queries(
    claim,
    keywords,
    queries
):

    if not keywords:
        return


    # --------------------------------------------------------
    # Main keyword query
    # --------------------------------------------------------

    if len(keywords) >= 2:

        add_query(

            queries,

            " ".join(
                keywords[:6]
            )
        )


    # --------------------------------------------------------
    # Shorter query
    # --------------------------------------------------------

    if len(keywords) >= 3:

        add_query(

            queries,

            " ".join(
                keywords[:4]
            )
        )


    # --------------------------------------------------------
    # Quoted query
    # --------------------------------------------------------

    if len(keywords) >= 2:

        quoted_query = " ".join(

            f'"{word}"'

            for word in keywords[:5]
        )


        add_query(
            queries,
            quoted_query
        )


    # --------------------------------------------------------
    # Original claim fallback
    #
    # Important for multilingual claims.
    # --------------------------------------------------------

    cleaned_claim = clean_text(
        claim
    )

    if cleaned_claim:

        words = cleaned_claim.split()

        if len(words) <= 15:

            add_query(
                queries,
                cleaned_claim
            )


# ============================================================
# MAIN SEARCH QUERY BUILDER
# ============================================================

def build_search_queries(
    claim
):

    cleaned = clean_text(
        claim
    )

    if not cleaned:

        return []


    keywords = get_search_keywords(
        claim,
        maximum=8
    )


    queries = []


    # ========================================================
    # 1. SCHOLARSHIP
    # ========================================================

    build_scholarship_queries(
        cleaned,
        queries
    )


    # ========================================================
    # 2. SPORTS
    # ========================================================

    build_sports_queries(
        cleaned,
        keywords,
        queries
    )


    # ========================================================
    # 3. INDIA / LOCATION
    # ========================================================

    build_location_query(
        cleaned,
        keywords,
        queries
    )


    # ========================================================
    # 4. GENERAL FALLBACK
    # ========================================================

    build_general_queries(
        claim,
        keywords,
        queries
    )


    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    final_queries = []

    for query in queries:

        query = query.strip()

        if not query:
            continue

        if query not in final_queries:

            final_queries.append(
                query
            )


    # ========================================================
    # MAXIMUM 6 QUERIES
    # ========================================================

    return final_queries[:6]


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n========================================"
    )

    print(
        " MULTILINGUAL NEWS SEARCH QUERY BUILDER"
    )

    print(
        "========================================"
    )


    claim = input(
        "\nEnter news claim:\n"
    )


    # --------------------------------------------------------
    # Keywords
    # --------------------------------------------------------

    keywords = extract_keywords(
        claim
    )


    print(
        "\nExtracted keywords:"
    )

    print(
        keywords
    )


    # --------------------------------------------------------
    # Concepts
    # --------------------------------------------------------

    concepts = detect_concepts(
        claim
    )


    print(
        "\nDetected concepts:"
    )

    print(
        concepts
    )


    # --------------------------------------------------------
    # Queries
    # --------------------------------------------------------

    queries = build_search_queries(
        claim
    )


    print(
        "\nGenerated search queries:"
    )


    if not queries:

        print(
            "No queries generated."
        )

    else:

        for index, query in enumerate(

            queries,

            start=1

        ):

            print(
                f"{index}. {query}"
            )