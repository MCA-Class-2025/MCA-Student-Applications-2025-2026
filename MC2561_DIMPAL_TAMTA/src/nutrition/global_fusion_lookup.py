# nutrition/global_fusion_lookup.py
#
# Loads the Colab-generated global fusion dataset (Kaggle base + USDA +
# Google Translate + Pixabay + Gemini origin/production + Open Food Facts)
# and exposes fuzzy lookup by food name.

import os
import pandas as pd
from difflib import get_close_matches
from utils.utils import get_logger

logger = get_logger(__name__)

# Point this at wherever you download/place the CSV from Colab
GLOBAL_FUSION_CSV_PATH = "knowledge_base/05_Global_Fusion_Database/nutricare_final_unified_dataset.csv"

_global_df_cache = None


def _load_global_df(csv_path: str = GLOBAL_FUSION_CSV_PATH) -> pd.DataFrame:
    global _global_df_cache
    if _global_df_cache is not None:
        return _global_df_cache
    if not os.path.exists(csv_path):
        logger.warning("Global fusion dataset not found at %s", csv_path)
        _global_df_cache = pd.DataFrame()
        return _global_df_cache
    df = pd.read_csv(csv_path)
    df["food_name_lower"] = df["food_name"].astype(str).str.lower().str.strip()
    _global_df_cache = df
    logger.info("Loaded global fusion dataset with %d foods.", len(df))
    return df


def search_global_food(query: str, limit: int = 5):
    df = _load_global_df()
    if df.empty:
        return []
    query = query.lower().strip()
    substring = df[df["food_name_lower"].str.contains(query, na=False)]
    names = list(substring["food_name"].unique())[:limit]
    if len(names) < limit:
        close = get_close_matches(query, df["food_name_lower"].tolist(), n=limit, cutoff=0.6)
        for c in close:
            match_row = df[df["food_name_lower"] == c].iloc[0]
            if match_row["food_name"] not in names:
                names.append(match_row["food_name"])
    return names[:limit]


def get_global_fusion_data(food_name: str):
    """Returns the full row dict for a food from the global fusion dataset,
    or None if not found. Includes nutrients, image, translations, and
    Gemini-sourced origin/production data."""
    df = _load_global_df()
    if df.empty:
        return None
    query = food_name.lower().strip()
    exact = df[df["food_name_lower"] == query]
    if exact.empty:
        candidates = search_global_food(query, limit=1)
        if not candidates:
            return None
        exact = df[df["food_name"] == candidates[0]]
    if exact.empty:
        return None
    row = exact.iloc[0].to_dict()
    row = {k: (None if pd.isna(v) else v) for k, v in row.items()}
    return row