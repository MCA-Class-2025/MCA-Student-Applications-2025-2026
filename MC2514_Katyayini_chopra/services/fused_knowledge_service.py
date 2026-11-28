import pandas as pd
from pathlib import Path


# =========================================================
# FUSED DATASET
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

FUSED_DATASET = (
    BASE_DIR
    / "data"
    / "fixai_fused_dataset.csv"
)


# =========================================================
# LOAD DATASET
# =========================================================

def load_fused_dataset():

    if not FUSED_DATASET.exists():

        return pd.DataFrame()

    return pd.read_csv(
        FUSED_DATASET
    )


# =========================================================
# SEARCH RELEVANT FUSED RECORDS
# =========================================================

def search_fused_knowledge(
    issue=None,
    category=None,
    service_type=None,
    element=None,
    limit=5
):

    df = load_fused_dataset()

    if df.empty:

        return []


    # Internal relevance score
    df["_score"] = 0


    # =====================================================
    # SERVICE TYPE MATCH
    # =====================================================

    if (
        service_type
        and "service_type" in df.columns
    ):

        mask = (
            df["service_type"]
            .astype(str)
            .str.lower()
            .str.strip()
            ==
            str(service_type)
            .lower()
            .strip()
        )

        df.loc[
            mask,
            "_score"
        ] += 4


    # =====================================================
    # ELEMENT MATCH
    # =====================================================

    if (
        element
        and "element" in df.columns
    ):

        mask = (
            df["element"]
            .astype(str)
            .str.lower()
            .str.strip()
            ==
            str(element)
            .lower()
            .strip()
        )

        df.loc[
            mask,
            "_score"
        ] += 3


    # =====================================================
    # DEFECT / ISSUE MATCH
    # =====================================================

    if (
        issue
        and "defect" in df.columns
    ):

        issue_text = (
            str(issue)
            .lower()
            .strip()
        )

        defect_text = (
            df["defect"]
            .astype(str)
            .str.lower()
            .str.strip()
        )


        # Exact match
        exact_match = (
            defect_text
            ==
            issue_text
        )

        df.loc[
            exact_match,
            "_score"
        ] += 5


        # Partial word match
        words = [
            word
            for word
            in issue_text.split()
            if len(word) > 2
        ]


        for word in words:

            contains_match = (
                defect_text
                .str.contains(
                    word,
                    regex=False,
                    na=False
                )
            )

            df.loc[
                contains_match,
                "_score"
            ] += 1


    # =====================================================
    # CATEGORY MATCH
    # =====================================================

    if category:

        category_text = (
            str(category)
            .lower()
            .strip()
        )


        category_words = [

            word

            for word
            in category_text.split()

            if len(word) > 2
        ]


        combined_text = (

            df.get(
                "element",
                pd.Series(
                    "",
                    index=df.index
                )
            )
            .astype(str)
            .str.lower()

            + " "

            +

            df.get(
                "work_type",
                pd.Series(
                    "",
                    index=df.index
                )
            )
            .astype(str)
            .str.lower()
        )


        for word in category_words:

            contains_match = (
                combined_text
                .str.contains(
                    word,
                    regex=False,
                    na=False
                )
            )

            df.loc[
                contains_match,
                "_score"
            ] += 1


    # =====================================================
    # SORT BY RELEVANCE
    # =====================================================

    sort_columns = [
        "_score"
    ]

    ascending = [
        False
    ]


    if "professional_rating" in df.columns:

        sort_columns.append(
            "professional_rating"
        )

        ascending.append(
            False
        )


    if "professional_experience" in df.columns:

        sort_columns.append(
            "professional_experience"
        )

        ascending.append(
            False
        )


    df = df.sort_values(
        by=sort_columns,
        ascending=ascending
    )


    # =====================================================
    # KEEP RELEVANT RECORDS
    # =====================================================

    relevant = df[
        df["_score"] > 0
    ].copy()


    # If nothing matches, return
    # top records as fallback.

    if relevant.empty:

        relevant = df.head(
            limit
        )

    else:

        relevant = relevant.head(
            limit
        )


    # =====================================================
    # REMOVE INTERNAL SCORE
    # =====================================================

    relevant = relevant.drop(
        columns=[
            "_score"
        ],
        errors="ignore"
    )


    # =====================================================
    # CLEAN NaN VALUES
    # =====================================================

    relevant = relevant.where(
        pd.notna(
            relevant
        ),
        None
    )


    return relevant.to_dict(
        orient="records"
    )