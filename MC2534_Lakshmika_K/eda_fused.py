import os
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# LOAD FUSED DATASET
# ==========================================

FILE = "api_data/final_fused_waste_dataset.csv"

df = pd.read_csv(FILE)

# Folder for EDA graphs
os.makedirs("eda_outputs", exist_ok=True)

print("\n======================================")
print("       FUSED DATASET - EDA")
print("======================================")

print("\nDataset Shape:")
print("Rows:", df.shape[0])
print("Columns:", df.shape[1])


# ==========================================
# 1. NUMERICAL SUMMARY
# ==========================================

numeric_cols = df.select_dtypes(include="number").columns

print("\n--- NUMERICAL ATTRIBUTES ---")
print("Number of numerical attributes:", len(numeric_cols))

print("\n--- DESCRIPTIVE STATISTICS ---")

stats = df[numeric_cols].describe().T[
    ["count", "mean", "std", "min", "25%", "50%", "75%", "max"]
]

print(stats.round(2).to_string())


# ==========================================
# 2. UNIVARIATE ANALYSIS
# ==========================================

# Select important original + API variables if available

preferred_columns = [
    "Daily_Waste_Generation_Tons",
    "Recycling_Rate",
    "Waste_Segregation_Rate",
    "Sustainability_Index",
    "Population",
    "Air_Quality_Index",
    "Rainfall_MM",
    "Temperature_C",
    "Humidity_Percent",
    "PM2_5",
    "PM10",
    "Wind_Speed"
]

selected = [
    col for col in preferred_columns
    if col in df.columns
]

print("\n--- SELECTED EDA VARIABLES ---")
print(selected)


for col in selected:

    plt.figure(figsize=(8, 5))

    plt.hist(
        df[col].dropna(),
        bins=15
    )

    plt.title(f"Distribution of {col}")
    plt.xlabel(col)
    plt.ylabel("Frequency")

    plt.tight_layout()

    filename = (
        "eda_outputs/"
        + col
        + "_distribution.png"
    )

    plt.savefig(filename)
    plt.show()
    plt.close()


# ==========================================
# 3. BOXPLOTS
# ==========================================

for col in selected:

    plt.figure(figsize=(8, 4))

    plt.boxplot(
        df[col].dropna(),
        vert=False
    )

    plt.title(f"Boxplot of {col}")
    plt.xlabel(col)

    plt.tight_layout()

    filename = (
        "eda_outputs/"
        + col
        + "_boxplot.png"
    )

    plt.savefig(filename)
    plt.show()
    plt.close()


# ==========================================
# 4. BIVARIATE ANALYSIS
# ==========================================

# Waste generation vs population

if (
    "Population" in df.columns
    and
    "Daily_Waste_Generation_Tons" in df.columns
):

    plt.figure(figsize=(8, 5))

    plt.scatter(
        df["Population"],
        df["Daily_Waste_Generation_Tons"]
    )

    plt.title(
        "Population vs Daily Waste Generation"
    )

    plt.xlabel("Population")
    plt.ylabel("Daily Waste Generation (Tons)")

    plt.tight_layout()

    plt.savefig(
        "eda_outputs/population_vs_waste.png"
    )

    plt.show()
    plt.close()


# API Air Quality vs Waste Generation

if (
    "Air_Quality_Index" in df.columns
    and
    "Daily_Waste_Generation_Tons" in df.columns
):

    plt.figure(figsize=(8, 5))

    plt.scatter(
        df["Air_Quality_Index"],
        df["Daily_Waste_Generation_Tons"]
    )

    plt.title(
        "Air Quality Index vs Daily Waste Generation"
    )

    plt.xlabel("Air Quality Index")
    plt.ylabel("Daily Waste Generation (Tons)")

    plt.tight_layout()

    plt.savefig(
        "eda_outputs/aqi_vs_waste.png"
    )

    plt.show()
    plt.close()


# ==========================================
# 5. CORRELATION ANALYSIS
# ==========================================

correlation_columns = [
    col for col in [
        "Population",
        "Daily_Waste_Generation_Tons",
        "Recycling_Rate",
        "Waste_Segregation_Rate",
        "Sustainability_Index",
        "Air_Quality_Index",
        "Rainfall_MM",
        "Temperature_C",
        "PM2_5",
        "PM10"
    ]
    if col in df.columns
]

if len(correlation_columns) >= 2:

    correlation = df[
        correlation_columns
    ].corr()

    print("\n--- CORRELATION MATRIX ---")
    print(correlation.round(2).to_string())

    plt.figure(figsize=(10, 8))

    plt.imshow(
        correlation,
        interpolation="nearest"
    )

    plt.colorbar()

    plt.xticks(
        range(len(correlation_columns)),
        correlation_columns,
        rotation=90
    )

    plt.yticks(
        range(len(correlation_columns)),
        correlation_columns
    )

    plt.title(
        "Correlation Heatmap of Important Variables"
    )

    plt.tight_layout()

    plt.savefig(
        "eda_outputs/correlation_heatmap.png"
    )

    plt.show()
    plt.close()


# ==========================================
# 6. CATEGORICAL ANALYSIS
# ==========================================

categorical_candidates = [
    "City",
    "Waste_Type",
    "Treatment_Method",
    "Waste_Management_Performance_Level",
    "Sustainability_Category"
]

for col in categorical_candidates:

    if col in df.columns:

        counts = df[col].value_counts().head(10)

        plt.figure(figsize=(8, 5))

        plt.bar(
            counts.index.astype(str),
            counts.values
        )

        plt.title(
            f"Distribution of {col}"
        )

        plt.xlabel(col)
        plt.ylabel("Count")

        plt.xticks(rotation=45)

        plt.tight_layout()

        filename = (
            "eda_outputs/"
            + col
            + "_bar.png"
        )

        plt.savefig(filename)

        plt.show()
        plt.close()


# ==========================================
# FINAL MESSAGE
# ==========================================

print("\n======================================")
print("       FUSED DATASET EDA COMPLETED")
print("======================================")

print("\nEDA graphs saved inside:")
print("eda_outputs/")