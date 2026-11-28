
import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Air Quality Data Visualization",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Real-Time Air Quality Monitoring")
st.subheader("Integrated Weather, Traffic and Air Quality Analysis")

st.markdown(
    "Interactive data visualization using the "
    "Weather and Air Quality Fused Dataset."
)

# --------------------------------------------------
# LOAD FUSED DATASET
# --------------------------------------------------

FILE_PATH = "Weather_AirQuality_Data_Fusion.xlsx"

if not os.path.exists(FILE_PATH):
    st.error("Fused dataset not found!")
    st.stop()

df = pd.read_excel(
    FILE_PATH,
    sheet_name="Fused_Data"
)

# Convert numeric columns safely
numeric_columns = [
    "WAQI_AQI",
    "WAQI_PM25_ug_m3",
    "OpenWeather_Temperature_C",
    "OpenWeather_Humidity_pct",
    "OpenWeather_WindSpeed_mps",
    "OpenWeather_Pressure_hPa",
    "TomTom_CurrentSpeed_kmh",
    "TomTom_FreeFlowSpeed_kmh",
    "Sentinel5P_NO2",
    "Predicted_PM25_1h_ug_m3"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# --------------------------------------------------
# DATASET OVERVIEW
# --------------------------------------------------

st.header("1. Dataset Overview")

col1, col2, col3 = st.columns(3)

col1.metric("Total Records", len(df))
col2.metric("Total Cities", df["City"].nunique())
col3.metric("Total Attributes", len(df.columns))

st.dataframe(df.head(10), use_container_width=True)

st.divider()

# --------------------------------------------------
# CITY-WISE AQI COMPARISON
# --------------------------------------------------

st.header("2. City-wise AQI Comparison")

city_aqi = (
    df.groupby("City", as_index=False)["WAQI_AQI"]
    .mean()
    .dropna()
    .sort_values("WAQI_AQI", ascending=False)
    .head(15)
)

fig1 = px.bar(
    city_aqi,
    x="City",
    y="WAQI_AQI",
    color="WAQI_AQI",
    title="Top 15 Cities by Average AQI",
    labels={
        "WAQI_AQI": "Average AQI",
        "City": "City"
    }
)

st.plotly_chart(fig1, use_container_width=True)

st.caption(
    "This chart compares the average AQI of the 15 cities "
    "with the highest recorded averages in this dataset."
)

st.divider()

# --------------------------------------------------
# AQI AND PM2.5 COMPARISON
# --------------------------------------------------

st.header("3. AQI vs PM2.5 Comparison")

fig2 = px.scatter(
    df,
    x="WAQI_AQI",
    y="WAQI_PM25_ug_m3",
    hover_name="City",
    title="Relationship Between AQI and PM2.5",
    labels={
        "WAQI_AQI": "Air Quality Index",
        "WAQI_PM25_ug_m3": "PM2.5 (µg/m³)"
    }
)

st.plotly_chart(fig2, use_container_width=True)

st.divider()

# --------------------------------------------------
# WEATHER CONDITION COMPARISON
# --------------------------------------------------

st.header("4. Weather vs Air Quality")

weather_aqi = (
    df.groupby("OpenWeather_Weather", as_index=False)
    .agg(
        Average_AQI=("WAQI_AQI", "mean"),
        Average_PM25=("WAQI_PM25_ug_m3", "mean"),
        Records=("City", "count")
    )
    .dropna(subset=["Average_AQI"])
)

fig3 = px.bar(
    weather_aqi,
    x="OpenWeather_Weather",
    y="Average_AQI",
    color="OpenWeather_Weather",
    title="Average AQI Under Different Weather Conditions",
    labels={
        "OpenWeather_Weather": "Weather Condition",
        "Average_AQI": "Average AQI"
    },
    text_auto=".2f"
)

st.plotly_chart(fig3, use_container_width=True)
st.dataframe(weather_aqi, use_container_width=True)

st.divider()

# --------------------------------------------------
# TEMPERATURE VS SATELLITE NO2
# --------------------------------------------------

st.header("5. Temperature vs Satellite NO₂")

no2_data = df.dropna(
    subset=[
        "OpenWeather_Temperature_C",
        "Sentinel5P_NO2"
    ]
)

fig4 = px.scatter(
    no2_data,
    x="OpenWeather_Temperature_C",
    y="Sentinel5P_NO2",
    hover_name="City",
    title="Temperature vs Satellite NO₂",
    labels={
        "OpenWeather_Temperature_C": "Temperature (°C)",
        "Sentinel5P_NO2": "Satellite NO₂"
    }
)

st.plotly_chart(fig4, use_container_width=True)

st.divider()

# --------------------------------------------------
# TRAFFIC VS AIR QUALITY
# --------------------------------------------------

st.header("6. Traffic Speed vs AQI")

fig5 = px.scatter(
    df,
    x="TomTom_CurrentSpeed_kmh",
    y="WAQI_AQI",
    hover_name="City",
    title="Current Traffic Speed vs AQI",
    labels={
        "TomTom_CurrentSpeed_kmh": "Current Traffic Speed (km/h)",
        "WAQI_AQI": "Air Quality Index"
    }
)

st.plotly_chart(fig5, use_container_width=True)

st.divider()

# --------------------------------------------------
# CORRELATION HEATMAP
# --------------------------------------------------

st.header("7. Correlation Heatmap")

heatmap_columns = [
    "OpenWeather_Temperature_C",
    "OpenWeather_Humidity_pct",
    "OpenWeather_WindSpeed_mps",
    "OpenWeather_Pressure_hPa",
    "WAQI_AQI",
    "WAQI_PM25_ug_m3",
    "TomTom_CurrentSpeed_kmh",
    "TomTom_FreeFlowSpeed_kmh",
    "Sentinel5P_NO2"
]

correlation = df[heatmap_columns].corr()

fig6 = px.imshow(
    correlation,
    text_auto=".2f",
    color_continuous_scale="RdBu_r",
    zmin=-1,
    zmax=1,
    title="Correlation Between Weather, Traffic and Air Quality"
)

st.plotly_chart(fig6, use_container_width=True)

st.divider()

# --------------------------------------------------
# ACTUAL VS PREDICTED PM2.5
# --------------------------------------------------

st.header("8. Actual vs Predicted PM2.5")

prediction_data = df.dropna(
    subset=[
        "WAQI_PM25_ug_m3",
        "Predicted_PM25_1h_ug_m3"
    ]
)

if not prediction_data.empty:

    fig7 = px.scatter(
        prediction_data,
        x="WAQI_PM25_ug_m3",
        y="Predicted_PM25_1h_ug_m3",
        hover_name="City",
        title="Actual PM2.5 vs Predicted PM2.5",
        labels={
            "WAQI_PM25_ug_m3": "Actual PM2.5 (µg/m³)",
            "Predicted_PM25_1h_ug_m3": "Predicted PM2.5 (µg/m³)"
        }
    )

    st.plotly_chart(fig7, use_container_width=True)

else:
    st.info(
        "Predicted PM2.5 values are not available "
        "in the current dataset."
    )

st.success("All available visualizations generated successfully!")
