from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

BASE = ROOT / "SecureSense_NSL_CIC_1000_API_Fusion_Base.csv"

API_FILES = {
    "abuseipdb": ROOT / "abuseipdb_api_data.csv",
    "virustotal": ROOT / "virustotal_api_data.csv",
    "otx": ROOT / "otx_api_data.csv",
    "shodan": ROOT / "shodan_api_data.csv",
    "threatfox": ROOT / "threatfox_api_data.csv",
}

OUT = ROOT / "data" / "api_results" / "presentation_final_fused_dataset.csv"


def clean_value(x):
    if pd.isna(x):
        return "0"
    s = str(x).strip()
    if s == "" or s.lower() in {"nan", "none", "null"}:
        return "0"
    return s


def status_to_clean_value(api, value):
    s = clean_value(value).lower()

    if s == "ok":
        return "OK"

    # API returned no intelligence
    if s in {"no_result", "no_match", "not_found"}:
        return "NO_DATA"

    # Any HTTP/network error
    if s.startswith("error"):
        return "0"

    if s == "not_applicable":
        return "NOT_APPLICABLE"

    return s


def main():
    base = pd.read_csv(BASE, dtype=str, keep_default_na=False)

    if len(base) != 1000:
        raise RuntimeError(
            f"Base dataset must contain 1000 rows, found {len(base)}"
        )

    if "threat_ip" not in base.columns:
        raise RuntimeError("Base dataset has no threat_ip column")

    base["threat_ip"] = base["threat_ip"].astype(str).str.strip()

    fused = base.copy()

    for api_name, path in API_FILES.items():

        if not path.exists():
            raise FileNotFoundError(path)

        api = pd.read_csv(path, dtype=str, keep_default_na=False)

        if "threat_ip" not in api.columns:
            raise RuntimeError(
                f"{api_name}: missing threat_ip"
            )

        api["threat_ip"] = (
            api["threat_ip"]
            .astype(str)
            .str.strip()
        )

        if api["threat_ip"].duplicated().any():
            raise RuntimeError(
                f"{api_name}: duplicate threat_ip values"
            )

        # Detect API status column
        status_col = None
        for c in ["api_status", f"{api_name}_api_status"]:
            if c in api.columns:
                status_col = c
                break

        # Prefix API fields
        renamed = {}
        for c in api.columns:
            if c != "threat_ip":
                renamed[c] = f"{api_name}_{c}"

        api = api.rename(columns=renamed)

        # Add explicit status based on actual response
        prefixed_status = (
            f"{api_name}_{status_col}"
            if status_col
            else None
        )

        if prefixed_status:
            api[f"{api_name}_status"] = api[
                prefixed_status
            ].apply(
                lambda x: status_to_clean_value(
                    api_name, x
                )
            )
        else:
            api[f"{api_name}_status"] = "NOT_AVAILABLE"

        before = len(fused)

        fused = fused.merge(
            api,
            on="threat_ip",
            how="left",
            validate="many_to_one"
        )

        if len(fused) != before:
            raise RuntimeError(
                f"{api_name} merge changed rows: "
                f"{before} -> {len(fused)}"
            )

    # Replace all errors / empty feature cells with 0.
    # Keep the separate status column to preserve provenance.
    for api_name in API_FILES:

        status_col = f"{api_name}_status"

        api_cols = [
            c for c in fused.columns
            if c.startswith(f"{api_name}_")
            and c != status_col
        ]

        for col in api_cols:
            fused[col] = fused[col].apply(clean_value)

            # Replace raw API errors in feature cells.
            fused[col] = fused[col].replace(
                to_replace=r"^error.*$",
                value="0",
                regex=True
            )

            fused[col] = fused[col].replace(
                ["NO_MATCH", "no_match", "no_result"],
                "0"
            )

    # Final global cleanup
    fused = fused.fillna("0")

    for col in fused.columns:
        fused[col] = fused[col].astype(str).str.strip()
        fused[col] = fused[col].replace(
            ["", "nan", "None", "null"],
            "0"
        )

    # Remove duplicate column names
    fused = fused.loc[:, ~fused.columns.duplicated()]

    # Validation
    assert len(fused) == 1000
    assert fused["threat_ip"].notna().all()
    assert not fused.isna().any().any()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fused.to_csv(OUT, index=False)

    print("=" * 70)
    print("PRESENTATION FINAL FUSION")
    print("=" * 70)
    print("Rows    :", len(fused))
    print("Columns :", len(fused.columns))
    print("Output  :", OUT)

    print("\nAPI STATUS")
    for api_name in API_FILES:
        print(
            f"{api_name}:",
            fused[f"{api_name}_status"].value_counts().to_dict()
        )

    print("\nDONE")


if __name__ == "__main__":
    main()