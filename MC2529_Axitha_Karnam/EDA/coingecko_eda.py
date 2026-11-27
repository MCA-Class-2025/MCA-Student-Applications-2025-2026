import os
import pandas as pd
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
    "fused_coingecko.csv"
)

EDA_DIR = os.path.join(
    BASE_DIR,
    "EDA",
    "CoinGecko"
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
# CREATE DIRECTORIES
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
# LOAD DATASET
# ============================================================

print("\n======================================")
print("COINGECKO EDA")
print("======================================")

print("\nReading:")
print(INPUT_FILE)


if not os.path.exists(INPUT_FILE):

    raise FileNotFoundError(
        f"\nCoinGecko fused CSV not found:\n{INPUT_FILE}"
    )


df = pd.read_csv(
    INPUT_FILE
)


print("\nDataset loaded successfully.")

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
# COINGECKO NUMERICAL COLUMNS
# ============================================================

crypto_columns = [

    "Price Usd",

    "Volume24h",

    "Volume30d",

    "MarketCap",

    "Dominance",

    "YtdPriceChangePercentage",

    "cmcRank",

    "marketPairCount",

    "circulatingSupply",

    "totalSupply"

]


# ============================================================
# CHECK COLUMNS
# ============================================================

available_columns = []

for column in crypto_columns:

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
        "No expected CoinGecko numerical columns "
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
        "COINGECKO API FUSED DATASET\n"
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
    "coingecko_univariate_statistics.csv"
)


statistics_df.to_csv(
    statistics_file,
    index=False
)


print(
    "\nCoinGecko Univariate Statistics:"
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
# MEANINGFUL CRYPTO RELATIONSHIPS
# ============================================================

relationships = [

    (
        "Price Usd",
        "MarketCap"
    ),

    (
        "Price Usd",
        "Volume24h"
    ),

    (
        "MarketCap",
        "Volume24h"
    ),

    (
        "MarketCap",
        "Dominance"
    ),

    (
        "YtdPriceChangePercentage",
        "Volume24h"
    ),

    (
        "circulatingSupply",
        "MarketCap"
    ),

    (
        "circulatingSupply",
        "Price Usd"
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
    "coingecko_correlation_matrix.csv"
)


correlation_matrix.to_csv(
    correlation_file
)


print(
    "\nCoinGecko Correlation Matrix:"
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
    figsize=(11, 9)
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
    "CoinGecko Cryptocurrency Correlation Heatmap"
)


plt.tight_layout()


plt.savefig(
    os.path.join(
        PLOTS_DIR,
        "coingecko_correlation_heatmap.png"
    ),
    dpi=300
)


plt.close()


# ============================================================
# COUNTRY / NAME GROUP ANALYSIS
# ============================================================

if "Name" in df.columns:

    name_statistics = (
        df
        .groupby("Name")[
            available_columns
        ]
        .mean()
        .reset_index()
    )


    name_statistics_file = os.path.join(
        REPORT_DIR,
        "crypto_name_wise_statistics.csv"
    )


    name_statistics.to_csv(
        name_statistics_file,
        index=False
    )


# ============================================================
# SYMBOL-WISE ANALYSIS
# ============================================================

if "Symbol" in df.columns:

    symbol_statistics = (
        df
        .groupby("Symbol")[
            available_columns
        ]
        .mean()
        .reset_index()
    )


    symbol_statistics_file = os.path.join(
        REPORT_DIR,
        "crypto_symbol_wise_statistics.csv"
    )


    symbol_statistics.to_csv(
        symbol_statistics_file,
        index=False
    )


# ============================================================
# TOP CRYPTOCURRENCIES BY MARKET CAP
# ============================================================

if (
    "Name" in df.columns
    and
    "MarketCap" in df.columns
):

    top_market_cap = (
        df[
            [
                "Name",
                "MarketCap"
            ]
        ]
        .dropna()
        .sort_values(
            "MarketCap",
            ascending=False
        )
        .head(10)
    )


    top_market_cap_file = os.path.join(
        REPORT_DIR,
        "top_10_crypto_by_market_cap.csv"
    )


    top_market_cap.to_csv(
        top_market_cap_file,
        index=False
    )


    # --------------------------------------------------------
    # BAR CHART
    # --------------------------------------------------------

    plt.figure(
        figsize=(10, 6)
    )


    plt.bar(
        top_market_cap["Name"],
        top_market_cap["MarketCap"]
    )


    plt.xlabel(
        "Cryptocurrency"
    )

    plt.ylabel(
        "Market Capitalization"
    )

    plt.title(
        "Top 10 Cryptocurrencies by Market Capitalization"
    )


    plt.xticks(
        rotation=45,
        ha="right"
    )


    plt.tight_layout()


    plt.savefig(
        os.path.join(
            PLOTS_DIR,
            "top_10_crypto_market_cap.png"
        ),
        dpi=300
    )


    plt.close()


# ============================================================
# TOP CRYPTOCURRENCIES BY 24H VOLUME
# ============================================================

if (
    "Name" in df.columns
    and
    "Volume24h" in df.columns
):

    top_volume = (
        df[
            [
                "Name",
                "Volume24h"
            ]
        ]
        .dropna()
        .sort_values(
            "Volume24h",
            ascending=False
        )
        .head(10)
    )


    top_volume_file = os.path.join(
        REPORT_DIR,
        "top_10_crypto_by_volume24h.csv"
    )


    top_volume.to_csv(
        top_volume_file,
        index=False
    )


    # --------------------------------------------------------
    # BAR CHART
    # --------------------------------------------------------

    plt.figure(
        figsize=(10, 6)
    )


    plt.bar(
        top_volume["Name"],
        top_volume["Volume24h"]
    )


    plt.xlabel(
        "Cryptocurrency"
    )

    plt.ylabel(
        "24 Hour Trading Volume"
    )

    plt.title(
        "Top 10 Cryptocurrencies by 24H Volume"
    )


    plt.xticks(
        rotation=45,
        ha="right"
    )


    plt.tight_layout()


    plt.savefig(
        os.path.join(
            PLOTS_DIR,
            "top_10_crypto_volume24h.png"
        ),
        dpi=300
    )


    plt.close()


# ============================================================
# FINAL CLEAN EDA DATASET
# ============================================================

cleaned_file = os.path.join(
    REPORT_DIR,
    "coingecko_eda_dataset.csv"
)


df.to_csv(
    cleaned_file,
    index=False
)


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n======================================")
print("COINGECKO EDA COMPLETED")
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
    "- Top 10 cryptocurrencies by Market Cap"
)

print(
    "- Top 10 cryptocurrencies by 24H Volume"
)

print(
    "- Cryptocurrency-wise statistics"
)

print(
    "- Symbol-wise statistics"
)


print("\n======================================")