from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# FUSED DATASET - PART E EDA
# STEP 1: UNIVARIATE ANALYSIS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = (
    BASE_DIR / "Weather_AirQuality_Data_Fusion.xlsx"
)

OUTPUT_DIR = (
    BASE_DIR / "EDA_Fused_Data"
)

HISTOGRAM_DIR = OUTPUT_DIR / "histograms"
BOXPLOT_DIR = OUTPUT_DIR / "boxplots"

OUTPUT_DIR.mkdir(exist_ok=True)
HISTOGRAM_DIR.mkdir(exist_ok=True)
BOXPLOT_DIR.mkdir(exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

if not INPUT_FILE.exists():
    print("ERROR: Fused Excel file not found.")
    print(INPUT_FILE)
    raise SystemExit(1)

df = pd.read_excel(
    INPUT_FILE,
    sheet_name="Fused_Data"
)

print("=" * 80)
print("PART E - EDA OF FUSED DATASET")
print("=" * 80)

print(f"\nRows    : {len(df):,}")
print(f"Columns : {len(df.columns)}")


# ============================================================
# SELECT IMPORTANT NUMERICAL VARIABLES
# ============================================================

candidate_columns = [
    "WAQI_AQI",
    "WAQI_PM25_ug_m3",
    "OpenWeather_Temperature_C",
    "OpenWeather_Humidity_pct",
    "OpenWeather_Pressure_hPa",
    "OpenWeather_WindSpeed_mps",
    "TomTom_CurrentSpeed_kmh",
    "TomTom_FreeFlowSpeed_kmh",
    "TomTom_Confidence",
    "Sentinel5P_NO2",
    "Predicted_PM25_1h_ug_m3",
    "Expected_PM25_Change_ug_m3",
]

numeric_columns = [
    column
    for column in candidate_columns
    if column in df.columns
]


# ============================================================
# CONVERT TO NUMERIC
# ============================================================

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# ============================================================
# DESCRIPTIVE STATISTICS
# ============================================================

print("\n" + "=" * 80)
print("DESCRIPTIVE STATISTICS")
print("=" * 80)

statistics = df[numeric_columns].describe().T

statistics["median"] = df[
    numeric_columns
].median()

statistics = statistics[
    [
        "count",
        "mean",
        "median",
        "std",
        "min",
        "25%",
        "50%",
        "75%",
        "max",
    ]
]

statistics = statistics.rename(
    columns={
        "25%": "Q1",
        "50%": "Q2_Median",
        "75%": "Q3",
    }
)

print(
    statistics.round(4).to_string()
)


# ============================================================
# SAVE STATISTICS
# ============================================================

statistics.to_csv(
    OUTPUT_DIR / "descriptive_statistics.csv"
)

print(
    f"\nSaved: "
    f"{OUTPUT_DIR / 'descriptive_statistics.csv'}"
)


# ============================================================
# CREATE HISTOGRAMS
# ============================================================

print("\n" + "=" * 80)
print("GENERATING HISTOGRAMS")
print("=" * 80)

for column in numeric_columns:

    values = df[column].dropna()

    if values.empty:
        print(
            f"Skipped histogram: {column} "
            "(no valid values)"
        )
        continue

    plt.figure(
        figsize=(8, 5)
    )

    plt.hist(
        values,
        bins=30,
        edgecolor="black"
    )

    plt.title(
        f"Distribution of {column}"
    )

    plt.xlabel(column)
    plt.ylabel("Frequency")

    plt.tight_layout()

    output_path = (
        HISTOGRAM_DIR
        / f"{column}_histogram.png"
    )

    plt.savefig(
        output_path,
        dpi=150
    )

    plt.close()

    print(
        f"Created: {output_path.name}"
    )


# ============================================================
# CREATE BOXPLOTS
# ============================================================

print("\n" + "=" * 80)
print("GENERATING BOXPLOTS")
print("=" * 80)

for column in numeric_columns:

    values = df[column].dropna()

    if values.empty:
        print(
            f"Skipped boxplot: {column} "
            "(no valid values)"
        )
        continue

    plt.figure(
        figsize=(7, 5)
    )

    plt.boxplot(
        values,
        vert=True
    )

    plt.title(
        f"Boxplot of {column}"
    )

    plt.ylabel(column)

    plt.tight_layout()

    output_path = (
        BOXPLOT_DIR
        / f"{column}_boxplot.png"
    )

    plt.savefig(
        output_path,
        dpi=150
    )

    plt.close()

    print(
        f"Created: {output_path.name}"
    )


# ============================================================
# CITY-WISE SUMMARY
# ============================================================

if "City" in df.columns:

    print("\n" + "=" * 80)
    print("CITY-WISE RECORD COUNT")
    print("=" * 80)

    city_counts = (
        df["City"]
        .value_counts()
        .sort_index()
    )

    print(
        city_counts.to_string()
    )

    city_counts.to_csv(
        OUTPUT_DIR / "city_record_counts.csv"
    )


# ============================================================
# FINAL MESSAGE
# ============================================================

print("\n" + "=" * 80)
print("UNIVARIATE EDA COMPLETE")
print("=" * 80)

print(
    f"\nEDA output folder:"
)

print(
    OUTPUT_DIR
)

print(
    "\nNext:"
)

print(
    "Review descriptive_statistics.csv, "
    "histograms and boxplots before moving "
    "to bivariate analysis."
)