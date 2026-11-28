# ============================================================
# PART E – EDA OF FUSED WEATHER DATASET
# ============================================================

import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# 1. CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_ROOT / "dataset" / "processed" / "fused_weather_data.csv"
OUTPUT_DIR = Path(__file__).resolve().parent / "results" / "fused_results"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. LOAD DATA
# ============================================================

df = pd.read_csv(INPUT_FILE)

# Convert timestamp to datetime
df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
)

print("\n======================================================")
print("PART E – EDA OF FUSED WEATHER DATASET")
print("======================================================")

print("\nDataset Shape:")
print(df.shape)

print("\nNumber of Records:", len(df))
print("Number of Attributes:", len(df.columns))


# ============================================================
# 3. UNIVARIATE ANALYSIS
# ============================================================

print("\n======================================================")
print("1. UNIVARIATE ANALYSIS")
print("======================================================")


numeric_columns = [
    "current_temperature_celsius",
    "historical_average_celsius",
    "historical_min_celsius",
    "historical_max_celsius",
    "temperature_difference_celsius",
    "current_humidity_percent",
    "current_wind_speed_mps",
    "current_wind_speed_kmh"
]


# ------------------------------------------------------------
# 3.1 DESCRIPTIVE STATISTICS
# ------------------------------------------------------------

print("\nDESCRIPTIVE STATISTICS")
print("----------------------")

statistics = df[numeric_columns].describe().T

statistics["median"] = (
    df[numeric_columns].median()
)

statistics = statistics[
    [
        "mean",
        "median",
        "std",
        "min",
        "25%",
        "50%",
        "75%",
        "max"
    ]
]

statistics.columns = [
    "Mean",
    "Median",
    "Std Dev",
    "Minimum",
    "Q1",
    "Median/Q2",
    "Q3",
    "Maximum"
]

print(
    statistics.round(2)
)


# Save statistics
statistics.to_csv(
    f"{OUTPUT_DIR}/univariate_statistics.csv"
)


# ============================================================
# 4. HISTOGRAMS
# ============================================================

print("\nGenerating histograms...")


for column in numeric_columns:

    plt.figure(figsize=(8, 5))

    plt.hist(
        df[column],
        bins=5
    )

    plt.title(
        f"Distribution of {column}"
    )

    plt.xlabel(column)

    plt.ylabel("Frequency")

    plt.tight_layout()

    filename = (
        column
        .replace("/", "_")
        + "_histogram.png"
    )

    plt.savefig(
        f"{OUTPUT_DIR}/{filename}"
    )

    plt.show()


# ============================================================
# 5. BOXPLOTS
# ============================================================

print("\nGenerating boxplots...")


for column in numeric_columns:

    plt.figure(figsize=(7, 5))

    plt.boxplot(
        df[column].dropna()
    )

    plt.title(
        f"Boxplot of {column}"
    )

    plt.ylabel(column)

    plt.tight_layout()

    filename = (
        column
        .replace("/", "_")
        + "_boxplot.png"
    )

    plt.savefig(
        f"{OUTPUT_DIR}/{filename}"
    )

    plt.show()


# ============================================================
# 6. WEATHER CONDITION DISTRIBUTION
# ============================================================

print("\n======================================================")
print("WEATHER CONDITION DISTRIBUTION")
print("======================================================")

condition_counts = (
    df["current_condition"]
    .value_counts()
)

print(condition_counts)


plt.figure(figsize=(7, 5))

condition_counts.plot(
    kind="bar"
)

plt.title(
    "Current Weather Condition Distribution"
)

plt.xlabel("Weather Condition")

plt.ylabel("Number of Observations")

plt.xticks(rotation=0)

plt.tight_layout()

plt.savefig(
    f"{OUTPUT_DIR}/weather_condition_distribution.png"
)

plt.show()


# ============================================================
# 7. BIVARIATE ANALYSIS
# ============================================================

print("\n======================================================")
print("2. BIVARIATE ANALYSIS")
print("======================================================")


# ------------------------------------------------------------
# 7.1 CURRENT TEMPERATURE VS HISTORICAL AVERAGE
# ------------------------------------------------------------

print("\nCurrent Temperature vs Historical Average:")

print(
    df[
        [
            "city",
            "current_temperature_celsius",
            "historical_average_celsius"
        ]
    ]
)


plt.figure(figsize=(8, 6))

plt.scatter(
    df["historical_average_celsius"],
    df["current_temperature_celsius"]
)

plt.xlabel(
    "Historical Average Temperature (°C)"
)

plt.ylabel(
    "Current API Temperature (°C)"
)

plt.title(
    "Current API Temperature vs Historical Average"
)

plt.tight_layout()

plt.savefig(
    f"{OUTPUT_DIR}/current_vs_historical_scatter.png"
)

plt.show()


# ------------------------------------------------------------
# 7.2 TEMPERATURE DIFFERENCE BY CITY
# ------------------------------------------------------------

print("\nTemperature Difference by Observation:")

print(
    df[
        [
            "city",
            "temperature_difference_celsius"
        ]
    ]
)


plt.figure(figsize=(8, 5))

plt.bar(
    range(len(df)),
    df["temperature_difference_celsius"]
)

plt.xticks(
    range(len(df)),
    df["city"]
)

plt.xlabel("City")

plt.ylabel(
    "Temperature Difference (°C)"
)

plt.title(
    "Current Temperature Difference from Historical Average"
)

plt.axhline(
    0,
    linewidth=1
)

plt.tight_layout()

plt.savefig(
    f"{OUTPUT_DIR}/temperature_difference_by_city.png"
)

plt.show()


# ------------------------------------------------------------
# 7.3 CURRENT TEMPERATURE VS HUMIDITY
# ------------------------------------------------------------

print("\nCurrent Temperature vs Humidity:")

print(
    df[
        [
            "current_temperature_celsius",
            "current_humidity_percent"
        ]
    ]
)


plt.figure(figsize=(8, 6))

plt.scatter(
    df["current_temperature_celsius"],
    df["current_humidity_percent"]
)

plt.xlabel(
    "Current Temperature (°C)"
)

plt.ylabel(
    "Humidity (%)"
)

plt.title(
    "Current Temperature vs Humidity"
)

plt.tight_layout()

plt.savefig(
    f"{OUTPUT_DIR}/temperature_vs_humidity.png"
)

plt.show()


# ============================================================
# 8. CORRELATION ANALYSIS
# ============================================================

print("\n======================================================")
print("3. MULTIVARIATE ANALYSIS")
print("======================================================")


correlation_columns = [
    "current_temperature_celsius",
    "historical_average_celsius",
    "temperature_difference_celsius",
    "current_humidity_percent",
    "current_wind_speed_mps",
    "current_wind_speed_kmh"
]


correlation_matrix = (
    df[correlation_columns]
    .corr()
)


print("\nCorrelation Matrix:")
print(
    correlation_matrix.round(3)
)


# Save correlation matrix
correlation_matrix.to_csv(
    f"{OUTPUT_DIR}/correlation_matrix.csv"
)


# ============================================================
# 9. CORRELATION HEATMAP
# ============================================================

plt.figure(figsize=(10, 8))

plt.imshow(
    correlation_matrix,
    interpolation="nearest"
)

plt.colorbar(
    label="Correlation"
)

plt.xticks(
    range(len(correlation_columns)),
    correlation_columns,
    rotation=45,
    ha="right"
)

plt.yticks(
    range(len(correlation_columns)),
    correlation_columns
)

plt.title(
    "Correlation Heatmap of Fused Weather Variables"
)

plt.tight_layout()

plt.savefig(
    f"{OUTPUT_DIR}/correlation_heatmap.png"
)

plt.show()


# ============================================================
# 10. API VARIABLE VS HISTORICAL VARIABLE
# ============================================================

print("\n======================================================")
print("API VS HISTORICAL ANALYSIS")
print("======================================================")


comparison = df[
    [
        "city",
        "current_temperature_celsius",
        "historical_average_celsius",
        "temperature_difference_celsius",
        "comparison_status"
    ]
]

print(comparison)


# ============================================================
# 11. FINAL EDA SUMMARY
# ============================================================

print("\n======================================================")
print("EDA COMPLETED SUCCESSFULLY")
print("======================================================")

print("\nResults saved in:")
print(OUTPUT_DIR)

print("\nGenerated files:")

for file in sorted(
    os.listdir(OUTPUT_DIR)
):

    print(
        " -",
        file
    )