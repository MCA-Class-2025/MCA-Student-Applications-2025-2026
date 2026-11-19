import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

INPUT_FILE = os.path.join(
    BASE_DIR,
    "csv",
    "fused",
    "fused_frankfurter.csv"
)

EDA_DIR = os.path.join(
    BASE_DIR,
    "EDA",
    "Frankfurter"
)

PLOTS_DIR = os.path.join(
    EDA_DIR,
    "plots"
)

REPORT_DIR = os.path.join(
    EDA_DIR,
    "reports"
)

os.makedirs(EDA_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


# ============================================================
# LOAD DATASET
# ============================================================

print("\n======================================")
print("FRANKFURTER EDA")
print("======================================")

print("\nReading:")
print(INPUT_FILE)

if not os.path.exists(INPUT_FILE):

    print("\nERROR:")
    print("Frankfurter fused CSV was not found.")

    print("\nExpected location:")
    print(INPUT_FILE)

    raise FileNotFoundError(
        f"File not found: {INPUT_FILE}"
    )


df = pd.read_csv(INPUT_FILE)


print("\nDataset loaded successfully.")

print("\nNumber of rows:", len(df))
print("Number of columns:", len(df))


# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

df.columns = (
    df.columns
    .astype(str)
    .str.strip()
)


# ============================================================
# DISPLAY DATASET INFORMATION
# ============================================================

print("\n======================================")
print("DATASET COLUMNS")
print("======================================")

for column in df.columns:
    print(column)


# ============================================================
# IMPORTANT FRANKFURTER COLUMNS
# ============================================================

economic_columns = [
    "GDP (in billion USD)",
    "Inflation Rate (%)",
    "Unemployment Rate (%)",
    "Economic Growth (%)"
]


# ============================================================
# CHECK AVAILABLE COLUMNS
# ============================================================

available_columns = []

for column in economic_columns:

    if column in df.columns:

        available_columns.append(column)

    else:

        print(
            f"\nWARNING: Column not found: {column}"
        )


if len(available_columns) == 0:

    raise ValueError(
        "None of the expected Frankfurter economic "
        "columns were found in the fused CSV."
    )


# ============================================================
# CONVERT NUMERIC COLUMNS
# ============================================================

for column in available_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# ============================================================
# BASIC DATASET INFORMATION
# ============================================================

basic_info_file = os.path.join(
    REPORT_DIR,
    "dataset_information.txt"
)

with open(
    basic_info_file,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "FRANKFURTER API FUSED DATASET\n"
    )

    file.write(
        "====================================\n\n"
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


# ============================================================
# PART 1 - UNIVARIATE ANALYSIS
# ============================================================

print("\n======================================")
print("1. UNIVARIATE ANALYSIS")
print("======================================")


# ------------------------------------------------------------
# DESCRIPTIVE STATISTICS
# ------------------------------------------------------------

statistics = []

for column in available_columns:

    series = df[column].dropna()

    if len(series) == 0:
        continue

    statistics.append({

        "Variable": column,

        "Mean": series.mean(),

        "Median": series.median(),

        "Standard Deviation": series.std(),

        "Minimum": series.min(),

        "Q1": series.quantile(0.25),

        "Q2": series.quantile(0.50),

        "Q3": series.quantile(0.75),

        "Maximum": series.max()

    })


statistics_df = pd.DataFrame(
    statistics
)


# ------------------------------------------------------------
# SAVE STATISTICS
# ------------------------------------------------------------

statistics_file = os.path.join(
    REPORT_DIR,
    "frankfurter_univariate_statistics.csv"
)

statistics_df.to_csv(
    statistics_file,
    index=False
)


print("\nUnivariate statistics:")

print(
    statistics_df.to_string(
        index=False
    )
)


# ------------------------------------------------------------
# HISTOGRAMS
# ------------------------------------------------------------

for column in available_columns:

    data = df[column].dropna()

    if data.empty:
        continue

    plt.figure(
        figsize=(8, 5)
    )

    plt.hist(
        data,
        bins=10
    )

    plt.xlabel(column)

    plt.ylabel("Frequency")

    plt.title(
        f"Distribution of {column}"
    )

    plt.tight_layout()

    filename = (
        column
        .replace("/", "_")
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("%", "percent")
    )

    plt.savefig(
        os.path.join(
            PLOTS_DIR,
            f"histogram_{filename}.png"
        ),
        dpi=300
    )

    plt.close()


# ------------------------------------------------------------
# BOXPLOTS
# ------------------------------------------------------------

for column in available_columns:

    data = df[column].dropna()

    if data.empty:
        continue

    plt.figure(
        figsize=(7, 5)
    )

    plt.boxplot(
        data
    )

    plt.ylabel(column)

    plt.title(
        f"Boxplot of {column}"
    )

    plt.tight_layout()

    filename = (
        column
        .replace("/", "_")
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("%", "percent")
    )

    plt.savefig(
        os.path.join(
            PLOTS_DIR,
            f"boxplot_{filename}.png"
        ),
        dpi=300
    )

    plt.close()


# ============================================================
# PART 2 - BIVARIATE ANALYSIS
# ============================================================

print("\n======================================")
print("2. BIVARIATE ANALYSIS")
print("======================================")


# ------------------------------------------------------------
# RELATIONSHIPS TO ANALYZE
# ------------------------------------------------------------

relationships = [

    (
        "GDP (in billion USD)",
        "Economic Growth (%)"
    ),

    (
        "GDP (in billion USD)",
        "Inflation Rate (%)"
    ),

    (
        "GDP (in billion USD)",
        "Unemployment Rate (%)"
    ),

    (
        "Inflation Rate (%)",
        "Economic Growth (%)"
    ),

    (
        "Unemployment Rate (%)",
        "Economic Growth (%)"
    )

]


# ------------------------------------------------------------
# SCATTER PLOTS
# ------------------------------------------------------------

for x_column, y_column in relationships:

    if (
        x_column not in df.columns
        or
        y_column not in df.columns
    ):
        continue

    plot_df = df[
        [x_column, y_column]
    ].dropna()

    if plot_df.empty:
        continue

    plt.figure(
        figsize=(8, 5)
    )

    plt.scatter(
        plot_df[x_column],
        plot_df[y_column]
    )

    plt.xlabel(x_column)

    plt.ylabel(y_column)

    plt.title(
        f"{x_column} vs {y_column}"
    )

    plt.tight_layout()

    x_name = (
        x_column
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("%", "percent")
    )

    y_name = (
        y_column
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("%", "percent")
    )

    plt.savefig(
        os.path.join(
            PLOTS_DIR,
            f"scatter_{x_name}_vs_{y_name}.png"
        ),
        dpi=300
    )

    plt.close()


# ------------------------------------------------------------
# BIVARIATE CORRELATION TABLE
# ------------------------------------------------------------

correlation_matrix = df[
    available_columns
].corr()


correlation_file = os.path.join(
    REPORT_DIR,
    "frankfurter_correlation_matrix.csv"
)

correlation_matrix.to_csv(
    correlation_file
)


print("\nCorrelation Matrix:")

print(
    correlation_matrix
)


# ============================================================
# PART 3 - MULTIVARIATE ANALYSIS
# ============================================================

print("\n======================================")
print("3. MULTIVARIATE ANALYSIS")
print("======================================")


# ------------------------------------------------------------
# CORRELATION HEATMAP
# ------------------------------------------------------------

plt.figure(
    figsize=(9, 7)
)

plt.imshow(
    correlation_matrix,
    interpolation="nearest"
)

plt.colorbar()


plt.xticks(
    range(
        len(correlation_matrix.columns)
    ),
    correlation_matrix.columns,
    rotation=45,
    ha="right"
)

plt.yticks(
    range(
        len(correlation_matrix.columns)
    ),
    correlation_matrix.columns
)


# Add correlation values

for i in range(
    len(correlation_matrix.columns)
):

    for j in range(
        len(correlation_matrix.columns)
    ):

        value = correlation_matrix.iloc[
            i,
            j
        ]

        if not pd.isna(value):

            plt.text(
                j,
                i,
                f"{value:.2f}",
                ha="center",
                va="center"
            )


plt.title(
    "Frankfurter Economic Variables Correlation Heatmap"
)

plt.tight_layout()


plt.savefig(
    os.path.join(
        PLOTS_DIR,
        "frankfurter_correlation_heatmap.png"
    ),
    dpi=300
)

plt.close()


# ============================================================
# COUNTRY-WISE ANALYSIS
# ============================================================

if "Country" in df.columns:

    country_statistics = (
        df
        .groupby("Country")[
            available_columns
        ]
        .mean()
        .reset_index()
    )

    country_statistics_file = os.path.join(
        REPORT_DIR,
        "country_wise_economic_statistics.csv"
    )

    country_statistics.to_csv(
        country_statistics_file,
        index=False
    )


# ============================================================
# YEAR-WISE ANALYSIS
# ============================================================

if "Year" in df.columns:

    year_numeric = pd.to_numeric(
        df["Year"],
        errors="coerce"
    )

    df["Year"] = year_numeric


    year_statistics = (
        df
        .groupby("Year")[
            available_columns
        ]
        .mean()
        .reset_index()
    )


    year_statistics_file = os.path.join(
        REPORT_DIR,
        "year_wise_economic_statistics.csv"
    )

    year_statistics.to_csv(
        year_statistics_file,
        index=False
    )


# ============================================================
# FINAL EDA DATASET
# ============================================================

cleaned_file = os.path.join(
    REPORT_DIR,
    "frankfurter_eda_dataset.csv"
)

df.to_csv(
    cleaned_file,
    index=False
)


# ============================================================
# FINAL MESSAGE
# ============================================================

print("\n======================================")
print("FRANKFURTER EDA COMPLETED")
print("======================================")

print("\nEDA folder:")
print(EDA_DIR)

print("\nPlots saved in:")
print(PLOTS_DIR)

print("\nReports saved in:")
print(REPORT_DIR)

print("\nGenerated files include:")

print(
    "- frankfurter_univariate_statistics.csv"
)

print(
    "- frankfurter_correlation_matrix.csv"
)

print(
    "- country_wise_economic_statistics.csv"
)

print(
    "- year_wise_economic_statistics.csv"
)

print(
    "- frankfurter_eda_dataset.csv"
)

print(
    "- Histogram PNG files"
)

print(
    "- Boxplot PNG files"
)

print(
    "- Scatter plot PNG files"
)

print(
    "- Correlation heatmap PNG"
)

print("\n======================================")