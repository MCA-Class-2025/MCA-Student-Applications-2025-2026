# fusion/crop_fusion.py – Geographic (crop-production) fusion
#
# Adds a THIRD fusion source to the pipeline: India's state-wise crop
# production data (data.gov.in style: Crop, Crop_Year, Season, State, Area,
# Production, Annual_Rainfall, Fertilizer, Pesticide, Yield).
#
# This is NOT a nutrient fusion — it answers a different question ("where is
# this food/crop grown, and how much") and only applies to raw agricultural
# crops (~30-60 of your 2,109 foods), not prepared dishes. Everything else
# legitimately gets NaN / is_major_crop = False. That's expected, not a bug.
#
# File location expected: knowledge_base/04_Crop_Production_Database/crop_production.csv

import os
import pandas as pd

CROP_CSV_DEFAULT_PATH = "knowledge_base/04_Crop_Production_Database/crop_production.csv"

# Manual crop -> food_name mapping. This is intentionally curated by hand
# (not fuzzy-matched) because crop-record naming ("Arhar/Tur", "Moong(Green
# Gram)") and IFCT food naming ("tur dal", "moong dal") diverge enough that
# an automatic match would produce false positives. Extend this dict as you
# check your actual food_name values against the crop list.
CROP_TO_FOOD_MAP = {
    "Rice": ["rice", "boiled rice", "raw rice"],
    "Wheat": ["wheat flour", "atta", "wheat"],
    "Bajra": ["bajra", "pearl millet"],
    "Jowar": ["jowar", "sorghum"],
    "Ragi": ["ragi", "finger millet"],
    "Arhar/Tur": ["tur dal", "arhar dal", "toor dal"],
    "Moong(Green Gram)": ["moong dal", "green gram"],
    "Urad": ["urad dal", "black gram"],
    "Gram": ["chana dal", "bengal gram", "kabuli chana"],
    "Masoor": ["masoor dal", "red lentil"],
    "Groundnut": ["groundnut", "peanut"],
    "Coconut ": ["coconut", "coconut oil"],
    "Sugarcane": ["sugarcane", "jaggery"],
    "Potato": ["potato"],
    "Onion": ["onion"],
    "Tomato": ["tomato"],
    "Banana": ["banana"],
    "Mango": ["mango"],
    "Soyabean": ["soybean", "soya"],
    "Sunflower": ["sunflower oil", "sunflower seed"],
    "Mustard": ["mustard oil", "mustard seed"],
    "Turmeric": ["turmeric"],
    "Ginger": ["ginger"],
    "Garlic": ["garlic"],
}


def load_crop_data(csv_path=CROP_CSV_DEFAULT_PATH):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"Crop dataset not found at {csv_path}. "
            f"Place it at knowledge_base/04_Crop_Production_Database/crop_production.csv"
        )
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()

    # Some public crop-production CSVs use "State_Name" instead of "State".
    # Normalize so the rest of the pipeline (which expects "State") works
    # regardless of which variant you downloaded.
    if "State" not in df.columns and "State_Name" in df.columns:
        df = df.rename(columns={"State_Name": "State"})

    required = {"Crop", "State", "Production"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Crop CSV is missing required column(s): {missing}. "
            f"Found columns: {df.columns.tolist()}. "
            f"This file may be a different dataset than expected — check its schema."
        )

    return df

def summarize_crop_states(crop_df):
    """
    Aggregate total Production by Crop + State (summed across all years and
    seasons — gives a stable 'who grows the most overall' picture, not a
    single-year snapshot), then rank states per crop.

    Returns one row per crop with: top_producing_state, top_3_states,
    production_share_pct (top state's share of that crop's national total).
    """
    totals = (
        crop_df.groupby(["Crop", "State"], as_index=False)["Production"]
        .sum()
        .rename(columns={"Production": "total_production"})
    )

    def _summarize(group):
        group = group.sort_values("total_production", ascending=False)
        total = group["total_production"].sum()
        top_state = group.iloc[0]["State"]
        top3 = ", ".join(group.head(3)["State"].tolist())
        share = round(group.iloc[0]["total_production"] / total * 100, 1) if total > 0 else None
        return pd.Series({
            "top_producing_state": top_state,
            "top_3_states": top3,
            "production_share_pct": share,
            "national_total_production": total,
        })

    summary = totals.groupby("Crop").apply(_summarize).reset_index()
    summary["Crop"] = summary["Crop"].str.strip()
    return summary


def build_crop_lookup(crop_summary, crop_to_food_map=CROP_TO_FOOD_MAP):
    """Flatten crop_summary into food_name_lower -> geographic feature row."""
    rows = []
    unmapped_crops = []
    for crop_name, food_names in crop_to_food_map.items():
        match = crop_summary[crop_summary["Crop"] == crop_name.strip()]
        if match.empty:
            unmapped_crops.append(crop_name)
            continue
        for fname in food_names:
            r = match.iloc[0].to_dict()
            r["food_name_lower"] = fname.lower().strip()
            r["matched_crop"] = crop_name
            rows.append(r)

    if unmapped_crops:
        print(f"[crop_fusion] Warning: {len(unmapped_crops)} crop(s) in the map "
              f"had no match in the crop CSV: {unmapped_crops}")

    return pd.DataFrame(rows)


def merge_crop_features(unified_df, crop_csv_path=CROP_CSV_DEFAULT_PATH,
                         crop_to_food_map=CROP_TO_FOOD_MAP):
    """
    Main entry point. Takes the already local+USDA fused dataframe and adds:
    top_producing_state, top_3_states, production_share_pct, is_major_crop.

    Matching is by SUBSTRING containment (e.g. the keyword "rice" matches
    "Rice, raw, brown (Oryza sativa )"), not exact equality — real food names
    in the local DB are descriptive ("Rice, raw, brown (...)"), not bare
    crop names ("rice"), so exact matching would find almost nothing.

    Every row is kept — foods with no crop match simply get NaN / False.
    """
    crop_df = load_crop_data(crop_csv_path)
    crop_summary = summarize_crop_states(crop_df)
    crop_lookup = build_crop_lookup(crop_summary, crop_to_food_map)

    out = unified_df.copy()
    out["food_name_lower"] = out["food_name"].astype(str).str.lower().str.strip()

    # Sort keywords longest-first so more specific phrases ("wheat flour")
    # win over shorter ones ("wheat") when a food name could match both.
    lookup_rows = crop_lookup.sort_values(
        by="food_name_lower", key=lambda s: s.str.len(), ascending=False
    ).to_dict("records")

    geo_cols = ["top_producing_state", "top_3_states", "production_share_pct", "matched_crop"]
    matches = {c: [None] * len(out) for c in geo_cols}

    for i, name in enumerate(out["food_name_lower"]):
        for row in lookup_rows:
            keyword = row["food_name_lower"]
            if keyword and keyword in name:
                for c in geo_cols:
                    matches[c][i] = row.get(c)
                break  # first (longest) keyword match wins for this food

    for c in geo_cols:
        out[c] = matches[c]
    out["is_major_crop"] = out["top_producing_state"].notna()
    out.drop(columns=["food_name_lower"], inplace=True)

    matched_count = int(out["is_major_crop"].sum())
    print(f"[crop_fusion] {matched_count}/{len(out)} foods matched to a crop-production record.")

    return out


CROP_FEATURE_COLS = ["top_producing_state", "top_3_states", "production_share_pct", "is_major_crop"]