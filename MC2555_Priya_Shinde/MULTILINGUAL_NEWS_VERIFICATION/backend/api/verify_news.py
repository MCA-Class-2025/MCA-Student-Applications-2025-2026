import sys
import time

from pathlib import Path
from datetime import datetime

import pandas as pd
import joblib

from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ============================================================
# PROJECT DIRECTORIES
# ============================================================

API_DIR = (
    PROJECT_ROOT
    / "backend"
    / "api"
)

ML_DIR = (
    PROJECT_ROOT
    / "backend"
    / "ml"
)

FUSION_DIR = (
    PROJECT_ROOT
    / "backend"
    / "fusion"
)

LLM_DIR = (
    PROJECT_ROOT
    / "backend"
    / "llm"
)


# ============================================================
# PYTHON IMPORT PATH
# ============================================================

if str(API_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(API_DIR)
    )


if str(ML_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(ML_DIR)
    )


if str(FUSION_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(FUSION_DIR)
    )


if str(LLM_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(LLM_DIR)
    )


# ============================================================
# IMPORT PROJECT MODULES
# ============================================================

from query_builder import build_search_queries

from news_aggregator import aggregate_news

from evidence_matcher import match_evidence

from fusion_engine import calculate_fusion

from llama_explainer import generate_explanation


# ============================================================
# MODEL PATHS
# ============================================================

MODEL_DIR = (
    PROJECT_ROOT
    / "models"
)

MODEL_FILE = (
    MODEL_DIR
    / "fake_news_model.pkl"
)

VECTORIZER_FILE = (
    MODEL_DIR
    / "tfidf_vectorizer.pkl"
)


# ============================================================
# OUTPUT PATH
# ============================================================

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)

EVIDENCE_FILE = (
    OUTPUT_DIR
    / "realtime_evidence.csv"
)


# ============================================================
# SEARCH SETTINGS
# ============================================================

MAX_QUERIES = 4

REQUEST_DELAY = 2


# ============================================================
# LANGUAGE MAP
# ============================================================

LANGUAGE_MAP = {

    "en": "English",

    "hi": "Hindi",

    "mr": "Marathi"

}


# ============================================================
# LOAD ML MODEL
# ============================================================

print(
    "\nLoading ML model..."
)

model = joblib.load(
    MODEL_FILE
)

vectorizer = joblib.load(
    VECTORIZER_FILE
)

print(
    "ML model loaded successfully."
)


# ============================================================
# LANGUAGE DETECTION
# ============================================================

def detect_language(text):

    try:

        detected_code = detect(
            text
        )

        return LANGUAGE_MAP.get(
            detected_code,
            "English"
        )

    except LangDetectException:

        return "English"


# ============================================================
# ML PREDICTION
# ============================================================

def predict_news(text):

    text_vector = vectorizer.transform(
        [text]
    )

    prediction = model.predict(
        text_vector
    )[0]

    probabilities = model.predict_proba(
        text_vector
    )[0]

    confidence = max(
        probabilities
    )

    return (
        prediction,
        float(confidence)
    )


# ============================================================
# REMOVE DUPLICATE ARTICLES
# ============================================================

def remove_duplicate_articles(
    articles
):

    unique_articles = []

    seen_urls = set()

    seen_titles = set()


    for article in articles:

        if not isinstance(
            article,
            dict
        ):

            continue


        url = str(
            article.get(
                "url",
                ""
            )
        ).strip().lower()


        title = str(
            article.get(
                "title",
                ""
            )
        ).strip().lower()


        # ----------------------------------------------------
        # URL DUPLICATE
        # ----------------------------------------------------

        if url and url in seen_urls:

            continue


        # ----------------------------------------------------
        # TITLE DUPLICATE
        # ----------------------------------------------------

        if title and title in seen_titles:

            continue


        if url:

            seen_urls.add(
                url
            )


        if title:

            seen_titles.add(
                title
            )


        unique_articles.append(
            article
        )


    return unique_articles


# ============================================================
# NORMALIZE API NAME
# ============================================================

def get_api_name(article):

    api_name = (

        article.get(
            "api_source",
            ""
        )

        or

        article.get(
            "api",
            ""
        )

        or

        article.get(
            "api_name",
            ""
        )

        or

        article.get(
            "source_api",
            ""
        )

    )


    return str(
        api_name
    ).strip()


# ============================================================
# ATTACH API NAME TO ARTICLES
# ============================================================

def normalize_article_metadata(
    articles
):

    normalized = []


    for article in articles:

        if not isinstance(
            article,
            dict
        ):

            continue


        item = dict(
            article
        )


        api_name = get_api_name(
            item
        )


        item[
            "api_source"
        ] = api_name


        normalized.append(
            item
        )


    return normalized


# ============================================================
# FILTER EVIDENCE FOR DISPLAY / FUSION
# ============================================================

def filter_meaningful_evidence(
    evidence_results
):

    meaningful = []


    for item in evidence_results:

        if not isinstance(
            item,
            dict
        ):

            continue


        evidence_type = str(
            item.get(
                "evidence_type",
                ""
            )
        ).lower().strip()


        # ====================================================
        # IMPORTANT
        #
        # Contradicting Evidence MUST be preserved.
        #
        # Otherwise the Fusion Engine cannot detect
        # evidence that disproves the claim.
        # ====================================================

        if evidence_type in [

            "strongly supporting",

            "supporting",

            "contradicting evidence",

            "contradicting",

            "related",

            "related - state government",

            "weakly related",

            "strongly related"

        ]:

            meaningful.append(
                item
            )


    return meaningful


# ============================================================
# PREPARE EVIDENCE FOR FUSION
# ============================================================

def prepare_fusion_evidence(
    evidence_results
):

    """
    Prepare evidence for the fusion engine.

    IMPORTANT:

    Semantic similarity alone does NOT prove a claim.

    Exact claim support is required before evidence can be
    treated as genuine supporting evidence.

    State-government evidence cannot support a Central
    Government claim.

    Contradicting evidence is preserved and passed directly
    to the Fusion Engine.
    """

    fusion_evidence = []


    for item in evidence_results:

        evidence = dict(
            item
        )


        evidence_type = str(
            evidence.get(
                "evidence_type",
                ""
            )
        ).strip()


        evidence_type_lower = (
            evidence_type.lower()
        )


        exact_support = bool(
            evidence.get(
                "exact_claim_support",
                False
            )
        )


        state_government = bool(
            evidence.get(
                "state_government",
                False
            )
        )


        central_government = bool(
            evidence.get(
                "central_government",
                False
            )
        )


        final_percentage = float(
            evidence.get(
                "final_evidence_percentage",
                evidence.get(
                    "final_evidence_score",
                    0
                )
            ) or 0
        )


        # ====================================================
        # RULE 1
        # CONTRADICTING EVIDENCE
        #
        # NEVER downgrade or remove contradiction.
        # ====================================================

        if (
            "contradict"
            in evidence_type_lower
        ):

            evidence[
                "evidence_type"
            ] = "Contradicting Evidence"


        # ====================================================
        # RULE 2
        # STATE GOVERNMENT
        # ====================================================

        elif (
            state_government
            and
            not central_government
        ):

            evidence[
                "evidence_type"
            ] = "Related - State Government"


        else:

            # =================================================
            # RULE 3
            # EXACT CLAIM SUPPORT
            # =================================================

            if exact_support:

                if final_percentage >= 70:

                    evidence[
                        "evidence_type"
                    ] = "Strongly Supporting"

                else:

                    evidence[
                        "evidence_type"
                    ] = "Supporting"


            # =================================================
            # RULE 4
            # SUPPORT WITHOUT EXACT SUPPORT
            # =================================================

            elif (
                evidence_type_lower
                in [
                    "supporting",
                    "strongly supporting"
                ]
            ):

                evidence[
                    "evidence_type"
                ] = "Related"


        fusion_evidence.append(
            evidence
        )


    return fusion_evidence


# ============================================================
# SAVE EVIDENCE
# ============================================================

def save_evidence(
    rows
):

    if not rows:

        return


    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


    new_df = pd.DataFrame(
        rows
    )


    # ========================================================
    # EXISTING CSV
    # ========================================================

    if EVIDENCE_FILE.exists():

        try:

            old_df = pd.read_csv(
                EVIDENCE_FILE
            )


            final_df = pd.concat(

                [
                    old_df,
                    new_df
                ],

                ignore_index=True

            )


        except Exception:

            final_df = new_df

    else:

        final_df = new_df


    # ========================================================
    # REMOVE DUPLICATE URLS
    # ========================================================

    if "url" in final_df.columns:

        final_df = final_df.drop_duplicates(

            subset=[
                "url"
            ],

            keep="last"

        )


    # ========================================================
    # SAVE CSV
    # ========================================================

    final_df.to_csv(

        EVIDENCE_FILE,

        index=False,

        encoding="utf-8-sig"

    )


# ============================================================
# NEWS VERIFICATION
# ============================================================

def verify_news(
    claim
):

    print(
        "\n========================================"
    )

    print(
        " MULTILINGUAL NEWS VERIFICATION"
    )

    print(
        "========================================"
    )


    # ========================================================
    # STEP 1 — LANGUAGE DETECTION
    # ========================================================

    language = detect_language(
        claim
    )


    print(
        "\nDetected Language:",
        language
    )


    # ========================================================
    # STEP 2 — ML PREDICTION
    # ========================================================

    prediction, ml_confidence = predict_news(
        claim
    )


    print(
        "\nML Prediction:",
        prediction
    )

    print(
        "ML Confidence:",
        f"{ml_confidence * 100:.2f}%"
    )


    # ========================================================
    # STEP 3 — QUERY BUILDER
    # ========================================================

    queries = build_search_queries(
        claim
    )


    print(
        "\nGenerated Search Queries:"
    )


    if not queries:

        print(
            "No suitable search queries generated."
        )


    else:

        for index, query in enumerate(

            queries[:MAX_QUERIES],

            start=1

        ):

            print(
                f"{index}. {query}"
            )


    # ========================================================
    # STEP 4 — MULTI-API NEWS SEARCH
    # ========================================================

    print(
        "\n========================================"
    )

    print(
        " MULTI-API NEWS SEARCH"
    )

    print(
        "========================================"
    )


    all_articles = []


    if queries:

        for index, query in enumerate(

            queries[:MAX_QUERIES],

            start=1

        ):

            print(
                "\n----------------------------------------"
            )

            print(
                f"SEARCH QUERY {index}/{min(len(queries), MAX_QUERIES)}"
            )

            print(
                "----------------------------------------"
            )

            print(
                "Query:",
                query
            )


            try:

                aggregated = aggregate_news(

                    query=query,

                    language=language

                )


                articles = aggregated.get(
                    "articles",
                    []
                )


                articles = normalize_article_metadata(
                    articles
                )


                print(
                    "\nArticles received from aggregator:",
                    len(articles)
                )


                # =================================================
                # API DISTRIBUTION
                # =================================================

                api_counts = {}


                for article in articles:

                    api_name = get_api_name(
                        article
                    )


                    if not api_name:

                        api_name = "Unknown"


                    api_counts[
                        api_name
                    ] = (

                        api_counts.get(
                            api_name,
                            0
                        )

                        + 1

                    )


                if api_counts:

                    print(
                        "API distribution:"
                    )


                    for api_name, count in api_counts.items():

                        print(
                            f"  {api_name}: {count}"
                        )


                all_articles.extend(
                    articles
                )


            except Exception as e:

                print(
                    "\nAggregator error:"
                )

                print(
                    str(e)
                )


            # =================================================
            # DELAY
            # =================================================

            if index < min(
                len(queries),
                MAX_QUERIES
            ):

                print(
                    "\nWaiting before next search query..."
                )

                time.sleep(
                    REQUEST_DELAY
                )


    # ========================================================
    # STEP 5 — GLOBAL DEDUPLICATION
    # ========================================================

    all_articles = remove_duplicate_articles(
        all_articles
    )


    # ========================================================
    # ARTICLE COLLECTION
    # ========================================================

    print(
        "\n========================================"
    )

    print(
        " ARTICLE COLLECTION"
    )

    print(
        "========================================"
    )


    print(
        "\nTotal unique articles collected:",
        len(all_articles)
    )


    if not all_articles:

        print(
            "\nNo current-news articles were returned."
        )

        print(
            "No broad unrelated-news fallback will be used."
        )


    # ========================================================
    # STEP 6 — ADVANCED EVIDENCE MATCHING
    # ========================================================

    print(
        "\n========================================"
    )

    print(
        " ADVANCED EVIDENCE MATCHING"
    )

    print(
        "========================================"
    )


    if all_articles:

        print(
            "\nRunning semantic + component evidence matching..."
        )


        evidence_results = match_evidence(

            claim,

            all_articles

        )


    else:

        evidence_results = []


    # ========================================================
    # STEP 7 — FILTER EVIDENCE
    # ========================================================

    meaningful_evidence = (
        filter_meaningful_evidence(
            evidence_results
        )
    )


    print(
        "\nMeaningful evidence:",
        len(meaningful_evidence)
    )


    # ========================================================
    # STEP 8 — PREPARE STRICT FUSION EVIDENCE
    # ========================================================

    fusion_evidence = prepare_fusion_evidence(
        meaningful_evidence
    )


    # ========================================================
    # SHOW EVIDENCE DISTRIBUTION
    # ========================================================

    evidence_distribution = {}


    for evidence in fusion_evidence:

        evidence_type = str(
            evidence.get(
                "evidence_type",
                "Unknown"
            )
        )


        evidence_distribution[
            evidence_type
        ] = (

            evidence_distribution.get(
                evidence_type,
                0
            )

            + 1

        )


    print(
        "\nEvidence distribution after filtering:"
    )


    if evidence_distribution:

        for evidence_type, count in evidence_distribution.items():

            print(
                f"  {evidence_type}: {count}"
            )

    else:

        print(
            "  No evidence"
        )


    # ========================================================
    # ACTUAL SUPPORTING EVIDENCE
    # ========================================================

    actual_supporting = [

        item

        for item in fusion_evidence

        if str(
            item.get(
                "evidence_type",
                ""
            )
        ).lower()

        in [

            "supporting",

            "strongly supporting"

        ]

    ]


    # ========================================================
    # ACTUAL CONTRADICTING EVIDENCE
    # ========================================================

    actual_contradicting = [

        item

        for item in fusion_evidence

        if (
            "contradict"
            in str(
                item.get(
                    "evidence_type",
                    ""
                )
            ).lower()
        )

    ]


    print(
        "\nActual supporting evidence after strict verification:",
        len(actual_supporting)
    )


    print(
        "Actual contradicting evidence after strict verification:",
        len(actual_contradicting)
    )


    # ========================================================
    # STEP 9 — DATA FUSION
    # ========================================================

    fusion_result = calculate_fusion(

        ml_prediction=prediction,

        ml_confidence=ml_confidence,

        evidence_results=fusion_evidence

    )


    # ========================================================
    # STEP 10 — LLAMA 3.2 AI EXPLANATION
    # ========================================================

    print(
        "\n========================================"
    )

    print(
        " LLAMA 3.2 AI EXPLANATION"
    )

    print(
        "========================================"
    )


    try:

        llm_explanation = generate_explanation(

            claim=claim,

            verdict=fusion_result[
                "verdict"
            ],

            ml_prediction=fusion_result[
                "ml_prediction"
            ],

            ml_confidence=fusion_result[
                "ml_confidence"
            ],

            evidence_score=fusion_result[
                "evidence_score"
            ],

            evidence_status=fusion_result[
                "evidence_status"
            ]

        )


    except Exception as e:

        print(
            "\nLlama explanation error:"
        )

        print(
            str(e)
        )

        llm_explanation = (
            "Llama explanation is currently unavailable."
        )


    print(
        "\nLlama Explanation:"
    )

    print(
        llm_explanation
    )


    # ========================================================
    # STEP 11 — SAVE CSV
    # ========================================================

    csv_rows = []


    for evidence in meaningful_evidence:

        row = {

            "claim":
                claim,

            "language":
                language,

            "ml_prediction":
                prediction,

            "ml_confidence":
                round(
                    ml_confidence * 100,
                    2
                ),

            "title":
                evidence.get(
                    "title",
                    ""
                ),

            "source":
                evidence.get(
                    "source",
                    ""
                ),

            "api_source":
                evidence.get(
                    "api_source",
                    ""
                ),

            "published_at":
                evidence.get(
                    "publishedAt",
                    ""
                ),

            "url":
                evidence.get(
                    "url",
                    ""
                ),

            "similarity_score":
                evidence.get(
                    "similarity_score",
                    0
                ),

            "similarity_percentage":
                evidence.get(
                    "similarity_percentage",
                    0
                ),

            "component_score":
                evidence.get(
                    "component_score",
                    0
                ),

            "component_percentage":
                evidence.get(
                    "component_percentage",
                    0
                ),

            "requirement_score":
                evidence.get(
                    "requirement_score",
                    0
                ),

            "requirement_percentage":
                evidence.get(
                    "requirement_percentage",
                    0
                ),

            "final_evidence_score":
                evidence.get(
                    "final_evidence_score",
                    0
                ),

            "final_evidence_percentage":
                evidence.get(
                    "final_evidence_percentage",
                    0
                ),

            "exact_claim_support":
                evidence.get(
                    "exact_claim_support",
                    False
                ),

            "central_government":
                evidence.get(
                    "central_government",
                    False
                ),

            "state_government":
                evidence.get(
                    "state_government",
                    False
                ),

            "india_confirmed":
                evidence.get(
                    "india_confirmed",
                    False
                ),

            "new_announcement":
                evidence.get(
                    "new_announcement",
                    False
                ),

            "weather_required":
                evidence.get(
                    "weather_required",
                    False
                ),

            "weather_confirmed":
                evidence.get(
                    "weather_confirmed",
                    False
                ),

            "weather_warning_required":
                evidence.get(
                    "weather_warning_required",
                    False
                ),

            "weather_warning_confirmed":
                evidence.get(
                    "weather_warning_confirmed",
                    False
                ),

            "weather_state_match":
                evidence.get(
                    "weather_state_match",
                    False
                ),

            "weather_direct_contradiction":
                evidence.get(
                    "weather_direct_contradiction",
                    False
                ),

            "exact_claim_support":
                evidence.get(
                    "exact_claim_support",
                    False
                ),

            "evidence_type":
                evidence.get(
                    "evidence_type",
                    ""
                ),

            "matched_components":
                ", ".join(
                    evidence.get(
                        "matched_components",
                        []
                    )
                ),

            "retrieved_at":
                datetime.now().isoformat()

        }


        csv_rows.append(
            row
        )


    save_evidence(
        csv_rows
    )


    # ========================================================
    # STEP 12 — VERIFICATION RESULTS
    # ========================================================

    print(
        "\n========================================"
    )

    print(
        " VERIFICATION RESULTS"
    )

    print(
        "========================================"
    )


    print(
        "\nFinal ML Prediction:",
        prediction
    )


    print(
        "ML Confidence:",
        f"{ml_confidence * 100:.2f}%"
    )


    print(
        "Unique Articles Found:",
        len(all_articles)
    )


    # ========================================================
    # STEP 13 — DATA FUSION RESULT
    # ========================================================

    print(
        "\n========================================"
    )

    print(
        " DATA FUSION RESULT"
    )

    print(
        "========================================"
    )


    print(
        "\nML Prediction:",
        fusion_result[
            "ml_prediction"
        ]
    )


    print(
        "ML Confidence:",
        f'{fusion_result["ml_confidence"]:.2f}%'
    )


    print(
        "ML Real Score:",
        f'{fusion_result["ml_real_score"]:.2f}%'
    )


    print(
        "Evidence Score:",
        f'{fusion_result["evidence_score"]:.2f}%'
    )


    print(
        "Final Fusion Score:",
        f'{fusion_result["final_score"]:.2f}%'
    )


    print(
        "Evidence Status:",
        fusion_result[
            "evidence_status"
        ]
    )


    print(
        "Supporting Evidence:",
        fusion_result[
            "supporting_evidence_count"
        ]
    )


    print(
        "Related Evidence:",
        fusion_result[
            "related_evidence_count"
        ]
    )


    print(
        "Contradicting Evidence:",
        fusion_result[
            "contradicting_evidence_count"
        ]
    )


    print(
        "Strongest Support:",
        f'{fusion_result["strongest_support"]:.2f}%'
    )


    print(
        "Strongest Contradiction:",
        f'{fusion_result["strongest_contradiction"]:.2f}%'
    )


    print(
        "Final Verdict:",
        fusion_result[
            "verdict"
        ]
    )


    # ========================================================
    # STEP 14 — REAL-TIME EVIDENCE
    # ========================================================

    if meaningful_evidence:

        print(
            "\n========================================"
        )

        print(
            " REAL-TIME EVIDENCE"
        )

        print(
            "========================================"
        )


        for index, evidence in enumerate(

            meaningful_evidence[:10],

            start=1

        ):

            print(
                "\n----------------------------------------"
            )

            print(
                f"Evidence {index}"
            )

            print(
                "----------------------------------------"
            )


            print(
                "Title:",
                evidence.get(
                    "title",
                    ""
                )
            )


            print(
                "Source:",
                evidence.get(
                    "source",
                    ""
                )
            )


            print(
                "API:",
                evidence.get(
                    "api_source",
                    ""
                )
            )


            print(
                "Published:",
                evidence.get(
                    "publishedAt",
                    ""
                )
            )


            print(
                "Semantic Similarity:",
                f'{evidence.get("similarity_percentage", 0):.2f}%'
            )


            print(
                "Component Match:",
                f'{evidence.get("component_percentage", 0):.2f}%'
            )


            print(
                "Requirement Match:",
                f'{evidence.get("requirement_percentage", 0):.2f}%'
            )


            print(
                "Final Evidence Score:",
                f'{evidence.get("final_evidence_percentage", 0):.2f}%'
            )


            print(
                "Exact Claim Support:",
                evidence.get(
                    "exact_claim_support",
                    False
                )
            )


            print(
                "Central Government:",
                evidence.get(
                    "central_government",
                    False
                )
            )


            print(
                "State Government:",
                evidence.get(
                    "state_government",
                    False
                )
            )


            print(
                "Weather Required:",
                evidence.get(
                    "weather_required",
                    False
                )
            )


            print(
                "Weather Confirmed:",
                evidence.get(
                    "weather_confirmed",
                    False
                )
            )


            print(
                "Weather Warning Required:",
                evidence.get(
                    "weather_warning_required",
                    False
                )
            )


            print(
                "Weather Warning Confirmed:",
                evidence.get(
                    "weather_warning_confirmed",
                    False
                )
            )


            print(
                "Weather State Match:",
                evidence.get(
                    "weather_state_match",
                    False
                )
            )


            print(
                "Weather Direct Contradiction:",
                evidence.get(
                    "weather_direct_contradiction",
                    False
                )
            )


            print(
                "Matched Components:",
                ", ".join(
                    evidence.get(
                        "matched_components",
                        []
                    )
                )
            )


            print(
                "Evidence Type:",
                evidence.get(
                    "evidence_type",
                    ""
                )
            )


            print(
                "URL:",
                evidence.get(
                    "url",
                    ""
                )
            )


    else:

        print(
            "\nNo relevant real-time evidence found."
        )


    # ========================================================
    # CSV LOCATION
    # ========================================================

    print(
        "\n========================================"
    )

    print(
        " REAL-TIME EVIDENCE CSV"
    )

    print(
        "========================================"
    )


    print(
        EVIDENCE_FILE
    )


    # ========================================================
    # COMPLETED
    # ========================================================

    print(
        "\n========================================"
    )

    print(
        " VERIFICATION COMPLETED"
    )

    print(
        "========================================"
    )


    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {

        "claim":
            claim,

        "language":
            language,

        "ml_prediction":
            prediction,

        "ml_confidence":
            ml_confidence,

        "articles_found":
            len(all_articles),

        "evidence":
            meaningful_evidence,

        "fusion_evidence":
            fusion_evidence,

        "fusion":
            fusion_result,

        "llm_explanation":
            llm_explanation

    }


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    claim = input(
        "\nEnter news claim/article:\n"
    )


    if not claim.strip():

        print(
            "\nPlease enter a valid news claim."
        )

    else:

        verify_news(
            claim
        )