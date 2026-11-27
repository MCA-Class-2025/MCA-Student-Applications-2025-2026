import os
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# PATHS
# ============================================================

# Project root
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# FRED fused dataset
INPUT_FILE = os.path.join(
    BASE_DIR,
    "csv",
    "fused",
    "fused_fred.csv"
)

# EDA output folders
EDA_DIR = os.path.join(
    BASE_DIR,
    "EDA",
    "FRED"
)

PLOTS_DIR = os.path.join(
    EDA_DIR,
    "plots"
)

REPORT_DIR = os.path.join(
    EDA_DIR,
    "reports"
)


# ============================================================
# CREATE EDA DIRECTORIES
# ============================================================

os.makedirs(
    PLOTS_DIR,
    exist_ok=True
)

os.makedirs(
    REPORT_DIR,
    exist_ok=True
)


# ============================================================
# LOAD FUSED FRED DATASET
# ============================================================

print("\n======================================")
print("FRED EDA")
print("======================================")

print("\nReading:")
print(INPUT_FILE)


if not os.path.exists(INPUT_FILE):

    raise FileNotFoundError(
        f"\nFRED fused CSV not found:\n{INPUT_FILE}"
    )


df = pd.read_csv(
    INPUT_FILE
)


print("\nFRED fused dataset loaded successfully.")

print(
    "Number of rows:",
    len(df)
)

print(
    "Number of columns:",
    len(df.columns)
)


# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

df.columns = (
    df.columns
    .astype(str)
    .str.strip()
)


# ============================================================
# DISPLAY COLUMNS
# ============================================================

print("\n======================================")
print("DATASET COLUMNS")
print("======================================")

for column in df.columns:

    print(column)


# ============================================================
# FRED NUMERICAL COLUMNS
# ============================================================

fred_columns = [

    "Year",

    "GDP (in billion USD)",

    "Inflation Rate (%)",

    "Unemployment Rate (%)",

    "Economic Growth (%)"

]


# ============================================================
# CHECK REQUIRED COLUMNS
# ============================================================

available_columns = []

for column in fred_columns:

    if column in df.columns:

        available_columns.append(
            column
        )

    else:

        print(
            f"\nWARNING: Column not found: {column}"
        )


if not available_columns:

    raise ValueError(
        "No expected FRED numerical columns "
        "were found in the fused CSV."
    )


# ============================================================
# CONVERT NUMERICAL COLUMNS
# ============================================================

for column in available_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# ============================================================
# DATASET INFORMATION
# ============================================================

dataset_info_file = os.path.join(
    REPORT_DIR,
    "dataset_information.txt"
)


with open(
    dataset_info_file,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "FRED API FUSED DATASET\n"
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
# PART 1
# UNIVARIATE ANALYSIS
# ============================================================

print("\n======================================")
print("1. UNIVARIATE ANALYSIS")
print("======================================")


# ============================================================
# DESCRIPTIVE STATISTICS
# ============================================================

statistics = []


for column in available_columns:

    series = df[column].dropna()

    if series.empty:

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


# ============================================================
# SAVE UNIVARIATE STATISTICS
# ============================================================

statistics_file = os.path.join(
    REPORT_DIR,
    "fred_univariate_statistics.csv"
)


statistics_df.to_csv(
    statistics_file,
    index=False
)


print(
    "\nFRED Univariate Statistics:"
)

print(
    statistics_df.to_string(
        index=False
    )
)


# ============================================================
# HISTOGRAMS
# ============================================================

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


    plt.xlabel(
        column
    )

    plt.ylabel(
        "Frequency"
    )

    plt.title(
        f"Distribution of {column}"
    )


    plt.tight_layout()


    filename = (
        column
        .replace(" ", "_")
        .replace("/", "_")
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


# ============================================================
# BOXPLOTS
# ============================================================

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


    plt.ylabel(
        column
    )

    plt.title(
        f"Boxplot of {column}"
    )


    plt.tight_layout()


    filename = (
        column
        .replace(" ", "_")
        .replace("/", "_")
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
# PART 2
# BIVARIATE ANALYSIS
# ============================================================

print("\n======================================")
print("2. BIVARIATE ANALYSIS")
print("======================================")


# ============================================================
# MEANINGFUL FRED RELATIONSHIPS
# ============================================================

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
    ),

    (
        "Inflation Rate (%)",
        "Unemployment Rate (%)"
    )

]


# ============================================================
# SCATTER PLOTS
# ============================================================

for x_column, y_column in relationships:

    if (
        x_column not in df.columns
        or
        y_column not in df.columns
    ):

        continue


    plot_df = df[
        [
            x_column,
            y_column
        ]
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


    plt.xlabel(
        x_column
    )

    plt.ylabel(
        y_column
    )

    plt.title(
        f"{x_column} vs {y_column}"
    )


    plt.tight_layout()


    x_name = (
        x_column
        .replace(" ", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("%", "percent")
    )


    y_name = (
        y_column
        .replace(" ", "_")
        .replace("/", "_")
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


# ============================================================
# CORRELATION MATRIX
# ============================================================

correlation_matrix = df[
    available_columns
].corr()


correlation_file = os.path.join(
    REPORT_DIR,
    "fred_correlation_matrix.csv"
)


correlation_matrix.to_csv(
    correlation_file
)


print(
    "\nFRED Correlation Matrix:"
)

print(
    correlation_matrix
)


# ============================================================
# PART 3
# MULTIVARIATE ANALYSIS
# ============================================================

print("\n======================================")
print("3. MULTIVARIATE ANALYSIS")
print("======================================")


# ============================================================
# CORRELATION HEATMAP
# ============================================================

plt.figure(
    figsize=(10, 8)
)


plt.imshow(
    correlation_matrix,
    interpolation="nearest"
)


plt.colorbar()


plt.xticks(
    range(
        len(
            correlation_matrix.columns
        )
    ),
    correlation_matrix.columns,
    rotation=45,
    ha="right"
)


plt.yticks(
    range(
        len(
            correlation_matrix.columns
        )
    ),
    correlation_matrix.columns
)


# ============================================================
# WRITE CORRELATION VALUES
# ============================================================

for i in range(
    len(
        correlation_matrix.columns
    )
):

    for j in range(
        len(
            correlation_matrix.columns
        )
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
    "FRED Economic Indicators Correlation Heatmap"
)


plt.tight_layout()


plt.savefig(
    os.path.join(
        PLOTS_DIR,
        "fred_correlation_heatmap.png"
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
        "country_wise_fred_statistics.csv"
    )


    country_statistics.to_csv(
        country_statistics_file,
        index=False
    )


# ============================================================
# GDP BY COUNTRY
# ============================================================

if (
    "Country" in df.columns
    and
    "GDP (in billion USD)" in df.columns
):

    country_gdp = (
        df[
            [
                "Country",
                "GDP (in billion USD)"
            ]
        ]
        .dropna()
        .groupby("Country")[
            "GDP (in billion USD)"
        ]
        .mean()
        .sort_values(
            ascending=False
        )
        .head(10)
        .reset_index()
    )


    country_gdp_file = os.path.join(
        REPORT_DIR,
        "top_10_countries_by_gdp.csv"
    )


    country_gdp.to_csv(
        country_gdp_file,
        index=False
    )


    # --------------------------------------------------------
    # BAR CHART
    # --------------------------------------------------------

    plt.figure(
        figsize=(10, 6)
    )


    plt.bar(
        country_gdp["Country"],
        country_gdp[
            "GDP (in billion USD)"
        ]
    )


    plt.xlabel(
        "Country"
    )

    plt.ylabel(
        "GDP (in billion USD)"
    )

    plt.title(
        "Top 10 Countries by Average GDP"
    )


    plt.xticks(
        rotation=45,
        ha="right"
    )


    plt.tight_layout()


    plt.savefig(
        os.path.join(
            PLOTS_DIR,
            "top_10_countries_gdp.png"
        ),
        dpi=300
    )


    plt.close()


# ============================================================
# ECONOMIC GROWTH BY COUNTRY
# ============================================================

if (
    "Country" in df.columns
    and
    "Economic Growth (%)" in df.columns
):

    growth_data = (
        df[
            [
                "Country",
                "Economic Growth (%)"
            ]
        ]
        .dropna()
        .groupby("Country")[
            "Economic Growth (%)"
        ]
        .mean()
        .sort_values(
            ascending=False
        )
        .head(10)
        .reset_index()
    )


    growth_file = os.path.join(
        REPORT_DIR,
        "top_10_countries_economic_growth.csv"
    )


    growth_data.to_csv(
        growth_file,
        index=False
    )


    # --------------------------------------------------------
    # BAR CHART
    # --------------------------------------------------------

    plt.figure(
        figsize=(10, 6)
    )


    plt.bar(
        growth_data["Country"],
        growth_data[
            "Economic Growth (%)"
        ]
    )


    plt.xlabel(
        "Country"
    )

    plt.ylabel(
        "Economic Growth (%)"
    )

    plt.title(
        "Top 10 Countries by Average Economic Growth"
    )


    plt.xticks(
        rotation=45,
        ha="right"
    )


    plt.tight_layout()


    plt.savefig(
        os.path.join(
            PLOTS_DIR,
            "top_10_countries_economic_growth.png"
        ),
        dpi=300
    )


    plt.close()


# ============================================================
# FINAL CLEAN EDA DATASET
# ============================================================

cleaned_file = os.path.join(
    REPORT_DIR,
    "fred_eda_dataset.csv"
)


df.to_csv(
    cleaned_file,
    index=False
)


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n======================================")
print("FRED EDA COMPLETED")
print("======================================")


print("\nEDA folder:")
print(EDA_DIR)


print("\nPlots saved in:")
print(PLOTS_DIR)


print("\nReports saved in:")
print(REPORT_DIR)


print("\nGenerated analysis includes:")

print(
    "- Univariate statistics"
)

print(
    "- Histograms"
)

print(
    "- Boxplots"
)

print(
    "- Scatter plots"
)

print(
    "- Correlation matrix"
)

print(
    "- Correlation heatmap"
)

print(
    "- Country-wise analysis"
)

print(
    "- Top 10 countries by GDP"
)

print(
    "- Top 10 countries by economic growth"
)


print("\n======================================")