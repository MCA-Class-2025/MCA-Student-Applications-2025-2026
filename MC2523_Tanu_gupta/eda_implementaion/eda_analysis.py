import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


# =========================================================
# CONFIGURATION
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = (
    PROJECT_ROOT / "dataset" / "raw" / "india_2000_2024_daily_weather.csv"
)
RESULTS_DIR = Path(__file__).resolve().parent / "results"
PLOTS_DIR = Path(__file__).resolve().parent / "visualizations"
SUMMARY_FILE = RESULTS_DIR / "eda_summary.txt"


# Create output directory
os.makedirs(PLOTS_DIR, exist_ok=True)


# =========================================================
# LOAD DATASET
# =========================================================

print("=" * 60)
print("EXPLORATORY DATA ANALYSIS - WEATHER DATASET")
print("=" * 60)

print("\nLoading dataset...")

df = pd.read_csv(DATASET_PATH)

print("Dataset loaded successfully.")


# =========================================================
# 1. DATASET SHAPE
# =========================================================

print("\n" + "=" * 60)
print("1. DATASET SHAPE")
print("=" * 60)

rows, columns = df.shape

print("Number of records :", rows)
print("Number of attributes :", columns)


# =========================================================
# 2. COLUMN INFORMATION
# =========================================================

print("\n" + "=" * 60)
print("2. COLUMN INFORMATION")
print("=" * 60)

print(df.columns.tolist())

print("\nData Types:")
print(df.dtypes)


# =========================================================
# 3. MISSING VALUES
# =========================================================

print("\n" + "=" * 60)
print("3. MISSING VALUES")
print("=" * 60)

missing_values = df.isnull().sum()

print(missing_values)

print(
    "\nTotal missing values:",
    missing_values.sum()
)


# =========================================================
# 4. DUPLICATE RECORDS
# =========================================================

print("\n" + "=" * 60)
print("4. DUPLICATE RECORDS")
print("=" * 60)

duplicates = df.duplicated().sum()

print("Duplicate records:", duplicates)


# =========================================================
# 5. STATISTICAL SUMMARY
# =========================================================

print("\n" + "=" * 60)
print("5. STATISTICAL SUMMARY")
print("=" * 60)

print(
    df.describe(include="all")
)


# =========================================================
# 6. CITY ANALYSIS
# =========================================================

print("\n" + "=" * 60)
print("6. CITY-WISE RECORD COUNT")
print("=" * 60)

city_counts = df["city"].value_counts()

print(city_counts)


plt.figure(figsize=(10, 6))

city_counts.plot(kind="bar")

plt.title("Number of Weather Records by City")
plt.xlabel("City")
plt.ylabel("Number of Records")

plt.xticks(rotation=45)

plt.tight_layout()

plt.savefig(
    os.path.join(
        PLOTS_DIR,
        "city_distribution.png"
    )
)

plt.close()


# =========================================================
# 7. DATE ANALYSIS
# =========================================================

print("\n" + "=" * 60)
print("7. DATE ANALYSIS")
print("=" * 60)

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)

print("Minimum date:", df["date"].min())
print("Maximum date:", df["date"].max())


# =========================================================
# 8. YEAR-WISE RECORDS
# =========================================================

df["year"] = df["date"].dt.year

year_counts = df["year"].value_counts().sort_index()

print("\nYear-wise records:")
print(year_counts)


plt.figure(figsize=(12, 6))

year_counts.plot(kind="line", marker="o")

plt.title("Weather Records by Year")
plt.xlabel("Year")
plt.ylabel("Number of Records")

plt.grid(True)

plt.tight_layout()

plt.savefig(
    os.path.join(
        PLOTS_DIR,
        "yearly_records.png"
    )
)

plt.close()


# =========================================================
# 9. TEMPERATURE ANALYSIS
# =========================================================

print("\n" + "=" * 60)
print("9. TEMPERATURE ANALYSIS")
print("=" * 60)

temperature_columns = [
    "temperature_2m_max",
    "temperature_2m_min"
]

for column in temperature_columns:

    print("\n", column)

    print(
        "Minimum:",
        df[column].min()
    )

    print(
        "Maximum:",
        df[column].max()
    )

    print(
        "Average:",
        round(df[column].mean(), 2)
    )

    print(
        "Median:",
        df[column].median()
    )


# Temperature distribution

plt.figure(figsize=(10, 6))

plt.hist(
    df["temperature_2m_max"].dropna(),
    bins=30
)

plt.title(
    "Distribution of Maximum Temperature"
)

plt.xlabel(
    "Maximum Temperature (°C)"
)

plt.ylabel(
    "Frequency"
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        PLOTS_DIR,
        "temperature_distribution.png"
    )
)

plt.close()


# =========================================================
# 10. RAINFALL ANALYSIS
# =========================================================

print("\n" + "=" * 60)
print("10. RAINFALL ANALYSIS")
print("=" * 60)

print(
    "Average precipitation:",
    round(
        df["precipitation_sum"].mean(),
        2
    ),
    "mm"
)

print(
    "Maximum precipitation:",
    df["precipitation_sum"].max(),
    "mm"
)

print(
    "Average rainfall:",
    round(
        df["rain_sum"].mean(),
        2
    ),
    "mm"
)

print(
    "Maximum rainfall:",
    df["rain_sum"].max(),
    "mm"
)


plt.figure(figsize=(10, 6))

plt.hist(
    df["rain_sum"].dropna(),
    bins=30
)

plt.title(
    "Distribution of Rainfall"
)

plt.xlabel(
    "Rainfall (mm)"
)

plt.ylabel(
    "Frequency"
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        PLOTS_DIR,
        "rainfall_distribution.png"
    )
)

plt.close()


# =========================================================
# 11. WEATHER CONDITION ANALYSIS
# =========================================================

print("\n" + "=" * 60)
print("11. WEATHER CONDITION ANALYSIS")
print("=" * 60)

weather_counts = df[
    "weather_code"
].value_counts().sort_index()

print(weather_counts)


plt.figure(figsize=(10, 6))

weather_counts.plot(
    kind="bar"
)

plt.title(
    "Weather Condition Distribution"
)

plt.xlabel(
    "Weather Code"
)

plt.ylabel(
    "Number of Records"
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        PLOTS_DIR,
        "weather_condition.png"
    )
)

plt.close()


# =========================================================
# 12. WIND SPEED ANALYSIS
# =========================================================

print("\n" + "=" * 60)
print("12. WIND SPEED ANALYSIS")
print("=" * 60)

print(
    "Average wind speed:",
    round(
        df["wind_speed_10m_max"].mean(),
        2
    ),
    "km/h"
)

print(
    "Maximum wind speed:",
    df["wind_speed_10m_max"].max(),
    "km/h"
)

print(
    "Average wind gust:",
    round(
        df["wind_gusts_10m_max"].mean(),
        2
    ),
    "km/h"
)


# =========================================================
# 13. CORRELATION ANALYSIS
# =========================================================

print("\n" + "=" * 60)
print("13. CORRELATION ANALYSIS")
print("=" * 60)

numeric_columns = [
    "temperature_2m_max",
    "temperature_2m_min",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "precipitation_sum",
    "rain_sum",
    "wind_speed_10m_max",
    "wind_gusts_10m_max"
]

correlation = df[
    numeric_columns
].corr()

print(correlation)


plt.figure(figsize=(10, 8))

plt.imshow(
    correlation,
    interpolation="nearest"
)

plt.colorbar()

plt.xticks(
    range(len(numeric_columns)),
    numeric_columns,
    rotation=45,
    ha="right"
)

plt.yticks(
    range(len(numeric_columns)),
    numeric_columns
)

plt.title(
    "Weather Attribute Correlation Matrix"
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        PLOTS_DIR,
        "correlation_heatmap.png"
    )
)

plt.close()


# =========================================================
# 14. OUTLIER ANALYSIS
# =========================================================

print("\n" + "=" * 60)
print("14. BASIC OUTLIER ANALYSIS")
print("=" * 60)

for column in numeric_columns:

    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)

    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    outliers = df[
        (df[column] < lower_bound)
        |
        (df[column] > upper_bound)
    ]

    print(
        column,
        "->",
        len(outliers),
        "potential outliers"
    )


# =========================================================
# 15. SAVE EDA SUMMARY
# =========================================================

summary = []

summary.append(
    "WEATHER DATASET - EDA SUMMARY"
)

summary.append("=" * 60)

summary.append(
    f"Number of records: {rows}"
)

summary.append(
    f"Number of attributes: {columns}"
)

summary.append(
    f"Total missing values: {missing_values.sum()}"
)

summary.append(
    f"Duplicate records: {duplicates}"
)

summary.append(
    f"Date range: {df['date'].min()} to {df['date'].max()}"
)

summary.append(
    f"Average maximum temperature: "
    f"{df['temperature_2m_max'].mean():.2f} °C"
)

summary.append(
    f"Average minimum temperature: "
    f"{df['temperature_2m_min'].mean():.2f} °C"
)

summary.append(
    f"Maximum recorded temperature: "
    f"{df['temperature_2m_max'].max():.2f} °C"
)

summary.append(
    f"Average rainfall: "
    f"{df['rain_sum'].mean():.2f} mm"
)

summary.append(
    f"Maximum rainfall: "
    f"{df['rain_sum'].max():.2f} mm"
)

summary.append(
    f"Average maximum wind speed: "
    f"{df['wind_speed_10m_max'].mean():.2f} km/h"
)


with open(
    SUMMARY_FILE,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "\n".join(summary)
    )


# =========================================================
# COMPLETE
# =========================================================

print("\n" + "=" * 60)
print("EDA COMPLETED SUCCESSFULLY")
print("=" * 60)

print(
    "\nEDA summary saved at:"
)

print(
    SUMMARY_FILE
)

print(
    "\nEDA plots saved at:"
)

print(
    PLOTS_DIR
)

print("\nOriginal dataset was NOT modified.")