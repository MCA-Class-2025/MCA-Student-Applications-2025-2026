import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


# ============================================================
# PHASE 1 - PART D : DATA QUALITY ASSESSMENT
# ============================================================

print("=" * 90)
print("PHASE 1 - PART D : DATA QUALITY ASSESSMENT")
print("=" * 90)


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "fused_dataset.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "data_quality_phase1"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


print("\nProject root:")
print(PROJECT_ROOT)

print("\nFused dataset:")
print(INPUT_FILE)

print("\nOutput directory:")
print(OUTPUT_DIR)


# ============================================================
# LOAD DATASET
# ============================================================

print("\n" + "=" * 90)
print("LOADING FUSED DATASET")
print("=" * 90)

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"\nFused dataset not found:\n{INPUT_FILE}"
    )

df = pd.read_csv(
    INPUT_FILE,
    low_memory=False
)

print("Dataset loaded successfully.")

print("Rows       :", len(df))
print("Columns    :", len(df.columns))


# ============================================================
# 1. STRUCTURAL CHECKS
# ============================================================

print("\n" + "=" * 90)
print("1. STRUCTURAL CHECKS")
print("=" * 90)


# ------------------------------------------------------------
# Dataset dimensions
# ------------------------------------------------------------

rows = len(df)
columns = len(df.columns)

print("\nDataset dimensions:")
print("Rows       :", rows)
print("Attributes :", columns)


dimension_summary = pd.DataFrame({
    "parameter": [
        "Number of records",
        "Number of attributes"
    ],
    "value": [
        rows,
        columns
    ]
})

dimension_summary.to_csv(
    OUTPUT_DIR / "01_dataset_dimensions.csv",
    index=False
)


# ------------------------------------------------------------
# Data types
# ------------------------------------------------------------

print("\nData types:")
print(df.dtypes)

data_types = pd.DataFrame({
    "attribute": df.columns,
    "data_type": [
        str(dtype) for dtype in df.dtypes
    ]
})

data_types.to_csv(
    OUTPUT_DIR / "02_data_types.csv",
    index=False
)


# ------------------------------------------------------------
# Unique values
# ------------------------------------------------------------

print("\nUnique values:")

unique_values = pd.DataFrame({
    "attribute": df.columns,
    "unique_values": [
        df[col].nunique(dropna=True)
        for col in df.columns
    ]
})

print(unique_values.to_string(index=False))

unique_values.to_csv(
    OUTPUT_DIR / "03_unique_values.csv",
    index=False
)


# ------------------------------------------------------------
# Duplicate rows
# ------------------------------------------------------------

duplicate_rows = int(
    df.duplicated().sum()
)

print("\nDuplicate records:")
print("Exact duplicate rows:", duplicate_rows)


# ============================================================
# DUPLICATE IDENTIFIER CHECK
# ============================================================

print("\nDuplicate identifiers:")

identifier_columns = [
    "fused_id",
    "original_id",
    "api_id",
    "url"
]

identifier_results = []

for col in identifier_columns:

    if col in df.columns:

        non_null = df[col].dropna()

        duplicate_count = int(
            non_null.duplicated().sum()
        )

        unique_count = int(
            non_null.nunique()
        )

        identifier_results.append({
            "attribute": col,
            "non_null_values": len(non_null),
            "unique_values": unique_count,
            "duplicate_values": duplicate_count
        })

        print(
            f"{col}: "
            f"unique={unique_count}, "
            f"duplicates={duplicate_count}"
        )


identifier_summary = pd.DataFrame(
    identifier_results
)

identifier_summary.to_csv(
    OUTPUT_DIR / "04_duplicate_identifiers.csv",
    index=False
)


# ============================================================
# 2. MISSING DATA
# ============================================================

print("\n" + "=" * 90)
print("2. MISSING DATA ANALYSIS")
print("=" * 90)


missing_count = df.isna().sum()

missing_percentage = (
    missing_count / len(df) * 100
)

empty_string_count = pd.Series(
    {
        col: int(
            df[col]
            .astype(str)
            .str.strip()
            .eq("")
            .sum()
        )
        for col in df.columns
    }
)

missing_summary = pd.DataFrame({
    "attribute": df.columns,
    "missing_count": [
        int(missing_count[col])
        for col in df.columns
    ],
    "missing_percentage": [
        round(float(missing_percentage[col]), 2)
        for col in df.columns
    ],
    "empty_string_count": [
        int(empty_string_count[col])
        for col in df.columns
    ]
})

print(
    missing_summary.to_string(index=False)
)

missing_summary.to_csv(
    OUTPUT_DIR / "05_missing_data.csv",
    index=False
)


# ------------------------------------------------------------
# Maximum missing data
# ------------------------------------------------------------

max_missing = missing_summary.sort_values(
    "missing_percentage",
    ascending=False
)

print("\nAttributes with maximum missing data:")

print(
    max_missing.head(10).to_string(index=False)
)


# ============================================================
# 3. DATA QUALITY BY RECORD TYPE
# ============================================================

print("\n" + "=" * 90)
print("3. QUALITY BY RECORD TYPE")
print("=" * 90)


if "record_type" in df.columns:

    record_type_summary = []

    for record_type, group in df.groupby(
        "record_type",
        dropna=False
    ):

        record_type_summary.append({
            "record_type": record_type,
            "records": len(group),
            "duplicate_rows": int(
                group.duplicated().sum()
            ),
            "missing_values": int(
                group.isna().sum().sum()
            )
        })

    record_type_summary = pd.DataFrame(
        record_type_summary
    )

    print(
        record_type_summary.to_string(
            index=False
        )
    )

    record_type_summary.to_csv(
        OUTPUT_DIR / "06_quality_by_record_type.csv",
        index=False
    )


# ============================================================
# 4. CONSISTENCY CHECKS
# ============================================================

print("\n" + "=" * 90)
print("4. CONSISTENCY CHECKS")
print("=" * 90)


# ------------------------------------------------------------
# Categorical consistency
# ------------------------------------------------------------

categorical_columns = [
    "record_type",
    "label",
    "subject",
    "api",
    "api_source",
    "language",
    "topic"
]

categorical_results = []

for col in categorical_columns:

    if col in df.columns:

        values = (
            df[col]
            .dropna()
            .astype(str)
            .str.strip()
        )

        value_counts = (
            values
            .value_counts()
            .reset_index()
        )

        value_counts.columns = [
            "value",
            "count"
        ]

        for _, row in value_counts.iterrows():

            categorical_results.append({
                "attribute": col,
                "value": row["value"],
                "count": int(row["count"])
            })

        print(
            f"\n{col}:"
        )

        print(
            value_counts.head(20).to_string(
                index=False
            )
        )


categorical_summary = pd.DataFrame(
    categorical_results
)

categorical_summary.to_csv(
    OUTPUT_DIR / "07_categorical_consistency.csv",
    index=False
)


# ============================================================
# DATE/TIME CONSISTENCY
# ============================================================

print("\n" + "=" * 90)
print("5. DATE/TIME CONSISTENCY")
print("=" * 90)


date_columns = [
    "date",
    "published",
    "published_at",
    "retrieved_at"
]

date_results = []

for col in date_columns:

    if col not in df.columns:
        continue

    parsed_dates = pd.to_datetime(
        df[col],
        errors="coerce",
        utc=True
    )

    valid = int(
        parsed_dates.notna().sum()
    )

    invalid = int(
        parsed_dates.isna().sum()
    )

    earliest = (
        parsed_dates.min()
        if valid > 0
        else None
    )

    latest = (
        parsed_dates.max()
        if valid > 0
        else None
    )

    date_results.append({
        "attribute": col,
        "valid_dates": valid,
        "invalid_dates": invalid,
        "earliest_date": earliest,
        "latest_date": latest
    })

    print(f"\n{col}")
    print("Valid dates   :", valid)
    print("Invalid dates :", invalid)
    print("Earliest      :", earliest)
    print("Latest        :", latest)


date_summary = pd.DataFrame(
    date_results
)

date_summary.to_csv(
    OUTPUT_DIR / "08_date_consistency.csv",
    index=False
)


# ============================================================
# TEXT CONSISTENCY
# ============================================================

print("\n" + "=" * 90)
print("6. TEXT CONSISTENCY")
print("=" * 90)


text_columns = [
    "title",
    "text",
    "description"
]

text_results = []

for col in text_columns:

    if col not in df.columns:
        continue

    series = df[col].fillna("").astype(str)

    whitespace_count = int(
        series.str.strip().eq("").sum()
    )

    text_results.append({
        "attribute": col,
        "empty_or_whitespace": whitespace_count,
        "minimum_length": int(
            series.str.len().min()
        ),
        "maximum_length": int(
            series.str.len().max()
        ),
        "mean_length": round(
            float(series.str.len().mean()),
            2
        )
    })


text_summary = pd.DataFrame(
    text_results
)

print(
    text_summary.to_string(index=False)
)

text_summary.to_csv(
    OUTPUT_DIR / "09_text_consistency.csv",
    index=False
)


# ============================================================
# 7. ORIGINAL VS API CONFLICT CHECK
# ============================================================

print("\n" + "=" * 90)
print("7. ORIGINAL VS API CONFLICT CHECK")
print("=" * 90)


conflict_results = []

# Check only records that have both original and API information
if (
    "original_id" in df.columns
    and "api_id" in df.columns
):

    both_sources = df[
        df["original_id"].notna()
        & df["api_id"].notna()
    ].copy()

    print(
        "Records containing both original and API data:",
        len(both_sources)
    )

    comparison_pairs = [
        ("title", "title"),
        ("date", "published"),
        ("source", "api_source")
    ]

    for original_col, api_col in comparison_pairs:

        if (
            original_col in both_sources.columns
            and api_col in both_sources.columns
        ):

            left = (
                both_sources[original_col]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.lower()
            )

            right = (
                both_sources[api_col]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.lower()
            )

            conflicts = int(
                (left != right).sum()
            )

            conflict_results.append({
                "original_attribute": original_col,
                "api_attribute": api_col,
                "records_compared": len(both_sources),
                "conflicting_values": conflicts
            })

            print(
                f"{original_col} vs {api_col}:",
                conflicts,
                "conflicts"
            )

else:

    print(
        "No records contain both original and API identifiers."
    )

    print(
        "Therefore direct source-to-source conflict comparison "
        "cannot be performed."
    )


conflict_summary = pd.DataFrame(
    conflict_results
)

conflict_summary.to_csv(
    OUTPUT_DIR / "10_source_conflicts.csv",
    index=False
)


# ============================================================
# 8. OUTLIER ANALYSIS USING IQR
# ============================================================

print("\n" + "=" * 90)
print("8. OUTLIER ANALYSIS USING IQR")
print("=" * 90)


# Automatically detect numerical columns
numeric_columns = df.select_dtypes(
    include=[np.number]
).columns.tolist()


outlier_results = []

for col in numeric_columns:

    series = pd.to_numeric(
        df[col],
        errors="coerce"
    ).dropna()

    if len(series) < 4:
        continue

    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)

    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    outliers = series[
        (series < lower_bound)
        | (series > upper_bound)
    ]

    count = len(outliers)

    percentage = (
        count / len(series) * 100
    )

    outlier_results.append({
        "attribute": col,
        "Q1": round(float(q1), 4),
        "Q3": round(float(q3), 4),
        "IQR": round(float(iqr), 4),
        "lower_bound": round(
            float(lower_bound),
            4
        ),
        "upper_bound": round(
            float(upper_bound),
            4
        ),
        "outlier_count": count,
        "outlier_percentage": round(
            percentage,
            2
        )
    })

    print(f"\n{col}")
    print("Q1              :", round(q1, 2))
    print("Q3              :", round(q3, 2))
    print("IQR             :", round(iqr, 2))
    print("Lower Bound     :", round(lower_bound, 2))
    print("Upper Bound     :", round(upper_bound, 2))
    print("Outliers        :", count)
    print(
        "Outlier %       :",
        round(percentage, 2)
    )


outlier_summary = pd.DataFrame(
    outlier_results
)

outlier_summary.to_csv(
    OUTPUT_DIR / "11_iqr_outlier_analysis.csv",
    index=False
)


# ============================================================
# 9. OUTLIER VISUALIZATION
# ============================================================

print("\nCreating outlier graphs...")


for col in numeric_columns:

    series = pd.to_numeric(
        df[col],
        errors="coerce"
    ).dropna()

    if len(series) < 4:
        continue

    plt.figure(figsize=(10, 6))

    plt.boxplot(
        series,
        tick_labels=[col]
    )

    plt.title(
        f"IQR Outlier Analysis - {col}"
    )

    plt.ylabel(col)

    plt.tight_layout()

    safe_name = (
        col
        .replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
    )

    plt.savefig(
        OUTPUT_DIR
        / f"outlier_{safe_name}.png",
        dpi=200,
        bbox_inches="tight"
    )

    plt.close()


# ============================================================
# 10. OVERALL QUALITY SUMMARY
# ============================================================

print("\n" + "=" * 90)
print("9. OVERALL DATA QUALITY SUMMARY")
print("=" * 90)


total_missing = int(
    df.isna().sum().sum()
)

total_empty = int(
    empty_string_count.sum()
)

quality_summary = pd.DataFrame({
    "metric": [
        "Total records",
        "Total attributes",
        "Duplicate rows",
        "Total missing values",
        "Total empty strings",
        "Numeric attributes checked for outliers"
    ],
    "value": [
        len(df),
        len(df.columns),
        duplicate_rows,
        total_missing,
        total_empty,
        len(numeric_columns)
    ]
})

print(
    quality_summary.to_string(index=False)
)

quality_summary.to_csv(
    OUTPUT_DIR / "12_overall_quality_summary.csv",
    index=False
)


# ============================================================
# FINAL REPORT
# ============================================================

print("\n" + "=" * 90)
print("PART D — DATA QUALITY ASSESSMENT COMPLETED")
print("=" * 90)

print("\nFinal fused dataset:")
print(INPUT_FILE)

print("\nRows:", len(df))
print("Columns:", len(df.columns))

print("\nOutput directory:")
print(OUTPUT_DIR)

print("\nGenerated files:")

for file in sorted(
    OUTPUT_DIR.iterdir()
):

    if file.is_file():
        print(" -", file.name)

print("\n" + "=" * 90)
print("READY FOR PHASE 1 REPORT - PART D")
print("=" * 90)