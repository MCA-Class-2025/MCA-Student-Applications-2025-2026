"""
Build the final DanceCompass fused-dataset workbook with ZERO blank/NaN
cells anywhere, without fabricating any data.

Approach:
  - Genuine gaps (an API found nothing for that row/field) are replaced
    with an explicit, honest label -- "Not available via <source>" --
    instead of a blank cell or an invented value. This is a labeling
    decision, not a data-fabrication one: the underlying *_found /
    kaggle_matched boolean flags are left untouched, so the true
    coverage is still fully auditable.
  - A separate "Kaggle Matched Subset" sheet contains ONLY the 12 rows
    that genuinely matched the Kaggle dataset, so that sheet has zero
    nulls by construction (no labels needed there at all).
"""

import pandas as pd

ROOT_DATA = "../data/dancecompass_merged.csv"
KAGGLE_FUSED = "dancecompass_kaggle_fused.csv"
KAGGLE_RAW = "dance_styles_kaggle.csv"
QA_CSV = "qa_findings.csv"
OUT_XLSX = "/mnt/user-data/outputs/dancecompass_final_unified_dataset.xlsx"

NA_LABEL = "Not available in source"


def label_nulls(df: pd.DataFrame, exclude_cols=()) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        if col in exclude_cols:
            continue
        if df[col].isnull().any():
            df[col] = df[col].fillna(NA_LABEL)
    return df


def main():
    merged = pd.read_csv(ROOT_DATA)
    kaggle_fused = pd.read_csv(KAGGLE_FUSED)
    kaggle_raw = pd.read_csv(KAGGLE_RAW, encoding="latin1")
    qa = pd.read_csv(QA_CSV)

    kaggle_new_cols = [c for c in kaggle_fused.columns if c.startswith("kaggle_")]
    combined = merged.merge(kaggle_fused[["name"] + kaggle_new_cols], on="name", how="left")

    # Boolean/flag columns should stay real booleans, not text labels.
    bool_cols = [c for c in combined.columns if c.endswith("_found") or c == "kaggle_matched"]
    combined["kaggle_matched"] = combined["kaggle_matched"].fillna(False)

    combined_labeled = label_nulls(combined, exclude_cols=bool_cols)

    matched_subset = kaggle_fused[kaggle_fused["kaggle_matched"] == True].copy()
    keep_cols = ["id", "name", "category", "origin_region"] + kaggle_new_cols
    matched_subset = matched_subset[keep_cols]

    assert combined_labeled.isnull().sum().sum() == 0, "Full sheet still has nulls!"
    assert matched_subset.isnull().sum().sum() == 0, "Matched subset still has nulls!"
    assert kaggle_raw.isnull().sum().sum() == 0, "Kaggle raw source has nulls!"
    assert qa.isnull().sum().sum() == 0, "QA sheet has nulls!"

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as writer:
        combined_labeled.to_excel(writer, sheet_name="Fused Dataset (83 cols)", index=False)
        matched_subset.to_excel(writer, sheet_name="Kaggle Matched Subset (12)", index=False)
        kaggle_raw.to_excel(writer, sheet_name="Kaggle Source (raw, 206 rows)", index=False)
        qa.to_excel(writer, sheet_name="Kaggle QA Findings", index=False)

    print("All sheets written with zero null cells.")
    print("Fused Dataset (83 cols):", combined_labeled.shape)
    print("Kaggle Matched Subset (12):", matched_subset.shape)
    print("Kaggle Source (raw):", kaggle_raw.shape)
    print("Kaggle QA Findings:", qa.shape)


if __name__ == "__main__":
    main()
