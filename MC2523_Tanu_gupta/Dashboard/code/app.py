from calendar import month_abbr
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = Path(__file__).resolve().parent / "assets" / "weather_app_img"
FUSED_DATA_FILE = PROJECT_ROOT / "dataset" / "processed" / "fused_weather_data.csv"
HISTORICAL_DATA_FILE = PROJECT_ROOT / "dataset" / "processed" / "weather_cleaned.csv"
WEATHER_IMAGE_DIR = ASSET_DIR

FUSED_REQUIRED_COLUMNS = {
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
HISTORICAL_REQUIRED_COLUMNS = {
    "city",
    "date",
    "temperature_2m_max",
    "temperature_2m_min",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "precipitation_sum",
    "rain_sum",
    "weather_code",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "wind_direction_10m_dominant",
    "weather_description",
}
FUSED_NUMERIC_COLUMNS = [
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
HISTORICAL_NUMERIC_COLUMNS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "precipitation_sum",
    "rain_sum",
    "weather_code",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "wind_direction_10m_dominant",
]
WEATHER_ICONS = {
    "Clear sky": "clear.png",
    "Clouds": "clouds.png",
    "Drizzle": "drizzle.png",
    "Rain": "rain.png",
    "Snow": "snow.png",
    "Mist": "mist.png",
    "Humidity": "humidity.png",
    "Wind": "wind.png",
    "Search": "search.png",
}

st.set_page_config(
    page_title="Weather Insights Dashboard",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        [data-testid="stAppViewContainer"] {
            background: radial-gradient(ellipse at top right, #19264a 0, #0b1020 48%);
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #121a31, #0e1426);
        }
        [data-testid="stMetric"] {
            background: #131b33;
            border: 1px solid #25305a;
            border-radius: 12px;
            padding: 14px 16px;
        }
        [data-testid="stMetricLabel"] { color: #aab6d3; }
        .block-container { max-width: 1500px; padding-top: 1.6rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

px.defaults.template = "plotly_dark"


@st.cache_data(show_spinner="Loading weather records...")
def load_fused_data(path: str) -> pd.DataFrame:
    data = pd.read_csv(path)
    missing_columns = FUSED_REQUIRED_COLUMNS.difference(data.columns)
    if missing_columns:
        raise ValueError(
            "The fused CSV is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce")
    for column in FUSED_NUMERIC_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    for column in ["city", "current_condition", "current_description", "comparison_status"]:
        data[column] = data[column].astype("string").str.strip()

    return data.dropna(subset=["timestamp", "city"]).copy()


@st.cache_data(show_spinner="Loading historical climate records...")
def load_historical_data(path: str) -> pd.DataFrame:
    data = pd.read_csv(path)
    missing_columns = HISTORICAL_REQUIRED_COLUMNS.difference(data.columns)
    if missing_columns:
        raise ValueError(
            "The historical CSV is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    for column in HISTORICAL_NUMERIC_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data["city"] = data["city"].astype("string").str.strip()
    data["weather_description"] = (
        data["weather_description"].astype("string").str.strip()
    )

    return data.dropna(subset=["date", "city"]).copy()


def date_bounds(selection):
    if isinstance(selection, (tuple, list)) and len(selection) == 2:
        return selection[0], selection[1]
    return selection, selection


def filter_data(data, city_column, date_column, cities, dates):
    start_date, end_date = date_bounds(dates)
    mask = data[city_column].isin(cities)
    mask &= data[date_column].dt.date.between(start_date, end_date)
    return data.loc[mask].copy()


def draw_chart(figure, key):
    figure.update_layout(
        margin=dict(l=12, r=12, t=42, b=12),
        legend_title_text="",
        title_font_size=15,
        title_x=0.02,
    )
    st.plotly_chart(
        figure,
        width="stretch",
        config={"displaylogo": False},
        key=key,
    )


def icon_for_description(description):
    value = str(description).casefold()
    if any(word in value for word in ("thunder", "rain")):
        return WEATHER_IMAGE_DIR / WEATHER_ICONS["Rain"]
    if "drizzle" in value:
        return WEATHER_IMAGE_DIR / WEATHER_ICONS["Drizzle"]
    if "snow" in value or "sleet" in value:
        return WEATHER_IMAGE_DIR / WEATHER_ICONS["Snow"]
    if any(word in value for word in ("mist", "fog", "haze", "smoke")):
        return WEATHER_IMAGE_DIR / WEATHER_ICONS["Mist"]
    if any(word in value for word in ("cloud", "overcast")):
        return WEATHER_IMAGE_DIR / WEATHER_ICONS["Clouds"]
    return WEATHER_IMAGE_DIR / WEATHER_ICONS["Clear sky"]


def show_icon_gallery():
    st.subheader("Weather icon key")
    columns = st.columns(len(WEATHER_ICONS))
    for column, (label, filename) in zip(columns, WEATHER_ICONS.items()):
        image_path = WEATHER_IMAGE_DIR / filename
        with column:
            if image_path.is_file():
                st.image(str(image_path), width=48)
            st.caption(label)


def annual_temperature_figure(data):
    annual = (
        data.assign(year=data["date"].dt.year)
        .groupby("year", as_index=False)
        .agg(
            Average_high=("temperature_2m_max", "mean"),
            Average_low=("temperature_2m_min", "mean"),
        )
    )
    long_form = annual.melt(
        id_vars="year",
        var_name="Temperature",
        value_name="Temperature (°C)",
    )
    return px.line(
        long_form,
        x="year",
        y="Temperature (°C)",
        color="Temperature",
        markers=True,
        title="Annual average daily high and low",
        labels={"year": "Year"},
        color_discrete_map={"Average_high": "#ff7a45", "Average_low": "#38bdf8"},
    )


def render_overview(historical, fused):
    st.header("Weather overview")
    st.caption(
        "Historical daily observations and saved live-weather captures in one "
        "interactive dashboard."
    )

    latest = fused.sort_values("timestamp").iloc[-1] if not fused.empty else None
    metrics = st.columns(3)
    metrics[0].metric("Historical records", f"{len(historical):,}")
    metrics[1].metric(
        "Historical cities",
        f"{historical['city'].nunique():,}" if not historical.empty else "0",
    )
    metrics[2].metric("Saved weather captures", f"{len(fused):,}")

    capture_metrics = st.columns(2)
    capture_metrics[0].metric(
        "Average captured temperature",
        f"{fused['current_temperature_celsius'].mean():.1f} °C"
        if not fused.empty
        else "—",
    )
    capture_metrics[1].metric(
        "Latest capture",
        f"{latest['current_temperature_celsius']:.1f} °C"
        if latest is not None
        else "—",
        (
            f"{latest['city']} · {latest['timestamp']:%d %b %Y}"
            if latest is not None
            else "No captures in this filter"
        ),
    )

    if latest is not None:
        icon_path = icon_for_description(latest["current_description"])
        if icon_path.is_file():
            image_col, detail_col = st.columns([1, 8])
            with image_col:
                st.image(str(icon_path), width=72)
            with detail_col:
                st.markdown(
                    f"**Latest saved observation:** {latest['city']} — "
                    f"{latest['current_description']} · "
                    f"{latest['current_temperature_celsius']:.1f} °C"
                )
                st.caption(
                    f"Captured {latest['timestamp']:%d %b %Y at %H:%M}. "
                    "This is a stored observation, not a live refresh."
                )

    left, right = st.columns(2)
    if not historical.empty:
        with left:
            draw_chart(
                annual_temperature_figure(historical),
                "overview_annual_temperature",
            )
    else:
        left.info("No historical records match the selected filters.")

    if not fused.empty:
        city_counts = (
            fused.groupby("city", as_index=False)
            .size()
            .sort_values("size", ascending=False)
        )
        with right:
            draw_chart(
                px.bar(
                    city_counts,
                    x="city",
                    y="size",
                    color="city",
                    title="Saved observations by city",
                    labels={"city": "City", "size": "Observations"},
                ),
                "overview_city_captures",
            )
    else:
        right.info("No saved observations match the selected filters.")

    left, right = st.columns(2)
    if not historical.empty:
        conditions = (
            historical["weather_description"]
            .fillna("Unknown")
            .value_counts()
            .rename_axis("Weather condition")
            .reset_index(name="Records")
        )
        with left:
            draw_chart(
                px.pie(
                    conditions,
                    names="Weather condition",
                    values="Records",
                    hole=0.56,
                    title="Historical weather conditions",
                ),
                "overview_historical_conditions",
            )
    else:
        left.info("Historical condition chart is unavailable for this selection.")

    if not fused.empty:
        conditions = (
            fused["current_condition"]
            .fillna("Unknown")
            .value_counts()
            .rename_axis("Current condition")
            .reset_index(name="Captures")
        )
        with right:
            draw_chart(
                px.pie(
                    conditions,
                    names="Current condition",
                    values="Captures",
                    hole=0.56,
                    title="Captured current conditions",
                ),
                "overview_current_conditions",
            )
    else:
        right.info("Current-condition chart is unavailable for this selection.")

    show_icon_gallery()


def render_historical(historical):
    st.header("Historical climate")
    st.caption(
        "Explore daily records from 2000–2024. The charts use the selected "
        "cities and historical date range."
    )
    if historical.empty:
        st.info("No historical records match the selected filters.")
        return

    draw_chart(annual_temperature_figure(historical), "historical_annual_temp")

    monthly = historical.assign(
        year=historical["date"].dt.year,
        month=historical["date"].dt.month,
    )
    monthly_pivot = monthly.pivot_table(
        index="year",
        columns="month",
        values="temperature_2m_max",
        aggfunc="mean",
    ).reindex(columns=range(1, 13))
    month_labels = [month_abbr[month] for month in range(1, 13)]
    heatmap = px.imshow(
        monthly_pivot,
        x=month_labels,
        y=monthly_pivot.index,
        aspect="auto",
        color_continuous_scale="RdYlBu_r",
        labels={
            "x": "Month",
            "y": "Year",
            "color": "Average high (°C)",
        },
        title="Seasonality heatmap — average daily high",
    )
    draw_chart(heatmap, "historical_seasonality_heatmap")

    left, right = st.columns(2)
    monthly_rain = (
        historical.assign(month=historical["date"].dt.month)
        .groupby("month", as_index=False)
        .agg(
            Average_rainfall=("rain_sum", "mean"),
            Average_precipitation=("precipitation_sum", "mean"),
        )
    )
    monthly_rain["Month"] = monthly_rain["month"].map(
        lambda month: month_abbr[month]
    )
    with left:
        draw_chart(
            px.bar(
                monthly_rain,
                x="Month",
                y=["Average_rainfall", "Average_precipitation"],
                barmode="group",
                title="Average rainfall and precipitation by month",
                labels={
                    "value": "Millimetres",
                    "variable": "Measure",
                    "Month": "Month",
                },
            ),
            "historical_monthly_rainfall",
        )

    city_temperature = (
        historical.groupby("city", as_index=False)
        .agg(
            Average_high=("temperature_2m_max", "mean"),
            Average_low=("temperature_2m_min", "mean"),
        )
        .sort_values("Average_high", ascending=True)
    )
    with right:
        draw_chart(
            px.bar(
                city_temperature,
                x=["Average_low", "Average_high"],
                y="city",
                barmode="group",
                orientation="h",
                title="Average daily temperatures by city",
                labels={
                    "value": "Temperature (°C)",
                    "variable": "Measure",
                    "city": "City",
                },
            ),
            "historical_city_temperature",
        )

    left, right = st.columns(2)
    conditions = (
        historical["weather_description"]
        .fillna("Unknown")
        .value_counts()
        .rename_axis("Weather condition")
        .reset_index(name="Records")
    )
    with left:
        draw_chart(
            px.bar(
                conditions,
                x="Weather condition",
                y="Records",
                color="Weather condition",
                title="Historical weather-condition frequency",
            ),
            "historical_condition_counts",
        )

    with right:
        draw_chart(
            px.scatter(
                historical,
                x="wind_speed_10m_max",
                y="wind_gusts_10m_max",
                color="city",
                hover_data=["date", "weather_description"],
                labels={
                    "wind_speed_10m_max": "Maximum wind speed (km/h)",
                    "wind_gusts_10m_max": "Maximum wind gust (km/h)",
                    "city": "City",
                },
                title="Maximum wind speed and gust",
            ),
            "historical_wind_gust",
        )

    left, right = st.columns(2)
    with left:
        draw_chart(
            px.histogram(
                historical,
                x="temperature_2m_max",
                color="city",
                nbins=30,
                opacity=0.75,
                labels={
                    "temperature_2m_max": "Daily high (°C)",
                    "city": "City",
                },
                title="Distribution of daily high temperatures",
            ),
            "historical_temperature_distribution",
        )

    with right:
        draw_chart(
            px.scatter(
                historical,
                x="temperature_2m_max",
                y="rain_sum",
                color="weather_description",
                hover_data=["city", "date"],
                labels={
                    "temperature_2m_max": "Daily high (°C)",
                    "rain_sum": "Rainfall (mm)",
                    "weather_description": "Condition",
                },
                title="Daily high temperature and rainfall",
            ),
            "historical_temperature_rain",
        )


def render_fusion(fused):
    st.header("Live and historical fusion")
    st.caption(
        "Compare saved current-weather captures with the historical statistics "
        "retrieved for each city."
    )
    if fused.empty:
        st.info("No saved observations match the selected filters.")
        return

    comparison = fused.dropna(
        subset=[
            "current_temperature_celsius",
            "historical_average_celsius",
            "temperature_difference_celsius",
        ]
    )

    latest = fused.sort_values("timestamp").iloc[-1]
    metrics = st.columns(2)
    metrics[0].metric(
        "Latest saved temperature",
        f"{latest['current_temperature_celsius']:.1f} °C",
        latest["city"],
    )
    metrics[1].metric(
        "Average humidity",
        f"{fused['current_humidity_percent'].mean():.1f}%",
    )
    metrics = st.columns(2)
    metrics[0].metric(
        "Average wind speed",
        f"{fused['current_wind_speed_kmh'].mean():.1f} km/h",
    )
    metrics[1].metric(
        "Records with historical match",
        f"{len(comparison):,} / {len(fused):,}",
    )

    left, right = st.columns(2)
    if not comparison.empty:
        lower = min(
            comparison["current_temperature_celsius"].min(),
            comparison["historical_average_celsius"].min(),
        )
        upper = max(
            comparison["current_temperature_celsius"].max(),
            comparison["historical_average_celsius"].max(),
        )
        figure = px.scatter(
            comparison,
            x="historical_average_celsius",
            y="current_temperature_celsius",
            color="comparison_status",
            hover_data=[
                "city",
                "timestamp",
                "temperature_difference_celsius",
                "historical_records_used",
            ],
            labels={
                "historical_average_celsius": "Historical average (°C)",
                "current_temperature_celsius": "Captured temperature (°C)",
                "comparison_status": "Comparison",
                "historical_records_used": "Historical records used",
            },
            title="Captured vs. historical average",
            color_discrete_map={
                "above historical average": "#ff7a45",
                "below historical average": "#38bdf8",
                "at historical average": "#34d399",
            },
        )
        figure.add_trace(
            go.Scatter(
                x=[lower, upper],
                y=[lower, upper],
                mode="lines",
                name="Equal to historical average",
                line=dict(color="#aab6d3", dash="dash"),
            )
        )
        with left:
            draw_chart(figure, "fusion_historical_scatter")
    else:
        left.info("No captures have complete historical comparison values.")

    temperature_trend = fused.sort_values("timestamp")
    with right:
        draw_chart(
            px.line(
                temperature_trend,
                x="timestamp",
                y="current_temperature_celsius",
                color="city",
                markers=True,
                hover_data=["current_description"],
                labels={
                    "timestamp": "Capture time",
                    "current_temperature_celsius": "Temperature (°C)",
                    "city": "City",
                },
                title="Temperature captures over time",
            ),
            "fusion_temperature_timeline",
        )

    left, right = st.columns(2)
    if not comparison.empty:
        deviation = comparison.sort_values("timestamp")
        with left:
            draw_chart(
                px.bar(
                    deviation,
                    x="timestamp",
                    y="temperature_difference_celsius",
                    color="comparison_status",
                    hover_data=["city", "historical_average_celsius"],
                    labels={
                        "timestamp": "Capture time",
                        "temperature_difference_celsius": "Difference (°C)",
                        "comparison_status": "Comparison",
                    },
                    title="Difference from historical average",
                    color_discrete_map={
                        "above historical average": "#ff7a45",
                        "below historical average": "#38bdf8",
                        "at historical average": "#34d399",
                    },
                ),
                "fusion_temperature_difference",
            )
    else:
        left.info("Temperature-difference chart needs historical comparison values.")

    with right:
        draw_chart(
            px.bar(
                fused,
                x="city",
                y="current_temperature_celsius",
                color="current_condition",
                barmode="group",
                hover_data=["timestamp", "current_description"],
                labels={
                    "city": "City",
                    "current_temperature_celsius": "Temperature (°C)",
                    "current_condition": "Condition",
                },
                title="Temperature by city",
            ),
            "fusion_city_temperature",
        )

    left, right = st.columns(2)
    with left:
        draw_chart(
            px.scatter(
                fused,
                x="current_temperature_celsius",
                y="current_humidity_percent",
                color="current_condition",
                size="historical_records_used",
                hover_data=["city", "timestamp"],
                labels={
                    "current_temperature_celsius": "Temperature (°C)",
                    "current_humidity_percent": "Humidity (%)",
                    "current_condition": "Condition",
                    "historical_records_used": "Historical records used",
                },
                title="Temperature vs. humidity",
            ),
            "fusion_temperature_humidity",
        )

    with right:
        draw_chart(
            px.scatter(
                fused,
                x="current_temperature_celsius",
                y="current_wind_speed_kmh",
                color="city",
                hover_data=["timestamp", "current_condition"],
                labels={
                    "current_temperature_celsius": "Temperature (°C)",
                    "current_wind_speed_kmh": "Wind speed (km/h)",
                    "city": "City",
                },
                title="Temperature vs. wind speed",
            ),
            "fusion_temperature_wind",
        )


def render_data_explorer(historical, fused):
    st.header("Data explorer")
    st.caption(
        "Inspect or download the filtered source records. Historical data and "
        "saved API captures remain separate datasets."
    )
    dataset = st.radio(
        "Dataset",
        ["Historical daily records", "Saved weather captures"],
        horizontal=True,
    )
    data = historical if dataset == "Historical daily records" else fused
    if data.empty:
        st.info("No records match the selected filters.")
        return

    if dataset == "Saved weather captures":
        duplicate_count = int(data.duplicated().sum())
        missing_comparisons = int(data["historical_average_celsius"].isna().sum())
        quality = st.columns(2)
        quality[0].metric("Exact duplicate rows", f"{duplicate_count:,}")
        quality[1].metric("Missing historical averages", f"{missing_comparisons:,}")

    display_count = st.slider(
        "Rows to show",
        min_value=1,
        max_value=len(data),
        value=min(500, len(data)),
        step=max(1, min(100, len(data))),
    )
    sort_column = "timestamp" if dataset == "Saved weather captures" else "date"
    st.dataframe(
        data.sort_values(sort_column, ascending=False).head(display_count),
        width="stretch",
        hide_index=True,
    )
    st.download_button(
        "Download all filtered rows as CSV",
        data=data.to_csv(index=False).encode("utf-8"),
        file_name=(
            "filtered_historical_weather.csv"
            if dataset == "Historical daily records"
            else "filtered_weather_captures.csv"
        ),
        mime="text/csv",
    )


st.title("Weather Insights")
st.caption("A unified dashboard for historical climate and captured live weather.")

try:
    fused_data = load_fused_data(str(FUSED_DATA_FILE))
    historical_data = load_historical_data(str(HISTORICAL_DATA_FILE))
except (OSError, pd.errors.ParserError, UnicodeDecodeError, ValueError) as error:
    st.error(f"Unable to load the dashboard datasets: {error}")
    st.stop()

with st.sidebar:
    st.header("Dashboard filters")
    st.caption("Filters apply across all dashboard sections.")

    historical_cities = sorted(
        historical_data["city"].dropna().unique().tolist(),
        key=str.casefold,
    )
    selected_historical_cities = st.multiselect(
        "Historical cities",
        historical_cities,
        default=historical_cities,
    )
    historical_start = historical_data["date"].min().date()
    historical_end = historical_data["date"].max().date()
    selected_historical_dates = st.date_input(
        "Historical date range",
        value=(historical_start, historical_end),
        min_value=historical_start,
        max_value=historical_end,
    )

    fused_cities = sorted(
        fused_data["city"].dropna().unique().tolist(),
        key=str.casefold,
    )
    selected_fused_cities = st.multiselect(
        "Captured-weather cities",
        fused_cities,
        default=fused_cities,
    )
    fused_start = fused_data["timestamp"].min().date()
    fused_end = fused_data["timestamp"].max().date()
    selected_fused_dates = st.date_input(
        "Capture date range",
        value=(fused_start, fused_end),
        min_value=fused_start,
        max_value=fused_end,
    )

    st.divider()
    st.caption("Historical data: daily records from 2000 to 2024.")
    st.caption("Capture data: observations saved by the weather application.")

filtered_historical = filter_data(
    historical_data,
    "city",
    "date",
    selected_historical_cities,
    selected_historical_dates,
)
filtered_fused = filter_data(
    fused_data,
    "city",
    "timestamp",
    selected_fused_cities,
    selected_fused_dates,
)

overview_tab, historical_tab, fusion_tab, explorer_tab = st.tabs(
    ["Overview", "Historical climate", "Live + historical fusion", "Data explorer"]
)
with overview_tab:
    render_overview(filtered_historical, filtered_fused)
with historical_tab:
    render_historical(filtered_historical)
with fusion_tab:
    render_fusion(filtered_fused)
with explorer_tab:
    render_data_explorer(filtered_historical, filtered_fused)
