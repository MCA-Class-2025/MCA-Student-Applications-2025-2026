from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# PART E - MULTIVARIATE ANALYSIS
# CORRELATION HEATMAP
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = (
    BASE_DIR / "Weather_AirQuality_Data_Fusion.xlsx"
)

OUTPUT_DIR = (
    BASE_DIR / "EDA_Fused_Data" / "multivariate"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD DATA
# ============================================================

if not INPUT_FILE.exists():
    print("ERROR: Fused Excel file not found.")
    raise SystemExit(1)

df = pd.read_excel(
    INPUT_FILE,
    sheet_name="Fused_Data"
)

print("=" * 80)
print("PART E - MULTIVARIATE ANALYSIS")
print("=" * 80)

print(f"\nRows: {len(df):,}")
print(f"Columns: {len(df.columns)}")


# ============================================================
# SELECT IMPORTANT NUMERICAL VARIABLES
# ============================================================

columns = [
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

available_columns = [
    column
    for column in columns
    if column in df.columns
]

# Convert to numeric.
for column in available_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# ============================================================
# CORRELATION MATRIX
# ============================================================

correlation = df[
    available_columns
].corr()

print("\n" + "=" * 80)
print("CORRELATION MATRIX")
print("=" * 80)

print(
    correlation.round(3).to_string()
)

correlation.to_csv(
    OUTPUT_DIR / "correlation_matrix.csv"
)


# ============================================================
# CREATE HEATMAP USING MATPLOTLIB
# ============================================================

plt.figure(
    figsize=(13, 10)
)

image = plt.imshow(
    correlation,
    interpolation="nearest",
    aspect="auto"
)

plt.colorbar(
    image,
    label="Correlation"
)

plt.xticks(
    range(len(available_columns)),
    available_columns,
    rotation=75,
    ha="right"
)

plt.yticks(
    range(len(available_columns)),
    available_columns
)

plt.title(
    "Correlation Heatmap of Fused Dataset"
)

# Add correlation values inside cells.
for i in range(
    len(available_columns)
):
    for j in range(
        len(available_columns)
    ):

        value = correlation.iloc[i, j]

        if pd.notna(value):

            plt.text(
                j,
                i,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=7
            )

plt.tight_layout()

heatmap_path = (
    OUTPUT_DIR
    / "correlation_heatmap.png"
)

plt.savefig(
    heatmap_path,
    dpi=180
)

plt.close()


# ============================================================
# STRONGEST CORRELATIONS
# ============================================================

print("\n" + "=" * 80)
print("STRONGEST VARIABLE RELATIONSHIPS")
print("=" * 80)

pairs = []

for i in range(
    len(correlation.columns)
):

    for j in range(
        i + 1,
        len(correlation.columns)
    ):

        value = correlation.iloc[i, j]

        if pd.notna(value):

            pairs.append(
                {
                    "Variable_1":
                        correlation.columns[i],
                    "Variable_2":
                        correlation.columns[j],
                    "Correlation":
                        value,
                    "Absolute_Correlation":
                        abs(value),
                }
            )

pairs_df = pd.DataFrame(
    pairs
)

if not pairs_df.empty:

    pairs_df = pairs_df.sort_values(
        "Absolute_Correlation",
        ascending=False
    )

    print(
        pairs_df[
            [
                "Variable_1",
                "Variable_2",
                "Correlation",
            ]
        ]
        .head(15)
        .round(4)
        .to_string(index=False)
    )

    pairs_df.to_csv(
        OUTPUT_DIR
        / "all_variable_correlations.csv",
        index=False
    )


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n" + "=" * 80)
print("MULTIVARIATE EDA COMPLETE")
print("=" * 80)

print(
    f"\nCorrelation matrix saved to:"
)

print(
    OUTPUT_DIR / "correlation_matrix.csv"
)

print(
    f"\nHeatmap saved to:"
)

print(
    heatmap_path
)