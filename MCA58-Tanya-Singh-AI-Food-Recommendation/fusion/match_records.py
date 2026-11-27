
import pandas as pd
import re


def normalize_name(name):
    """Normalize food names for matching."""

    if pd.isna(name):
        return ""

    name = str(name).lower().strip()
    name = re.sub(r"[^a-z0-9\s]", " ", name)
    name = re.sub(r"\s+", " ", name)

    return name


def attach_food_id(api_df, original_df, source_name):

    if api_df.empty:
        print(source_name, ": No API records to match.")
        return api_df.copy()

    original = original_df.copy()
    external = api_df.copy()

    original["_match_key"] = original["food_name"].apply(
        normalize_name
    )

    external["_match_key"] = external["food_name"].apply(
        normalize_name
    )

    # One search name can correspond to multiple original food IDs.
    mapping = (
        original[["_match_key", "food_id"]]
        .drop_duplicates()
    )

    matched = external.merge(
        mapping,
        on="_match_key",
        how="inner"
    )

    unmatched_names = set(external["_match_key"]) - set(
        mapping["_match_key"]
    )

    print(f"\n{source_name} matching results")
    print("API rows:", len(external))
    print("Matched rows:", len(matched))
    print("Unmatched search names:", len(unmatched_names))

    if unmatched_names:
        print("Unmatched names:", sorted(unmatched_names))

    matched = matched.drop(columns=["_match_key"])

    return matched
