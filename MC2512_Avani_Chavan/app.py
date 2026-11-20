from pathlib import Path
import html
import json
import os

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from gemini_api import ask_weather

try:
    from satellite_api import get_no2_data
except Exception:
    get_no2_data = None

try:
    from weather_alerts_api import get_weather_alerts
except Exception:
    get_weather_alerts = None


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
LIVE_DIR = BASE_DIR / "live_data"
DATA_DIR = BASE_DIR / "data"

PREDICTION_FILE = LIVE_DIR / "live_predictions.csv"

WEATHER_FILES = [
    LIVE_DIR / "openweather_current.csv",
    LIVE_DIR / "openweather_live_data.csv",
    LIVE_DIR / "api_weather_data.csv",
]

WAQI_FILES = [
    LIVE_DIR / "waqi_live_data.csv",
    LIVE_DIR / "waqi_current.csv",
]

CPCB_HISTORICAL_FILE = DATA_DIR / "cpcb_historical_data.csv"
COORDINATES_FILE = LIVE_DIR / "openweather_city_coordinates.csv"
WEATHER_ALERTS_FILE = LIVE_DIR / "weather_alerts_current.csv"
SATELLITE_FILE = LIVE_DIR / "sentinel5p_no2_current.csv"

COMPARISON_FILE = LIVE_DIR / "city_comparison.csv"


# ============================================================
# TOMTOM API KEY
# ============================================================

try:
    from config import TOMTOM_API_KEY as CONFIG_TOMTOM_API_KEY
except Exception:
    CONFIG_TOMTOM_API_KEY = ""

TOMTOM_API_KEY = (
    os.getenv("TOMTOM_API_KEY")
    or os.getenv("TOMTOM_MAP_API_KEY")
    or CONFIG_TOMTOM_API_KEY
)


# ============================================================
# FALLBACK COORDINATES
# Used when a city is one of the original monitored cities.
# Other cities use coordinates saved by openweather_api.py.
# ============================================================

CITY_COORDINATES = {
    "Ahmedabad": (23.0225, 72.5714),
    "Bengaluru": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Delhi": (28.6139, 77.2090),
    "Hyderabad": (17.3850, 78.4867),
    "Jaipur": (26.9124, 75.7873),
    "Kolkata": (22.5726, 88.3639),
    "Mumbai": (19.0760, 72.8777),
    "Nagpur": (21.1458, 79.0882),
    "Nashik": (19.9975, 73.7898),
    "Pune": (18.5204, 73.8567),
}


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Real-Time Weather Monitoring System",
    page_icon="🌍",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.15rem;
        font-weight: 750;
        margin-bottom: 0.15rem;
    }
    .subtitle {
        color: #777;
        font-size: 0.98rem;
        margin-bottom: 1.2rem;
    }
    .section-title {
        font-size: 1.55rem;
        font-weight: 700;
        margin-top: 1rem;
        margin-bottom: 0.9rem;
    }
    .small-note {
        color: #777;
        font-size: 0.85rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.65rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-title">🌍 Real-Time Weather Monitoring System</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'CPCB Historical Air Quality + OpenWeather + WAQI + '
    'Random Forest Prediction + Sentinel-5P + Weather Alerts + TomTom + Gemini'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def read_csv(path):
    if path is None or not path.exists():
        return None

    try:
        df = pd.read_csv(
            path,
            low_memory=False
        )
        df.columns = [
            str(c).strip()
            for c in df.columns
        ]
        return df

    except Exception as exc:
        st.warning(
            f"Could not read {path.name}: {exc}"
        )
        return None


def first_existing(paths):
    for path in paths:
        if path.exists():
            return path
    return None


def num(value):
    try:
        if pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def category(value):
    value = num(value)

    if value is None:
        return "Unknown"
    if value <= 30:
        return "Good"
    if value <= 60:
        return "Satisfactory"
    if value <= 90:
        return "Moderate"
    if value <= 120:
        return "Poor"
    if value <= 250:
        return "Very Poor"
    return "Severe"


def direction(value):
    value = num(value)

    if value is None:
        return "Unknown"
    if value > 0.5:
        return "Increase"
    if value < -0.5:
        return "Decrease"
    return "Stable"


def find_column(df, names):
    if df is None:
        return None

    exact = {
        str(c).strip().lower(): c
        for c in df.columns
    }

    for name in names:
        key = str(name).strip().lower()
        if key in exact:
            return exact[key]

    for column in df.columns:
        lower = str(column).lower()
        for name in names:
            if str(name).lower() in lower:
                return column

    return None


def safe_text(value):
    if value is None or pd.isna(value):
        return "N/A"
    return html.escape(str(value))


def load_coordinates():
    coords = dict(CITY_COORDINATES)

    if COORDINATES_FILE.exists():
        try:
            df = pd.read_csv(
                COORDINATES_FILE,
                low_memory=False
            )
            df.columns = [
                str(c).strip()
                for c in df.columns
            ]

            if {
                "City",
                "Latitude",
                "Longitude",
            }.issubset(df.columns):

                for _, r in df.iterrows():
                    try:
                        city = str(
                            r["City"]
                        ).strip()

                        lat = float(
                            r["Latitude"]
                        )

                        lon = float(
                            r["Longitude"]
                        )

                        if (
                            city
                            and pd.notna(lat)
                            and pd.notna(lon)
                        ):
                            coords[city] = (
                                lat,
                                lon
                            )

                    except Exception:
                        continue

        except Exception as exc:
            print(
                "Coordinate file error:",
                exc
            )

    return coords


# ============================================================
# LOAD PREDICTIONS
# ============================================================

pred = read_csv(PREDICTION_FILE)

if pred is None or pred.empty:
    st.error(
        "live_predictions.csv is missing or empty. "
        "Run the live air-quality/prediction pipeline first."
    )
    st.stop()

if "City" not in pred.columns:
    st.error(
        "Prediction file does not contain a City column."
    )
    st.stop()

pred["City"] = (
    pred["City"]
    .astype(str)
    .str.strip()
)


# ============================================================
# NORMALIZE PREDICTION COLUMNS
# ============================================================

current_col = find_column(
    pred,
    [
        "Current_PM25",
        "Current_PM2.5",
        "PM2.5",
        "PM2.5 (µg/m³)",
    ],
)

prediction_col = find_column(
    pred,
    [
        "Predicted_PM25_Next_1Hour",
        "Predicted_PM25_Next_15Min",
        "Predicted_PM25",
    ],
)

change_col = find_column(
    pred,
    [
        "Expected_Change",
        "PM25_Change",
        "Predicted_Change",
    ],
)

if current_col is None:
    pred["Current_PM25"] = pd.NA
else:
    pred["Current_PM25"] = pd.to_numeric(
        pred[current_col],
        errors="coerce"
    )

if prediction_col is None:
    pred["Predicted_PM25"] = pd.NA
else:
    pred["Predicted_PM25"] = pd.to_numeric(
        pred[prediction_col],
        errors="coerce"
    )

if change_col:
    pred["Expected_Change"] = pd.to_numeric(
        pred[change_col],
        errors="coerce"
    )
else:
    pred["Expected_Change"] = (
        pred["Predicted_PM25"]
        - pred["Current_PM25"]
    )

pred["Expected_Direction"] = (
    pred["Expected_Change"].apply(direction)
)

pred["Predicted_Category"] = (
    pred["Predicted_PM25"].apply(category)
)


# ============================================================
# LOAD OPENWEATHER
# ============================================================

weather_path = first_existing(
    WEATHER_FILES
)

weather = (
    read_csv(weather_path)
    if weather_path
    else None
)

if (
    weather is not None
    and not weather.empty
    and "City" in weather.columns
):

    weather["City"] = (
        weather["City"]
        .astype(str)
        .str.strip()
    )

    if "Timestamp" in weather.columns:
        weather["Timestamp"] = pd.to_datetime(
            weather["Timestamp"],
            errors="coerce",
            utc=True
        )

        weather = (
            weather
            .sort_values("Timestamp")
            .drop_duplicates(
                "City",
                keep="last"
            )
        )
    else:
        weather = weather.drop_duplicates(
            "City",
            keep="last"
        )

    weather_map = {
        "Temperature": "Temperature (°C)",
        "Humidity": "Humidity (%)",
        "Pressure": "Pressure (hPa)",
        "WindSpeed": "Wind_Speed (m/s)",
        "WindDirection": "Wind_Direction (deg)",
        "Rain1h": "Rain_1h (mm)",
        "Weather": "Weather",
        "Weather_Description": "Weather_Description",
        "Clouds": "Clouds (%)",
        "Visibility": "Visibility (m)",
    }

    weather_selected = ["City"]

    for _, source in weather_map.items():
        if source in weather.columns:
            weather_selected.append(source)

    if len(weather_selected) > 1:

        w = weather[weather_selected].copy()

        rename_map = {
            source: target
            for target, source
            in weather_map.items()
            if source in w.columns
        }

        w = w.rename(
            columns=rename_map
        )

        pred = pred.merge(
            w,
            on="City",
            how="left",
            suffixes=("", "_weather"),
        )

        for col in weather_map:

            weather_col = (
                col + "_weather"
            )

            if weather_col in pred.columns:

                if col not in pred.columns:
                    pred[col] = pred[
                        weather_col
                    ]

                else:
                    pred[col] = pred[col].fillna(
                        pred[weather_col]
                    )

                pred.drop(
                    columns=[weather_col],
                    inplace=True
                )


# ============================================================
# LOAD WAQI
# ============================================================

waqi_path = first_existing(
    WAQI_FILES
)

waqi = (
    read_csv(waqi_path)
    if waqi_path
    else None
)

waqi_available = (
    waqi is not None
    and not waqi.empty
    and "City" in waqi.columns
)

if waqi_available:

    waqi["City"] = (
        waqi["City"]
        .astype(str)
        .str.strip()
    )

    if "Timestamp" in waqi.columns:

        waqi["Timestamp"] = pd.to_datetime(
            waqi["Timestamp"],
            errors="coerce"
        )

        waqi = (
            waqi
            .sort_values("Timestamp")
            .drop_duplicates(
                "City",
                keep="last"
            )
        )

    else:

        waqi = waqi.drop_duplicates(
            "City",
            keep="last"
        )

    for col in [
        "AQI",
        "PM2.5",
        "PM10",
        "NO2",
        "SO2",
        "O3",
        "CO",
        "Temperature",
        "Humidity",
        "Pressure",
    ]:
        if col in waqi.columns:
            waqi[col] = pd.to_numeric(
                waqi[col],
                errors="coerce"
            )


# ============================================================
# LOAD CPCB HISTORICAL DATA
# ============================================================

cpcb = None

if CPCB_HISTORICAL_FILE.exists():

    try:

        cpcb_columns = {
            "City",
            "Location",
            "Timestamp",
            "PM2.5 (µg/m³)",
            "PM10 (µg/m³)",
            "NO2 (µg/m³)",
            "SO2 (µg/m³)",
            "CO (mg/m³)",
            "Ozone (µg/m³)",
            "NH3 (µg/m³)",
            "AT (°C)",
            "RH (%)",
            "WS (m/s)",
            "WD (deg)",
            "RF (mm)",
        }

        cpcb = pd.read_csv(
            CPCB_HISTORICAL_FILE,
            low_memory=False,
            usecols=lambda c: c in cpcb_columns
        )

        cpcb.columns = [
            str(c).strip()
            for c in cpcb.columns
        ]

        if "City" in cpcb.columns:

            cpcb["City"] = (
                cpcb["City"]
                .astype(str)
                .str.strip()
            )

            cpcb = cpcb[
                (cpcb["City"] != "")
                & (
                    cpcb["City"].str.lower()
                    != "unknown"
                )
                & (
                    cpcb["City"].str.lower()
                    != "nan"
                )
            ]

        if "Timestamp" in cpcb.columns:

            cpcb["Timestamp"] = pd.to_datetime(
                cpcb["Timestamp"],
                errors="coerce",
                utc=True
            )

    except Exception as exc:

        cpcb = None

        st.warning(
            "Could not load CPCB historical data: "
            f"{exc}"
        )


# ============================================================
# LOAD COORDINATES
# ============================================================

CITY_COORDINATES = load_coordinates()


# ============================================================
# CITY SELECTION
# ============================================================

if cpcb is not None and "City" in cpcb.columns:

    cities = sorted(
        cpcb["City"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )

else:

    cities = sorted(
        pred["City"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )

if not cities:

    st.error(
        "No cities are available."
    )

    st.stop()

st.sidebar.header(
    "Dashboard Controls"
)

selected_city = st.sidebar.selectbox(
    "Select City",
    cities,
    index=(
        cities.index("Pune")
        if "Pune" in cities
        else 0
    ),
)

st.sidebar.divider()

st.sidebar.write(
    f"**CPCB cities available: {len(cities)}**"
)

if cpcb is not None:

    selected_cpcb_count = int(
        (
            cpcb["City"]
            == selected_city
        ).sum()
    )

    st.sidebar.write(
        f"**Historical CPCB records: "
        f"{selected_cpcb_count:,}**"
    )

if selected_city in CITY_COORDINATES:

    lat, lon = CITY_COORDINATES[
        selected_city
    ]

    st.sidebar.caption(
        f"Coordinates: "
        f"{lat:.4f}, {lon:.4f}"
    )

else:

    st.sidebar.caption(
        "Coordinates are not currently available "
        "for this city."
    )

if st.sidebar.button(
    "🔄 Refresh Data"
):
    st.rerun()


# ============================================================
# SELECTED CITY LIVE/PREDICTION DATA
# ============================================================

city_rows = pred[
    pred["City"] == selected_city
]

has_prediction = not city_rows.empty

if has_prediction:

    row = city_rows.iloc[-1]

    current = num(
        row.get("Current_PM25")
    )

    future = num(
        row.get("Predicted_PM25")
    )

    change = num(
        row.get("Expected_Change")
    )

else:

    row = pd.Series(dtype=object)

    current = None
    future = None
    change = None

pred_category = category(
    future
)

trend = direction(
    change
)


# ============================================================
# SELECTED CITY HEADER
# ============================================================

st.markdown(
    f'<div class="section-title">'
    f'📍 {safe_text(selected_city)}'
    f'</div>',
    unsafe_allow_html=True,
)

if has_prediction:
    st.caption(
        "Live prediction record available."
    )
else:
    st.caption(
        "This city is available in the CPCB "
        "historical dataset, but a live Random Forest "
        "prediction record is not currently available."
    )


# ============================================================
# AIR QUALITY / MODEL
# ============================================================

st.markdown(
    "### 🌫️ Air Quality Prediction"
)

a, b, c, d = st.columns(4)

a.metric(
    "Current PM2.5",
    (
        "N/A"
        if current is None
        else f"{current:.2f} µg/m³"
    )
)

b.metric(
    "Next 1-Hour Prediction",
    (
        "N/A"
        if future is None
        else f"{future:.2f} µg/m³"
    )
)

c.metric(
    "Expected Change",
    (
        "N/A"
        if change is None
        else f"{change:+.2f} µg/m³"
    )
)

d.metric(
    "Predicted Category",
    pred_category
)


# ============================================================
# WAQI REFERENCE
# ============================================================

st.markdown(
    "### 🌐 WAQI Live Air Quality Reference"
)

if waqi_available:

    selected_waqi = waqi[
        waqi["City"] == selected_city
    ]

    if not selected_waqi.empty:

        wr = selected_waqi.iloc[-1]

        waqi_aqi = num(
            wr.get("AQI")
        )

        waqi_pm25 = num(
            wr.get("PM2.5")
        )

        waqi_pm10 = num(
            wr.get("PM10")
        )

        q1, q2, q3 = st.columns(3)

        q1.metric(
            "WAQI AQI",
            (
                "N/A"
                if waqi_aqi is None
                else f"{waqi_aqi:.0f}"
            )
        )

        q2.metric(
            "WAQI PM2.5",
            (
                "N/A"
                if waqi_pm25 is None
                else f"{waqi_pm25:.1f} µg/m³"
            )
        )

        q3.metric(
            "WAQI PM10",
            (
                "N/A"
                if waqi_pm10 is None
                else f"{waqi_pm10:.1f} µg/m³"
            )
        )

        station = wr.get(
            "WAQI_Station"
        )

        if (
            station is not None
            and not pd.isna(station)
        ):
            st.caption(
                f"WAQI monitoring station: {station}"
            )

    else:

        st.info(
            f"No real WAQI record is currently "
            f"available for {selected_city}."
        )

else:

    st.info(
        "WAQI data file was not found. "
        "Run `python waqi_api.py` first."
    )


# ============================================================
# TREND
# ============================================================

st.markdown(
    "### 📈 Expected Trend"
)

if not has_prediction:
    st.info(
        "A live Random Forest prediction is not "
        "available for this city yet."
    )

elif change is None:
    st.info(
        "Prediction trend is unavailable."
    )

elif change > 0.5:

    st.warning(
        f"↑ PM2.5 is expected to increase by "
        f"{abs(change):.2f} µg/m³ in the next hour."
    )

elif change < -0.5:

    st.success(
        f"↓ PM2.5 is expected to decrease by "
        f"{abs(change):.2f} µg/m³ in the next hour."
    )

else:

    st.info(
        "PM2.5 is expected to remain relatively stable."
    )


# ============================================================
# LIVE WEATHER
# ============================================================

st.markdown(
    "### 🌦️ Live Weather Conditions"
)

t = num(
    row.get("Temperature")
    if has_prediction
    else None
)

h = num(
    row.get("Humidity")
    if has_prediction
    else None
)

p = num(
    row.get("Pressure")
    if has_prediction
    else None
)

ws = num(
    row.get("WindSpeed")
    if has_prediction
    else None
)

wd = num(
    row.get("WindDirection")
    if has_prediction
    else None
)

rain = num(
    row.get("Rain1h")
    if has_prediction
    else None
)

weather_name = (
    row.get("Weather")
    if has_prediction
    else None
)

# Prefer actual OpenWeather record for the selected city.
selected_weather = None

if (
    weather is not None
    and not weather.empty
    and "City" in weather.columns
):

    selected_weather_rows = weather[
        weather["City"] == selected_city
    ]

    if not selected_weather_rows.empty:

        selected_weather = (
            selected_weather_rows.iloc[-1]
        )

        t = num(
            selected_weather.get(
                "Temperature"
            )
        )

        h = num(
            selected_weather.get(
                "Humidity"
            )
        )

        p = num(
            selected_weather.get(
                "Pressure"
            )
        )

        ws = num(
            selected_weather.get(
                "WindSpeed"
            )
        )

        wd = num(
            selected_weather.get(
                "WindDirection"
            )
        )

        rain = num(
            selected_weather.get(
                "Rain1h"
            )
        )

        weather_name = selected_weather.get(
            "Weather"
        )

w1, w2, w3, w4 = st.columns(4)

w1.metric(
    "Temperature",
    (
        "N/A"
        if t is None
        else f"{t:.2f} °C"
    )
)

w2.metric(
    "Humidity",
    (
        "N/A"
        if h is None
        else f"{h:.0f} %"
    )
)

w3.metric(
    "Pressure",
    (
        "N/A"
        if p is None
        else f"{p:.0f} hPa"
    )
)

w4.metric(
    "Wind Speed",
    (
        "N/A"
        if ws is None
        else f"{ws:.2f} m/s"
    )
)

x1, x2, x3 = st.columns(3)

x1.write(
    "🧭 **Wind Direction:** "
    + (
        "N/A"
        if wd is None
        else f"{wd:.0f}°"
    )
)

x2.write(
    "🌧️ **Rain (1h):** "
    + (
        "N/A"
        if rain is None
        else f"{rain:.2f} mm"
    )
)

x3.write(
    "☁️ **Weather:** "
    + (
        "N/A"
        if weather_name is None
        or pd.isna(weather_name)
        else str(weather_name)
    )
)


# ============================================================
# CPCB HISTORICAL DATA
# ============================================================

st.divider()

st.markdown(
    "### 📚 CPCB Historical Air Quality Data"
)

if cpcb is not None:

    selected_cpcb = cpcb[
        cpcb["City"] == selected_city
    ].copy()

    if not selected_cpcb.empty:

        st.caption(
            f"Real CPCB historical records for "
            f"{selected_city}: "
            f"{len(selected_cpcb):,}"
        )

        historical_columns = [
            "City",
            "Location",
            "Timestamp",
            "PM2.5 (µg/m³)",
            "PM10 (µg/m³)",
            "NO2 (µg/m³)",
            "SO2 (µg/m³)",
            "CO (mg/m³)",
            "Ozone (µg/m³)",
            "NH3 (µg/m³)",
            "AT (°C)",
            "RH (%)",
            "WS (m/s)",
            "WD (deg)",
            "RF (mm)",
        ]

        available_columns = [
            column
            for column in historical_columns
            if column in selected_cpcb.columns
        ]

        if "Timestamp" in selected_cpcb.columns:

            selected_cpcb = (
                selected_cpcb
                .sort_values(
                    "Timestamp",
                    ascending=False
                )
            )

        st.dataframe(
            selected_cpcb[
                available_columns
            ].head(100),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            f"No CPCB historical records found "
            f"for {selected_city}."
        )

else:

    st.warning(
        "CPCB historical dataset was not found. "
        "Expected file: data/cpcb_historical_data.csv"
    )


# ============================================================
# SENTINEL-5P SATELLITE
# ============================================================

st.divider()

st.markdown(
    "### 🛰️ Sentinel-5P Satellite Monitoring"
)

st.caption(
    "Real satellite-observed atmospheric NO₂. "
    "Satellite availability depends on valid observations."
)

satellite_value = None

# First try the saved real satellite data.
satellite_df = read_csv(
    SATELLITE_FILE
)

if (
    satellite_df is not None
    and not satellite_df.empty
    and "City" in satellite_df.columns
):

    selected_sat = satellite_df[
        satellite_df["City"].astype(str).str.strip()
        == selected_city
    ]

    if not selected_sat.empty:

        sat_row = selected_sat.iloc[-1]

        satellite_value = num(
            sat_row.get("Mean_NO2")
        )

        if satellite_value is not None:

            s1, s2, s3 = st.columns(3)

            s1.metric(
                "Satellite",
                "Sentinel-5P"
            )

            s2.metric(
                "Parameter",
                "NO₂"
            )

            s3.metric(
                "Mean NO₂",
                f"{satellite_value:.8f}"
            )

            st.caption(
                "Using a real Sentinel-5P observation "
                "saved by satellite_api.py."
            )

if satellite_value is None:

    # Optionally request a fresh value for the selected city
    # when coordinates and the satellite module are available.
    coords = CITY_COORDINATES.get(
        selected_city
    )

    if (
        coords is not None
        and get_no2_data is not None
    ):

        with st.spinner(
            "Checking Sentinel-5P satellite data..."
        ):

            try:

                fresh_satellite = get_no2_data(
                    coords[0],
                    coords[1],
                    days_back=2
                )

                if fresh_satellite is not None:

                    s1, s2, s3 = st.columns(3)

                    s1.metric(
                        "Satellite",
                        "Sentinel-5P"
                    )

                    s2.metric(
                        "Parameter",
                        "NO₂"
                    )

                    s3.metric(
                        "Mean NO₂",
                        f"{fresh_satellite:.8f}"
                    )

                    satellite_value = (
                        fresh_satellite
                    )

                else:

                    st.info(
                        "No valid Sentinel-5P observation "
                        "is currently available for this city."
                    )

            except Exception as exc:

                st.info(
                    "Sentinel-5P observation is not "
                    "currently available for this location."
                )

                print(
                    "Sentinel-5P app error:",
                    exc
                )

    else:

        st.info(
            "Coordinates or Sentinel-5P API support "
            "are not currently available for this city."
        )


# ============================================================
# WEATHER ALERTS
# ============================================================

st.divider()

st.markdown(
    "### ⚠️ Weather Alerts"
)

st.caption(
    "Current weather warnings and alerts for the selected city."
)

# Prefer the real saved alert data.
alerts_df = read_csv(
    WEATHER_ALERTS_FILE
)

shown_saved_alert = False

if (
    alerts_df is not None
    and not alerts_df.empty
    and "City" in alerts_df.columns
):

    selected_alerts = alerts_df[
        alerts_df["City"].astype(str).str.strip()
        == selected_city
    ]

    if not selected_alerts.empty:

        shown_saved_alert = True

        active_flag = selected_alerts.get(
            "Has_Active_Alert"
        )

        has_active = False

        if active_flag is not None:

            has_active = (
                selected_alerts[
                    "Has_Active_Alert"
                ]
                .astype(bool)
                .any()
            )

        if has_active:

            st.warning(
                f"Active weather alert(s) found "
                f"for {selected_city}."
            )

            for _, alert in selected_alerts.iterrows():

                headline = alert.get(
                    "Alert_Headline"
                )

                if headline is not None and not pd.isna(
                    headline
                ):

                    with st.expander(
                        f"⚠️ {headline}"
                    ):

                        st.write(
                            f"**Event:** "
                            f"{alert.get('Alert_Event', 'N/A')}"
                        )

                        st.write(
                            f"**Severity:** "
                            f"{alert.get('Alert_Severity', 'N/A')}"
                        )

                        st.write(
                            f"**Urgency:** "
                            f"{alert.get('Alert_Urgency', 'N/A')}"
                        )

                        st.write(
                            f"**Effective:** "
                            f"{alert.get('Alert_Effective', 'N/A')}"
                        )

                        st.write(
                            f"**Expires:** "
                            f"{alert.get('Alert_Expires', 'N/A')}"
                        )

                        st.write(
                            f"**Description:** "
                            f"{alert.get('Alert_Description', 'N/A')}"
                        )

        else:

            st.success(
                f"✓ No active weather alerts for "
                f"{selected_city}."
            )


# Fresh API fallback if no saved record exists.
if (
    not shown_saved_alert
    and get_weather_alerts is not None
):

    try:

        live_alerts = get_weather_alerts(
            selected_city
        )

        if live_alerts:

            st.warning(
                f"{len(live_alerts)} active weather "
                f"alert(s) for {selected_city}."
            )

            for alert in live_alerts:

                headline = alert.get(
                    "headline",
                    "Weather Alert"
                )

                with st.expander(
                    f"⚠️ {headline}"
                ):

                    st.write(
                        f"**Event:** "
                        f"{alert.get('event', 'N/A')}"
                    )

                    st.write(
                        f"**Severity:** "
                        f"{alert.get('severity', 'N/A')}"
                    )

                    st.write(
                        f"**Urgency:** "
                        f"{alert.get('urgency', 'N/A')}"
                    )

                    st.write(
                        f"**Effective:** "
                        f"{alert.get('effective', 'N/A')}"
                    )

                    st.write(
                        f"**Expires:** "
                        f"{alert.get('expires', 'N/A')}"
                    )

                    st.write(
                        f"**Description:** "
                        f"{alert.get('desc', 'N/A')}"
                    )

        else:

            st.success(
                f"✓ No active weather alerts for "
                f"{selected_city}."
            )

    except Exception as exc:

        st.info(
            "Weather alert data is not currently "
            "available for this location."
        )

        print(
            "Weather Alerts app error:",
            exc
        )


# ============================================================
# TOMTOM MAP
# Only prediction cities with known coordinates are mapped.
# This does NOT restrict the city selector.
# ============================================================

st.divider()

st.markdown(
    "### 🗺️ Live Traffic / Air Quality Map"
)

st.caption(
    "TomTom map with live prediction cities. "
    "The city selector above contains all CPCB cities."
)

map_rows = []

for _, r in pred.iterrows():

    city = str(
        r["City"]
    ).strip()

    if city not in CITY_COORDINATES:
        continue

    lat, lon = CITY_COORDINATES[
        city
    ]

    map_rows.append(
        {
            "city": city,
            "lat": lat,
            "lon": lon,
            "current": num(
                r.get("Current_PM25")
            ),
            "predicted": num(
                r.get("Predicted_PM25")
            ),
            "change": num(
                r.get("Expected_Change")
            ),
            "category": category(
                r.get("Predicted_PM25")
            ),
            "weather": r.get(
                "Weather",
                "N/A"
            ),
        }
    )

if not TOMTOM_API_KEY:

    st.warning(
        "TomTom API key is not configured. "
        "Add TOMTOM_API_KEY to config.py."
    )

elif map_rows:

    tile_url = (
        "https://api.tomtom.com/maps/orbis/"
        "display/raster/tile/"
        "{z}/{x}/{y}"
        "?apiVersion=2"
        f"&style=street-light"
        f"&key={TOMTOM_API_KEY}"
        "&tileSize=256"
        "&geopoliticalView=Unified"
    )

    map_data_json = json.dumps(
        map_rows
    )

    selected_json = json.dumps(
        selected_city
    )

    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">

        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
        />

        <style>
            html, body {{
                margin: 0;
                padding: 0;
                height: 100%;
                width: 100%;
            }}

            #map {{
                width: 100%;
                height: 560px;
                border-radius: 12px;
            }}

            .legend {{
                background: white;
                padding: 10px 12px;
                line-height: 20px;
                border-radius: 8px;
                box-shadow: 0 1px 5px rgba(0,0,0,.25);
                font-family: Arial, sans-serif;
                font-size: 12px;
            }}

            .legend i {{
                width: 12px;
                height: 12px;
                float: left;
                margin-right: 7px;
                margin-top: 4px;
                border-radius: 50%;
            }}
        </style>
    </head>

    <body>

        <div id="map"></div>

        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

        <script>

            const cities = {map_data_json};
            const selectedCity = {selected_json};

            const map = L.map("map", {{
                zoomControl: true
            }}).setView(
                [22.5, 79.0],
                5
            );

            const tomtomTiles = "{tile_url}";

            L.tileLayer(
                tomtomTiles,
                {{
                    maxZoom: 20,
                    attribution: "&copy; TomTom"
                }}
            ).addTo(map);

            function getColor(category) {{
                if (category === "Good") return "#2e7d32";
                if (category === "Satisfactory") return "#66bb6a";
                if (category === "Moderate") return "#f9a825";
                if (category === "Poor") return "#ef6c00";
                if (category === "Very Poor") return "#e53935";
                if (category === "Severe") return "#8e0000";
                return "#607d8b";
            }}

            cities.forEach(
                function(c) {{

                    const isSelected =
                        c.city === selectedCity;

                    const marker =
                        L.circleMarker(
                            [c.lat, c.lon],
                            {{
                                radius:
                                    isSelected
                                    ? 11
                                    : 8,

                                color:
                                    isSelected
                                    ? "#000000"
                                    : "#ffffff",

                                weight:
                                    isSelected
                                    ? 3
                                    : 2,

                                fillColor:
                                    getColor(
                                        c.category
                                    ),

                                fillOpacity: 0.90
                            }}
                        ).addTo(map);

                    marker.bindPopup(
                        "<b>" + c.city + "</b><br>" +
                        "Current PM2.5: " +
                        (
                            c.current === null
                            ? "N/A"
                            : c.current.toFixed(2)
                        ) +
                        " µg/m³<br>" +

                        "Next 1-hour: " +
                        (
                            c.predicted === null
                            ? "N/A"
                            : c.predicted.toFixed(2)
                        ) +
                        " µg/m³<br>" +

                        "Change: " +
                        (
                            c.change === null
                            ? "N/A"
                            :
                            (
                                c.change >= 0
                                ? "+"
                                : ""
                            ) +
                            c.change.toFixed(2)
                        ) +
                        " µg/m³<br>" +

                        "Category: " +
                        c.category +
                        "<br>" +

                        "Weather: " +
                        (
                            c.weather || "N/A"
                        )
                    );

                    if (isSelected) {{
                        marker.openPopup();
                    }}

                }}
            );

        </script>

    </body>
    </html>
    """

    components.html(
        map_html,
        height=575,
        scrolling=False
    )


# ============================================================
# WAQI ALL-CITY TABLE
# ============================================================

if (
    waqi_available
    and waqi is not None
):

    st.divider()

    st.markdown(
        "### 🌐 WAQI Live AQI — Available Cities"
    )

    waqi_table_cols = [
        column
        for column in [
            "City",
            "WAQI_Station",
            "AQI",
            "PM2.5",
            "PM10",
            "NO2",
            "SO2",
            "O3",
            "CO",
            "Timestamp",
        ]
        if column in waqi.columns
    ]

    st.dataframe(
        waqi[waqi_table_cols],
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# CITY COMPARISON
# ============================================================

st.divider()

st.markdown(
    "### 🏙️ Live Prediction City Comparison"
)

st.caption(
    "Comparison is based on cities that currently have "
    "Random Forest live prediction records."
)

comparison = read_csv(
    COMPARISON_FILE
)

if (
    comparison is not None
    and not comparison.empty
):

    display_cols = [
        "Current_Rank",
        "City",
        "Current_PM25",
        "Predicted_PM25_Next_1Hour",
        "Expected_Change",
        "Expected_Direction",
        "Predicted_Category",
    ]

    available_cols = [
        c
        for c in display_cols
        if c in comparison.columns
    ]

    st.dataframe(
        comparison[
            available_cols
        ] if available_cols else comparison,
        use_container_width=True,
        hide_index=True,
    )

else:

    comparison = pred[
        [
            "City",
            "Current_PM25",
            "Predicted_PM25",
            "Expected_Change",
            "Expected_Direction",
            "Predicted_Category",
        ]
    ].copy()

    comparison = comparison.sort_values(
        "Current_PM25",
        ascending=False
    ).reset_index(drop=True)

    comparison.insert(
        0,
        "Current_Rank",
        range(
            1,
            len(comparison) + 1
        )
    )

    comparison = comparison.rename(
        columns={
            "Predicted_PM25":
                "Predicted_PM25_Next_1Hour"
        }
    )

    st.dataframe(
        comparison,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# OVERALL SUMMARY
# ============================================================

st.markdown(
    "### 📊 Overall Air Quality Summary"
)

summary_cols = st.columns(4)

current_valid = pred.dropna(
    subset=["Current_PM25"]
).copy()

change_valid = pred.dropna(
    subset=["Expected_Change"]
).copy()

if not current_valid.empty:

    highest_current = current_valid.loc[
        current_valid[
            "Current_PM25"
        ].idxmax()
    ]

    lowest_current = current_valid.loc[
        current_valid[
            "Current_PM25"
        ].idxmin()
    ]

    summary_cols[0].metric(
        "Highest Current PM2.5",
        str(highest_current["City"]),
        f"{highest_current['Current_PM25']:.2f} µg/m³",
    )

    summary_cols[1].metric(
        "Lowest Current PM2.5",
        str(lowest_current["City"]),
        f"{lowest_current['Current_PM25']:.2f} µg/m³",
    )

if not change_valid.empty:

    largest_increase = change_valid.loc[
        change_valid[
            "Expected_Change"
        ].idxmax()
    ]

    largest_decrease = change_valid.loc[
        change_valid[
            "Expected_Change"
        ].idxmin()
    ]

    summary_cols[2].metric(
        "Largest Expected Increase",
        str(largest_increase["City"]),
        f"{largest_increase['Expected_Change']:+.2f} µg/m³",
    )

    summary_cols[3].metric(
        "Largest Expected Decrease",
        str(largest_decrease["City"]),
        f"{largest_decrease['Expected_Change']:+.2f} µg/m³",
    )


# ============================================================
# SYSTEM INFORMATION
# ============================================================

st.divider()

st.markdown(
    "### ℹ️ System Information"
)

s1, s2, s3, s4 = st.columns(4)

s1.metric(
    "CPCB Cities Available",
    len(cities)
)

s2.metric(
    "Live Prediction Cities",
    pred["City"].nunique()
)

s3.write(
    "**Prediction Horizon**"
)

s3.write(
    "Next 1 Hour"
)

s4.write(
    "**Prediction Model**"
)

s4.write(
    "Random Forest"
)


# ============================================================
# DATA STATUS
# ============================================================

timestamp_col = find_column(
    pred,
    [
        "Timestamp",
        "timestamp",
        "last_update",
    ]
)

if timestamp_col:

    timestamps = pd.to_datetime(
        pred[timestamp_col],
        errors="coerce",
        utc=True
    ).dropna()

    if len(timestamps):

        st.caption(
            "Latest prediction timestamp: "
            f"{timestamps.max()}"
        )

st.caption(
    "Real-Time Weather Monitoring System | "
    "CPCB Historical Data + OpenWeather + WAQI + "
    "TomTom + Sentinel-5P + Weather Alerts + "
    "Random Forest + Gemini"
)


# ============================================================
# CHAT WITH YOUR WEATHER
# ============================================================

st.divider()

st.markdown(
    "### 💬 Chat with Your Weather"
)

st.caption(
    "Ask questions about a selected city's air quality, "
    "weather, prediction, satellite observations, "
    "weather alerts, or available project data."
)

if (
    "weather_chat_history"
    not in st.session_state
):

    st.session_state.weather_chat_history = []


for message in (
    st.session_state.weather_chat_history
):

    with st.chat_message(
        message["role"]
    ):
        st.markdown(
            message["content"]
        )


# Build a compact context for the Gemini API.
def build_weather_context():

    selected_history = ""

    if (
        cpcb is not None
        and "City" in cpcb.columns
    ):

        selected_history_df = cpcb[
            cpcb["City"]
            == selected_city
        ].copy()

        if not selected_history_df.empty:

            if "Timestamp" in (
                selected_history_df.columns
            ):

                selected_history_df = (
                    selected_history_df
                    .sort_values(
                        "Timestamp",
                        ascending=False
                    )
                )

            selected_history = (
                selected_history_df
                .head(25)
                .fillna("Not available")
                .to_string(
                    index=False
                )
            )

    waqi_context = "WAQI: Not available"

    if waqi_available:

        selected_waqi = waqi[
            waqi["City"]
            == selected_city
        ]

        if not selected_waqi.empty:

            waqi_context = (
                selected_waqi
                .tail(1)
                .fillna("Not available")
                .to_string(
                    index=False
                )
            )

    return f"""
PROJECT:
Real-Time Weather Monitoring System

SELECTED CITY:
{selected_city}

LIVE PREDICTION:
{row.fillna("Not available").to_string()
 if has_prediction else "No live prediction record available."}

OPENWEATHER:
{selected_weather.fillna("Not available").to_string()
 if selected_weather is not None else "Not available"}

WAQI:
{waqi_context}

CPCB HISTORICAL SAMPLE:
{selected_history if selected_history else "Not available"}

SATELLITE:
{satellite_value if satellite_value is not None else "Not available"}

RULE:
Use only real supplied project data. Do not invent
missing values or future forecasts.
"""


user_question = st.chat_input(
    "Ask something about your weather..."
)

if user_question:

    st.session_state.weather_chat_history.append(
        {
            "role": "user",
            "content": user_question,
        }
    )

    with st.chat_message("user"):
        st.markdown(
            user_question
        )

    with st.chat_message("assistant"):

        with st.spinner(
            "Analyzing your weather data..."
        ):

            try:

                answer = ask_weather(
                    user_question
                )

                st.markdown(
                    answer
                )

                st.session_state.weather_chat_history.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

            except Exception as exc:

                # Fall back to a dashboard-only response
                # when Gemini is temporarily unavailable.
                st.error(
                    "Gemini could not process the question "
                    "right now. Please try again."
                )

                print(
                    "Gemini chat error:",
                    exc
                )

                st.session_state.weather_chat_history.append(
                    {
                        "role": "assistant",
                        "content":
                            "Gemini could not process the question "
                            "right now. Please try again.",
                    }
                )