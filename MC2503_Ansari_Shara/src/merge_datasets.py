
from pathlib import Path
import pandas as pd

# ==========================================================
# CONFIGURATION
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

AUTH_FILE = (
    BASE_DIR / "data" / "processed"
    / "authentication_dataset_cleaned.csv"
)

API_FILE = BASE_DIR / "API dataset.csv"

OUTPUT_CSV = BASE_DIR / "SecureShare_Fused_Dataset.csv"
OUTPUT_EXCEL = BASE_DIR / "SecureShare_Final_Fused_Dataset.xlsx"


# ==========================================================
# HELPER: FIND IP ADDRESS COLUMN
# ==========================================================

def find_ip_column(dataframe, candidates, dataset_name):
    for column in candidates:
        if column in dataframe.columns:
            return column

    raise ValueError(
        f"Could not find an IP address column in {dataset_name}. "
        f"Available columns: {list(dataframe.columns)}"
    )


# ==========================================================
# MAIN FUSION PROCESS
# ==========================================================

def main():
    print("=" * 65)
    print("SECURESHARE IP-BASED DATA FUSION")
    print("=" * 65)

    # ------------------------------------------------------
    # 1. Load datasets
    # ------------------------------------------------------

    if not AUTH_FILE.exists():
        raise FileNotFoundError(f"Authentication file not found: {AUTH_FILE}")

    if not API_FILE.exists():
        raise FileNotFoundError(f"API dataset not found: {API_FILE}")

    auth = pd.read_csv(AUTH_FILE, dtype=str)
    api = pd.read_csv(API_FILE, dtype=str)

    print(f"\nOriginal authentication rows: {len(auth)}")
    print(f"API dataset rows: {len(api)}")

    # ------------------------------------------------------
    # 2. Identify the common attribute
    # ------------------------------------------------------

    auth_ip_col = find_ip_column(
        auth,
        ["ip_address", "IP Address", "ip", "IP"],
        "authentication dataset"
    )

    api_ip_col = find_ip_column(
        api,
        ["ip_address", "IP Address", "ip", "IP"],
        "API dataset"
    )

    # ------------------------------------------------------
    # 3. Select IP records only
    # ------------------------------------------------------

    if "Entity Type" in api.columns:
        api_ip = api[
            api["Entity Type"].astype(str).str.strip().str.upper() == "IP"
        ].copy()
    else:
        api_ip = api.copy()

    # Convert blank strings to missing values.
    api_ip = api_ip.replace(r"^\s*$", pd.NA, regex=True)

    # Clean join keys.
    auth[auth_ip_col] = auth[auth_ip_col].str.strip()
    api_ip[api_ip_col] = api_ip[api_ip_col].str.strip()

    # Remove records without a usable API IP key.
    api_ip = api_ip.dropna(subset=[api_ip_col])
    api_ip = api_ip[api_ip[api_ip_col] != ""]

    # ------------------------------------------------------
    # 4. Check duplicate API keys
    # ------------------------------------------------------

    duplicate_api_keys = int(
        api_ip.duplicated(subset=[api_ip_col]).sum()
    )

    print(f"IP API records before duplicate removal: {len(api_ip)}")
    print(f"Duplicate API IP keys: {duplicate_api_keys}")

    # Keep one API record per IP to avoid multiplying
    # authentication rows during the merge.
    api_ip = api_ip.drop_duplicates(
        subset=[api_ip_col],
        keep="first"
    )

    # ------------------------------------------------------
    # 5. Keep relevant, populated API attributes
    # ------------------------------------------------------

    excluded_columns = {
        "Entity Type",
        "Entity Identifier",
        api_ip_col
    }

    api_attributes = [
        column
        for column in api_ip.columns
        if column not in excluded_columns
        and api_ip[column].notna().any()
    ]

    api_ip = api_ip[[api_ip_col] + api_attributes]

    # Prefix API fields if they already exist in the
    # authentication dataset, avoiding ambiguous columns.
    rename_columns = {}

    for column in api_attributes:
        if column in auth.columns:
            rename_columns[column] = f"api_{column}"

    api_ip = api_ip.rename(columns=rename_columns)

    # ------------------------------------------------------
    # 6. LEFT JOIN using IP address
    # ------------------------------------------------------

    fused = auth.merge(
        api_ip,
        how="left",
        left_on=auth_ip_col,
        right_on=api_ip_col,
        indicator=True,
        validate="many_to_one"
    )

    # Calculate match statistics before removing the marker.
    matched_rows = int((fused["_merge"] == "both").sum())
    unmatched_rows = int((fused["_merge"] == "left_only").sum())

    fused["API_Match_Status"] = fused["_merge"].map({
        "both": "Matched",
        "left_only": "No API match",
        "right_only": "API only"
    })

    fused = fused.drop(columns=["_merge"])

    # Remove a duplicate join-key column if the source names differ.
    if api_ip_col != auth_ip_col and api_ip_col in fused.columns:
        fused = fused.drop(columns=[api_ip_col])

    # ------------------------------------------------------
    # 7. Calculate quality metrics
    # ------------------------------------------------------

    missing_cells = int(fused.isna().sum().sum())
    duplicate_fused_rows = int(fused.duplicated().sum())

    summary = pd.DataFrame({
        "Metric": [
            "Original authentication rows",
            "API dataset rows",
            "IP API records used",
            "Unique IP API keys",
            "Duplicate API IP keys removed",
            "Fused dataset rows",
            "Fused dataset columns",
            "Authentication rows matched to API",
            "Authentication rows without API match",
            "API match coverage (%)",
            "Missing cells in fused dataset",
            "Duplicate fused rows"
        ],
        "Value": [
            len(auth),
            len(api),
            len(api_ip),
            api_ip[api_ip_col].nunique(),
            duplicate_api_keys,
            len(fused),
            len(fused.columns),
            matched_rows,
            unmatched_rows,
            round(matched_rows / len(auth) * 100, 2)
                if len(auth) else 0,
            missing_cells,
            duplicate_fused_rows
        ]
    })

    # ------------------------------------------------------
    # 8. Save both output formats
    # ------------------------------------------------------

    fused.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(OUTPUT_EXCEL, engine="openpyxl") as writer:
        fused.to_excel(
            writer,
            sheet_name="Fused Dataset",
            index=False
        )

        summary.to_excel(
            writer,
            sheet_name="Fusion Summary",
            index=False
        )

        for sheet_name in ["Fused Dataset", "Fusion Summary"]:
            sheet = writer.sheets[sheet_name]
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions

            for cells in sheet.columns:
                max_length = max(
                    len(str(cell.value or ""))
                    for cell in list(cells)[:200]
                )
                sheet.column_dimensions[cells[0].column_letter].width = min(
                    max(max_length + 2, 12), 35
                )

    # ------------------------------------------------------
    # 9. Final report
    # ------------------------------------------------------

    print("\n" + "=" * 65)
    print("DATA FUSION COMPLETED")
    print("=" * 65)

    print(f"Authentication rows: {len(auth)}")
    print(f"IP API records used: {len(api_ip)}")
    print(f"Matched authentication rows: {matched_rows}")
    print(f"Unmatched authentication rows: {unmatched_rows}")
    print(
        f"API match coverage: "
        f"{round(matched_rows / len(auth) * 100, 2) if len(auth) else 0}%"
    )
    print(f"Fused rows: {len(fused)}")
    print(f"Fused columns: {len(fused.columns)}")

    print(f"\nCSV output: {OUTPUT_CSV}")
    print(f"Excel output: {OUTPUT_EXCEL}")
    print("\nSee the 'Fusion Summary' sheet for validation metrics.")
    print("=" * 65)


if __name__ == "__main__":
    main()
