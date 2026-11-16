from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = ROOT / "data" / "api_results" / "public_entity_fused_dataset_complete.csv"
OUTPUT_FILE = ROOT / "data" / "api_results" / "public_entity_fused_dataset_final.csv"
PLACEHOLDERS = {"", "NOT_AVAILABLE", "nan", "NaN", "null", "NULL", "None", "NONE"}


def main() -> pd.DataFrame:
    df = pd.read_csv(INPUT_FILE, dtype=str, keep_default_na=False)
    original_columns = list(df.columns)
    removed = []

    for column in list(df.columns):
        values = df[column].astype(str).str.strip()
        if values.isin(PLACEHOLDERS).all():
            removed.append((column, "all rows are empty/NOT_AVAILABLE/null-like"))

    df = df.drop(columns=[column for column, _ in removed])
    df = df.fillna("NOT_AVAILABLE").replace("", "NOT_AVAILABLE")

    feature_columns = [
        column for column in df.columns
        if column.startswith(("abuseipdb_", "virustotal_", "otx_", "shodan_", "threatfox_"))
        and not column.endswith(("_status", "_matched", "_raw_status", "_api_status", "_api_error_detail"))
    ]
    residual_empty_features = [
        column for column in feature_columns
        if df[column].astype(str).str.strip().isin(PLACEHOLDERS).all()
    ]
    if residual_empty_features:
        raise RuntimeError(f"Completely unavailable feature columns remain: {residual_empty_features}")

    if len(df) != 245:
        raise RuntimeError(f"Expected 245 public entity rows; found {len(df)}")
    if df["enrichment_ip"].nunique() != 245:
        raise RuntimeError("enrichment_ip is not unique")
    if df.isna().any().any() or (df == "").any().any():
        raise RuntimeError("Null or blank cells remain")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"Input file        : {INPUT_FILE}")
    print(f"Output file       : {OUTPUT_FILE}")
    print(f"Original columns  : {len(original_columns)}")
    print(f"Removed columns   : {[column for column, _ in removed]}")
    print(f"Retained columns  : {len(df.columns)}")
    print(f"Final rows        : {len(df)}")
    print(f"Final columns     : {len(df.columns)}")
    print(f"Remaining blanks  : {int((df == '').sum().sum())}")
    print(f"Remaining nulls   : {int(df.isna().sum().sum())}")
    print("Validation        : PASSED")
    return df


if __name__ == "__main__":
    main()
