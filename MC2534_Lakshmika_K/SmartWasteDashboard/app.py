
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="SmartWaste Analytics Dashboard",
    page_icon="♻️",
    layout="wide"
)

st.title("♻️ SmartWaste Analytics Dashboard")
st.write(
    "Interactive EDA Dashboard using Fused Weather, "
    "Air Quality and Recycling API Data"
)

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    df = pd.read_csv("final_fused_waste_dataset.csv")

    numeric_cols = [
        "Latitude", "Longitude",
        "OpenWeather_Temperature_C",
        "OpenWeather_Humidity_Percent",
        "OpenWeather_Wind_Speed_mps",
        "WeatherAPI_Precipitation_MM",
        "OpenMeteo_PM2_5",
        "OpenMeteo_PM10",
        "OpenMeteo_US_AQI",
        "Recycling_Facility_Count",
        "Average_Facility_Distance_Meters",
        "European_AQI",
        "WeatherAPI_UV_Index"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


try:
    df = load_data()
except Exception as e:
    st.error(f"Dataset load nahi hui: {e}")
    st.stop()

# ---------------- FILTERS ----------------
st.sidebar.header("🔎 Dashboard Filters")

data = df.copy()


def apply_multiselect(data, column, label):
    if column in data.columns:
        options = sorted(data[column].dropna().astype(str).unique())
        selected = st.sidebar.multiselect(label, options)

        if selected:
            data = data[data[column].astype(str).isin(selected)]

    return data


data = apply_multiselect(data, "State", "Select State")
data = apply_multiselect(data, "Region", "Select Region")
data = apply_multiselect(data, "City", "Select City")

weather_col = "OpenWeather_Weather_Main"

if weather_col not in data.columns:
    weather_col = "WeatherAPI_Condition"

data = apply_multiselect(data, weather_col, "Weather Condition")

temp_col = "OpenWeather_Temperature_C"

if temp_col in data.columns and data[temp_col].notna().any():
    min_temp = float(data[temp_col].min())
    max_temp = float(data[temp_col].max())

    if min_temp < max_temp:
        temp_range = st.sidebar.slider(
            "Temperature Range (°C)",
            min_value=min_temp,
            max_value=max_temp,
            value=(min_temp, max_temp)
        )

        data = data[
            data[temp_col].between(
                temp_range[0], temp_range[1]
            )
        ]

st.sidebar.caption(f"Filtered records: {len(data)}")

if data.empty:
    st.warning("No records found. Please change the filters.")
    st.stop()

# ---------------- KPI CARDS ----------------
k1, k2, k3, k4 = st.columns(4)

k1.metric("Total Records", len(data))

k2.metric(
    "Unique Cities",
    data["City"].nunique() if "City" in data.columns else "N/A"
)

avg_temp = (
    data[temp_col].mean()
    if temp_col in data.columns
    else float("nan")
)

k3.metric(
    "Average Temperature",
    f"{avg_temp:.1f} °C" if pd.notna(avg_temp) else "N/A"
)

aqi_col = "OpenMeteo_US_AQI"
avg_aqi = (
    data[aqi_col].mean()
    if aqi_col in data.columns
    else float("nan")
)

k4.metric(
    "Average US AQI",
    f"{avg_aqi:.1f}" if pd.notna(avg_aqi) else "N/A"
)

st.divider()


# ---------------- CHART HELPER ----------------
def show_chart(title, columns, builder):
    missing = [col for col in columns if col not in data.columns]

    if missing:
        st.warning(f"{title}: required data column unavailable.")
        return

    valid = data.dropna(subset=columns)

    if valid.empty:
        st.info(f"{title}: no valid data after filtering.")
        return

    fig = builder(valid)
    fig.update_layout(
        title=title,
        margin=dict(l=30, r=30, t=65, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)


def city_mean(column):
    return (
        data.dropna(subset=["City", column])
        .groupby("City", as_index=False)[column]
        .mean()
        .sort_values(column, ascending=False)
    )


# 1. PIE CHART
st.subheader("1. Weather Condition Distribution")

show_chart(
    "Weather Condition Distribution",
    [weather_col],
    lambda d: px.pie(
        d,
        names=weather_col,
        hole=0.35
    )
)

# 2. BAR CHART
st.subheader("2. Recycling Facilities by City")

facility_col = "Recycling_Facility_Count"

show_chart(
    "Recycling Facilities by City",
    ["City", facility_col],
    lambda d: px.bar(
        city_mean(facility_col),
        x="City",
        y=facility_col,
        color=facility_col,
        labels={facility_col: "Facility Count"}
    )
)

# 3. HISTOGRAM
st.subheader("3. Temperature Distribution")

show_chart(
    "Temperature Distribution",
    [temp_col],
    lambda d: px.histogram(
        d,
        x=temp_col,
        nbins=20,
        labels={temp_col: "Temperature (°C)"}
    )
)

# 4. BOX PLOT
st.subheader("4. Humidity Distribution")

humidity_col = "OpenWeather_Humidity_Percent"

show_chart(
    "Humidity Distribution",
    [humidity_col],
    lambda d: px.box(
        d,
        y=humidity_col,
        points="all",
        labels={humidity_col: "Humidity (%)"}
    )
)

# 5. SCATTER PLOT
st.subheader("5. Temperature vs Humidity")

show_chart(
    "Temperature vs Humidity",
    [temp_col, humidity_col],
    lambda d: px.scatter(
        d,
        x=temp_col,
        y=humidity_col,
        color="Region" if "Region" in d.columns else None,
        hover_name="City" if "City" in d.columns else None,
        labels={
            temp_col: "Temperature (°C)",
            humidity_col: "Humidity (%)"
        }
    )
)

# 6. CORRELATION HEATMAP
st.subheader("6. Correlation Heatmap")

corr_candidates = [
    temp_col,
    humidity_col,
    "OpenWeather_Wind_Speed_mps",
    "WeatherAPI_Precipitation_MM",
    "OpenMeteo_PM2_5",
    "OpenMeteo_PM10",
    "OpenMeteo_US_AQI",
    facility_col,
    "Average_Facility_Distance_Meters"
]

corr_cols = [
    c for c in corr_candidates
    if c in data.columns
    and pd.api.types.is_numeric_dtype(data[c])
    and data[c].notna().any()
]

if len(corr_cols) >= 2:
    corr = data[corr_cols].corr()

    fig = px.imshow(
        corr,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1
    )

    fig.update_layout(title="Correlation Heatmap")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Heatmap ke liye enough numeric columns nahi hain.")

# 7. LINE CHART
st.subheader("7. City-wise Temperature Comparison")

show_chart(
    "Temperature by City (Sorted Comparison, Not Time Trend)",
    ["City", temp_col],
    lambda d: px.line(
        city_mean(temp_col).sort_values("City"),
        x="City",
        y=temp_col,
        markers=True,
        labels={temp_col: "Temperature (°C)"}
    )
)

# 8. VIOLIN PLOT
st.subheader("8. Wind Speed Distribution")

wind_col = "OpenWeather_Wind_Speed_mps"

show_chart(
    "Wind Speed Distribution",
    [wind_col],
    lambda d: px.violin(
        d,
        y=wind_col,
        box=True,
        points="all",
        labels={wind_col: "Wind Speed (m/s)"}
    )
)

# 9. TREEMAP
st.subheader("9. Records by Region and City")

if "Region" in data.columns and "City" in data.columns:
    tree_data = (
        data.groupby(["Region", "City"], dropna=False)
        .size()
        .reset_index(name="Record_Count")
    )

    if not tree_data.empty:
        fig = px.treemap(
            tree_data,
            path=["Region", "City"],
            values="Record_Count",
            color="Record_Count"
        )
        fig.update_layout(title="Records by Region and City")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Treemap ke liye Region aur City columns required hain.")

# 10. DENSITY CONTOUR
st.subheader("10. PM2.5 vs PM10 Density Contour")

pm25 = "OpenMeteo_PM2_5"
pm10 = "OpenMeteo_PM10"

show_chart(
    "Air Pollution Density Contour",
    [pm25, pm10],
    lambda d: px.density_contour(
        d,
        x=pm25,
        y=pm10,
        labels={
            pm25: "PM2.5",
            pm10: "PM10"
        }
    )
)

# 11. BUBBLE CHART
st.subheader("11. Temperature, Humidity and AQI")

show_chart(
    "Bubble Chart: Temperature, Humidity and AQI",
    [temp_col, humidity_col, aqi_col],
    lambda d: px.scatter(
        d,
        x=temp_col,
        y=humidity_col,
        size=aqi_col,
        color=aqi_col,
        hover_name="City" if "City" in d.columns else None,
        size_max=45,
        labels={
            temp_col: "Temperature (°C)",
            humidity_col: "Humidity (%)",
            aqi_col: "US AQI"
        }
    )
)

# 12. LOLLIPOP CHART
st.subheader("12. Average AQI by City — Lollipop Chart")

if "City" in data.columns and aqi_col in data.columns:
    lollipop_data = city_mean(aqi_col).sort_values(aqi_col).tail(15)

    if not lollipop_data.empty:
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=lollipop_data[aqi_col],
            y=lollipop_data["City"],
            mode="markers+text",
            text=lollipop_data[aqi_col].round(1),
            textposition="middle right",
            marker=dict(size=12),
            name="Average AQI"
        ))

        for _, row in lollipop_data.iterrows():
            fig.add_shape(
                type="line",
                x0=0,
                x1=row[aqi_col],
                y0=row["City"],
                y1=row["City"],
                line=dict(width=2)
            )

        fig.update_layout(
            title="Average US AQI by City",
            xaxis_title="Average US AQI",
            yaxis_title="City"
        )

        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Lollipop chart ke liye City aur AQI columns required hain.")

# ---------------- DATA PREVIEW ----------------
st.divider()
st.subheader("Filtered Dataset Preview")

st.dataframe(data, use_container_width=True)

st.download_button(
    "Download Filtered Dataset",
    data=data.to_csv(index=False).encode("utf-8"),
    file_name="filtered_fused_waste_dataset.csv",
    mime="text/csv"
)
