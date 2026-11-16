from __future__ import annotations

import ipaddress
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE_FILE = PROJECT_ROOT / "data" / "sample_network_data" / "SecureSense_NSL_CIC_1000_API_Fusion_Base.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "api_results"
OUTPUT_FILE = OUTPUT_DIR / "final_fused_dataset_clean.csv"
PUBLIC_OUTPUT_FILE = OUTPUT_DIR / "public_enrichment_dataset.csv"

API_FILES = {
    "abuseipdb": PROJECT_ROOT / "abuseipdb_api_data.csv",
    "virustotal": PROJECT_ROOT / "virustotal_api_data.csv",
    "otx": PROJECT_ROOT / "otx_api_data.csv",
    "shodan": PROJECT_ROOT / "shodan_api_data.csv",
    "threatfox": PROJECT_ROOT / "threatfox_api_data.csv",
}


def is_private_ip(value: str) -> bool:
    try:
        return not ipaddress.ip_address(value).is_global
    except ValueError:
        return False


def normalize_status(raw_status: str, private_ip: bool) -> str:
    if private_ip:
        return "NOT_APPLICABLE_PRIVATE_IP"
    status = str(raw_status).strip().lower()
    if status in {"ok", "api_ok"}:
        return "API_OK"
    if status in {"no_result", "no_match", "not_found", "no_data"}:
        return "NO_MATCH"
    if status in {"not_applicable", "not_applicable_private_ip"}:
        return "NOT_APPLICABLE"
    return "API_ERROR"


def load_base() -> pd.DataFrame:
    if not BASE_FILE.exists():
        raise FileNotFoundError(BASE_FILE)
    base = pd.read_csv(BASE_FILE, dtype=str, keep_default_na=False)
    required = {"working_record_id", "attack", "threat_ip", "cic_source_ip", "cic_destination_ip"}
    missing = sorted(required - set(base.columns))
    if missing:
        raise ValueError(f"Base dataset missing columns: {missing}")
    if len(base) != 1000:
        raise ValueError(f"Base dataset must contain exactly 1000 rows; found {len(base)}")
    base["threat_ip"] = base["threat_ip"].str.strip()
    if base["threat_ip"].eq("").any():
        raise ValueError("Base dataset contains blank threat_ip values")
    if base["working_record_id"].duplicated().any():
        raise ValueError("Base dataset contains duplicate working_record_id values")
    if "enrichment_ip" not in base.columns or "ip_entity_role" not in base.columns:
        raise ValueError("Base dataset must contain enrichment_ip and ip_entity_role; run regenerate_enrichment_apis.py first")
    base["enrichment_ip"] = base["enrichment_ip"].str.strip()
    base["ip_entity_role"] = base["ip_entity_role"].str.strip()
    valid_enrichment = base["enrichment_ip"].eq("") | base["enrichment_ip"].map(lambda value: not is_private_ip(value))
    if not valid_enrichment.all():
        raise ValueError("Base dataset contains private enrichment_ip values")
    return base


def find_status_column(api_name: str, columns: pd.Index) -> str:
    for column in (f"{api_name}_api_status", "api_status", "shodan_api_status"):
        if column in columns:
            return column
    raise ValueError(f"{api_name}: no API status column found")


def load_api(api_name: str, path: Path) -> tuple[pd.DataFrame, str, int]:
    if not path.exists():
        raise FileNotFoundError(f"{api_name} CSV not found: {path}")
    api = pd.read_csv(path, dtype=str, keep_default_na=False)
    if "enrichment_ip" not in api.columns and "threat_ip" in api.columns:
        api = api.rename(columns={"threat_ip": "enrichment_ip"})
        print(f"WARNING: {api_name} using legacy threat_ip artifact; regeneration incomplete")
    if "enrichment_ip" not in api.columns:
        raise ValueError(f"{api_name}: missing enrichment_ip column")
    api["enrichment_ip"] = api["enrichment_ip"].str.strip()
    if api["enrichment_ip"].eq("").any():
        raise ValueError(f"{api_name}: blank enrichment_ip values found")
    duplicate_count = int(api["enrichment_ip"].duplicated().sum())
    if duplicate_count:
        raise ValueError(f"{api_name}: {duplicate_count} duplicate threat_ip rows found")
    status_column = find_status_column(api_name, api.columns)
    api["_raw_status"] = api[status_column]
    return api, status_column, duplicate_count


def prefix_api_columns(api_name: str, api: pd.DataFrame, status_column: str) -> pd.DataFrame:
    result = api.copy()
    result[f"{api_name}_raw_status"] = result["_raw_status"]
    result[f"{api_name}_status"] = result.apply(
        lambda row: normalize_status(row["_raw_status"], is_private_ip(row["enrichment_ip"])),
        axis=1,
    )
    result[f"{api_name}_matched"] = result[f"{api_name}_status"].eq("API_OK").map({True: "Yes", False: "No"})

    rename_map = {}
    protected = {"enrichment_ip", "_raw_status", status_column, f"{api_name}_raw_status", f"{api_name}_status", f"{api_name}_matched"}
    for column in result.columns:
        if column not in protected and not column.startswith(f"{api_name}_"):
            rename_map[column] = f"{api_name}_{column}"
    result = result.rename(columns=rename_map)
    return result.drop(columns=["_raw_status", status_column], errors="ignore")


def clean_feature_values(fused: pd.DataFrame, api_name: str) -> None:
    protected = {f"{api_name}_raw_status", f"{api_name}_status", f"{api_name}_matched"}
    feature_columns = [
        column for column in fused.columns
        if column.startswith(f"{api_name}_") and column not in protected
    ]
    non_success = fused[f"{api_name}_status"].ne("API_OK")
    for column in feature_columns:
        fused[column] = fused[column].replace({"": "NOT_AVAILABLE", "nan": "NOT_AVAILABLE", "None": "NOT_AVAILABLE"})
        fused.loc[non_success & fused[column].isna(), column] = "NOT_AVAILABLE"
        fused.loc[non_success, column] = fused.loc[non_success, column].replace(
            to_replace=r"^(error|http[_:].*)$",
            value="NOT_AVAILABLE",
            regex=True,
        )


def remove_unusable_api_features(fused: pd.DataFrame) -> list[str]:
    removed = []
    provenance_suffixes = ("_status", "_matched", "_raw_status", "_api_status", "_api_error_detail")
    for api_name in API_FILES:
        feature_columns = [
            column
            for column in fused.columns
            if column.startswith(f"{api_name}_")
            and not column.endswith(provenance_suffixes)
        ]
        for column in feature_columns:
            values = fused[column].astype(str).str.strip()
            if values.isin({"", "NOT_AVAILABLE", "nan", "NaN", "null", "NULL", "None", "NONE"}).all():
                removed.append(column)
    if removed:
        fused.drop(columns=removed, inplace=True)
    return removed


def print_report(base: pd.DataFrame, fused: pd.DataFrame, reports: dict[str, dict]) -> None:
    private_count = int(base["threat_ip"].map(is_private_ip).sum())
    public_enrichment_count = int(base["enrichment_ip"].ne("").sum())
    print("=" * 72)
    print("SECURESENSE AI FINAL THREAT-IP FUSION VALIDATION")
    print("=" * 72)
    print(f"Base row count       : {len(base)}")
    print(f"Final row count      : {len(fused)}")
    print(f"Final column count   : {len(fused.columns)}")
    print(f"Unique threat_ip     : {base['threat_ip'].nunique()}")
    print(f"Private IP count     : {private_count}")
    print(f"Public IP count      : {len(base) - private_count}")
    print(f"Public enrichment rows: {public_enrichment_count}")
    print(f"Unmatched join count : {sum(report['unmatched'] for report in reports.values())}")
    print(f"Missing-cell count   : {int(fused.isna().sum().sum())}")
    for api_name, report in reports.items():
        print(f"{api_name} duplicate keys: {report['duplicate_keys']}")
        print(f"{api_name} statuses      : {report['statuses']}")
    print(f"Final output path    : {OUTPUT_FILE}")
    print("=" * 72)


def main() -> pd.DataFrame:
    base = load_base()
    fused = base.copy()
    reports = {}

    for api_name, path in API_FILES.items():
        api, status_column, duplicate_count = load_api(api_name, path)
        api = prefix_api_columns(api_name, api, status_column)
        before = len(fused)
        fused = fused.merge(api, on="enrichment_ip", how="left", validate="many_to_one")
        if len(fused) != before:
            raise RuntimeError(f"{api_name} merge changed row count: {before} -> {len(fused)}")

        status_column = f"{api_name}_status"
        missing = fused[status_column].isna() | fused[status_column].eq("")
        not_applicable = fused["enrichment_ip"].eq("")
        fused.loc[not_applicable, status_column] = "NOT_APPLICABLE"
        fused.loc[not_applicable, f"{api_name}_matched"] = "No"
        fused.loc[not_applicable, f"{api_name}_raw_status"] = "NOT_APPLICABLE"
        private = fused["enrichment_ip"].map(is_private_ip)
        fused.loc[private, status_column] = "NOT_APPLICABLE"
        fused.loc[private, f"{api_name}_matched"] = "No"
        fused.loc[missing & ~private & ~not_applicable, status_column] = "API_ERROR"
        fused.loc[missing, f"{api_name}_matched"] = "No"
        fused[f"{api_name}_raw_status"] = fused[f"{api_name}_raw_status"].fillna("NO_ROW").replace("", "NO_ROW")
        clean_feature_values(fused, api_name)
        reports[api_name] = {
            "duplicate_keys": duplicate_count,
            "unmatched": int(missing.sum()),
            "statuses": fused[status_column].value_counts().to_dict(),
        }

    if len(fused) != 1000:
        raise RuntimeError(f"Final dataset must contain exactly 1000 rows; found {len(fused)}")
    allowed_statuses = {"API_OK", "NO_MATCH", "API_ERROR", "NOT_APPLICABLE", "NOT_APPLICABLE_PRIVATE_IP"}
    for api_name in API_FILES:
        statuses = set(fused[f"{api_name}_status"])
        if not statuses <= allowed_statuses:
            raise RuntimeError(f"{api_name}: invalid normalized statuses: {sorted(statuses - allowed_statuses)}")
        feature_columns = [
            column for column in fused.columns
            if column.startswith(f"{api_name}_")
            and column not in {f"{api_name}_raw_status", f"{api_name}_status", f"{api_name}_matched"}
        ]
        for column in feature_columns:
            if fused[column].astype(str).str.match(r"^(error|http[_:].*)$", case=False).any():
                raise RuntimeError(f"{api_name}: raw error value remains in feature column {column}")
    if fused["attack"].tolist() != base["attack"].tolist():
        raise RuntimeError("NSL-KDD attack labels changed during fusion")
    if fused["enrichment_ip"].ne("").sum() != len(fused[fused["ip_entity_role"].ne("none")]):
        raise RuntimeError("enrichment_ip and ip_entity_role counts disagree")
    if not fused[fused["enrichment_ip"].ne("")]["enrichment_ip"].map(lambda value: not is_private_ip(value)).all():
        raise RuntimeError("Non-public enrichment_ip found in final dataset")
    removed_columns = remove_unusable_api_features(fused)
    public_fused = fused[fused["enrichment_ip"].ne("")].copy()
    fused["enrichment_ip"] = fused["enrichment_ip"].replace("", "NOT_AVAILABLE")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fused.to_csv(OUTPUT_FILE, index=False)
    public_fused.to_csv(PUBLIC_OUTPUT_FILE, index=False)
    print(f"Removed unusable API feature columns: {removed_columns}")
    print_report(base, fused, reports)
    return fused


if __name__ == "__main__":
    main()
