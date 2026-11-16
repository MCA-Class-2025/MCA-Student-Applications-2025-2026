
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# 1. PATHS AND DATA LOADING
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "SecureShare_Fused_Dataset.csv"
OUTPUT_DIR = BASE_DIR / "outputs" / "eda"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Fused dataset not found: {DATA_PATH}\n"
        "Run python src/merge_datasets.py first."
    )

df = pd.read_csv(DATA_PATH, low_memory=False)

print("=" * 65)
print("FUSED DATASET: QUALITY ASSESSMENT AND EDA")
print("=" * 65)
print(f"Input file: {DATA_PATH}")
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")


# ============================================================
# 2. DATA STRUCTURE AND QUALITY REPORTS
# ============================================================

structure = pd.DataFrame({
    "Column": df.columns,
    "Data Type": [str(df[c].dtype) for c in df.columns],
    "Non-Null Count": [int(df[c].notna().sum()) for c in df.columns],
    "Missing Count": [int(df[c].isna().sum()) for c in df.columns],
    "Missing Percentage": [
        round(df[c].isna().mean() * 100, 2)
        for c in df.columns
    ],
    "Unique Values": [
        int(df[c].nunique(dropna=True))
        for c in df.columns
    ]
})

structure.to_csv(
    OUTPUT_DIR / "data_structure_quality.csv",
    index=False
)

missing_report = structure[
    ["Column", "Missing Count", "Missing Percentage"]
].sort_values(
    "Missing Count",
    ascending=False
)

missing_report.to_csv(
    OUTPUT_DIR / "missing_values_report.csv",
    index=False
)

duplicate_count = int(df.duplicated().sum())
missing_cells = int(df.isna().sum().sum())
total_cells = int(df.shape[0] * df.shape[1])

print("\n--- DATA QUALITY ---")
print(f"Duplicate complete rows: {duplicate_count}")
print(f"Missing cells: {missing_cells:,}")
print(
    "Missing cell percentage:",
    round(missing_cells / total_cells * 100, 2)
    if total_cells else 0
)

# Check that all original authentication columns remain.
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

print(
    "Missing original authentication columns:",
    missing_original_columns if missing_original_columns else "None"
)

print("\nColumns with most missing values:")
print(missing_report.head(10).to_string(index=False))


# ============================================================
# 3. CONVERT NUMERIC-LOOKING COLUMNS SAFELY
# ============================================================

# Work on a copy for analysis. The source CSV is not modified.
analysis_df = df.copy()

# Convert numeric-looking object columns only when at least 90%
# of their existing non-missing values can be parsed as numbers.
for col in analysis_df.columns:
    if analysis_df[col].dtype == "object":
        original_nonmissing = analysis_df[col].notna().sum()

        if original_nonmissing == 0:
            continue

        converted = pd.to_numeric(
            analysis_df[col],
            errors="coerce"
        )

        conversion_rate = (
            converted.notna().sum() / original_nonmissing
        )

        if conversion_rate >= 0.90:
            analysis_df[col] = converted

numeric_cols = analysis_df.select_dtypes(
    include=np.number
).columns.tolist()

# Identifier and categorical codes are not automatically treated
# as continuous measurements for correlation analysis.
numeric_analysis_cols = [
    col for col in numeric_cols
    if col.lower() not in {
        "user_id",
        "id",
        "privilege_level"
    }
    and not col.lower().endswith("_id")
]

print("\nNumeric columns identified:")
print(numeric_cols)


# ============================================================
# 4. NUMERIC SUMMARY STATISTICS
# ============================================================

if numeric_cols:
    numeric_summary = analysis_df[numeric_cols].describe().T
    numeric_summary.to_csv(
        OUTPUT_DIR / "numeric_summary.csv"
    )
else:
    numeric_summary = pd.DataFrame()
    print("No numeric columns available for summary statistics.")


# ============================================================
# 5. POTENTIAL OUTLIER ANALYSIS USING THE IQR METHOD
# ============================================================

outlier_rows = []

for col in numeric_cols:
    values = analysis_df[col].dropna()

    if len(values) < 4:
        continue

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    outlier_mask = (
        (values < lower_bound) |
        (values > upper_bound)
    )

    outlier_count = int(outlier_mask.sum())

    outlier_rows.append({
        "Column": col,
        "Q1": q1,
        "Q3": q3,
        "IQR": iqr,
        "Lower Bound": lower_bound,
        "Upper Bound": upper_bound,
        "Potential Outlier Count": outlier_count,
        "Potential Outlier Percentage": round(
            outlier_count / len(values) * 100, 2
        )
    })

outlier_report = pd.DataFrame(outlier_rows)

outlier_report.to_csv(
    OUTPUT_DIR / "potential_outliers_report.csv",
    index=False
)


# ============================================================
# 6. FUSION MATCH COVERAGE REPORT AND CHART
# ============================================================

match_column = "API_Match_Status"

if match_column in df.columns:
    match_counts = (
        df[match_column]
        .fillna("Unknown")
        .value_counts()
    )

    match_report = match_counts.rename_axis(
        "Match Status"
    ).reset_index(name="Row Count")

    match_report["Percentage"] = (
        match_report["Row Count"] / len(df) * 100
    ).round(2)

    match_report.to_csv(
        OUTPUT_DIR / "fusion_match_report.csv",
        index=False
    )

    fig, ax = plt.subplots(figsize=(8, 5))

    bars = ax.bar(
        match_counts.index.astype(str),
        match_counts.values
    )

    ax.set_title("Fusion Insight: API Match Coverage")
    ax.set_xlabel("API Match Status")
    ax.set_ylabel("Number of Authentication Rows")
    ax.tick_params(axis="x", rotation=12)

    for bar, count in zip(bars, match_counts.values):
        percentage = count / len(df) * 100 if len(df) else 0

        ax.annotate(
            f"{count:,}\n({percentage:.1f}%)",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom"
        )
    ax.set_ylim(0, max(match_counts.values) * 1.18)

    fig.tight_layout()
    fig.savefig(
        OUTPUT_DIR / "01_fusion_match_coverage.png",
        dpi=200
    )
    plt.close(fig)

else:
    print(
        "\nWARNING: API_Match_Status not found. "
        "Fusion coverage chart was not generated."
    )


# ============================================================
# 7. DISTRIBUTION HISTOGRAM
# ============================================================

preferred_distribution = [
    "failed_attempts",
    "session_duration",
    "privilege_level"
]

distribution_col = next(
    (
        col for col in preferred_distribution
        if col in analysis_df.columns
        and pd.api.types.is_numeric_dtype(analysis_df[col])
    ),
    numeric_analysis_cols[0] if numeric_analysis_cols else None
)

if distribution_col:
    values = analysis_df[distribution_col].dropna()

    if len(values):
        fig, ax = plt.subplots(figsize=(8, 5))

        # failed_attempts is discrete, so use one bin per integer
        # when its observed values are integer-like.
        if (
            distribution_col == "failed_attempts"
            and values.nunique() <= 30
            and np.allclose(values, np.round(values))
        ):
            bins = np.arange(
                values.min() - 0.5,
                values.max() + 1.5,
                1
            )
        else:
            bins = 30

        ax.hist(
            values,
            bins=bins,
            edgecolor="black"
        )

        ax.set_title(f"Distribution of {distribution_col}")
        ax.set_xlabel(distribution_col)
        ax.set_ylabel("Frequency")

        fig.tight_layout()
        fig.savefig(
            OUTPUT_DIR / "02_distribution.png",
            dpi=200
        )
        plt.close(fig)


# ============================================================
# 8. BOXPLOT
# ============================================================

preferred_box = [
    "session_duration",
    "failed_attempts",
    "privilege_level"
]

box_col = next(
    (
        col for col in preferred_box
        if col in analysis_df.columns
        and pd.api.types.is_numeric_dtype(analysis_df[col])
    ),
    numeric_analysis_cols[0] if numeric_analysis_cols else None
)

if box_col:
    values = analysis_df[box_col].dropna()

    if len(values):
        fig, ax = plt.subplots(figsize=(7, 5))

        ax.boxplot(
            values,
            orientation="vertical"
        )

        ax.set_title(f"Boxplot of {box_col}")
        ax.set_ylabel(box_col)

        fig.tight_layout()
        fig.savefig(
            OUTPUT_DIR / "03_boxplot.png",
            dpi=200
        )
        plt.close(fig)


# ============================================================
# 9. RELATIONSHIP PLOT 1
# Session duration grouped by failed-attempt count
# ============================================================

if (
    "failed_attempts" in analysis_df.columns
    and "session_duration" in analysis_df.columns
):
    plot_data = analysis_df[
        ["failed_attempts", "session_duration"]
    ].copy()

    plot_data["failed_attempts"] = pd.to_numeric(
        plot_data["failed_attempts"],
        errors="coerce"
    )

    plot_data["session_duration"] = pd.to_numeric(
        plot_data["session_duration"],
        errors="coerce"
    )

    plot_data = plot_data.dropna()

    grouped = plot_data.groupby(
        "failed_attempts",
        sort=True
    )

    group_values = [
        group["session_duration"].to_numpy()
        for _, group in grouped
        if len(group) > 0
    ]

    group_labels = [
        str(value)
        for value, group in grouped
        if len(group) > 0
    ]

    if group_values:
        fig, ax = plt.subplots(figsize=(10, 5))

        ax.boxplot(
            group_values,
            tick_labels=group_labels
        )

        ax.set_title(
            "Session Duration by Number of Failed Attempts"
        )
        ax.set_xlabel("Failed Attempts")
        ax.set_ylabel("Session Duration")

        fig.tight_layout()
        fig.savefig(
            OUTPUT_DIR / "04_relationship_scatter.png",
            dpi=200
        )
        plt.close(fig)



# ============================================================
# 10. RELATIONSHIP PLOT 2
# Distribution of failed attempts by API match status
# ============================================================

if (
    match_column in df.columns
    and "failed_attempts" in analysis_df.columns
):
    plot_data = pd.DataFrame({
        "API_Match_Status": df[match_column],
        "failed_attempts": analysis_df["failed_attempts"]
    })

    plot_data["API_Match_Status"] = (
        plot_data["API_Match_Status"].fillna("Unknown")
    )

    plot_data["failed_attempts"] = pd.to_numeric(
        plot_data["failed_attempts"],
        errors="coerce"
    )

    plot_data = plot_data.dropna(
        subset=["failed_attempts"]
    )

    # Compare the percentage distribution within each match group
    distribution = pd.crosstab(
        plot_data["failed_attempts"],
        plot_data["API_Match_Status"],
        normalize="columns"
    ) * 100

    fig, ax = plt.subplots(figsize=(10, 5))

    distribution.plot(
        kind="bar",
        ax=ax,
        width=0.8
    )

    ax.set_title(
        "Distribution of Failed Attempts by API Match Status"
    )
    ax.set_xlabel("Failed Attempts")
    ax.set_ylabel("Percentage of Records (%)")
    ax.legend(title="API Match Status")

    ax.tick_params(axis="x", rotation=0)

    fig.tight_layout()
    fig.savefig(
        OUTPUT_DIR / "05_relationship_match_status.png",
        dpi=200
    )
    plt.close(fig)



# ============================================================
# 11. CORRELATION HEATMAP
# Include original and API-derived numerical variables
# ============================================================

corr_candidates = [
    "failed_attempts",
    "session_duration",
    "AbuseIPDB Total Reports"
]

corr_cols = [
    col for col in corr_candidates
    if col in analysis_df.columns
]

corr_data = analysis_df[corr_cols].apply(
    pd.to_numeric,
    errors="coerce"
)

# Exclude columns with no variation
corr_data = corr_data.loc[
    :, corr_data.nunique(dropna=True) > 1
]

if len(corr_data.columns) >= 2:

    corr = corr_data.corr(
        method="pearson",
        min_periods=2
    )

    corr.to_csv(
        OUTPUT_DIR / "correlation_matrix.csv"
    )

    fig, ax = plt.subplots(figsize=(8, 6))

    image = ax.imshow(
        corr.to_numpy(),
        vmin=-1,
        vmax=1,
        cmap="coolwarm"
    )

    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.columns)))

    ax.set_xticklabels(
        corr.columns,
        rotation=30,
        ha="right"
    )

    ax.set_yticklabels(corr.columns)

    for i in range(len(corr.columns)):
        for j in range(len(corr.columns)):
            value = corr.iloc[i, j]

            if pd.notna(value):
                ax.text(
                    j, i,
                    f"{value:.2f}",
                    ha="center",
                    va="center"
                )

    ax.set_title(
        "Correlation Heatmap: Authentication and API Variables"
    )

    fig.colorbar(
        image,
        ax=ax,
        label="Pearson Correlation Coefficient"
    )

    fig.tight_layout()

    fig.savefig(
        OUTPUT_DIR / "06_correlation_heatmap.png",
        dpi=200
    )

    plt.close(fig)

else:
    print("Not enough variable numerical columns for heatmap.")



# ============================================================
# 12. QUALITY SUMMARY
# ============================================================

summary_rows = [
    {"Metric": "Total rows", "Value": len(df)},
    {"Metric": "Total columns", "Value": len(df.columns)},
    {"Metric": "Duplicate complete rows", "Value": duplicate_count},
    {"Metric": "Missing cells", "Value": missing_cells},
    {
        "Metric": "Missing cell percentage",
        "Value": round(
            missing_cells / total_cells * 100, 2
        ) if total_cells else 0
    },
    {
        "Metric": "Original columns missing",
        "Value": len(missing_original_columns)
    }
]

if match_column in df.columns:
    matched_count = int(
        (df[match_column] == "Matched").sum()
    )

    summary_rows.extend([
        {"Metric": "Matched rows", "Value": matched_count},
        {
            "Metric": "Unmatched rows",
            "Value": len(df) - matched_count
        },
        {
            "Metric": "API match coverage percentage",
            "Value": round(
                matched_count / len(df) * 100, 2
            ) if len(df) else 0
        }
    ])

pd.DataFrame(summary_rows).to_csv(
    OUTPUT_DIR / "quality_summary.csv",
    index=False
)


# ============================================================
# 13. COMPLETION MESSAGE
# ============================================================

print("\n" + "=" * 65)
print("ANALYSIS COMPLETED")
print("=" * 65)

print(f"Rows analysed: {len(df)}")
print(f"Columns analysed: {len(df.columns)}")
print(f"Duplicate complete rows: {duplicate_count}")
print(f"Missing cells: {missing_cells:,}")

print(f"\nReports and charts saved to:\n{OUTPUT_DIR}")

print("\nExpected chart files:")
for filename in [
    "01_fusion_match_coverage.png",
    "02_distribution.png",
    "03_boxplot.png",
    "04_relationship_scatter.png",
    "05_relationship_match_status.png",
    "06_correlation_heatmap.png"
]:
    print(f" - {filename}")

print("\nReview the generated reports before writing conclusions.")
print("Potential outliers are flagged for review, not deleted.")
