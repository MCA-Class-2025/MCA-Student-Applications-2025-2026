"""StoryVerse Analytics: Interactive Data Science and Visualization Dashboard.

Run with:  streamlit run app.py
Only Python is used. Streamlit draws the page, Plotly draws the charts and
pandas / NumPy do all calculations. Theme colours live in .streamlit/config.toml.

Every chart / card has its own "Filter" button that affects only that card.
"""

from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from src import analysis, visualizations as viz
from src.data_loader import DatasetError, load_excel
from src.filters import (ALL_FIELDS, STANDARD_FIELDS, WEATHER_FIELDS, chart_filter, reset_all_filters)
from src.preprocessing import preprocess

APP_TITLE = "StoryVerse Analytics: Interactive Data Science and Visualization Dashboard"
DEFAULT_DATA_PATH = Path(__file__).parent / "data" / "storyverse_dataset.xlsx"

st.set_page_config(page_title="StoryVerse Analytics", page_icon="📚", layout="wide",
                   initial_sidebar_state="expanded")


# --------------------------------------------------------------------------- #
# Data loading (cached so the app stays fast)
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner="Loading and preparing the dataset...")
def load_and_prepare(file_bytes: bytes = None, path: str = None, modified: float = 0.0):
    """Load the Excel file, then return (raw, processed, preprocessing_log, sheet_name).

    `modified` is only part of the cache key so edits to the file refresh the cache.
    """
    source = BytesIO(file_bytes) if file_bytes is not None else path
    raw, sheet = load_excel(source)
    processed, log = preprocess(raw)
    return raw, processed, log, sheet


# --------------------------------------------------------------------------- #
# Sidebar: brand, data source, dataset info
# --------------------------------------------------------------------------- #
st.sidebar.title("📚 StoryVerse")
st.sidebar.caption("Story analytics workspace")
st.sidebar.subheader("Dataset")
source_choice = st.sidebar.radio("Data source", ["Bundled dataset (data folder)", "Upload an Excel file"],
                                 label_visibility="collapsed")
uploaded = None
if source_choice == "Upload an Excel file":
    uploaded = st.sidebar.file_uploader("Upload storyverse_dataset.xlsx", type=["xlsx"])
    if uploaded is None:
        st.info("Upload an .xlsx file in the sidebar, or switch back to the bundled dataset.")
        st.stop()

try:
    if uploaded is not None:
        raw_df, df_all, preprocessing_log, sheet_used = load_and_prepare(file_bytes=uploaded.getvalue())
        dataset_id = f"upload{uploaded.size}"
    else:
        raw_df, df_all, preprocessing_log, sheet_used = load_and_prepare(
            path=str(DEFAULT_DATA_PATH),
            modified=DEFAULT_DATA_PATH.stat().st_mtime if DEFAULT_DATA_PATH.exists() else 0.0)
        dataset_id = "bundled"
except DatasetError as error:
    st.error(f"⚠️ {error}")
    st.stop()
except Exception as error:  # last-resort safety net with a friendly message
    st.error(f"Something unexpected went wrong while loading the data: {error}")
    st.stop()

time_info = analysis.timestamp_summary(raw_df["Timestamp"])
st.sidebar.metric("Rows × Columns", f"{raw_df.shape[0]} × {raw_df.shape[1]}")
if time_info.get("valid"):
    st.sidebar.caption(f"Sheet “{sheet_used}” · {time_info['start']:%d %b %Y} → {time_info['end']:%d %b %Y}")
st.sidebar.divider()
st.sidebar.subheader("Filters")
st.sidebar.caption("Every chart has its own **Filter** button (top-right of the card). "
                   "A filter changes only that chart.")
st.sidebar.button("↺ Reset all filters", on_click=reset_all_filters, width="stretch")


# --------------------------------------------------------------------------- #
# Layout helpers
# --------------------------------------------------------------------------- #
def panel(scope, header, render, fields=STANDARD_FIELDS, extras=None, ratio=(3, 1), height=None):
    """A white bordered card with a header line, its own Filter button and a body.

    `render(filtered_df, options)` draws the body using only this card's filtered data.
    """
    with st.container(border=True, height=height or "content"):
        left, right = st.columns(list(ratio), vertical_alignment="center")
        left.caption(header)
        with right:
            sub, options, active = chart_filter(df_all, scope, dataset_id, fields, extras=extras)
        render(sub, options)
        if active:
            st.caption(f"Filtered view: {len(sub)} of {len(df_all)} stories")


def chart_panel(scope, header, builder, caption, fields=STANDARD_FIELDS, extras=None, ratio=(3, 1), height=None):
    """A card that shows one Plotly chart. `builder(df, **options)` returns a figure or (figure, note)."""
    def render(sub, options):
        output = builder(sub, **options)
        figure, note = output if isinstance(output, tuple) else (output, "")
        st.plotly_chart(figure, width="stretch", key=f"chart_{scope}")
        st.caption(caption + (f"  \n*{note}*" if note else ""))
    panel(scope, header, render, fields, extras, ratio, height)


def section_header(title, description, scope=None, fields=ALL_FIELDS):
    """Section heading with a one-line description; optionally its own Filter button on the right."""
    st.write("")
    left, right = st.columns([5, 1], vertical_alignment="bottom")
    with left:
        st.subheader(title)
        st.caption(description)
    if scope is None:
        return None
    with right:
        sub, _, active = chart_filter(df_all, scope, dataset_id, fields)
    return sub, active


def format_value(value, kind):
    """Format KPI values; None (not calculable) becomes N/A."""
    if value is None:
        return "N/A"
    return {"int": f"{value:,}", "pct": f"{value:.1f}%", "float": f"{value:.3f}"}.get(kind, str(value))


# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #
head_left, head_right = st.columns([4, 1], vertical_alignment="center")
with head_left:
    st.title(APP_TITLE)
    period = (f"{time_info['start']:%d %b %Y} to {time_info['end']:%d %b %Y}" if time_info.get("valid")
              else "no valid timestamps")
    st.caption(f"{len(df_all)} AI-generated stories · {period} · language, emotion, weather and multimedia "
               "analysis of the StoryVerse app")
with head_right:
    st.download_button("⬇ Export all data (CSV)", data=df_all.drop(columns=["Date"]).to_csv(index=False).encode("utf-8-sig"),
                       file_name="storyverse_all_processed.csv", mime="text/csv", type="primary", width="stretch")

st.markdown(
    "This dashboard explores stories created by the StoryVerse application. Each record contains the story's "
    "language, generation mode (image upload or weather-based), detected emotion with a confidence score, optional "
    "city / weather information, and whether background music and a video were created.")

# --------------------------------------------------------------------------- #
# KPI cards (own filter)
# --------------------------------------------------------------------------- #
kpi_df, kpi_active = section_header("Key Performance Indicators",
                                    "Eight KPIs calculated from the data selected by this section's filter.", "kpi")
if kpi_df.empty:
    st.warning("No stories match this section's filter. Open **Filter** and press **Reset this filter**.")
else:
    kpi = analysis.compute_kpis(kpi_df)
    spark = analysis.kpi_sparklines(kpi_df)
    days_active = int(kpi_df["Date"].nunique())
    conf_median = kpi_df["Emotion Confidence"].median()
    music_n = int((kpi_df["Background Music Added"] == True).sum())   # noqa: E712
    video_n = int((kpi_df["Video Created"] == True).sum())            # noqa: E712

    def kpi_card(column, label, value, delta=None, series=None, kind="area", help_text=None):
        """One KPI card; sparkline only when there are at least two active days."""
        with column:
            st.metric(label, value, delta=delta, delta_color="off", delta_arrow="off", border=True,
                      chart_data=series, chart_type=kind, help=help_text)

    r1 = st.columns(4)
    kpi_card(r1[0], "Total Stories", format_value(kpi["total_stories"], "int"), f"{days_active} active days",
             spark["stories"], help_text="Sparkline: stories per active day.")
    kpi_card(r1[1], "Avg Emotion Confidence", format_value(kpi["avg_confidence"], "float"),
             f"median {conf_median:.3f}" if pd.notna(conf_median) else None, spark["confidence"], "line",
             f"Mean of {kpi['confidence_valid_n']} valid scores (0–1 scale); missing values are ignored.")
    kpi_card(r1[2], "Stories with Background Music", format_value(kpi["music_pct"], "pct"),
             f"{music_n} of {kpi['total_stories']} stories", spark["music"], "bar",
             "Sparkline: % with music per active day.")
    kpi_card(r1[3], "Stories with Video", format_value(kpi["video_pct"], "pct"),
             f"{video_n} of {kpi['total_stories']} stories", spark["video"], "bar",
             "Sparkline: % with video per active day.")
    r2 = st.columns(4)
    kpi_card(r2[0], "Unique Languages", format_value(kpi["unique_languages"], "int"))
    kpi_card(r2[1], "Unique Cities", format_value(kpi["unique_cities"], "int"),
             help_text="City is recorded only for weather-based stories.")
    kpi_card(r2[2], "Most Frequent Emotion", kpi["top_emotion"], f"{kpi['top_emotion_count']} stories")
    kpi_card(r2[3], "Most Used Language", kpi["top_language"], f"{kpi['top_language_count']} stories")
    if kpi_active:
        st.caption(f"KPI filter active: {len(kpi_df)} of {len(df_all)} stories.")

# --------------------------------------------------------------------------- #
# Overview: trend + donut, then bar / multimedia progress / language table
# --------------------------------------------------------------------------- #
section_header("Overview", "The most important charts at a glance. Each card has its own filter.")
top_left, top_right = st.columns([2, 1])
with top_left:
    chart_panel("line_trend", "Line chart · daily trend", viz.line_trend,
                "**Line chart** – stories created on each day (days with none count as 0).", height=520)
with top_right:
    chart_panel("donut_emotion", "Donut chart · emotion share", viz.donut_emotion,
                "**Donut chart** – each emotion's share of all detected emotions.", ratio=(1, 1), height=520)

mid_a, mid_b, mid_c = st.columns(3)
with mid_a:
    chart_panel("bar_language", "Bar chart · language comparison", viz.bar_language,
                "**Bar chart** – number of stories per language.", ratio=(1, 1), height=520)


def render_multimedia(sub, _options):
    """Progress-bar card: share of stories with audio, music and video."""
    st.markdown("**Multimedia coverage**")
    if sub.empty:
        st.info("No stories match this card's filter.")
        return
    table = analysis.multimedia_summary(sub)
    for _, row in table.iterrows():
        pct = row["Percent"]
        if pd.isna(pct):
            st.caption(f"{row['Media type']}: no data")
            continue
        st.progress(min(max(pct / 100, 0.0), 1.0),
                    text=f"{row['Media type']} · {pct:.1f}% ({int(row['Stories with it'])} of "
                         f"{int(row['Stories with it'] + row['Stories without'])})")
    st.caption("An empty audio/video path simply means that media was not created.")


with mid_b:
    panel("multimedia_progress", "Progress bars · multimedia", render_multimedia, ratio=(1, 1), height=520)


def render_language_table(sub, _options):
    """Table card: per-language summary with in-cell progress bars."""
    st.markdown("**Language summary**")
    if sub.empty:
        st.info("No stories match this card's filter.")
        return
    summary = analysis.grouped_summary(sub, "Language")[["Language", "Stories", "Avg Confidence", "Music %", "Video %"]]
    st.dataframe(summary, hide_index=True, width="stretch", column_config={
        "Avg Confidence": st.column_config.NumberColumn(format="%.3f"),
        "Music %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f%%"),
        "Video %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f%%"),
    })
    st.caption("Grouped summary: stories, average confidence and multimedia share per language.")


with mid_c:
    panel("language_table", "Table · grouped summary", render_language_table, ratio=(1, 1), height=520)

# --------------------------------------------------------------------------- #
# Further analysis, grouped by purpose
# --------------------------------------------------------------------------- #
section_header("A. Composition & Categories", "How stories are split across languages, emotions and categories.")
c1, c2 = st.columns(2)
with c1:
    chart_panel("treemap", "Treemap · hierarchy", viz.treemap_language_emotion,
                "**Treemap** – tile area is the number of stories; shows the language → emotion hierarchy.")
with c2:
    chart_panel("grouped_bar", "Grouped bar chart · emotions by language", viz.grouped_bar_emotion_language,
                "**Grouped bar chart** – emotions side by side inside each language.")
c1, c2 = st.columns(2)
with c1:
    chart_panel("bubble", "Bubble chart · count and confidence", viz.bubble_language_emotion,
                "**Bubble chart** – bubble size is the number of stories; colour is the average confidence.")
with c2:
    chart_panel("pareto", "Pareto chart · cumulative share", viz.pareto_chart,
                "**Pareto chart** – bars are counts (high to low); the red line is the cumulative percentage.",
                extras=lambda prefix: {"column": st.selectbox(
                    "Pareto category", ["Detected Emotion", "Language", "Mode", "City"], key=f"{prefix}opt")})

section_header("B. Time Analysis", "When stories were created. Needs valid timestamps.")
c1, c2 = st.columns(2)
with c1:
    chart_panel("area_monthly", "Area chart · monthly volume", viz.area_monthly, "**Area chart** – story volume per month.")
with c2:
    chart_panel("calendar", "Calendar heatmap · daily activity", viz.calendar_heatmap,
                "**Calendar heatmap** – each cell is one day; darker blue means more stories that day.")

section_header("C. Confidence Analysis", "How certain the emotion detector is (0 = not certain, 1 = fully certain).")
c1, c2 = st.columns(2)
with c1:
    chart_panel("hist_conf", "Histogram · distribution", viz.histogram_confidence,
                "**Histogram** – how emotion-confidence scores are distributed.")
with c2:
    chart_panel("box_conf", "Box plot · spread by language", viz.box_confidence_language,
                "**Box plot** – median, spread and outliers of confidence per language (dots are stories).")
c1, c2 = st.columns(2)
with c1:
    chart_panel("violin_conf", "Violin plot · density by emotion", viz.violin_confidence_emotion,
                "**Violin plot** – where confidence scores cluster for each emotion; emotions with very few "
                "stories give narrow, unreliable shapes.")
with c2:
    chart_panel("scatter_temp", "Scatter plot · temperature vs confidence", viz.scatter_temperature_confidence,
                "**Scatter plot** – each dot is a weather-based story. It shows association only, never causation.",
                fields=WEATHER_FIELDS)

section_header("D. Relationships Between Numeric Variables", "Correlation and multivariate patterns (association, not causation).")
c1, c2 = st.columns(2)
with c1:
    chart_panel("heat_corr", "Heatmap · correlation matrix", viz.heatmap_correlation,
                "**Heatmap** – correlation between numeric variables (−1 negative, 0 none, +1 positive).",
                fields=WEATHER_FIELDS)
with c2:
    chart_panel("scatter_matrix", "Scatter matrix · multivariate", viz.scatter_matrix_numeric,
                "**Scatter matrix** – every numeric variable against every other, coloured by language.",
                fields=WEATHER_FIELDS)

section_header("E. Multimedia & Places", "Audio, background music, video and the cities behind weather-based stories.")
c1, c2 = st.columns(2)
with c1:
    chart_panel("stacked_media", "Stacked bar chart · multimedia mix", viz.stacked_bar_media_by_language,
                "**Stacked bar chart** – for each language: music, video, both or neither.")
with c2:
    chart_panel("top_cities", "Horizontal bar chart · top cities", viz.hbar_top_cities,
                "**Horizontal bar chart** – cities with the most weather-based stories.", fields=WEATHER_FIELDS)

section_header("F. Text Analysis", "What the generated stories talk about and how long they are.")
c1, c2 = st.columns(2)
with c1:
    chart_panel("word_freq", "Word-frequency chart · Story Text", viz.word_frequency_chart,
                "**Word-frequency chart** – most common words after removing basic English, Hindi and Marathi stop words.")
with c2:
    chart_panel("story_length", "Histogram · story length", viz.story_length_histogram,
                "**Histogram** – story length in words, split by language.")

# --------------------------------------------------------------------------- #
# Data quality and preprocessing (describes the complete raw dataset)
# --------------------------------------------------------------------------- #
section_header("Data Quality & Preprocessing", "Understanding the raw data before analysis. Always uses the complete dataset.")
quality = analysis.data_quality_summary(raw_df, df_all)
q1, q2, q3, q4 = st.columns(4)
q1.metric("Duplicate rows", quality["duplicate_rows"], border=True)
q2.metric("Missing cells", f"{quality['missing_cells']} ({quality['missing_pct']}%)", border=True)
q3.metric("Invalid timestamps", quality["invalid_timestamps"], border=True)
q4.metric("Confidence scale", quality["confidence_scale"], border=True)

if quality["columns_with_unexpected_missing"]:
    st.warning("Columns with unexplained missing values: " + ", ".join(quality["columns_with_unexpected_missing"]))
else:
    st.success("All missing values are explained by the data design (see the Missing values tab). "
               "No records were deleted.")
if quality["inconsistent_labels"]:
    st.warning(f"Inconsistent category labels found: {quality['inconsistent_labels']}")
else:
    st.caption("No inconsistent category spellings detected (labels were also standardised for safety).")

with st.container(border=True):
    tab_missing, tab_types, tab_unique, tab_preview, tab_num, tab_log, tab_cols, tab_ml = st.tabs(
        ["Missing values", "Data types", "Unique values", "First & last rows", "Numeric summary",
         "Preprocessing steps", "Columns not used for statistics", "Machine learning?"])
    with tab_missing:
        st.dataframe(analysis.missing_value_table(raw_df), width="stretch", hide_index=True)
        st.caption("Empty audio/video paths are normal: a path exists only when that media was created. "
                   "City, weather and temperature are only filled for weather-based stories.")
    with tab_types:
        st.dataframe(analysis.dtype_table(raw_df), width="stretch", hide_index=True)
        st.caption(f"Timestamp spans {time_info.get('span_days', 'N/A')} days across "
                   f"{time_info.get('distinct_months', 'N/A')} calendar month(s).")
    with tab_unique:
        st.dataframe(analysis.categorical_unique_values(
            df_all, ["Mode", "Language", "Detected Emotion", "City", "Weather Condition", "Music Label", "Video Label"]),
            width="stretch", hide_index=True)
    with tab_preview:
        preview_cols = ["Timestamp", "Mode", "Title", "Language", "Detected Emotion", "Emotion Confidence", "City"]
        st.markdown("**First 5 records**")
        st.dataframe(df_all[preview_cols].head(), width="stretch", hide_index=True)
        st.markdown("**Last 5 records**")
        st.dataframe(df_all[preview_cols].tail(), width="stretch", hide_index=True)
    with tab_num:
        st.dataframe(analysis.descriptive_statistics(df_all), width="stretch", hide_index=True)
    with tab_log:
        for step in preprocessing_log:
            st.markdown(f"- {step}")
        st.caption("The original dataset is kept unchanged; all cleaning is done on a separate processed copy.")
    with tab_cols:
        st.dataframe(pd.DataFrame({"Column": list(analysis.NON_STATISTICAL_COLUMNS),
                                   "Why it is not used for statistics": list(analysis.NON_STATISTICAL_COLUMNS.values())}),
                     width="stretch", hide_index=True)
    with tab_ml:
        n_temp = int(df_all["Temperature (C)"].notna().sum())
        class_counts = df_all["Detected Emotion"].value_counts()
        st.markdown(
            f"No machine-learning model is included on purpose. The dataset has only **{len(df_all)}** stories, "
            f"**{n_temp}** temperature readings and the smallest emotion class has **{int(class_counts.min())}** stories. "
            "With so few examples any prediction accuracy would be unreliable, and quoting it would be misleading. "
            "The project therefore focuses on descriptive and statistical analysis. With a few hundred more stories, a "
            "simple classifier (for example predicting emotion from language and mode) could be evaluated with "
            "cross-validation.")

# --------------------------------------------------------------------------- #
# Statistical analysis (own filter)
# --------------------------------------------------------------------------- #
stats_df, stats_active = section_header(
    "Statistical Analysis", "Univariate, bivariate, multivariate, grouped and outlier analysis.", "stats")
with st.container(border=True):
    if stats_active:
        st.caption(f"Statistics filter active: {len(stats_df)} of {len(df_all)} stories.")
    if stats_df.empty:
        st.warning("No stories match this section's filter.")
    else:
        tab_uni, tab_bi, tab_multi, tab_group, tab_corr, tab_out, tab_media = st.tabs(
            ["Univariate", "Bivariate", "Multivariate", "Grouped summary", "Correlation", "Outliers (IQR)", "Multimedia"])
        with tab_uni:
            st.markdown("**Frequency analysis of categorical variables**")
            cols = st.columns(3)
            for i, column in enumerate(["Language", "Detected Emotion", "Mode", "City", "Weather Condition"]):
                with cols[i % 3]:
                    st.markdown(f"*{column}*")
                    table = analysis.frequency_table(stats_df, column)
                    if table.empty:
                        st.caption("No data.")
                    else:
                        st.dataframe(table, width="stretch", hide_index=True)
            st.markdown("**Descriptive statistics of numeric variables**")
            stats = analysis.descriptive_statistics(stats_df)
            if stats.empty:
                st.caption("No numeric data.")
            else:
                st.dataframe(stats, width="stretch", hide_index=True)
        with tab_bi:
            st.markdown("**Language vs Detected Emotion (story counts)**")
            st.dataframe(pd.crosstab(stats_df["Language"], stats_df["Detected Emotion"], margins=True,
                                     margins_name="Total"), width="stretch")
            st.markdown("**Language vs Multimedia (percent of stories)**")
            st.dataframe(analysis.grouped_summary(stats_df, "Language")[["Language", "Stories", "Music %", "Video %"]],
                         width="stretch", hide_index=True)
            pair = analysis.pairwise_correlation(stats_df, "Temperature (C)", "Emotion Confidence")
            st.markdown("**Temperature vs Emotion Confidence**")
            if pair["pearson"] is None:
                st.caption(f"Only {pair['n']} stories have both values, which is too few to calculate a correlation.")
            else:
                st.markdown(f"Pearson r = **{pair['pearson']:.3f}**, Spearman ρ = **{pair['spearman']:.3f}** "
                            f"({analysis.describe_correlation(pair['pearson'])}) using {pair['n']} stories.")
        with tab_multi:
            st.markdown("**Average confidence by Language × Emotion** (blank = no stories in that combination)")
            pivot = stats_df.pivot_table(index="Language", columns="Detected Emotion", values="Emotion Confidence",
                                         aggfunc="mean").round(3)
            st.dataframe(pivot, width="stretch")
            st.markdown("**Story counts by Mode × Language × Emotion**")
            triple = stats_df.groupby(["Mode", "Language", "Detected Emotion"]).size().reset_index(name="Stories")
            st.dataframe(triple, width="stretch", hide_index=True)
            st.caption("Many cells hold only 1–3 stories, so patterns here are descriptive and should not be generalised.")
        with tab_group:
            group_by = st.selectbox("Group by", ["Language", "Detected Emotion", "Mode", "City", "Weather Condition"])
            st.dataframe(analysis.grouped_summary(stats_df, group_by), width="stretch", hide_index=True)
        with tab_corr:
            corr, pair_counts = analysis.correlation_matrix(stats_df)
            if corr.empty:
                st.caption("Not enough numeric variables with valid values to calculate correlations.")
            else:
                st.markdown("**Pearson correlation matrix**")
                st.dataframe(corr.round(3), width="stretch")
                st.markdown("**Number of valid pairs behind each cell**")
                st.dataframe(pair_counts, width="stretch")
            st.info("Limitations: correlation measures linear association only, it does not prove causation, and "
                    "temperature exists only for weather-based stories, so those coefficients use very few observations.")
        with tab_out:
            outlier_column = st.selectbox("Numeric column", analysis.NUMERIC_ANALYSIS_COLUMNS)
            result = analysis.iqr_outliers(stats_df, outlier_column)
            if result["lower"] is None:
                st.caption(f"Only {result['n']} valid values; at least 4 are needed for the IQR method.")
            else:
                st.markdown(f"Q1 = {result['q1']:.3f}, Q3 = {result['q3']:.3f}, IQR = {result['iqr']:.3f}. "
                            f"Values outside **[{result['lower']:.3f}, {result['upper']:.3f}]** are flagged.")
                if result["outliers"].empty:
                    st.success("No statistical outliers found.")
                else:
                    st.dataframe(result["outliers"], width="stretch", hide_index=True)
            st.caption("A statistical outlier is simply an unusual value. It is not automatically an error and was not removed.")
        with tab_media:
            st.dataframe(analysis.multimedia_summary(stats_df), width="stretch", hide_index=True)

# --------------------------------------------------------------------------- #
# Insights (own filter)
# --------------------------------------------------------------------------- #
insight_df, insight_active = section_header(
    "Key Business Insights", "Written automatically from the data selected by this section's filter.", "insights")
with st.container(border=True):
    if insight_active:
        st.caption(f"Insights filter active: {len(insight_df)} of {len(df_all)} stories.")
    for level, message in analysis.generate_insights(insight_df):
        (st.warning if level == "warning" else st.info)(message, icon="⚠️" if level == "warning" else "💡")

# --------------------------------------------------------------------------- #
# Detailed data + download (own filter)
# --------------------------------------------------------------------------- #
table_df, table_active = section_header(
    "Detailed Data", "Browse the stories selected by this section's filter and download them as CSV.", "table")
with st.container(border=True):
    if table_df.empty:
        st.warning("No stories match this section's filter.")
    else:
        default_columns = ["Timestamp", "Mode", "Title", "Language", "Detected Emotion", "Emotion Confidence", "City",
                           "Weather Condition", "Temperature (C)", "Music Label", "Video Label", "Story Word Count"]
        shown_columns = st.multiselect("Columns to display", table_df.columns.tolist(), default=default_columns)
        st.dataframe(table_df[shown_columns] if shown_columns else table_df, width="stretch", hide_index=True,
                     height=360)
        # utf-8-sig keeps Hindi/Marathi text readable when the CSV is opened in Excel.
        csv_bytes = table_df.drop(columns=["Date"]).to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇ Download filtered data (CSV)", data=csv_bytes, file_name="storyverse_filtered.csv",
                           mime="text/csv", type="primary")
        st.caption(f"{len(table_df)} rows × {table_df.shape[1] - 1} columns will be downloaded (all processed columns).")

st.divider()
st.caption("Built with Python only · pandas & NumPy (analysis) · Plotly (charts) · Streamlit (dashboard) · "
           "openpyxl (reading Excel).")
