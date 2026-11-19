# ============================================================
# PART E - ALPHA VANTAGE EXPLORATORY DATA ANALYSIS
# ============================================================
#
# This script:
# 1. Reads the fused Alpha Vantage CSV
# 2. Performs data inspection
# 3. Performs univariate analysis
# 4. Performs bivariate analysis
# 5. Performs multivariate analysis
# 6. Saves all results INSIDE the EDA folder
#
# ============================================================

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


# ============================================================
# 1. PATH CONFIGURATION
# ============================================================

# Current file location:
# PersonalFinanceRAG/EDA/alpha_vantage_eda.py

EDA_DIR = os.path.dirname(os.path.abspath(__file__))

# Project root:
# PersonalFinanceRAG/
PROJECT_ROOT = os.path.dirname(EDA_DIR)

# Original fused Alpha Vantage CSV
FUSED_ALPHA_CSV = os.path.join(
    PROJECT_ROOT,
    "csv",
    "fused",
    "fused_alpha_vantage.csv"
)

# All EDA output stays inside EDA/
OUTPUT_DIR = os.path.join(
    EDA_DIR,
    "Alpha_Vantage_Results"
)

STATISTICS_DIR = os.path.join(
    OUTPUT_DIR,
    "statistics"
)

UNIVARIATE_DIR = os.path.join(
    OUTPUT_DIR,
    "univariate"
)

BIVARIATE_DIR = os.path.join(
    OUTPUT_DIR,
    "bivariate"
)

MULTIVARIATE_DIR = os.path.join(
    OUTPUT_DIR,
    "multivariate"
)


# ============================================================
# 2. CREATE OUTPUT DIRECTORIES
# ============================================================

for directory in [
    OUTPUT_DIR,
    STATISTICS_DIR,
    UNIVARIATE_DIR,
    BIVARIATE_DIR,
    MULTIVARIATE_DIR
]:
    os.makedirs(
        directory,
        exist_ok=True
    )


# ============================================================
# 3. CHECK WHETHER FUSED CSV EXISTS
# ============================================================

print("\n==============================================")
print("ALPHA VANTAGE EDA")
print("==============================================")

print("\nChecking fused CSV:")

print(FUSED_ALPHA_CSV)

if not os.path.exists(FUSED_ALPHA_CSV):

    print("\nERROR:")
    print("fused_alpha_vantage.csv was not found.")

    print("\nExpected location:")

    print(FUSED_ALPHA_CSV)

    print(
        "\nMake sure your RAG has generated "
        "csv/fused/fused_alpha_vantage.csv first."
    )

    raise FileNotFoundError(
        FUSED_ALPHA_CSV
    )


# ============================================================
# 4. READ FUSED ALPHA CSV
# ============================================================

df = pd.read_csv(
    FUSED_ALPHA_CSV
)

print("\nAlpha fused dataset loaded successfully.")


# ============================================================
# 5. BASIC DATA INFORMATION
# ============================================================

print("\n==============================================")
print("DATASET INFORMATION")
print("==============================================")

print(
    "\nNumber of rows:",
    len(df)
)

print(
    "Number of columns:",
    len(df.columns)
)

print(
    "\nColumns:"
)

for column in df.columns:
    print(
        "-",
        column
    )


# ============================================================
# 6. SAVE DATASET INFORMATION
# ============================================================

info_file = os.path.join(
    STATISTICS_DIR,
    "alpha_dataset_info.txt"
)

with open(
    info_file,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "ALPHA VANTAGE FUSED DATASET INFORMATION\n"
    )

    file.write(
        "========================================\n\n"
    )

    file.write(
        f"Rows: {len(df)}\n"
    )

    file.write(
        f"Columns: {len(df.columns)}\n\n"
    )

    file.write(
        "Columns:\n"
    )

    for column in df.columns:

        file.write(
            f"- {column}\n"
        )

    file.write(
        "\nData Types:\n"
    )

    file.write(
        str(df.dtypes)
    )

    file.write(
        "\n\nMissing Values:\n"
    )

    file.write(
        str(df.isnull().sum())
    )


# ============================================================
# 7. MISSING VALUE ANALYSIS
# ============================================================

missing_values = pd.DataFrame({
    "Column": df.columns,
    "Missing_Count": [
        df[column].isnull().sum()
        for column in df.columns
    ]
})

missing_values["Missing_Percentage"] = (
    missing_values["Missing_Count"]
    / len(df)
    * 100
)

missing_file = os.path.join(
    STATISTICS_DIR,
    "alpha_missing_values.csv"
)

missing_values.to_csv(
    missing_file,
    index=False
)


# ============================================================
# 8. NUMERICAL COLUMNS
# ============================================================

preferred_numeric_columns = [
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "SMA_10",
    "EMA_10",
    "Volatility",
    "Wavelet_Trend",
    "Wavelet_Noise",
    "Wavelet_HighFreq",
    "General_Index",
    "Economic_Score",
    "Close_Next"
]


# Keep only columns that actually exist
numeric_columns = [
    column
    for column in preferred_numeric_columns
    if column in df.columns
]


# Convert numerical columns to numeric
for column in numeric_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


print("\n==============================================")
print("NUMERICAL COLUMNS")
print("==============================================")

for column in numeric_columns:

    print(
        "-",
        column
    )


# ============================================================
# 9. UNIVARIATE STATISTICS
# ============================================================

print("\n==============================================")
print("UNIVARIATE STATISTICS")
print("==============================================")


summary = df[numeric_columns].describe(
    percentiles=[
        0.25,
        0.50,
        0.75
    ]
).T


summary = summary.rename(
    columns={
        "25%": "Q1",
        "50%": "Median",
        "75%": "Q3"
    }
)


summary["Mean"] = df[
    numeric_columns
].mean()

summary["Median"] = df[
    numeric_columns
].median()

summary["Std_Deviation"] = df[
    numeric_columns
].std()

summary["Minimum"] = df[
    numeric_columns
].min()

summary["Maximum"] = df[
    numeric_columns
].max()

summary["Q1"] = df[
    numeric_columns
].quantile(
    0.25
)

summary["Q3"] = df[
    numeric_columns
].quantile(
    0.75
)


summary = summary[
    [
        "count",
        "Mean",
        "Median",
        "Std_Deviation",
        "Minimum",
        "Q1",
        "Q3",
        "Maximum"
    ]
]


summary = summary.round(
    4
)


summary_file = os.path.join(
    STATISTICS_DIR,
    "alpha_summary_statistics.csv"
)

summary.to_csv(
    summary_file
)


print(
    summary
)


# ============================================================
# 10. UNIVARIATE HISTOGRAMS
# ============================================================

print("\n==============================================")
print("CREATING HISTOGRAMS")
print("==============================================")


histogram_columns = [
    "Close",
    "Volume",
    "Volatility",
    "Economic_Score"
]


for column in histogram_columns:

    if column not in df.columns:
        continue

    data = df[column].dropna()

    if data.empty:
        continue

    plt.figure(
        figsize=(9, 6)
    )

    plt.hist(
        data,
        bins=20
    )

    plt.title(
        f"Distribution of {column}"
    )

    plt.xlabel(
        column
    )

    plt.ylabel(
        "Frequency"
    )

    plt.tight_layout()

    output_file = os.path.join(
        UNIVARIATE_DIR,
        f"histogram_{column.lower()}.png"
    )

    plt.savefig(
        output_file,
        dpi=300
    )

    plt.close()

    print(
        "Saved:",
        output_file
    )


# ============================================================
# 11. UNIVARIATE BOXPLOTS
# ============================================================

print("\n==============================================")
print("CREATING BOXPLOTS")
print("==============================================")


boxplot_columns = [
    "Close",
    "Volume",
    "Volatility",
    "Economic_Score"
]


for column in boxplot_columns:

    if column not in df.columns:
        continue

    data = df[column].dropna()

    if data.empty:
        continue

    plt.figure(
        figsize=(8, 5)
    )

    plt.boxplot(
        data
    )

    plt.title(
        f"Boxplot of {column}"
    )

    plt.ylabel(
        column
    )

    plt.tight_layout()

    output_file = os.path.join(
        UNIVARIATE_DIR,
        f"boxplot_{column.lower()}.png"
    )

    plt.savefig(
        output_file,
        dpi=300
    )

    plt.close()

    print(
        "Saved:",
        output_file
    )


# ============================================================
# 12. MARKET SENTIMENT BAR CHART
# ============================================================

if "Market_Sentiment" in df.columns:

    sentiment_counts = (
        df["Market_Sentiment"]
        .fillna("Unknown")
        .value_counts()
    )

    plt.figure(
        figsize=(8, 5)
    )

    sentiment_counts.plot(
        kind="bar"
    )

    plt.title(
        "Market Sentiment Distribution"
    )

    plt.xlabel(
        "Market Sentiment"
    )

    plt.ylabel(
        "Number of Records"
    )

    plt.xticks(
        rotation=0
    )

    plt.tight_layout()

    output_file = os.path.join(
        UNIVARIATE_DIR,
        "market_sentiment_bar.png"
    )

    plt.savefig(
        output_file,
        dpi=300
    )

    plt.close()

    print(
        "Saved:",
        output_file
    )


# ============================================================
# 13. BIVARIATE ANALYSIS
# ============================================================

print("\n==============================================")
print("BIVARIATE ANALYSIS")
print("==============================================")


bivariate_pairs = [
    (
        "Close",
        "Close_Next",
        "Close vs Close_Next"
    ),

    (
        "Volume",
        "Close",
        "Volume vs Close"
    ),

    (
        "Volatility",
        "Close",
        "Volatility vs Close"
    ),

    (
        "Economic_Score",
        "Close",
        "Economic Score vs Close"
    )
]


bivariate_results = []


for x_column, y_column, title in bivariate_pairs:

    if (
        x_column not in df.columns
        or y_column not in df.columns
    ):
        continue

    plot_df = df[
        [
            x_column,
            y_column
        ]
    ].dropna()

    if len(plot_df) < 2:
        continue

    correlation = plot_df[
        x_column
    ].corr(
        plot_df[y_column]
    )

    bivariate_results.append({
        "Variable_1": x_column,
        "Variable_2": y_column,
        "Correlation": correlation
    })


    plt.figure(
        figsize=(9, 6)
    )

    plt.scatter(
        plot_df[x_column],
        plot_df[y_column]
    )

    plt.title(
        title
    )

    plt.xlabel(
        x_column
    )

    plt.ylabel(
        y_column
    )

    plt.tight_layout()

    filename = (
        x_column.lower()
        + "_vs_"
        + y_column.lower()
        + ".png"
    )

    output_file = os.path.join(
        BIVARIATE_DIR,
        filename
    )

    plt.savefig(
        output_file,
        dpi=300
    )

    plt.close()

    print(
        "Saved:",
        output_file
    )


# ============================================================
# 14. SAVE BIVARIATE CORRELATIONS
# ============================================================

bivariate_correlation_df = pd.DataFrame(
    bivariate_results
)

bivariate_file = os.path.join(
    BIVARIATE_DIR,
    "bivariate_correlations.csv"
)

bivariate_correlation_df.to_csv(
    bivariate_file,
    index=False
)


# ============================================================
# 15. MULTIVARIATE CORRELATION MATRIX
# ============================================================

print("\n==============================================")
print("MULTIVARIATE ANALYSIS")
print("==============================================")


correlation_matrix = df[
    numeric_columns
].corr()


correlation_matrix_file = os.path.join(
    MULTIVARIATE_DIR,
    "alpha_correlation_matrix.csv"
)

correlation_matrix.to_csv(
    correlation_matrix_file
)


# ============================================================
# 16. CORRELATION HEATMAP
# ============================================================

plt.figure(
    figsize=(15, 12)
)

sns.heatmap(
    correlation_matrix,
    annot=True,
    fmt=".2f",
    center=0
)

plt.title(
    "Alpha Vantage Fused Dataset - Correlation Heatmap"
)

plt.tight_layout()


heatmap_file = os.path.join(
    MULTIVARIATE_DIR,
    "alpha_correlation_heatmap.png"
)

plt.savefig(
    heatmap_file,
    dpi=300
)

plt.close()


print(
    "Saved:",
    heatmap_file
)


# ============================================================
# 17. FINAL OUTPUT
# ============================================================

print("\n==============================================")
print("ALPHA VANTAGE EDA COMPLETED")
print("==============================================")

print("\nInput dataset:")

print(
    FUSED_ALPHA_CSV
)

print("\nAll EDA results saved inside:")

print(
    OUTPUT_DIR
)

print("\nFolder structure:")

print(
    """
Alpha_Vantage_Results/
│
├── statistics/
│   ├── alpha_dataset_info.txt
│   ├── alpha_missing_values.csv
│   └── alpha_summary_statistics.csv
│
├── univariate/
│   ├── histogram_close.png
│   ├── histogram_volume.png
│   ├── histogram_volatility.png
│   ├── histogram_economic_score.png
│   ├── boxplot_close.png
│   ├── boxplot_volume.png
│   ├── boxplot_volatility.png
│   ├── boxplot_economic_score.png
│   └── market_sentiment_bar.png
│
├── bivariate/
│   ├── close_vs_close_next.png
│   ├── volume_vs_close.png
│   ├── volatility_vs_close.png
│   ├── economic_score_vs_close.png
│   └── bivariate_correlations.csv
│
└── multivariate/
    ├── alpha_correlation_matrix.csv
    └── alpha_correlation_heatmap.png
"""
)

print(
    "\nYou can now use the generated PNG files "
    "as screenshots/figures for Part E."
)