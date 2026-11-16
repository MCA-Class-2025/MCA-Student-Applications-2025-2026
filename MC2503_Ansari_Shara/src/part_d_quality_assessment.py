
from pathlib import Path
import ipaddress

import pandas as pd
import numpy as np


# ============================================================
# 1. FUNCTION DEFINITIONS
# ============================================================

def is_valid_ip(value):
    """Return True if the value is a valid IPv4 or IPv6 address."""
    try:
        ipaddress.ip_address(str(value).strip())
        return True
    except (ValueError, TypeError):
        return False


def add_check(report, check, column, count, details):
    """Add a result to the quality assessment report."""
    report.append({
        "Check": check,
        "Column": column,
        "Issue Count": int(count),
        "Details": str(details)
    })


# ============================================================
# 2. PATHS AND DATA LOADING
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "SecureShare_Fused_Dataset.csv"
OUTPUT_DIR = BASE_DIR / "outputs" / "eda"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if not INPUT_PATH.exists():
    raise FileNotFoundError(
        f"Fused dataset not found: {INPUT_PATH}\n"
        "Run python src/merge_datasets.py first."
    )

df = pd.read_csv(INPUT_PATH, low_memory=False)
report = []

print("=" * 65)
print("PART D: DATA QUALITY ASSESSMENT")
print("=" * 65)

print(f"Input file: {INPUT_PATH}")
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")


# ============================================================
# 3. STRUCTURAL QUALITY
# ============================================================

duplicate_rows = int(df.duplicated().sum())
missing_cells = int(df.isna().sum().sum())
total_cells = int(df.shape[0] * df.shape[1])

add_check(
    report, "Dataset structure", "ALL", len(df),
    f"{len(df)} rows and {len(df.columns)} columns"
)

add_check(
    report, "Duplicate complete rows", "ALL", duplicate_rows,
    "Rows identical across all columns"
)

add_check(
    report, "Missing cells", "ALL", missing_cells,
    f"{missing_cells / total_cells * 100:.2f}% of all cells are missing"
    if total_cells else "Dataset has no cells"
)

original_columns = [
    "user_id",
    "ip_address",
    "device_type",
    "os_type",
    "browser",
    "success",
    "account_status",
    "failed_attempts",
    "session_duration",
    "role",
    "privilege_level",
    "suspicious_activity",
    "blocked"
]

missing_original_columns = [
    col for col in original_columns if col not in df.columns
]

add_check(
    report, "Missing original columns", "ALL",
    len(missing_original_columns),
    (
        ", ".join(missing_original_columns)
        if missing_original_columns else "All original columns are present"
    )
)

print("\n--- STRUCTURAL QUALITY ---")
print(f"Duplicate complete rows: {duplicate_rows}")
print(f"Missing cells: {missing_cells:,}")
print(
    "Missing cell percentage:",
    round(missing_cells / total_cells * 100, 2)
    if total_cells else 0
)
print("Missing original columns:", missing_original_columns or "None")


# ============================================================
# 4. MISSING-VALUE ANALYSIS BY COLUMN
# ============================================================

missing_rows = []

for col in df.columns:
    count = int(df[col].isna().sum())

    missing_rows.append({
        "Column": col,
        "Missing Count": count,
        "Missing Percentage": round(
            count / len(df) * 100, 2
        ) if len(df) else 0,
        "Non-Missing Count": int(df[col].notna().sum())
    })

missing_report = pd.DataFrame(missing_rows).sort_values(
    "Missing Count", ascending=False
)

missing_report.to_csv(
    OUTPUT_DIR / "part_d_missing_values.csv",
    index=False
)

for _, row in missing_report.iterrows():
    if row["Missing Count"] > 0:
        add_check(
            report,
            "Missing values",
            row["Column"],
            row["Missing Count"],
            f'{row["Missing Percentage"]}% of rows are missing'
        )

print("\n--- COLUMNS WITH MOST MISSING VALUES ---")
print(missing_report.head(10).to_string(index=False))


# ============================================================
# 5. IP ADDRESS VALIDATION
# ============================================================

if "ip_address" in df.columns:
    ip_values = df["ip_address"].dropna().astype(str).str.strip()

    invalid_ip_mask = ~ip_values.map(is_valid_ip)
    invalid_ip_count = int(invalid_ip_mask.sum())

    add_check(
        report,
        "Invalid IP address format",
        "ip_address",
        invalid_ip_count,
        "Non-empty values that are not valid IPv4 or IPv6 addresses"
    )

    duplicate_ip_count = int(
        df["ip_address"].dropna().duplicated().sum()
    )

    add_check(
        report,
        "Repeated authentication IP addresses",
        "ip_address",
        duplicate_ip_count,
        "Repeated IP values; these may be legitimate and need context"
    )

    print("\n--- IP ADDRESS CHECKS ---")
    print(f"Invalid IP addresses: {invalid_ip_count}")
    print(f"Repeated IP addresses: {duplicate_ip_count}")
else:
    print("\nWARNING: ip_address column not found.")


# ============================================================
# 6. CATEGORICAL CONSISTENCY
# ============================================================

allowed_values = {
    "success": {"true", "false"},
    "blocked": {"true", "false"},
    "suspicious_activity": {"true", "false"},
    "account_status": {"active", "locked", "suspended"}
}

for col, allowed in allowed_values.items():
    if col not in df.columns:
        add_check(
            report, "Category validation", col, 0,
            "Column not present; validation skipped"
        )
        continue

    actual_values = set(
        df[col].dropna().astype(str).str.strip().str.lower()
    )

    unexpected_values = sorted(actual_values - allowed)

    add_check(
        report,
        "Unexpected category values",
        col,
        len(unexpected_values),
        (
            f"Unexpected distinct values: {unexpected_values}"
            if unexpected_values else "All observed values match expected categories"
        )
    )

    print(f"\n{col} unexpected values: {unexpected_values or 'None'}")


# ============================================================
# 7. NUMERIC VALIDITY CHECKS
# ============================================================

numeric_ranges = {
    "failed_attempts": (0, None),
    "session_duration": (0, 3600),
    "privilege_level": (1, 5),
    "AbuseIPDB Abuse Confidence Score": (0, 100),
    "AbuseIPDB Total Reports": (0, None)
}

for col, (minimum, maximum) in numeric_ranges.items():
    if col not in df.columns:
        continue

    values = pd.to_numeric(df[col], errors="coerce")

    # Flag non-empty values that cannot be interpreted as numbers.
    original_nonempty = df[col].notna()
    invalid_numeric = original_nonempty & values.isna()

    add_check(
        report,
        "Non-numeric values in numeric field",
        col,
        int(invalid_numeric.sum()),
        "Non-empty values that could not be parsed as numbers"
    )

    out_of_range = values.notna() & (values < minimum)

    if maximum is not None:
        out_of_range |= values.notna() & (values > maximum)

    add_check(
        report,
        "Out-of-range numeric values",
        col,
        int(out_of_range.sum()),
        f"Expected minimum={minimum}, maximum={maximum}"
    )


# ============================================================
# 8. FUSION STATUS VALIDATION
# ============================================================

if "API_Match_Status" in df.columns:
    status_series = df["API_Match_Status"].fillna("Missing status")
    status_counts = status_series.value_counts(dropna=False)

    status_report = status_counts.rename_axis(
        "API Match Status"
    ).reset_index(name="Row Count")

    status_report["Percentage"] = (
        status_report["Row Count"] / len(df) * 100
    ).round(2) if len(df) else 0

    status_report.to_csv(
        OUTPUT_DIR / "part_d_fusion_status.csv",
        index=False
    )

    print("\n--- FUSION STATUS ---")
    print(status_report.to_string(index=False))

    for _, row in status_report.iterrows():
        add_check(
            report,
            "Fusion match status",
            "API_Match_Status",
            row["Row Count"],
            f'{row["API Match Status"]}: {row["Percentage"]}%'
        )
else:
    add_check(
        report,
        "Fusion status validation",
        "API_Match_Status",
        0,
        "Column not found; fusion status was not validated"
    )


# ============================================================
# 9. API COMPLETENESS AMONG MATCHED ROWS
# ============================================================

api_columns = [
    col for col in df.columns
    if col.startswith("AbuseIPDB ") or col.startswith("IPinfo ")
]

if "API_Match_Status" in df.columns:
    matched = df[
        df["API_Match_Status"].astype(str).str.strip().str.lower()
        == "matched"
    ]

    completeness_rows = []

    for col in api_columns:
        available = int(matched[col].notna().sum())
        total = len(matched)

        completeness_rows.append({
            "API Column": col,
            "Matched Rows": total,
            "Available Values": available,
            "Missing Values Among Matches": total - available,
            "Availability Percentage": round(
                available / total * 100, 2
            ) if total else 0
        })

    completeness = pd.DataFrame(completeness_rows)

    completeness.to_csv(
        OUTPUT_DIR / "part_d_matched_api_completeness.csv",
        index=False
    )

    print("\n--- API COMPLETENESS AMONG MATCHED ROWS ---")
    print(f"Matched rows: {len(matched)}")
    if not completeness.empty:
        print(completeness.to_string(index=False))


# ============================================================
# 10. POTENTIAL OUTLIERS (IQR METHOD)
# ============================================================

outlier_columns = [
    "failed_attempts",
    "session_duration",
    "privilege_level",
    "AbuseIPDB Abuse Confidence Score",
    "AbuseIPDB Total Reports"
]

outlier_rows = []

for col in outlier_columns:
    if col not in df.columns:
        continue

    values = pd.to_numeric(df[col], errors="coerce").dropna()

    if len(values) < 4:
        continue

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    mask = (values < lower_bound) | (values > upper_bound)
    count = int(mask.sum())

    outlier_rows.append({
        "Column": col,
        "Q1": q1,
        "Q3": q3,
        "IQR": iqr,
        "Lower Bound": lower_bound,
        "Upper Bound": upper_bound,
        "Potential Outlier Count": count,
        "Potential Outlier Percentage": round(
            count / len(values) * 100, 2
        )
    })

    add_check(
        report,
        "Potential IQR outliers",
        col,
        count,
        "Flagged for review only; values have not been removed"
    )

outlier_report = pd.DataFrame(outlier_rows)
outlier_report.to_csv(
    OUTPUT_DIR / "part_d_potential_outliers.csv",
    index=False
)


# ============================================================
# 11. SAVE COMPLETE QUALITY REPORT
# ============================================================

quality_report = pd.DataFrame(report)

quality_report.to_csv(
    OUTPUT_DIR / "part_d_quality_report.csv",
    index=False
)

print("\n" + "=" * 65)
print("PART D ASSESSMENT COMPLETED")
print("=" * 65)
print(f"Rows assessed: {len(df)}")
print(f"Columns assessed: {len(df.columns)}")
print(f"Duplicate complete rows: {duplicate_rows}")
print(f"Missing cells: {missing_cells:,}")
print(f"Quality report: {OUTPUT_DIR / 'part_d_quality_report.csv'}")
print(f"Missing values: {OUTPUT_DIR / 'part_d_missing_values.csv'}")
print(f"Fusion status: {OUTPUT_DIR / 'part_d_fusion_status.csv'}")
print(f"API completeness: {OUTPUT_DIR / 'part_d_matched_api_completeness.csv'}")
print(f"Outlier report: {OUTPUT_DIR / 'part_d_potential_outliers.csv'}")
print("\nNo data has been deleted or overwritten.")
print("Review flagged issues before deciding on corrections.")
