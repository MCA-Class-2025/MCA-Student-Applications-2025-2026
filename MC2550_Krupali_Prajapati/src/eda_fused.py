import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

# ============================================================
# PART E - EXPLORATORY DATA ANALYSIS OF FUSED DATASET
# ============================================================

INPUT_FILE = "data/fused_country_intelligence.csv"
OUTPUT_DIR = "data/eda_outputs"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 75)
print("PART E - EXPLORATORY DATA ANALYSIS OF FUSED DATASET")
print("=" * 75)

# ============================================================
# 1. LOAD FUSED DATASET
# ============================================================

df = pd.read_csv(INPUT_FILE)

print("\nDataset loaded successfully.")
print(f"Records   : {df.shape[0]}")
print(f"Attributes: {df.shape[1]}")

# Work on a copy so the original fused dataset is NOT modified
eda_df = df.copy()

# ============================================================
# 2. NUMERICAL COLUMNS
# ============================================================

numeric_columns = [
    "GDP",
    "GDP per capita",
    "Population",
    "Life expectancy",
    "Unemployment",
    "Internet usage",
    "Temperature (°C)",
    "Apparent Temperature (°C)",
    "Relative Humidity (%)",
    "Precipitation (mm)",
    "Wind Speed (km/h)",
    "Exchange Rate",
    "PM2.5",
    "PM10",
    "NO2",
    "O3",
    "Public Holidays 2026"
]

# Convert numerical columns to numeric
for col in numeric_columns:
    if col in eda_df.columns:
        eda_df[col] = pd.to_numeric(
            eda_df[col],
            errors="coerce"
        )

# ============================================================
# 3. HANDLE INVALID AIR-QUALITY VALUES FOR EDA
# ============================================================
# Negative pollutant concentrations are invalid.
# They are converted to NaN ONLY in the EDA copy.
# The original fused dataset remains unchanged.

pollutant_columns = [
    "PM2.5",
    "PM10",
    "NO2",
    "O3"
]

for col in pollutant_columns:
    if col in eda_df.columns:
        eda_df.loc[eda_df[col] < 0, col] = np.nan


# ============================================================
# 4. UNIVARIATE ANALYSIS
# ============================================================

print("\n" + "=" * 75)
print("1. UNIVARIATE ANALYSIS")
print("=" * 75)

univariate_columns = [
    "GDP per capita",
    "Population",
    "Life expectancy",
    "Temperature (°C)",
    "Relative Humidity (%)",
    "Wind Speed (km/h)",
    "Exchange Rate",
    "PM2.5",
    "PM10",
    "NO2",
    "O3",
    "Public Holidays 2026"
]

univariate_results = []

for col in univariate_columns:

    if col not in eda_df.columns:
        continue

    series = eda_df[col].dropna()

    if len(series) == 0:
        continue

    univariate_results.append({
        "Attribute": col,
        "Mean": series.mean(),
        "Median": series.median(),
        "Std Dev": series.std(),
        "Minimum": series.min(),
        "Q1": series.quantile(0.25),
        "Q3": series.quantile(0.75),
        "Maximum": series.max(),
        "Available Records": len(series)
    })

univariate_stats = pd.DataFrame(univariate_results)

print("\nDescriptive Statistics:")
print(
    univariate_stats.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)

univariate_stats.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "univariate_statistics.csv"
    ),
    index=False
)

# ============================================================
# 5. DISTRIBUTION PLOTS
# ============================================================

print("\nGenerating distribution plots...")

distribution_columns = [
    "GDP per capita",
    "Population",
    "Life expectancy",
    "Temperature (°C)",
    "Relative Humidity (%)",
    "Exchange Rate",
    "PM2.5",
    "Public Holidays 2026"
]

for col in distribution_columns:

    if col not in eda_df.columns:
        continue

    series = eda_df[col].dropna()

    if len(series) < 2:
        continue

    plt.figure(figsize=(9, 6))

    plt.hist(
        series,
        bins=20,
        edgecolor="black"
    )

    plt.title(f"Distribution of {col}")
    plt.xlabel(col)
    plt.ylabel("Number of Countries")
    plt.grid(axis="y", alpha=0.3)

    plt.tight_layout()

    filename = (
        col.lower()
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("°", "")
        .replace("/", "_")
        .replace(".", "")
        .replace("%", "percent")
    )

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            f"distribution_{filename}.png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


# ============================================================
# 6. BOX PLOT
# ============================================================

print("Generating boxplot...")

boxplot_columns = [
    "GDP per capita",
    "Population",
    "Life expectancy",
    "Temperature (°C)",
    "Relative Humidity (%)",
    "Wind Speed (km/h)",
    "Exchange Rate",
    "PM2.5",
    "PM10",
    "Public Holidays 2026"
]

box_data = []
box_labels = []

for col in boxplot_columns:

    if col not in eda_df.columns:
        continue

    values = eda_df[col].dropna()

    if len(values) > 0:
        box_data.append(values)
        box_labels.append(col)

plt.figure(figsize=(14, 8))

# UPDATED FOR CURRENT MATPLOTLIB VERSION:
# labels -> tick_labels

plt.boxplot(
    box_data,
    tick_labels=box_labels,
    vert=True
)

plt.title(
    "Boxplot of Selected Numerical Variables"
)

plt.ylabel("Values")

plt.xticks(
    rotation=45,
    ha="right"
)

plt.grid(
    axis="y",
    alpha=0.3
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_DIR,
        "boxplot_selected_variables.png"
    ),
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 7. BIVARIATE ANALYSIS
# ============================================================

print("Generating bivariate relationship plots...")

relationship_pairs = [
    (
        "GDP per capita",
        "Life expectancy",
        "GDP per Capita vs Life Expectancy"
    ),
    (
        "GDP per capita",
        "Internet usage",
        "GDP per Capita vs Internet Usage"
    ),
    (
        "GDP per capita",
        "PM2.5",
        "GDP per Capita vs PM2.5"
    ),
    (
        "GDP per capita",
        "Public Holidays 2026",
        "GDP per Capita vs Public Holiday Count"
    )
]

for x_col, y_col, title in relationship_pairs:

    if x_col not in eda_df.columns:
        continue

    if y_col not in eda_df.columns:
        continue

    plot_df = eda_df[
        [x_col, y_col]
    ].dropna()

    if len(plot_df) < 2:
        continue

    plt.figure(figsize=(9, 6))

    plt.scatter(
        plot_df[x_col],
        plot_df[y_col],
        alpha=0.7
    )

    plt.title(title)
    plt.xlabel(x_col)
    plt.ylabel(y_col)

    plt.grid(
        alpha=0.3
    )

    plt.tight_layout()

    filename = (
        "relationship_"
        + x_col.lower()
        .replace(" ", "_")
        .replace(".", "")
        + "_vs_"
        + y_col.lower()
        .replace(" ", "_")
        .replace(".", "")
        .replace("%", "percent")
    )

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            filename + ".png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


# ============================================================
# 8. CORRELATION ANALYSIS
# ============================================================

print("\n" + "=" * 75)
print("2. CORRELATION ANALYSIS")
print("=" * 75)

correlation_columns = [
    "GDP per capita",
    "Population",
    "Life expectancy",
    "Unemployment",
    "Internet usage",
    "Temperature (°C)",
    "Relative Humidity (%)",
    "Wind Speed (km/h)",
    "Exchange Rate",
    "PM2.5",
    "PM10",
    "NO2",
    "Public Holidays 2026"
]

available_correlation_columns = [
    col
    for col in correlation_columns
    if col in eda_df.columns
]

correlation_df = eda_df[
    available_correlation_columns
].corr(
    numeric_only=True
)

print("\nCorrelation Matrix:")
print(
    correlation_df.to_string(
        float_format=lambda x: f"{x:.3f}"
    )
)

correlation_df.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "correlation_matrix.csv"
    )
)


# ============================================================
# 9. SELECTED CORRELATIONS
# ============================================================

selected_pairs = [
    ("GDP per capita", "Life expectancy"),
    ("GDP per capita", "Internet usage"),
    ("GDP per capita", "PM2.5"),
    ("GDP per capita", "Public Holidays 2026"),
    ("Population", "PM2.5"),
    ("Internet usage", "Life expectancy")
]

selected_results = []

for x_col, y_col in selected_pairs:

    if (
        x_col not in eda_df.columns
        or y_col not in eda_df.columns
    ):
        continue

    temp = eda_df[
        [x_col, y_col]
    ].dropna()

    if len(temp) < 3:
        continue

    correlation = temp[x_col].corr(
        temp[y_col]
    )

    selected_results.append({
        "Variable 1": x_col,
        "Variable 2": y_col,
        "Correlation": correlation,
        "Available Records": len(temp)
    })

selected_correlations = pd.DataFrame(
    selected_results
)

print("\nSelected correlations:")

if len(selected_correlations) > 0:
    print(
        selected_correlations.to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}"
        )
    )

selected_correlations.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "selected_correlations.csv"
    ),
    index=False
)


# ============================================================
# 10. CORRELATION HEATMAP
# ============================================================

print("\nGenerating correlation heatmap...")

plt.figure(
    figsize=(14, 10)
)

plt.imshow(
    correlation_df,
    aspect="auto"
)

plt.colorbar(
    label="Correlation"
)

plt.xticks(
    range(len(correlation_df.columns)),
    correlation_df.columns,
    rotation=60,
    ha="right"
)

plt.yticks(
    range(len(correlation_df.columns)),
    correlation_df.columns
)

plt.title(
    "Correlation Heatmap of Fused Dataset Variables"
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_DIR,
        "correlation_heatmap.png"
    ),
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 11. FUSION INSIGHT
# GDP PER CAPITA GROUP VS PM2.5
# ============================================================

print("\nGenerating fusion insight visualization...")

fusion_df = eda_df[
    [
        "GDP per capita",
        "PM2.5"
    ]
].dropna()

fusion_df = fusion_df[
    fusion_df["GDP per capita"] > 0
]

fusion_df = fusion_df[
    fusion_df["PM2.5"] >= 0
]

if len(fusion_df) >= 4:

    # Create four GDP-per-capita groups
    fusion_df["GDP Group"] = pd.qcut(
        fusion_df["GDP per capita"],
        q=4,
        labels=[
            "Low GDP",
            "Lower-Middle GDP",
            "Upper-Middle GDP",
            "High GDP"
        ],
        duplicates="drop"
    )

    fusion_insight = (
        fusion_df
        .groupby(
            "GDP Group",
            observed=True
        )["PM2.5"]
        .agg(
            [
                "mean",
                "median",
                "count"
            ]
        )
        .reset_index()
    )

    fusion_insight.columns = [
        "GDP Group",
        "Average PM2.5",
        "Median PM2.5",
        "Countries"
    ]

    print("\nFusion Insight - GDP Group vs PM2.5:")
    print(
        fusion_insight.to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}"
        )
    )

    fusion_insight.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "fusion_insight_gdp_group_vs_pm25.csv"
        ),
        index=False
    )

    plt.figure(
        figsize=(10, 6)
    )

    plt.bar(
        fusion_insight["GDP Group"],
        fusion_insight["Average PM2.5"]
    )

    plt.title(
        "Average PM2.5 Across GDP-per-Capita Groups"
    )

    plt.xlabel(
        "GDP-per-Capita Group"
    )

    plt.ylabel(
        "Average PM2.5"
    )

    plt.xticks(
        rotation=20
    )

    plt.grid(
        axis="y",
        alpha=0.3
    )

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            "fusion_insight_gdp_group_vs_pm25.png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

else:

    print(
        "Not enough valid GDP per capita and PM2.5 "
        "records for fusion insight."
    )


# ============================================================
# 12. MULTIVARIATE ANALYSIS
# ============================================================

print("\nGenerating multivariate visualization...")

multivariate_df = eda_df[
    [
        "GDP per capita",
        "Life expectancy",
        "Population"
    ]
].dropna()

if len(multivariate_df) >= 3:

    # Bubble plot:
    # X = GDP per capita
    # Y = Life expectancy
    # Bubble size = Population

    bubble_sizes = (
        np.sqrt(
            multivariate_df["Population"]
        ) * 0.5
    )

    plt.figure(
        figsize=(10, 7)
    )

    plt.scatter(
        multivariate_df["GDP per capita"],
        multivariate_df["Life expectancy"],
        s=bubble_sizes,
        alpha=0.5
    )

    plt.title(
        "GDP per Capita vs Life Expectancy "
        "with Population as Bubble Size"
    )

    plt.xlabel(
        "GDP per Capita"
    )

    plt.ylabel(
        "Life Expectancy"
    )

    plt.grid(
        alpha=0.3
    )

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            "multivariate_gdp_life_population.png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


# ============================================================
# 13. ADDITIONAL API-FOCUSED ANALYSIS
# ============================================================

print("\nGenerating API-focused analysis...")

api_relationships = [
    (
        "Temperature (°C)",
        "Relative Humidity (%)",
        "Weather Temperature vs Humidity"
    ),
    (
        "Temperature (°C)",
        "Wind Speed (km/h)",
        "Weather Temperature vs Wind Speed"
    ),
    (
        "Public Holidays 2026",
        "Life expectancy",
        "Public Holidays vs Life Expectancy"
    )
]

for x_col, y_col, title in api_relationships:

    if (
        x_col not in eda_df.columns
        or y_col not in eda_df.columns
    ):
        continue

    temp = eda_df[
        [x_col, y_col]
    ].dropna()

    if len(temp) < 2:
        continue

    plt.figure(
        figsize=(9, 6)
    )

    plt.scatter(
        temp[x_col],
        temp[y_col],
        alpha=0.7
    )

    plt.title(title)
    plt.xlabel(x_col)
    plt.ylabel(y_col)

    plt.grid(
        alpha=0.3
    )

    plt.tight_layout()

    filename = (
        "api_relationship_"
        + x_col.lower()
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("°", "")
        .replace("/", "_")
        .replace("%", "percent")
        + "_vs_"
        + y_col.lower()
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("°", "")
        .replace("/", "_")
        .replace("%", "percent")
    )

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            filename + ".png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


# ============================================================
# 14. FINAL OUTPUT SUMMARY
# ============================================================

print("\n" + "=" * 75)
print("PART E OUTPUT FILES")
print("=" * 75)

print(f"\nAll EDA outputs saved to:")
print(f"  {OUTPUT_DIR}")

print("\nGenerated files:")

for filename in sorted(
    os.listdir(OUTPUT_DIR)
):
    print(
        f"  - {filename}"
    )

print("\n" + "=" * 75)
print("PART E COMPLETED SUCCESSFULLY")
print("=" * 75)

print(
    "\nThe fused dataset was analyzed using:"
)
print(
    "1. Univariate descriptive statistics"
)
print(
    "2. Distribution visualizations"
)
print(
    "3. Boxplot analysis"
)
print(
    "4. Bivariate relationship analysis"
)
print(
    "5. Correlation analysis"
)
print(
    "6. Correlation heatmap"
)
print(
    "7. API + original-data fusion insight"
)
print(
    "8. Multivariate analysis"
)
print(
    "9. API-focused relationship analysis"
)

print(
    "\nOriginal fused dataset was not modified during EDA."
)

print("=" * 75)