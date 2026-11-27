from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# PART E - BIVARIATE ANALYSIS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "Weather_AirQuality_Data_Fusion.xlsx"

OUTPUT_DIR = BASE_DIR / "EDA_Fused_Data" / "bivariate"

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
print("PART E - BIVARIATE ANALYSIS")
print("=" * 80)

print(f"\nRows: {len(df):,}")
print(f"Columns: {len(df.columns)}")


# ============================================================
# CONVERT NUMERICAL COLUMNS
# ============================================================

numeric_columns = [
    "WAQI_AQI",
    "WAQI_PM25_ug_m3",
    "OpenWeather_Temperature_C",
    "OpenWeather_Humidity_pct",
    "OpenWeather_Pressure_hPa",
    "OpenWeather_WindSpeed_mps",
    "TomTom_CurrentSpeed_kmh",
    "TomTom_FreeFlowSpeed_kmh",
    "Sentinel5P_NO2",
    "Predicted_PM25_1h_ug_m3",
    "Expected_PM25_Change_ug_m3",
]

for column in numeric_columns:
    if column in df.columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )


# ============================================================
# FUNCTION FOR SCATTER PLOTS
# ============================================================

def create_scatter(
    x_column,
    y_column,
    filename,
    title
):

    if (
        x_column not in df.columns
        or y_column not in df.columns
    ):
        print(
            f"Skipped: {title} "
            "(required column missing)"
        )
        return

    temp = df[
        [x_column, y_column]
    ].dropna()

    if len(temp) < 2:
        print(
            f"Skipped: {title} "
            "(not enough valid data)"
        )
        return

    plt.figure(
        figsize=(8, 5)
    )

    plt.scatter(
        temp[x_column],
        temp[y_column],
        alpha=0.6
    )

    plt.title(title)
    plt.xlabel(x_column)
    plt.ylabel(y_column)

    plt.tight_layout()

    path = OUTPUT_DIR / filename

    plt.savefig(
        path,
        dpi=150
    )

    plt.close()

    correlation = temp[
        x_column
    ].corr(
        temp[y_column]
    )

    print(
        f"{title}: "
        f"records={len(temp)}, "
        f"correlation={correlation:.4f}"
    )


# ============================================================
# 1. WAQI PM2.5 vs AQI
# ============================================================

create_scatter(
    "WAQI_PM25_ug_m3",
    "WAQI_AQI",
    "waqi_pm25_vs_aqi.png",
    "WAQI PM2.5 vs WAQI AQI"
)


# ============================================================
# 2. TEMPERATURE vs PM2.5
# ============================================================

create_scatter(
    "OpenWeather_Temperature_C",
    "WAQI_PM25_ug_m3",
    "temperature_vs_pm25.png",
    "Temperature vs WAQI PM2.5"
)


# ============================================================
# 3. HUMIDITY vs PM2.5
# ============================================================

create_scatter(
    "OpenWeather_Humidity_pct",
    "WAQI_PM25_ug_m3",
    "humidity_vs_pm25.png",
    "Humidity vs WAQI PM2.5"
)


# ============================================================
# 4. WIND SPEED vs PM2.5
# ============================================================

create_scatter(
    "OpenWeather_WindSpeed_mps",
    "WAQI_PM25_ug_m3",
    "wind_speed_vs_pm25.png",
    "Wind Speed vs WAQI PM2.5"
)


# ============================================================
# 5. TRAFFIC SPEED vs PM2.5
# ============================================================

create_scatter(
    "TomTom_CurrentSpeed_kmh",
    "WAQI_PM25_ug_m3",
    "traffic_vs_pm25.png",
    "Traffic Speed vs WAQI PM2.5"
)


# ============================================================
# 6. SATELLITE NO2 vs PM2.5
# ============================================================

create_scatter(
    "Sentinel5P_NO2",
    "WAQI_PM25_ug_m3",
    "satellite_no2_vs_pm25.png",
    "Sentinel-5P NO2 vs WAQI PM2.5"
)


# ============================================================
# 7. CURRENT vs PREDICTED PM2.5
# ============================================================

if (
    "WAQI_PM25_ug_m3" in df.columns
    and "Predicted_PM25_1h_ug_m3" in df.columns
):

    temp = df[
        [
            "WAQI_PM25_ug_m3",
            "Predicted_PM25_1h_ug_m3"
        ]
    ].dropna()

    if len(temp) >= 2:

        plt.figure(
            figsize=(8, 5)
        )

        plt.scatter(
            temp["WAQI_PM25_ug_m3"],
            temp["Predicted_PM25_1h_ug_m3"],
            alpha=0.6
        )

        plt.title(
            "Current PM2.5 vs Predicted PM2.5"
        )

        plt.xlabel(
            "Current WAQI PM2.5"
        )

        plt.ylabel(
            "Predicted PM2.5 (1 Hour)"
        )

        plt.tight_layout()

        path = (
            OUTPUT_DIR
            / "current_vs_predicted_pm25.png"
        )

        plt.savefig(
            path,
            dpi=150
        )

        plt.close()

        correlation = temp[
            "WAQI_PM25_ug_m3"
        ].corr(
            temp["Predicted_PM25_1h_ug_m3"]
        )

        print(
            "Current vs Predicted PM2.5: "
            f"records={len(temp)}, "
            f"correlation={correlation:.4f}"
        )

    else:

        print(
            "Current vs Predicted PM2.5 skipped: "
            "not enough prediction records."
        )


# ============================================================
# CORRELATION SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("BIVARIATE CORRELATION SUMMARY")
print("=" * 80)

pairs = [
    (
        "WAQI_PM25_ug_m3",
        "WAQI_AQI"
    ),
    (
        "OpenWeather_Temperature_C",
        "WAQI_PM25_ug_m3"
    ),
    (
        "OpenWeather_Humidity_pct",
        "WAQI_PM25_ug_m3"
    ),
    (
        "OpenWeather_WindSpeed_mps",
        "WAQI_PM25_ug_m3"
    ),
    (
        "TomTom_CurrentSpeed_kmh",
        "WAQI_PM25_ug_m3"
    ),
    (
        "Sentinel5P_NO2",
        "WAQI_PM25_ug_m3"
    ),
]

correlation_results = []

for x, y in pairs:

    if (
        x not in df.columns
        or y not in df.columns
    ):
        continue

    temp = df[
        [x, y]
    ].dropna()

    if len(temp) < 2:
        continue

    corr = temp[x].corr(
        temp[y]
    )

    correlation_results.append(
        {
            "Variable_1": x,
            "Variable_2": y,
            "Valid_Records": len(temp),
            "Correlation": corr
        }
    )

correlation_df = pd.DataFrame(
    correlation_results
)

if not correlation_df.empty:

    print(
        correlation_df.to_string(
            index=False
        )
    )

    correlation_df.to_csv(
        OUTPUT_DIR
        / "bivariate_correlations.csv",
        index=False
    )


# ============================================================
# CITY-WISE BAR CHART
# ============================================================

if (
    "City" in df.columns
    and "WAQI_PM25_ug_m3" in df.columns
):

    city_avg = (
        df.groupby("City")[
            "WAQI_PM25_ug_m3"
        ]
        .mean()
        .sort_values(
            ascending=False
        )
        .head(15)
    )

    if not city_avg.empty:

        plt.figure(
            figsize=(12, 6)
        )

        plt.bar(
            city_avg.index,
            city_avg.values
        )

        plt.title(
            "Top 15 Cities by Average WAQI PM2.5"
        )

        plt.xlabel("City")
        plt.ylabel(
            "Average WAQI PM2.5"
        )

        plt.xticks(
            rotation=60,
            ha="right"
        )

        plt.tight_layout()

        path = (
            OUTPUT_DIR
            / "top_15_cities_pm25.png"
        )

        plt.savefig(
            path,
            dpi=150
        )

        plt.close()

        print(
            f"\nCreated: {path}"
        )


# ============================================================
# FINAL MESSAGE
# ============================================================

print("\n" + "=" * 80)
print("BIVARIATE EDA COMPLETE")
print("=" * 80)

print(
    f"\nOutput folder: {OUTPUT_DIR}"
)