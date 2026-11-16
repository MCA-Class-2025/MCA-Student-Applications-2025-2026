from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
BASE_FILE = ROOT / "data" / "sample_network_data" / "SecureSense_NSL_CIC_1000_API_Fusion_Base.csv"
OUTPUT_FILE = ROOT / "data" / "api_results" / "public_entity_fused_dataset_final.csv"
API_NAMES = ["abuseipdb", "virustotal", "otx", "shodan", "threatfox"]
API_FILES = {name: ROOT / f"{name}_api_data.csv" for name in API_NAMES}
PLACEHOLDERS = {"", "NOT_AVAILABLE", "nan", "NaN", "null", "NULL", "None", "NONE"}


def main() -> pd.DataFrame:
    base = pd.read_csv(BASE_FILE, dtype=str, keep_default_na=False)
    public = base[base["enrichment_ip"].ne("")].copy()
    if public.empty:
        raise ValueError("No public enrichment entities found in the base dataset")

    def combine(values: pd.Series) -> str:
        unique_values = sorted({str(value).strip() for value in values if str(value).strip()})
        return "|".join(unique_values) if unique_values else "NOT_AVAILABLE"

    aggregations = {
        column: (column, combine)
        for column in public.columns
        if column != "enrichment_ip"
    }
    entity = public.groupby("enrichment_ip", sort=True, as_index=False).agg(**aggregations)
    entity.insert(1, "base_record_count", public.groupby("enrichment_ip").size().reindex(entity["enrichment_ip"]).to_numpy())

    for api_name in API_NAMES:
        path = API_FILES[api_name]
        api = pd.read_csv(path, dtype=str, keep_default_na=False)
        if "enrichment_ip" not in api.columns:
            raise ValueError(f"{api_name}: missing enrichment_ip")
        if api["enrichment_ip"].duplicated().any():
            raise ValueError(f"{api_name}: duplicate enrichment_ip values")
        renamed = {
            column: f"{api_name}_{column}"
            for column in api.columns
            if column != "enrichment_ip"
        }
        entity = entity.merge(
            api.rename(columns=renamed),
            on="enrichment_ip",
            how="left",
            validate="one_to_one",
        )

    if len(entity) != public["enrichment_ip"].nunique():
        raise RuntimeError("Entity-level row count changed during API fusion")
    entity = entity.fillna("NOT_AVAILABLE").replace("", "NOT_AVAILABLE")
    removed_columns = []
    provenance_suffixes = ("_status", "_matched", "_raw_status", "_api_status", "_api_error_detail")
    for api_name in API_NAMES:
        feature_columns = [
            column
            for column in entity.columns
            if column.startswith(f"{api_name}_")
            and not column.endswith(provenance_suffixes)
        ]
        for column in feature_columns:
            if entity[column].astype(str).str.strip().isin(PLACEHOLDERS).all():
                removed_columns.append(column)
    entity = entity.drop(columns=removed_columns)
    if entity["enrichment_ip"].duplicated().any():
        raise RuntimeError("Duplicate enrichment_ip values in entity-level output")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    entity.to_csv(OUTPUT_FILE, index=False)
    print(f"Output: {OUTPUT_FILE}")
    print(f"Entity rows: {len(entity)}")
    print(f"Original public traffic rows represented: {len(public)}")
    print(f"Unique enrichment_ip values: {entity['enrichment_ip'].nunique()}")
    print(f"Columns: {len(entity.columns)}")
    print(f"Removed unusable API feature columns: {removed_columns}")
    for api_name in API_NAMES:
        print(f"{api_name}: {entity[f'{api_name}_api_status'].value_counts().to_dict()}")
    return entity


if __name__ == "__main__":
    main()
