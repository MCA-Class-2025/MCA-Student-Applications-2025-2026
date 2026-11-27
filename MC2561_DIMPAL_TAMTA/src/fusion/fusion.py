import os, numpy as np, pandas as pd, matplotlib.pyplot as plt, seaborn as sns
from fusion.usda_client import get_usda_food_cached, normalize_food_name
from fusion.crop_fusion import merge_crop_features, CROP_FEATURE_COLS, CROP_CSV_DEFAULT_PATH

RENAME_MAP = {
    "food_name": "food_name",
    "food_group_nin": "food_group_nin",
    "energy_kcal": "local_calories",
    "protein_g": "local_protein",
    "fat_g": "local_fat",
    "carb_g": "local_carbohydrates",
    "fibre_g": "local_fiber",
    "calcium_mg": "local_calcium",
    "iron_mg": "local_iron",
    "sodium_mg": "local_sodium",
    "freesugar_g": "local_sugar",
}

PRETTY_NAMES = {
    "food_name": "Food Name",
    "food_group_nin": "Category",
    "local_calories": "Calories (Local)",
    "usda_calories": "Calories (USDA)",
    "local_protein": "Protein g (Local)",
    "usda_protein": "Protein g (USDA)",
    "local_fat": "Fat g (Local)",
    "usda_fat": "Fat g (USDA)",
    "local_carbohydrates": "Carbs g (Local)",
    "usda_carbohydrates": "Carbs g (USDA)",
    "local_fiber": "Fiber g (Local)",
    "usda_fiber": "Fiber g (USDA)",
    "local_sugar": "Sugar g (Local)",
    "usda_sugar": "Sugar g (USDA)",
    "local_calcium": "Calcium mg (Local)",
    "usda_calcium": "Calcium mg (USDA)",
    "local_iron": "Iron mg (Local)",
    "usda_iron": "Iron mg (USDA)",
    "local_sodium": "Sodium mg (Local)",
    "usda_sodium": "Sodium mg (USDA)",
    "calories_difference": "Δ Calories (USDA − Local)",
    "protein_difference": "Δ Protein",
    "fat_difference": "Δ Fat",
    "carbohydrates_difference": "Δ Carbs",
    "fiber_difference": "Δ Fiber",
    "protein_density": "Protein Density (%)",
    "fiber_density": "Fiber Density (%)",
    "fat_protein_ratio": "Fat:Protein Ratio",
    "carb_protein_ratio": "Carb:Protein Ratio",
    "food_key": "Food Key",
    "top_producing_state": "Top Producing State",
    "top_3_states": "Top 3 States",
    "production_share_pct": "Top State Share (%)",
    "is_major_crop": "Is Major Crop",
}

RAW_COLS = [
    "food_name", "food_group_nin",
    "local_calories", "usda_calories",
    "local_protein", "usda_protein",
    "local_fat", "usda_fat",
    "local_carbohydrates", "usda_carbohydrates",
    "local_fiber", "usda_fiber",
    "local_sugar", "usda_sugar",
    "local_calcium", "usda_calcium",
    "local_iron", "usda_iron",
    "local_sodium", "usda_sodium",
]

FEATURE_COLS = [
    "calories_difference", "protein_difference", "fat_difference",
    "carbohydrates_difference", "fiber_difference",
    "protein_density", "fiber_density", "fat_protein_ratio", "carb_protein_ratio",
]

GEO_COLS = CROP_FEATURE_COLS

def prettify(df, cols=None):
    sub = df[cols].copy() if cols else df.copy()
    sub = sub.rename(columns={c: PRETTY_NAMES.get(c, c) for c in sub.columns})
    return sub

def _prepare_local(df):
    existing = [c for c in RENAME_MAP if c in df.columns]
    df_sub = df[existing].copy()
    df_sub.rename(columns={c: RENAME_MAP[c] for c in existing}, inplace=True)
    df_sub["food_key"] = df_sub["food_name"].apply(normalize_food_name)
    before = len(df_sub)
    df_sub = df_sub.drop_duplicates(subset="food_key", keep="first").reset_index(drop=True)
    dropped = before - len(df_sub)
    if dropped:
        print(f"[fusion] Dropped {dropped} duplicate food_key rows.")
    return df_sub

def fetch_raw_sources(local_csv_path, limit=500):
    df = pd.read_csv(local_csv_path, encoding="latin-1")
    df_sub = _prepare_local(df)
    usda_rows = []
    metadata_rows = []
    n = min(limit, len(df_sub))
    for idx in range(n):
        row = df_sub.iloc[idx]
        food_name = row["food_name"]
        data, status = get_usda_food_cached(food_name)
        usda_rows.append(data if data else {})
        metadata_rows.append({
            "food_key": row["food_key"],
            "food_name": food_name,
            "usda_status": status,
            "usda_matched_name": data.get("usda_food_name", "") if data else "",
            "usda_fdc_id": data.get("usda_fdc_id", "") if data else "",
        })
        if (idx + 1) % 25 == 0 or idx == n - 1:
            print(f"[fusion] Fetched {idx + 1}/{n} foods from USDA")
    usda_df = pd.DataFrame(usda_rows)
    usda_df["food_key"] = df_sub["food_key"].iloc[:n].values
    return df_sub.iloc[:n].reset_index(drop=True), usda_df, pd.DataFrame(metadata_rows)

def build_unified_dataset(local_csv_path, output_csv_path, limit=500,
                           metadata_csv_path="data/fusion/fusion_metadata.csv",
                           include_crop_fusion=True,
                           crop_csv_path=CROP_CSV_DEFAULT_PATH):
    df_sub, usda_df, metadata_df = fetch_raw_sources(local_csv_path, limit=limit)
    merged = pd.merge(df_sub, usda_df, on="food_key", how="left")

    # Feature fusion
    for nut in ["calories", "protein", "fat", "carbohydrates", "fiber"]:
        local_col, usda_col = f"local_{nut}", f"usda_{nut}"
        if local_col in merged.columns and usda_col in merged.columns:
            merged[f"{nut}_difference"] = merged[usda_col] - merged[local_col]
            merged[f"{nut}_difference_pct"] = (
                merged[f"{nut}_difference"] / merged[local_col].replace(0, np.nan)
            ) * 100
    if "local_calories" in merged.columns and "local_protein" in merged.columns:
        merged["protein_density"] = merged["local_protein"] / merged["local_calories"].replace(0, np.nan) * 100
    if "local_calories" in merged.columns and "local_fiber" in merged.columns:
        merged["fiber_density"] = merged["local_fiber"] / merged["local_calories"].replace(0, np.nan) * 100
    if "local_protein" in merged.columns and "local_fat" in merged.columns:
        merged["fat_protein_ratio"] = merged["local_fat"] / merged["local_protein"].replace(0, np.nan)
    if "local_carbohydrates" in merged.columns and "local_protein" in merged.columns:
        merged["carb_protein_ratio"] = merged["local_carbohydrates"] / merged["local_protein"].replace(0, np.nan)

    # Completeness
    usda_nutrient_cols = [c for c in merged.columns if c.startswith("usda_") and c not in ("usda_food_name", "usda_fdc_id")]
    if usda_nutrient_cols:
        merged["data_completeness_pct"] = merged[usda_nutrient_cols].notna().sum(axis=1) / len(usda_nutrient_cols) * 100

    # Geographic fusion
    if include_crop_fusion:
        try:
            merged = merge_crop_features(merged, crop_csv_path=crop_csv_path)
        except FileNotFoundError as e:
            print(f"[fusion] Skipping crop fusion: {e}")
            for c in GEO_COLS:
                merged[c] = np.nan

    # Drop empty USDA columns (no data at all)
    for col in merged.columns:
        if col.startswith("usda_") and col not in ("usda_food_name", "usda_fdc_id"):
            if merged[col].isna().all():
                merged = merged.drop(columns=[col])
                print(f"[fusion] Dropped empty column: {col}")

    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    merged.to_csv(output_csv_path, index=False)

    os.makedirs(os.path.dirname(metadata_csv_path), exist_ok=True)
    metadata_df.to_csv(metadata_csv_path, index=False)

    return merged

def compute_correlation(df, columns):
    sub = df[columns].dropna()
    if sub.empty or len(sub.columns) < 2:
        return None
    corr = sub.corr()
    display_cols = [PRETTY_NAMES.get(c, c) for c in corr.columns]
    corr.columns = display_cols
    corr.index = display_cols
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5, ax=ax)
    ax.set_title("Correlation Matrix — Local vs USDA Nutrition Features")
    plt.tight_layout()
    return fig