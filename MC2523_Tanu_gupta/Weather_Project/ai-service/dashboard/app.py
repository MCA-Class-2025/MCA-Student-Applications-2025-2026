from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


DATA_FILE = Path(__file__).resolve().parents[1] / "fused_weather_data.csv"
REQUIRED_COLUMNS = {
    "timestamp",
    "city",
    "current_temperature_celsius",
    "historical_average_celsius",
    "historical_min_celsius",
    "historical_max_celsius",
    "temperature_difference_celsius",
    "comparison_status",
    "current_humidity_percent",
    "current_wind_speed_mps",
    "current_wind_speed_kmh",
    "current_condition",
    "current_description",
    "historical_records_used",
}
TEMPERATURE_COLUMNS = [
    "current_temperature_celsius",
    "historical_average_celsius",
    "historical_min_celsius",
    "historical_max_celsius",
    "temperature_difference_celsius",
    "current_humidity_percent",
    "current_wind_speed_mps",
    "current_wind_speed_kmh",
    "historical_records_used",
]

st.set_page_config(
    page_title="Weather Insights",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .stApp { background: #f4f7fb; }
        [data-testid="stHeader"] { background: rgba(0, 0, 0, 0); }
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e6ebf2;
            padding: 18px 20px;
            border-radius: 14px;
            box-shadow: 0 3px 12px rgba(29, 48, 77, 0.05);
        }
        [data-testid="stMetricLabel"] { color: #64748b; }
        h1, h2, h3 { color: #172554; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_weather_data(path: str) -> pd.DataFrame:
    data = pd.read_csv(path)
    missing_columns = REQUIRED_COLUMNS.difference(data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"The CSV is missing required columns: {missing}")

    data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce")
    for column in TEMPERATURE_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    for column in ["city", "current_condition", "current_description", "comparison_status"]:
        data[column] = data[column].astype("string").str.strip()

    return data.dropna(subset=["timestamp", "city"]).copy()


st.title("🌦️ Weather Insights")
st.caption("Explore current observations and compare them with historical weather records.")

if not DATA_FILE.is_file():
    st.error(f"Could not find the dataset at `{DATA_FILE}`.")
    st.stop()

try:
    weather = load_weather_data(str(DATA_FILE))
except (OSError, pd.errors.ParserError, UnicodeDecodeError, ValueError) as error:
    st.error(f"Unable to load the weather dataset: {error}")
    st.stop()

if weather.empty:
    st.warning("The dataset has no valid weather records to display.")
    st.stop()

with st.sidebar:
    st.header("Filter data")
    st.caption(f"Source: `{DATA_FILE.name}`")

    city_options = sorted(weather["city"].dropna().unique().tolist(), key=str.casefold)
    selected_cities = st.multiselect("City", city_options, default=city_options)

    condition_options = sorted(
        weather["current_condition"].dropna().unique().tolist(),
        key=str.casefold,
    )
    selected_conditions = st.multiselect(
        "Weather condition", condition_options, default=condition_options
    )

    first_date = weather["timestamp"].min().date()
    last_date = weather["timestamp"].max().date()
    selected_dates = st.date_input(
        "Observation date range",
        value=(first_date, last_date),
        min_value=first_date,
        max_value=last_date,
    )

filtered = weather[
    weather["city"].isin(selected_cities)
    & weather["current_condition"].isin(selected_conditions)
].copy()

if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
    filtered = filtered[
        filtered["timestamp"].dt.date.between(start_date, end_date)
    ]

if filtered.empty:
    st.info("No records match these filters. Change your selections to see the dashboard.")
    st.stop()

filtered = filtered.sort_values("timestamp")
latest = filtered.iloc[-1]

metric_columns = st.columns(4)
metric_columns[0].metric(
    "Latest temperature",
    f"{latest['current_temperature_celsius']:.1f} °C"
    if pd.notna(latest["current_temperature_celsius"])
    else "—",
    f"{latest['city']} · {latest['timestamp']:%d %b %Y, %H:%M}",
)
metric_columns[1].metric(
    "Average temperature",
    f"{filtered['current_temperature_celsius'].mean():.1f} °C"
    if filtered["current_temperature_celsius"].notna().any()
    else "—",
)
metric_columns[2].metric(
    "Average humidity",
    f"{filtered['current_humidity_percent'].mean():.1f}%"
    if filtered["current_humidity_percent"].notna().any()
    else "—",
)
metric_columns[3].metric("Weather observations", f"{len(filtered):,}")

st.subheader("1. Temperature distribution")
distribution_chart = px.histogram(
    filtered,
    x="current_temperature_celsius",
    color="current_condition",
    nbins=15,
    labels={
        "current_temperature_celsius": "API current temperature (°C)",
        "count": "Observations",
        "current_condition": "Weather condition",
    },
    template="plotly_white",
)
distribution_chart.update_layout(
    barmode="overlay",
    margin=dict(l=10, r=10, t=25, b=10),
    legend_title_text="Condition",
)
distribution_chart.update_traces(opacity=0.78)
st.plotly_chart(distribution_chart, width="stretch")

st.subheader("2. Temperature spread by city — boxplot")
boxplot_chart = px.box(
    filtered,
    x="city",
    y="current_temperature_celsius",
    color="city",
    points="all",
    labels={
        "city": "City",
        "current_temperature_celsius": "API current temperature (°C)",
    },
    template="plotly_white",
)
boxplot_chart.update_layout(
    showlegend=False,
    margin=dict(l=10, r=10, t=25, b=10),
)
st.plotly_chart(boxplot_chart, width="stretch")

st.subheader("3–4. Relationships")
relationship_left, relationship_right = st.columns(2)

with relationship_left:
    st.markdown("**Temperature vs. humidity**")
    temperature_humidity_chart = px.scatter(
        filtered,
        x="current_temperature_celsius",
        y="current_humidity_percent",
        color="current_condition",
        hover_data=["city", "timestamp"],
        labels={
            "current_temperature_celsius": "API current temperature (°C)",
            "current_humidity_percent": "Humidity (%)",
            "current_condition": "Weather condition",
        },
        template="plotly_white",
    )
    temperature_humidity_chart.update_layout(
        margin=dict(l=10, r=10, t=25, b=10),
        legend_title_text="Condition",
    )
    st.plotly_chart(temperature_humidity_chart, width="stretch")

with relationship_right:
    st.markdown("**Temperature vs. wind speed**")
    temperature_wind_chart = px.scatter(
        filtered,
        x="current_temperature_celsius",
        y="current_wind_speed_kmh",
        color="current_condition",
        hover_data=["city", "timestamp"],
        labels={
            "current_temperature_celsius": "API current temperature (°C)",
            "current_wind_speed_kmh": "Wind speed (km/h)",
            "current_condition": "Weather condition",
        },
        template="plotly_white",
    )
    temperature_wind_chart.update_layout(
        margin=dict(l=10, r=10, t=25, b=10),
        legend_title_text="Condition",
    )
    st.plotly_chart(temperature_wind_chart, width="stretch")

st.subheader("5. Correlation heatmap")
correlation_labels = {
    "current_temperature_celsius": "API temperature (°C)",
    "historical_average_celsius": "Original historical average (°C)",
    "temperature_difference_celsius": "Temperature difference (°C)",
    "current_humidity_percent": "Humidity (%)",
    "current_wind_speed_kmh": "Wind speed (km/h)",
    "historical_records_used": "Historical records used",
}
correlation_data = filtered[list(correlation_labels)].rename(
    columns=correlation_labels
)
correlation_data = correlation_data.loc[
    :, correlation_data.nunique(dropna=True) > 1
]

if correlation_data.shape[1] < 2:
    st.info("At least two varying numeric fields are needed for a correlation heatmap.")
else:
    correlation_matrix = correlation_data.corr()
    heatmap = px.imshow(
        correlation_matrix,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        color_continuous_midpoint=0,
        zmin=-1,
        zmax=1,
        aspect="auto",
        labels={"color": "Correlation"},
        template="plotly_white",
    )
    heatmap.update_layout(margin=dict(l=10, r=10, t=25, b=10))
    st.plotly_chart(heatmap, width="stretch")

st.subheader("6. API–original data fusion insight")
st.caption(
    "Each point compares an API current temperature with the original-data "
    "historical average used to contextualize it. Points above the diagonal "
    "are warmer than the historical average; points below are cooler."
)
fusion_data = filtered.dropna(
    subset=[
        "current_temperature_celsius",
        "historical_average_celsius",
        "temperature_difference_celsius",
    ]
)

if fusion_data.empty:
    st.info("No complete API and historical temperature pairs match these filters.")
else:
    average_difference = fusion_data["temperature_difference_celsius"].mean()
    warmer_share = (
        fusion_data["comparison_status"].eq("above historical average").mean() * 100
    )
    insight_left, insight_right = st.columns(2)
    insight_left.metric(
        "Mean API − historical average",
        f"{average_difference:+.1f} °C",
        help="Calculated from the fused temperature_difference_celsius field.",
    )
    insight_right.metric(
        "Observations above historical average",
        f"{warmer_share:.0f}%",
        help="Share of fused observations marked above their historical average.",
    )

    fusion_chart = px.scatter(
        fusion_data,
        x="historical_average_celsius",
        y="current_temperature_celsius",
        color="comparison_status",
        hover_data={
            "city": True,
            "timestamp": True,
            "temperature_difference_celsius": ":.2f",
            "historical_average_celsius": ":.2f",
            "current_temperature_celsius": ":.2f",
        },
        color_discrete_map={
            "above historical average": "#ef553b",
            "below historical average": "#636efa",
            "at historical average": "#00a884",
        },
        labels={
            "historical_average_celsius": "Original historical average (°C)",
            "current_temperature_celsius": "API current temperature (°C)",
            "comparison_status": "Fusion result",
            "temperature_difference_celsius": "API − historical (°C)",
        },
        template="plotly_white",
    )
    shared_min = min(
        fusion_data["historical_average_celsius"].min(),
        fusion_data["current_temperature_celsius"].min(),
    )
    shared_max = max(
        fusion_data["historical_average_celsius"].max(),
        fusion_data["current_temperature_celsius"].max(),
    )
    fusion_chart.add_trace(
        go.Scatter(
            x=[shared_min, shared_max],
            y=[shared_min, shared_max],
            mode="lines",
            name="Same as historical average",
            line=dict(color="#334155", dash="dash"),
        )
    )
    fusion_chart.update_layout(
        xaxis=dict(range=[shared_min, shared_max]),
        yaxis=dict(range=[shared_min, shared_max], scaleanchor="x", scaleratio=1),
        margin=dict(l=10, r=10, t=25, b=10),
        legend_title_text="Fusion result",
    )
    st.plotly_chart(fusion_chart, width="stretch")

st.subheader("Weather records")
st.dataframe(
    filtered.sort_values("timestamp", ascending=False),
    width="stretch",
    hide_index=True,
)

st.download_button(
    "Download filtered data as CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_weather_data.csv",
    mime="text/csv",
)
