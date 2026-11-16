
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
df = pd.read_csv(BASE_DIR / "SecureShare_Fused_Dataset.csv")

print("=" * 60)
print("FUSION VALIDATION AND INITIAL INSIGHTS")
print("=" * 60)

# 1. Validate expected structure
print("\n1. DATASET STRUCTURE")
print("Rows:", len(df))
print("Columns:", len(df.columns))

original_columns = [
    "user_id", "ip_address", "device_type", "os_type", "browser",
    "success", "account_status", "failed_attempts",
    "session_duration", "role", "privilege_level",
    "suspicious_activity", "blocked"
]

missing_original = [c for c in original_columns if c not in df.columns]
print("Missing original columns:", missing_original or "None")

# 2. Match coverage
print("\n2. API MATCH COVERAGE")
if "API_Match_Status" in df.columns:
    print(df["API_Match_Status"].value_counts(dropna=False).to_string())
else:
    print("API_Match_Status column not found.")

# 3. API field availability among matched records
api_cols = [
    c for c in df.columns
    if c.startswith("AbuseIPDB ") or c.startswith("IPinfo ")
]

if "API_Match_Status" in df.columns:
    matched = df[df["API_Match_Status"] == "Matched"].copy()
else:
    matched = pd.DataFrame()

print("\n3. API DATA COMPLETENESS AMONG MATCHED ROWS")
print("Matched rows:", len(matched))

if len(matched):
    rows = []
    for col in api_cols:
        available = matched[col].notna()
        # Empty strings are also treated as unavailable values.
        if matched[col].dtype == "object":
            available = available & matched[col].astype(str).str.strip().ne("")

        rows.append({
            "API Column": col,
            "Available Values": int(available.sum()),
            "Missing/Blank Values": int((~available).sum()),
            "Availability %": round(available.mean() * 100, 2)
        })

    availability = pd.DataFrame(rows).sort_values("Availability %")
    print(availability.to_string(index=False))
    availability.to_csv(
        BASE_DIR / "outputs" / "eda" / "matched_api_completeness.csv",
        index=False
    )

# 4. Initial authentication statistics
print("\n4. AUTHENTICATION STATISTICS")

for col in ["success", "account_status", "suspicious_activity", "blocked"]:
    if col in df.columns:
        print(f"\n{col} distribution:")
        print(df[col].value_counts(dropna=False).head(15).to_string())

for col in ["failed_attempts", "session_duration", "privilege_level"]:
    if col in df.columns:
        numeric = pd.to_numeric(df[col], errors="coerce")
        print(f"\n{col} summary:")
        print(numeric.describe().round(2).to_string())

# 5. Relationships worth investigating
print("\n5. FAILED ATTEMPTS BY AUTHENTICATION OUTCOME")
if "success" in df.columns and "failed_attempts" in df.columns:
    temp = df[["success", "failed_attempts"]].copy()
    temp["failed_attempts"] = pd.to_numeric(
        temp["failed_attempts"], errors="coerce"
    )
    print(
        temp.groupby("success")["failed_attempts"]
        .agg(["count", "mean", "median", "max"])
        .round(2).to_string()
    )

print("\n6. SUSPICIOUS ACTIVITY VS BLOCKED STATUS")
if "suspicious_activity" in df.columns and "blocked" in df.columns:
    print(pd.crosstab(
        df["suspicious_activity"],
        df["blocked"],
        margins=True
    ).to_string())

print("\nValidation complete.")
print("Detailed matched API completeness saved in outputs/eda.")
