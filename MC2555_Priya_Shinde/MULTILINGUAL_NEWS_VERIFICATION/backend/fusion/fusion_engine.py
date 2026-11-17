# ============================================================
# DATA FUSION ENGINE
# ============================================================
#
# Combines:
#
#   ML prediction
#          +
#   Real-time evidence
#          +
#   Advanced evidence matcher
#
# Final result:
#
#   Likely Real
#   Likely Fake
#   Needs Verification
#
# IMPORTANT:
#   Related evidence is NOT treated as proof.
#   Only genuine Supporting / Strongly Supporting evidence
#   can positively verify a claim.
#
# ============================================================


# ============================================================
# CONFIGURATION
# ============================================================

ML_WEIGHT = 0.40
EVIDENCE_WEIGHT = 0.60

# Evidence thresholds
STRONG_SUPPORT_THRESHOLD = 0.70
SUPPORT_THRESHOLD = 0.60
CONTRADICTION_THRESHOLD = 0.65


# ============================================================
# NORMALIZE SCORE
# ============================================================

def normalize_score(score):

    try:

        score = float(score)

    except (
        TypeError,
        ValueError
    ):

        return 0.0

    # Percentage -> decimal

    if score > 1:

        score = score / 100.0

    return max(
        0.0,
        min(
            1.0,
            score
        )
    )


# ============================================================
# NORMALIZE ML PREDICTION
# ============================================================

def normalize_prediction(prediction):

    prediction = str(
        prediction
    ).strip().lower()

    if prediction == "real":

        return "Real"

    if prediction == "fake":

        return "Fake"

    return "Unknown"


# ============================================================
# GET EVIDENCE SCORE
# ============================================================

def get_evidence_score(item):

    # --------------------------------------------------------
    # Prefer advanced evidence matcher score
    # --------------------------------------------------------

    score = item.get(
        "final_evidence_score",
        None
    )

    # --------------------------------------------------------
    # Backward compatibility
    # --------------------------------------------------------

    if score is None:

        score = item.get(
            "similarity_score",
            0.0
        )

    return normalize_score(
        score
    )


# ============================================================
# CLASSIFY EVIDENCE
# ============================================================

def classify_evidence_item(item):

    evidence_type = str(
        item.get(
            "evidence_type",
            ""
        )
    ).strip().lower()


    # ========================================================
    # CONTRADICTION
    # ========================================================

    if (
        "contradict" in evidence_type
        or
        bool(
            item.get(
                "sports_contradicted",
                False
            )
        )
    ):

        return "contradicting"


    # ========================================================
    # STRONG SUPPORT
    # ========================================================

    if (
        "strongly supporting"
        in evidence_type
    ):

        return "strong_supporting"


    # ========================================================
    # NORMAL SUPPORT
    # ========================================================

    if (
        evidence_type == "supporting"
        or
        evidence_type == "support"
    ):

        return "supporting"


    # ========================================================
    # RELATED
    # ========================================================

    if (
        "related"
        in evidence_type
        or
        "weakly"
        in evidence_type
    ):

        return "related"


    # ========================================================
    # UNKNOWN
    # ========================================================

    return "unknown"


# ============================================================
# CALCULATE EVIDENCE SCORE
# ============================================================

def calculate_evidence_score(
    supporting_scores,
    strong_supporting_scores,
    related_scores,
    contradicting_scores
):

    # ========================================================
    # CONTRADICTION HAS HIGHEST PRIORITY
    # ========================================================

    if contradicting_scores:

        return (
            -max(
                contradicting_scores
            ),
            "Contradicting Evidence"
        )


    # ========================================================
    # STRONG SUPPORT
    # ========================================================

    if strong_supporting_scores:

        return (
            max(
                strong_supporting_scores
            ),
            "Strong Supporting Evidence"
        )


    # ========================================================
    # NORMAL SUPPORT
    # ========================================================

    if supporting_scores:

        return (
            max(
                supporting_scores
            ),
            "Supporting Evidence"
        )


    # ========================================================
    # RELATED
    #
    # Related evidence is deliberately reduced because
    # similarity does not mean verification.
    # ========================================================

    if related_scores:

        return (
            max(
                related_scores
            ) * 0.50,
            "Related but not conclusive"
        )


    # ========================================================
    # NO EVIDENCE
    # ========================================================

    return (
        0.0,
        "No Evidence"
    )


# ============================================================
# CALCULATE FUSION
# ============================================================

def calculate_fusion(
    ml_prediction,
    ml_confidence,
    evidence_results
):

    """
    DATA FUSION ENGINE

    ML contribution       = 40%
    Evidence contribution = 60%

    Important principles:

    1. ML alone does not prove a news claim.

    2. Related evidence does not prove the claim.

    3. Genuine supporting evidence can increase confidence.

    4. Contradicting evidence can strongly reduce confidence.

    5. No evidence results in Needs Verification.

    6. The strongest genuine evidence is used as the primary
       evidence signal.

    7. Evidence classification is performed before fusion.
    """


    # ========================================================
    # NORMALIZE ML
    # ========================================================

    ml_prediction = normalize_prediction(
        ml_prediction
    )

    ml_confidence = normalize_score(
        ml_confidence
    )


    # ========================================================
    # ML REAL SCORE
    # ========================================================

    if ml_prediction == "Real":

        ml_real_score = ml_confidence

    elif ml_prediction == "Fake":

        ml_real_score = (
            1.0
            -
            ml_confidence
        )

    else:

        ml_real_score = 0.50


    # ========================================================
    # EVIDENCE ARRAYS
    # ========================================================

    supporting_scores = []

    strong_supporting_scores = []

    related_scores = []

    contradicting_scores = []


    # ========================================================
    # PROCESS EVIDENCE
    # ========================================================

    for item in evidence_results or []:

        if not isinstance(
            item,
            dict
        ):

            continue


        evidence_class = (
            classify_evidence_item(
                item
            )
        )


        score = get_evidence_score(
            item
        )


        # ----------------------------------------------------
        # Strong supporting
        # ----------------------------------------------------

        if evidence_class == "strong_supporting":

            strong_supporting_scores.append(
                score
            )

            supporting_scores.append(
                score
            )


        # ----------------------------------------------------
        # Supporting
        # ----------------------------------------------------

        elif evidence_class == "supporting":

            supporting_scores.append(
                score
            )


        # ----------------------------------------------------
        # Contradicting
        # ----------------------------------------------------

        elif evidence_class == "contradicting":

            contradicting_scores.append(
                score
            )


        # ----------------------------------------------------
        # Related
        # ----------------------------------------------------

        elif evidence_class == "related":

            related_scores.append(
                score
            )


    # ========================================================
    # COUNTS
    # ========================================================

    supporting_count = len(
        supporting_scores
    )

    related_count = len(
        related_scores
    )

    contradicting_count = len(
        contradicting_scores
    )


    # ========================================================
    # STRONGEST VALUES
    # ========================================================

    strongest_support = (

        max(
            supporting_scores
        )

        if supporting_scores

        else 0.0
    )


    strongest_strong_support = (

        max(
            strong_supporting_scores
        )

        if strong_supporting_scores

        else 0.0
    )


    strongest_related = (

        max(
            related_scores
        )

        if related_scores

        else 0.0
    )


    strongest_contradiction = (

        max(
            contradicting_scores
        )

        if contradicting_scores

        else 0.0
    )


    # ========================================================
    # EVIDENCE SCORE
    # ========================================================

    evidence_score, evidence_status = (
        calculate_evidence_score(

            supporting_scores=
                supporting_scores,

            strong_supporting_scores=
                strong_supporting_scores,

            related_scores=
                related_scores,

            contradicting_scores=
                contradicting_scores

        )
    )


    # ========================================================
    # FUSION SCORE
    # ========================================================

    final_score = (

        (
            ml_real_score
            *
            ML_WEIGHT
        )

        +

        (
            evidence_score
            *
            EVIDENCE_WEIGHT
        )

    )


    # ========================================================
    # CLAMP FINAL SCORE
    # ========================================================

    final_score = max(
        0.0,
        min(
            1.0,
            final_score
        )
    )


    # ========================================================
    # FINAL VERDICT
    # ========================================================

    verdict = determine_verdict(

        ml_prediction=
            ml_prediction,

        ml_confidence=
            ml_confidence,

        ml_real_score=
            ml_real_score,

        evidence_score=
            evidence_score,

        strongest_support=
            strongest_support,

        strongest_strong_support=
            strongest_strong_support,

        strongest_contradiction=
            strongest_contradiction,

        supporting_count=
            supporting_count,

        contradicting_count=
            contradicting_count,

        related_count=
            related_count

    )


    # ========================================================
    # DISPLAY EVIDENCE SCORE
    # ========================================================

    display_evidence_score = max(
        0.0,
        evidence_score
    )


    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {

        "ml_prediction":
            ml_prediction,

        "ml_confidence":
            round(
                ml_confidence * 100,
                2
            ),

        "ml_real_score":
            round(
                ml_real_score * 100,
                2
            ),

        "evidence_score":
            round(
                display_evidence_score * 100,
                2
            ),

        "final_score":
            round(
                final_score * 100,
                2
            ),

        "evidence_status":
            evidence_status,

        "supporting_evidence_count":
            supporting_count,

        "related_evidence_count":
            related_count,

        "contradicting_evidence_count":
            contradicting_count,

        "strongest_support":
            round(
                strongest_support * 100,
                2
            ),

        "strongest_contradiction":
            round(
                strongest_contradiction * 100,
                2
            ),

        "verdict":
            verdict

    }


# ============================================================
# FINAL VERDICT LOGIC
# ============================================================

def determine_verdict(
    ml_prediction,
    ml_confidence,
    ml_real_score,
    evidence_score,
    strongest_support,
    strongest_strong_support,
    strongest_contradiction,
    supporting_count,
    contradicting_count,
    related_count
):

    # ========================================================
    # RULE 1 — STRONG CONTRADICTION
    #
    # Contradicting evidence has highest priority.
    # ========================================================

    if (
        contradicting_count > 0
        and
        strongest_contradiction >=
            CONTRADICTION_THRESHOLD
    ):

        return "Likely Fake"


    # ========================================================
    # RULE 2 — MODERATE CONTRADICTION
    # ========================================================

    if (
        contradicting_count > 0
        and
        strongest_contradiction >= 0.50
    ):

        if ml_prediction == "Fake":

            return "Likely Fake"

        return "Needs Verification"


    # ========================================================
    # RULE 3 — STRONG SUPPORTING EVIDENCE
    #
    # IMPORTANT CHANGE:
    #
    # The evidence matcher currently produces genuine
    # Strongly Supporting evidence at 70%.
    #
    # Therefore 70% is sufficient when:
    #
    #   - evidence is Strongly Supporting
    #   - ML says Real with >= 50% confidence
    #
    # ========================================================

    if (
        strong_supporting_scores_exist(
            strongest_strong_support
        )
        and
        strongest_strong_support >=
            STRONG_SUPPORT_THRESHOLD
        and
        evidence_score >=
            STRONG_SUPPORT_THRESHOLD
    ):

        # ----------------------------------------------------
        # Real ML + strong evidence
        # ----------------------------------------------------

        if (
            ml_prediction == "Real"
            and
            ml_confidence >= 0.50
        ):

            return "Likely Real"


        # ----------------------------------------------------
        # Fake ML + strong real-time evidence
        #
        # Allow evidence to override only a relatively weak
        # Fake ML prediction.
        # ----------------------------------------------------

        if (
            ml_prediction == "Fake"
            and
            ml_confidence < 0.70
        ):

            return "Likely Real"


        return "Needs Verification"


    # ========================================================
    # RULE 4 — NORMAL SUPPORTING EVIDENCE
    # ========================================================

    if (
        supporting_count > 0
        and
        strongest_support >=
            SUPPORT_THRESHOLD
        and
        evidence_score >=
            SUPPORT_THRESHOLD
    ):

        if (
            ml_prediction == "Real"
            and
            ml_confidence >= 0.60
        ):

            return "Likely Real"


        if (
            ml_prediction == "Fake"
            and
            ml_confidence < 0.60
        ):

            return "Likely Real"


        return "Needs Verification"


    # ========================================================
    # RULE 5 — STRONG ML FAKE WITHOUT REAL SUPPORT
    # ========================================================

    if (
        ml_prediction == "Fake"
        and
        ml_confidence >= 0.70
        and
        supporting_count == 0
        and
        contradicting_count == 0
    ):

        return "Likely Fake"


    # ========================================================
    # RULE 6 — STRONG ML REAL + SUPPORT
    # ========================================================

    if (
        ml_prediction == "Real"
        and
        ml_confidence >= 0.80
        and
        contradicting_count == 0
        and
        supporting_count > 0
        and
        strongest_support >= 0.60
    ):

        return "Likely Real"


    # ========================================================
    # RULE 7 — RELATED ONLY
    # ========================================================

    if (
        related_count > 0
        and
        supporting_count == 0
        and
        contradicting_count == 0
    ):

        return "Needs Verification"


    # ========================================================
    # RULE 8 — NO EVIDENCE
    # ========================================================

    if (
        supporting_count == 0
        and
        contradicting_count == 0
        and
        related_count == 0
    ):

        return "Needs Verification"


    # ========================================================
    # DEFAULT
    # ========================================================

    return "Needs Verification"


# ============================================================
# HELPER
# ============================================================

def strong_supporting_scores_exist(
    strongest_strong_support
):

    return (
        strongest_strong_support > 0
    )


# ============================================================
# TEST HELPER
# ============================================================

def print_result(
    title,
    result
):

    print(
        "\n----------------------------------------"
    )

    print(
        title
    )

    print(
        "----------------------------------------"
    )

    print(
        "ML Prediction:",
        result[
            "ml_prediction"
        ]
    )

    print(
        "ML Confidence:",
        f'{result["ml_confidence"]:.2f}%'
    )

    print(
        "ML Real Score:",
        f'{result["ml_real_score"]:.2f}%'
    )

    print(
        "Evidence Score:",
        f'{result["evidence_score"]:.2f}%'
    )

    print(
        "Final Fusion Score:",
        f'{result["final_score"]:.2f}%'
    )

    print(
        "Evidence Status:",
        result[
            "evidence_status"
        ]
    )

    print(
        "Supporting Evidence:",
        result[
            "supporting_evidence_count"
        ]
    )

    print(
        "Related Evidence:",
        result[
            "related_evidence_count"
        ]
    )

    print(
        "Contradicting Evidence:",
        result[
            "contradicting_evidence_count"
        ]
    )

    print(
        "Strongest Support:",
        f'{result["strongest_support"]:.2f}%'
    )

    print(
        "Strongest Contradiction:",
        f'{result["strongest_contradiction"]:.2f}%'
    )

    print(
        "Final Verdict:",
        result[
            "verdict"
        ]
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n========================================"
    )

    print(
        " DATA FUSION ENGINE TEST"
    )

    print(
        "========================================"
    )


    # ========================================================
    # TEST 1
    # FAKE ML + STRONG SUPPORTING EVIDENCE
    # ========================================================

    result_1 = calculate_fusion(

        ml_prediction="Fake",

        ml_confidence=69.16,

        evidence_results=[

            {
                "similarity_score":
                    0.8137,

                "final_evidence_score":
                    0.8597,

                "evidence_type":
                    "Strongly Supporting"
            }

        ]

    )


    print_result(
        "TEST 1 - Fake ML + Strong Supporting Evidence",
        result_1
    )


    # ========================================================
    # TEST 2
    # FAKE ML + STRONG CONTRADICTION
    # ========================================================

    result_2 = calculate_fusion(

        ml_prediction="Fake",

        ml_confidence=69.16,

        evidence_results=[

            {
                "similarity_score":
                    0.7066,

                "final_evidence_score":
                    0.6773,

                "evidence_type":
                    "Contradicting Evidence",

                "sports_contradicted":
                    True
            }

        ]

    )


    print_result(
        "TEST 2 - Fake ML + Contradicting Evidence",
        result_2
    )


    # ========================================================
    # TEST 3
    # REAL ML + STRONG SUPPORT
    # ========================================================

    result_3 = calculate_fusion(

        ml_prediction="Real",

        ml_confidence=80.0,

        evidence_results=[

            {
                "similarity_score":
                    0.80,

                "final_evidence_score":
                    0.85,

                "evidence_type":
                    "Strongly Supporting"
            }

        ]

    )


    print_result(
        "TEST 3 - Real ML + Strong Supporting Evidence",
        result_3
    )


    # ========================================================
    # TEST 4
    # REAL ML + STRONG CONTRADICTION
    # ========================================================

    result_4 = calculate_fusion(

        ml_prediction="Real",

        ml_confidence=80.0,

        evidence_results=[

            {
                "similarity_score":
                    0.80,

                "final_evidence_score":
                    0.85,

                "evidence_type":
                    "Contradicting Evidence",

                "sports_contradicted":
                    True
            }

        ]

    )


    print_result(
        "TEST 4 - Real ML + Strong Contradicting Evidence",
        result_4
    )


    # ========================================================
    # TEST 5
    # RELATED ONLY
    # ========================================================

    result_5 = calculate_fusion(

        ml_prediction="Fake",

        ml_confidence=69.16,

        evidence_results=[

            {
                "similarity_score":
                    0.58,

                "final_evidence_score":
                    0.54,

                "evidence_type":
                    "Related"
            },

            {
                "similarity_score":
                    0.52,

                "final_evidence_score":
                    0.50,

                "evidence_type":
                    "Related"
            }

        ]

    )


    print_result(
        "TEST 5 - Related Evidence Only",
        result_5
    )


    # ========================================================
    # TEST 6
    # NO EVIDENCE
    # ========================================================

    result_6 = calculate_fusion(

        ml_prediction="Real",

        ml_confidence=54.52,

        evidence_results=[]

    )


    print_result(
        "TEST 6 - No Evidence",
        result_6
    )


    # ========================================================
    # TEST 7
    # YOUR CURRENT WEATHER CASE
    # ========================================================

    result_7 = calculate_fusion(

        ml_prediction="Real",

        ml_confidence=73.04,

        evidence_results=[

            {
                "similarity_score":
                    0.2478,

                "final_evidence_score":
                    0.70,

                "evidence_type":
                    "Strongly Supporting",

                "exact_claim_support":
                    True
            },

            {
                "similarity_score":
                    0.1936,

                "final_evidence_score":
                    0.70,

                "evidence_type":
                    "Strongly Supporting",

                "exact_claim_support":
                    True
            }

        ]

    )


    print_result(
        "TEST 7 - Maharashtra Weather Case",
        result_7
    )


    print(
        "\n========================================"
    )

    print(
        " FUSION TEST COMPLETED"
    )

    print(
        "========================================"
    )