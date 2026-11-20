from pathlib import Path
import joblib
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

LIVE_AIR_FILE = Path(
    "live_data/live_air_quality_processed.csv"
)

WEATHER_FILE = Path(
    "live_data/api_weather_data.csv"
)

HISTORY_FILE = Path(
    "live_data/pm25_history.csv"
)

HISTORICAL_FILE = Path(
    "cleaned_data/maharashtra_pune_mumbai_cleaned.csv"
)

MODEL_FILE = Path(
    "models/random_forest_pm25.pkl"
)

OUTPUT_FILE = Path(
    "live_data/live_prediction_features.csv"
)


# ============================================================
# HEADER
# ============================================================

print("=" * 80)
print("AIR QUALITY - LIVE FEATURE ENGINEERING")
print("=" * 80)


# ============================================================
# CHECK FILES
# ============================================================

for file in [
    LIVE_AIR_FILE,
    WEATHER_FILE,
    HISTORY_FILE,
    HISTORICAL_FILE,
    MODEL_FILE
]:
    if not file.exists():
        raise FileNotFoundError(
            f"Required file not found:\n{file}"
        )


# ============================================================
# LOAD LIVE AIR QUALITY
# ============================================================

print()
print("Loading live CPCB air quality data:")
print(LIVE_AIR_FILE)

air = pd.read_csv(LIVE_AIR_FILE)

print(
    f"Live air-quality rows: {len(air)}"
)


# ============================================================
# NORMALIZE COLUMN NAMES
# ============================================================

rename_air = {}

for column in air.columns:

    if column == "city":
        rename_air[column] = "City"

    elif column == "station":
        rename_air[column] = "Station"

    elif column == "last_update":
        rename_air[column] = "Timestamp"


air = air.rename(
    columns=rename_air
)


required_air_columns = [
    "City",
    "Timestamp",
    "PM2.5 (µg/m³)"
]


missing_air = [
    c for c in required_air_columns
    if c not in air.columns
]


if missing_air:

    raise ValueError(
        "Required columns missing from live air data:\n"
        + "\n".join(
            f"- {c}" for c in missing_air
        )
    )


# ============================================================
# DATETIME
# ============================================================

air["Timestamp"] = pd.to_datetime(
    air["Timestamp"],
    errors="coerce",
    utc=True
)


# ============================================================
# NUMERIC POLLUTANTS
# ============================================================

pollutant_columns = [
    "PM2.5 (µg/m³)",
    "PM10 (µg/m³)",
    "NO2 (µg/m³)",
    "NH3 (µg/m³)",
    "SO2 (µg/m³)",
    "CO (mg/m³)",
    "Ozone (µg/m³)"
]


for column in pollutant_columns:

    if column in air.columns:

        air[column] = pd.to_numeric(
            air[column],
            errors="coerce"
        )


air = air.dropna(
    subset=[
        "City",
        "Timestamp",
        "PM2.5 (µg/m³)"
    ]
)


print()
print(
    "Valid live air-quality rows:",
    len(air)
)


# ============================================================
# LOAD WEATHER API DATA
# ============================================================

print()
print("Loading OpenWeather data:")
print(WEATHER_FILE)

weather = pd.read_csv(
    WEATHER_FILE
)

print(
    f"Weather rows: {len(weather)}"
)


# ============================================================
# NORMALIZE WEATHER COLUMNS
# ============================================================

weather_columns = {
    "city": "City",
    "timestamp": "Weather_Timestamp",
    "AT (°C)": "AT (°C)",
    "RH (%)": "RH (%)",
    "WS (m/s)": "WS (m/s)",
    "WD (deg)": "WD (deg)"
}


weather = weather.rename(
    columns={
        k: v
        for k, v in weather_columns.items()
        if k in weather.columns
    }
)


if "City" not in weather.columns:

    raise ValueError(
        "City column missing from weather API data."
    )


weather_required = [
    "AT (°C)",
    "RH (%)",
    "WS (m/s)",
    "WD (deg)"
]


for column in weather_required:

    if column not in weather.columns:

        raise ValueError(
            f"Weather API data missing:\n{column}"
        )

    weather[column] = pd.to_numeric(
        weather[column],
        errors="coerce"
    )


# ============================================================
# SELECT MUMBAI AND PUNE
# ============================================================

cities = [
    "Mumbai",
    "Pune"
]


air["City"] = (
    air["City"]
    .astype(str)
    .str.strip()
)


weather["City"] = (
    weather["City"]
    .astype(str)
    .str.strip()
)


air = air[
    air["City"].isin(cities)
].copy()


weather = weather[
    weather["City"].isin(cities)
].copy()


# ============================================================
# FIND LATEST VALID AIR RECORD PER CITY
# ============================================================

print()
print("Selecting latest valid live pollution record...")


model_pollutants = [
    "PM10 (µg/m³)",
    "NO2 (µg/m³)",
    "NH3 (µg/m³)",
    "SO2 (µg/m³)",
    "CO (mg/m³)",
    "Ozone (µg/m³)"
]


# We need a complete pollutant vector for the model.
# Instead of filling missing values artificially, search
# backwards within the live CPCB data for the latest row
# that contains all required pollutants.

selected_air = []


for city in cities:

    city_df = air[
        air["City"] == city
    ].copy()

    city_df = city_df.sort_values(
        "Timestamp",
        ascending=False
    )

    valid_rows = city_df.dropna(
        subset=model_pollutants
    )

    if valid_rows.empty:

        raise ValueError(
            f"No complete live pollutant record "
            f"available for {city}."
        )

    selected_air.append(
        valid_rows.iloc[0]
    )


air_latest = pd.DataFrame(
    selected_air
).reset_index(drop=True)


print()
print("Selected live air-quality records:")

print(
    air_latest[
        [
            "City",
            "Timestamp",
            "PM2.5 (µg/m³)"
        ]
        + model_pollutants
    ].to_string(index=False)
)


# ============================================================
# SELECT WEATHER RECORD PER CITY
# ============================================================

selected_weather = []


for city in cities:

    city_weather = weather[
        weather["City"] == city
    ].copy()

    if city_weather.empty:

        raise ValueError(
            f"No weather API data available for {city}."
        )

    valid_weather = city_weather.dropna(
        subset=weather_required
    )

    if valid_weather.empty:

        raise ValueError(
            f"No complete weather API data available "
            f"for {city}."
        )

    if "Weather_Timestamp" in valid_weather.columns:

        valid_weather["Weather_Timestamp"] = pd.to_datetime(
            valid_weather["Weather_Timestamp"],
            errors="coerce",
            utc=True
        )

        valid_weather = valid_weather.sort_values(
            "Weather_Timestamp",
            ascending=False
        )

    selected_weather.append(
        valid_weather.iloc[0]
    )


weather_latest = pd.DataFrame(
    selected_weather
).reset_index(drop=True)


print()
print("Selected real-time weather:")

print(
    weather_latest[
        ["City"] + weather_required
    ].to_string(index=False)
)


# ============================================================
# COMBINE AIR + WEATHER
# ============================================================

print()
print("Combining live pollution and weather data...")


live = air_latest.merge(
    weather_latest[
        ["City"] + weather_required
    ],
    on="City",
    how="inner"
)


if live.empty:

    raise ValueError(
        "Could not combine live air-quality and "
        "weather data."
    )


# ============================================================
# LOAD LIVE PM2.5 HISTORY
# ============================================================

print()
print("Loading live PM2.5 history:")
print(HISTORY_FILE)

history = pd.read_csv(
    HISTORY_FILE
)

print(
    f"Live history rows: {len(history)}"
)


history = history.rename(
    columns={
        "city": "City",
        "last_update": "Timestamp"
    }
)


if "City" not in history.columns:

    raise ValueError(
        "City column missing from PM2.5 history."
    )


if "Timestamp" not in history.columns:

    raise ValueError(
        "Timestamp column missing from PM2.5 history."
    )


if "PM2.5 (µg/m³)" not in history.columns:

    raise ValueError(
        "PM2.5 column missing from PM2.5 history."
    )


history["Timestamp"] = pd.to_datetime(
    history["Timestamp"],
    errors="coerce",
    utc=True
)


history["PM2.5 (µg/m³)"] = pd.to_numeric(
    history["PM2.5 (µg/m³)"],
    errors="coerce"
)


history = history.dropna(
    subset=[
        "City",
        "Timestamp",
        "PM2.5 (µg/m³)"
    ]
)


# ============================================================
# LOAD HISTORICAL DATA
# ============================================================

print()
print("Loading historical PM2.5 data:")

historical = pd.read_csv(
    HISTORICAL_FILE,
    low_memory=False
)

print(
    f"Historical rows: {len(historical)}"
)


# ============================================================
# NORMALIZE HISTORICAL COLUMNS
# ============================================================

historical = historical.rename(
    columns={
        "city": "City",
        "timestamp": "Timestamp",
        "Timestamp": "Timestamp"
    }
)


if "City" not in historical.columns:

    raise ValueError(
        "City column missing from historical data."
    )


if "Timestamp" not in historical.columns:

    raise ValueError(
        "Timestamp column missing from historical data."
    )


if "PM2.5 (µg/m³)" not in historical.columns:

    raise ValueError(
        "PM2.5 column missing from historical data."
    )


historical["City"] = (
    historical["City"]
    .astype(str)
    .str.strip()
)


historical["Timestamp"] = pd.to_datetime(
    historical["Timestamp"],
    errors="coerce",
    utc=True
)


historical["PM2.5 (µg/m³)"] = pd.to_numeric(
    historical["PM2.5 (µg/m³)"],
    errors="coerce"
)


historical = historical[
    historical["City"].isin(cities)
].dropna(
    subset=[
        "City",
        "Timestamp",
        "PM2.5 (µg/m³)"
    ]
)


# ============================================================
# BUILD PM2.5 HISTORY
# ============================================================

print()
print("Building PM2.5 lag and rolling features...")


history_base = historical[
    [
        "City",
        "Timestamp",
        "PM2.5 (µg/m³)"
    ]
].copy()


live_history = history[
    [
        "City",
        "Timestamp",
        "PM2.5 (µg/m³)"
    ]
].copy()


combined_history = pd.concat(
    [
        history_base,
        live_history
    ],
    ignore_index=True
)


combined_history = combined_history.drop_duplicates(
    subset=[
        "City",
        "Timestamp"
    ],
    keep="last"
)


combined_history = combined_history.sort_values(
    [
        "City",
        "Timestamp"
    ]
)


# ============================================================
# CREATE LAG FEATURES
# ============================================================

print()
print("Creating PM2.5 lag features...")


for city in cities:

    city_mask = (
        combined_history["City"] == city
    )

    city_values = (
        combined_history.loc[
            city_mask,
            "PM2.5 (µg/m³)"
        ]
        .astype(float)
    )

    combined_history.loc[
        city_mask,
        "PM25_Lag_1"
    ] = city_values.shift(1).values

    combined_history.loc[
        city_mask,
        "PM25_Lag_4"
    ] = city_values.shift(4).values

    combined_history.loc[
        city_mask,
        "PM25_Lag_8"
    ] = city_values.shift(8).values

    combined_history.loc[
        city_mask,
        "PM25_Lag_96"
    ] = city_values.shift(96).values

    combined_history.loc[
        city_mask,
        "PM25_Lag_672"
    ] = city_values.shift(672).values


# ============================================================
# ROLLING FEATURES
# ============================================================

for city in cities:

    city_mask = (
        combined_history["City"] == city
    )

    city_values = (
        combined_history.loc[
            city_mask,
            "PM2.5 (µg/m³)"
        ]
        .astype(float)
    )

    combined_history.loc[
        city_mask,
        "PM25_RollingMean_1H"
    ] = (
        city_values
        .rolling(
            window=4,
            min_periods=1
        )
        .mean()
        .values
    )

    combined_history.loc[
        city_mask,
        "PM25_RollingMean_3H"
    ] = (
        city_values
        .rolling(
            window=12,
            min_periods=1
        )
        .mean()
        .values
    )

    combined_history.loc[
        city_mask,
        "PM25_RollingStd_1H"
    ] = (
        city_values
        .rolling(
            window=4,
            min_periods=2
        )
        .std()
        .values
    )


# ============================================================
# GET LIVE FEATURE ROWS
# ============================================================

live = live.merge(
    combined_history[
        [
            "City",
            "Timestamp",
            "PM25_Lag_1",
            "PM25_Lag_4",
            "PM25_Lag_8",
            "PM25_Lag_96",
            "PM25_Lag_672",
            "PM25_RollingMean_1H",
            "PM25_RollingMean_3H",
            "PM25_RollingStd_1H"
        ]
    ],
    on=[
        "City",
        "Timestamp"
    ],
    how="left"
)


# ============================================================
# CALENDAR FEATURES
# ============================================================

print()
print("Creating calendar features...")


live["Hour"] = (
    live["Timestamp"].dt.hour
)

live["Minute"] = (
    live["Timestamp"].dt.minute
)

live["DayOfWeek"] = (
    live["Timestamp"].dt.dayofweek
)

live["DayOfMonth"] = (
    live["Timestamp"].dt.day
)

live["Month"] = (
    live["Timestamp"].dt.month
)

live["IsWeekend"] = (
    live["DayOfWeek"] >= 5
).astype(int)


live["HourSin"] = np.sin(
    2 * np.pi * live["Hour"] / 24
)

live["HourCos"] = np.cos(
    2 * np.pi * live["Hour"] / 24
)

live["MonthSin"] = np.sin(
    2 * np.pi * live["Month"] / 12
)

live["MonthCos"] = np.cos(
    2 * np.pi * live["Month"] / 12
)


# ============================================================
# CITY FEATURES
# ============================================================

print()
print("Creating city features...")


live["City_Mumbai"] = (
    live["City"]
    .astype(str)
    .str.strip()
    .str.lower()
    .eq("mumbai")
    .astype(int)
)


live["City_Pune"] = (
    live["City"]
    .astype(str)
    .str.strip()
    .str.lower()
    .eq("pune")
    .astype(int)
)


# ============================================================
# LOAD MODEL FEATURE STRUCTURE
# ============================================================

print()
print("Reading exact Random Forest feature structure...")


model = joblib.load(
    MODEL_FILE
)


if not hasattr(
    model,
    "feature_names_in_"
):

    raise ValueError(
        "Random Forest does not contain "
        "feature_names_in_."
    )


model_features = list(
    model.feature_names_in_
)


print(
    f"Model requires {len(model_features)} features."
)


# ============================================================
# CHECK FEATURES
# ============================================================

missing_features = [
    feature
    for feature in model_features
    if feature not in live.columns
]


if missing_features:

    print()
    print("=" * 80)
    print("ERROR: MISSING MODEL FEATURES")
    print("=" * 80)

    for feature in missing_features:
        print(f"- {feature}")

    raise ValueError(
        "Live data does not contain all "
        "Random Forest features."
    )


# ============================================================
# SELECT EXACT FEATURES
# ============================================================

final_features = live[
    [
        "Timestamp",
        "City"
    ] + model_features
].copy()


# ============================================================
# HANDLE ROLLING STD
# ============================================================

# Standard deviation can be NaN when there is only
# one observation in a very short history. In that
# situation zero is mathematically appropriate because
# there is no observed variation.

if "PM25_RollingStd_1H" in final_features.columns:

    final_features[
        "PM25_RollingStd_1H"
    ] = final_features[
        "PM25_RollingStd_1H"
    ].fillna(0)


# ============================================================
# FINAL NULL CHECK
# ============================================================

numeric_model_features = [
    feature
    for feature in model_features
    if feature not in [
        "City_Mumbai",
        "City_Pune"
    ]
]


missing_values = (
    final_features[
        numeric_model_features
    ]
    .isna()
    .sum()
)


missing_values = missing_values[
    missing_values > 0
]


if len(missing_values) > 0:

    print()
    print("=" * 80)
    print("ERROR: MISSING VALUES IN LIVE FEATURES")
    print("=" * 80)

    print(
        missing_values.to_string()
    )

    print()
    print(
        "The live feature data cannot be used "
        "until all required lag/weather values "
        "are available."
    )

    raise ValueError(
        "Missing values detected in live model features."
    )


# ============================================================
# FINAL COLUMN ORDER
# ============================================================

final_features = final_features[
    [
        "Timestamp",
        "City"
    ] + model_features
]


# ============================================================
# DISPLAY
# ============================================================

print()
print("=" * 80)
print("LIVE FEATURE ENGINEERING COMPLETE")
print("=" * 80)

print()
print(
    f"Rows: {len(final_features)}"
)

print(
    f"Columns: {len(final_features.columns)}"
)

print()
print("Cities:")

print(
    final_features[
        "City"
    ].value_counts().to_string()
)

print()
print("Final model features:")

for feature in model_features:
    print(f"- {feature}")


print()
print("Final live feature data:")

display_columns = [
    "Timestamp",
    "City"
] + model_features


print(
    final_features[
        display_columns
    ].to_string(index=False)
)


# ============================================================
# SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


final_features.to_csv(
    OUTPUT_FILE,
    index=False
)


print()
print("Saved:")
print(OUTPUT_FILE)

print("=" * 80)