"""Plotly chart functions. Each function takes the (filtered) DataFrame and returns a figure.

Every function is safe to call with an empty DataFrame or missing values:
it returns a figure that shows a short explanatory message instead of crashing.
"""

from typing import Optional, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src import analysis
from src.preprocessing import NOT_RECORDED

# ---- colour palette (from the project brief) ------------------------------ #
NAVY, BLUE, TEAL, PURPLE = "#14213D", "#2563EB", "#0F766E", "#7C3AED"
ORANGE, RED, GREEN, TEXT = "#F59E0B", "#DC2626", "#16A34A", "#1F2937"
GRID = "#E5E7EB"
FALLBACK_COLORS = [BLUE, ORANGE, TEAL, PURPLE, RED, GREEN, "#0EA5E9", "#DB2777"]

# Colours with a meaning: emotions get intuitive colours, languages get fixed ones.
EMOTION_COLORS = {"Joy": ORANGE, "Sadness": BLUE, "Anger": RED, "Love": PURPLE,
                  "Fear": TEAL, "Surprise": GREEN, "Neutral": "#6B7280"}
LANGUAGE_COLORS = {"English": BLUE, "Hindi": ORANGE, "Marathi": TEAL}
CHART_HEIGHT = 380


def _color_map(values, preferred: dict) -> dict:
    """Map each category to its preferred colour, using the fallback palette for new ones."""
    mapping, fallback = {}, iter(FALLBACK_COLORS * 3)
    for value in values:
        mapping[value] = preferred.get(value) or next(fallback)
    return mapping


def _style(fig: go.Figure, title: str, height: int = CHART_HEIGHT, x_title: Optional[str] = None,
           y_title: Optional[str] = None, legend_title: Optional[str] = None) -> go.Figure:
    """Apply the shared professional look to every figure."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color=NAVY), x=0.01, xanchor="left"),
        height=height, margin=dict(l=50, r=25, t=60, b=50),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", size=12, color=TEXT),
        legend=dict(title=legend_title, bgcolor="rgba(255,255,255,0.7)"),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    fig.update_xaxes(title=x_title, gridcolor=GRID, linecolor=GRID, zeroline=False)
    fig.update_yaxes(title=y_title, gridcolor=GRID, linecolor=GRID, zeroline=False)
    return fig


def empty_figure(title: str, message: str, height: int = CHART_HEIGHT) -> go.Figure:
    """A blank figure that explains why nothing can be drawn."""
    fig = go.Figure()
    fig.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
                       font=dict(size=14, color="#6B7280"))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _style(fig, title, height)


def _valid(df: pd.DataFrame, columns, minimum: int = 1) -> pd.DataFrame:
    """Rows where all given columns have values."""
    return df.dropna(subset=list(columns)) if len(df) else df


# --------------------------------------------------------------------------- #
# Required visualizations 1-12
# --------------------------------------------------------------------------- #
def bar_language(df: pd.DataFrame) -> go.Figure:
    """1. Bar chart: stories per language."""
    title = "Stories by Language"
    freq = analysis.frequency_table(df, "Language")
    if freq.empty:
        return empty_figure(title, "No language data for the current filters.")
    fig = px.bar(freq, x="Language", y="Stories", color="Language", text="Stories",
                 color_discrete_map=_color_map(freq["Language"], LANGUAGE_COLORS),
                 hover_data={"Percent": ":.1f"})
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(showlegend=False)
    return _style(fig, title, x_title="Language", y_title="Number of stories")


def donut_emotion(df: pd.DataFrame) -> go.Figure:
    """2. Donut chart: share of each detected emotion."""
    title = "Emotion Distribution"
    freq = analysis.frequency_table(df, "Detected Emotion")
    if freq.empty:
        return empty_figure(title, "No emotion data for the current filters.")
    cmap = _color_map(freq["Detected Emotion"], EMOTION_COLORS)
    fig = go.Figure(go.Pie(labels=freq["Detected Emotion"], values=freq["Stories"], hole=0.55,
                           marker=dict(colors=[cmap[e] for e in freq["Detected Emotion"]],
                                       line=dict(color="white", width=2)),
                           textinfo="percent", sort=False,
                           hovertemplate="%{label}: %{value} stories (%{percent})<extra></extra>"))
    fig.add_annotation(text=f"<b>{int(freq['Stories'].sum())}</b><br>stories", showarrow=False,
                       font=dict(size=16, color=NAVY))
    fig = _style(fig, title, legend_title="Emotion")
    fig.update_layout(legend=dict(orientation="v", x=1.0, y=0.5, xanchor="left", yanchor="middle"))
    return fig


def line_trend(df: pd.DataFrame) -> go.Figure:
    """3. Line chart: stories created per day."""
    title = "Story Generation Trend (Daily)"
    daily = analysis.daily_counts(df)
    if len(daily) < 2:
        return empty_figure(title, "At least two different dates are needed to draw a trend.")
    fig = go.Figure(go.Scatter(x=daily["Date"], y=daily["Stories"], mode="lines+markers", fill="tozeroy",
                               line=dict(color=PURPLE, width=3, shape="spline", smoothing=0.6),
                               fillcolor="rgba(124,58,237,0.12)", marker=dict(size=6, color=PURPLE),
                               hovertemplate="%{x|%d %b %Y}: %{y} stories<extra></extra>"))
    fig.update_yaxes(rangemode="tozero")
    return _style(fig, title, x_title="Date", y_title="Stories created")


def histogram_confidence(df: pd.DataFrame) -> go.Figure:
    """4. Histogram: distribution of Emotion Confidence."""
    title = "Emotion Confidence Distribution"
    data = _valid(df, ["Emotion Confidence"])
    if data.empty:
        return empty_figure(title, "No valid confidence scores for the current filters.")
    fig = px.histogram(data, x="Emotion Confidence", nbins=min(20, max(5, len(data) // 2)),
                       color_discrete_sequence=[TEAL])
    fig.update_traces(marker_line_color="white", marker_line_width=1)
    mean = data["Emotion Confidence"].mean()
    fig.add_vline(x=mean, line_dash="dash", line_color=NAVY, annotation_text=f"Mean {mean:.3f}",
                  annotation_position="top right")
    return _style(fig, title, x_title="Emotion Confidence (0–1)", y_title="Number of stories")


def box_confidence_language(df: pd.DataFrame) -> go.Figure:
    """5. Box plot: confidence spread per language."""
    title = "Emotion Confidence by Language"
    data = _valid(df, ["Emotion Confidence", "Language"])
    if data.empty:
        return empty_figure(title, "No valid confidence scores for the current filters.")
    order = data["Language"].value_counts().index.tolist()
    fig = px.box(data, x="Language", y="Emotion Confidence", color="Language", points="all",
                 category_orders={"Language": order},
                 color_discrete_map=_color_map(order, LANGUAGE_COLORS),
                 hover_data=["Title", "Detected Emotion"])
    fig.update_layout(showlegend=False)
    return _style(fig, title, x_title="Language", y_title="Emotion Confidence (0–1)")


def scatter_temperature_confidence(df: pd.DataFrame) -> go.Figure:
    """6. Scatter plot: temperature vs confidence (relationship, not causation)."""
    title = "Temperature vs Emotion Confidence"
    data = _valid(df, ["Temperature (C)", "Emotion Confidence"])
    if len(data) < 3:
        return empty_figure(title, f"Only {len(data)} stories have both temperature and confidence "
                                   "(needs at least 3).")
    cmap = _color_map(data["Detected Emotion"].unique(), EMOTION_COLORS)
    fig = px.scatter(data, x="Temperature (C)", y="Emotion Confidence", color="Detected Emotion",
                     color_discrete_map=cmap, hover_data=["City", "Weather Condition", "Language"])
    fig.update_traces(marker=dict(size=12, line=dict(width=1, color="white")))
    # Simple least-squares line so the direction of any relationship is visible.
    if data["Temperature (C)"].nunique() > 1:
        slope, intercept = np.polyfit(data["Temperature (C)"], data["Emotion Confidence"], 1)
        xs = np.array([data["Temperature (C)"].min(), data["Temperature (C)"].max()])
        fig.add_trace(go.Scatter(x=xs, y=slope * xs + intercept, mode="lines", name="Trend line",
                                 line=dict(color=NAVY, dash="dash")))
    return _style(fig, f"{title} (n = {len(data)})", x_title="Temperature (°C)",
                  y_title="Emotion Confidence (0–1)", legend_title="Emotion")


def heatmap_correlation(df: pd.DataFrame) -> Tuple[go.Figure, str]:
    """7. Heatmap: correlation matrix; falls back to language x emotion counts if data is too thin."""
    title = "Correlation Analysis"
    corr, pairs = analysis.correlation_matrix(df)
    usable = (not corr.empty) and corr.notna().to_numpy().sum() > corr.shape[0]
    if usable:
        text = corr.round(2).astype(str)
        text = text.where(corr.notna(), "n/a")
        fig = go.Figure(go.Heatmap(
            z=corr.values, x=corr.columns, y=corr.index, zmin=-1, zmax=1, colorscale="RdBu_r",
            text=text.values, texttemplate="%{text}", colorbar=dict(title="r"),
            customdata=pairs.values,
            hovertemplate="%{y} vs %{x}<br>r = %{z:.2f}<br>valid pairs = %{customdata}<extra></extra>"))
        min_pairs = int(pairs.to_numpy().min())
        note = (f"Pearson correlation using pairwise complete rows. Temperature exists only for weather-based "
                f"stories, so its correlations rest on as few as {min_pairs} observations and are not reliable. "
                "Correlation never proves causation.")
        return _style(fig, title), note
    return heatmap_language_emotion(df), ("Not enough numeric observations for a correlation matrix, so a "
                                          "language × emotion frequency heatmap is shown instead.")


def heatmap_language_emotion(df: pd.DataFrame) -> go.Figure:
    """Fallback heatmap: counts of stories by language and emotion."""
    title = "Language × Emotion Heatmap"
    data = _valid(df, ["Language", "Detected Emotion"])
    if data.empty:
        return empty_figure(title, "No data for the current filters.")
    table = pd.crosstab(data["Language"], data["Detected Emotion"])
    fig = px.imshow(table, text_auto=True, color_continuous_scale="Blues", aspect="auto")
    return _style(fig, title, x_title="Detected emotion", y_title="Language")


def treemap_language_emotion(df: pd.DataFrame) -> go.Figure:
    """8. Treemap: language -> emotion hierarchy."""
    title = "Story Distribution by Language and Emotion"
    data = _valid(df, ["Language", "Detected Emotion"])
    if data.empty:
        return empty_figure(title, "No data for the current filters.")
    counts = data.groupby(["Language", "Detected Emotion"]).size().reset_index(name="Stories")
    fig = px.treemap(counts, path=[px.Constant("All stories"), "Language", "Detected Emotion"], values="Stories",
                     color="Language", color_discrete_map={**_color_map(counts["Language"].unique(), LANGUAGE_COLORS),
                                                          "(?)": "#E5E7EB"})
    fig.update_traces(textinfo="label+value", marker=dict(line=dict(color="white", width=2)))
    return _style(fig, title)


def area_monthly(df: pd.DataFrame) -> Tuple[go.Figure, str]:
    """9. Area chart: stories per month (falls back to daily if only one month is selected)."""
    title = "Monthly Story Creation Trend"
    monthly = analysis.monthly_counts(df)
    if len(monthly) >= 2:
        fig = go.Figure(go.Scatter(x=monthly["Month"], y=monthly["Stories"], mode="lines+markers", fill="tozeroy",
                                   line=dict(color=PURPLE, width=3), fillcolor="rgba(124,58,237,0.2)",
                                   hovertemplate="%{x}: %{y} stories<extra></extra>"))
        fig.update_xaxes(type="category")
        return _style(fig, title, x_title="Month", y_title="Stories created"), \
            "Months with no stories are shown as zero."
    daily = analysis.daily_counts(df)
    if len(daily) >= 2:
        fig = go.Figure(go.Scatter(x=daily["Date"], y=daily["Stories"], mode="lines", fill="tozeroy",
                                   line=dict(color=PURPLE, width=2), fillcolor="rgba(124,58,237,0.2)"))
        return _style(fig, "Daily Story Creation (only one month selected)", x_title="Date",
                      y_title="Stories created"), "Only one month is in the filter, so daily values are shown."
    return empty_figure(title, "At least two months (or two days) of data are needed."), ""


def violin_confidence_emotion(df: pd.DataFrame) -> go.Figure:
    """10. Violin plot: confidence density per emotion."""
    title = "Emotion Confidence Distribution by Emotion"
    data = _valid(df, ["Emotion Confidence", "Detected Emotion"])
    if data.empty:
        return empty_figure(title, "No valid confidence scores for the current filters.")
    order = data["Detected Emotion"].value_counts().index.tolist()
    fig = px.violin(data, x="Detected Emotion", y="Emotion Confidence", color="Detected Emotion", box=True,
                    points="all", category_orders={"Detected Emotion": order},
                    color_discrete_map=_color_map(order, EMOTION_COLORS), hover_data=["Title", "Language"])
    fig.update_layout(showlegend=False)
    return _style(fig, title, x_title="Detected emotion", y_title="Emotion Confidence (0–1)")


def stacked_bar_media_by_language(df: pd.DataFrame) -> go.Figure:
    """11. Stacked bar: music / video combinations per language."""
    title = "Background Music and Video Creation by Language"
    data = _valid(df, ["Language", "Background Music Added", "Video Created"])
    if data.empty:
        return empty_figure(title, "No multimedia data for the current filters.")
    music, video = data["Background Music Added"].astype(bool), data["Video Created"].astype(bool)
    data = data.assign(Media=np.select(
        [music & video, music & ~video, ~music & video], ["Music + Video", "Music only", "Video only"],
        default="Neither"))
    counts = data.groupby(["Language", "Media"]).size().reset_index(name="Stories")
    colors = {"Music + Video": GREEN, "Music only": BLUE, "Video only": ORANGE, "Neither": "#9CA3AF"}
    fig = px.bar(counts, x="Language", y="Stories", color="Media", color_discrete_map=colors, text="Stories",
                 category_orders={"Media": ["Music + Video", "Music only", "Video only", "Neither"]})
    fig.update_layout(barmode="stack")
    return _style(fig, title, x_title="Language", y_title="Number of stories", legend_title="Multimedia")


def scatter_matrix_numeric(df: pd.DataFrame) -> Tuple[go.Figure, str]:
    """12. Scatter matrix of numeric variables (bubble chart fallback if too little data)."""
    title = "Multivariate Data Relationships"
    columns = [c for c in analysis.NUMERIC_ANALYSIS_COLUMNS if c in df.columns and df[c].notna().sum() >= 5
               and df[c].nunique() > 1]
    if len(columns) >= 3:
        data = df.dropna(subset=["Emotion Confidence"]).copy()
        cmap = _color_map(data["Language"].unique(), LANGUAGE_COLORS)
        fig = px.scatter_matrix(data, dimensions=columns, color="Language", color_discrete_map=cmap,
                                hover_name="Title")
        fig.update_traces(diagonal_visible=False, marker=dict(size=6, opacity=0.8), showupperhalf=False)
        counts = ", ".join(f"{c}: {int(df[c].notna().sum())}" for c in columns)
        note = (f"Valid observations per variable → {counts}. Temperature is missing for most stories, so those "
                "points are simply not drawn.")
        return _style(fig, title, height=520, legend_title="Language"), note
    fig = bubble_language_emotion(df)
    return fig, "Too few numeric columns for a scatter matrix, so a bubble chart is shown instead."


# --------------------------------------------------------------------------- #
# Additional visualizations
# --------------------------------------------------------------------------- #
def hbar_top_cities(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Horizontal bar: top cities by number of stories."""
    title = "Top Cities by Story Count"
    freq = analysis.frequency_table(df, "City").head(top_n)
    if freq.empty:
        return empty_figure(title, "No city data for the current filters (city exists only for weather-based stories).")
    fig = px.bar(freq.iloc[::-1], x="Stories", y="City", orientation="h", text="Stories",
                 color_discrete_sequence=[GREEN])
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _style(fig, title, x_title="Number of stories", y_title="City")


def grouped_bar_emotion_language(df: pd.DataFrame) -> go.Figure:
    """Grouped bar: emotion counts side by side for each language."""
    title = "Emotions Across Languages"
    data = _valid(df, ["Language", "Detected Emotion"])
    if data.empty:
        return empty_figure(title, "No data for the current filters.")
    counts = data.groupby(["Language", "Detected Emotion"]).size().reset_index(name="Stories")
    fig = px.bar(counts, x="Language", y="Stories", color="Detected Emotion", barmode="group", text="Stories",
                 color_discrete_map=_color_map(counts["Detected Emotion"].unique(), EMOTION_COLORS))
    return _style(fig, title, x_title="Language", y_title="Number of stories", legend_title="Emotion")


def bubble_language_emotion(df: pd.DataFrame) -> go.Figure:
    """Bubble chart: bubble size = number of stories, colour = average confidence."""
    title = "Language × Emotion Bubble Chart"
    data = _valid(df, ["Language", "Detected Emotion"])
    if data.empty:
        return empty_figure(title, "No data for the current filters.")
    grouped = data.groupby(["Language", "Detected Emotion"]).agg(
        Stories=("Story ID", "count"), AvgConfidence=("Emotion Confidence", "mean")).reset_index()
    grouped["AvgConfidence"] = grouped["AvgConfidence"].round(3)
    fig = px.scatter(grouped, x="Language", y="Detected Emotion", size="Stories", color="AvgConfidence",
                     color_continuous_scale="Viridis", size_max=45, hover_data={"Stories": True, "AvgConfidence": True})
    fig.update_coloraxes(colorbar_title="Avg confidence")
    return _style(fig, title + " (size = stories, colour = avg confidence)", x_title="Language", y_title="Emotion")


def calendar_heatmap(df: pd.DataFrame) -> go.Figure:
    """Calendar-style heatmap: weekday rows x week columns, colour = stories created that day."""
    title = "Daily Activity Calendar"
    dates = df["Date"].dropna() if len(df) else pd.Series(dtype="datetime64[ns]")
    if dates.empty:
        return empty_figure(title, "No valid timestamps for the current filters.")
    counts = dates.value_counts()
    all_days = pd.date_range(counts.index.min(), counts.index.max(), freq="D")
    cal = pd.DataFrame({"Date": all_days})
    cal["Stories"] = cal["Date"].map(counts).fillna(0).astype(int)
    cal["Weekday"] = cal["Date"].dt.weekday
    cal["WeekStart"] = (cal["Date"] - pd.to_timedelta(cal["Weekday"], unit="D"))
    weeks = sorted(cal["WeekStart"].unique())
    z = np.full((7, len(weeks)), np.nan)
    hover = np.full((7, len(weeks)), "", dtype=object)
    for _, row in cal.iterrows():
        col = weeks.index(row["WeekStart"])
        z[row["Weekday"], col] = row["Stories"]
        hover[row["Weekday"], col] = f"{row['Date']:%a %d %b %Y}: {row['Stories']} stories"
    fig = go.Figure(go.Heatmap(
        z=z, x=[pd.Timestamp(w).strftime("%d %b") for w in weeks],
        y=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], text=hover, hoverinfo="text",
        colorscale=[[0, "#EEF2FF"], [1, BLUE]], xgap=3, ygap=3, colorbar=dict(title="Stories")))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(type="category")
    return _style(fig, title, x_title="Week starting (Monday)", y_title="Weekday")


def pareto_chart(df: pd.DataFrame, column: str = "Detected Emotion") -> go.Figure:
    """Pareto: bars sorted high-to-low plus cumulative percentage line."""
    title = f"Pareto Chart: Stories by {column}"
    table = analysis.pareto_table(df, column)
    if table.empty:
        return empty_figure(title, "No data for the current filters.")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=table[column], y=table["Stories"], name="Stories", marker_color=BLUE))
    fig.add_trace(go.Scatter(x=table[column], y=table["Cumulative %"], name="Cumulative %", yaxis="y2",
                             mode="lines+markers", line=dict(color=RED, width=3)))
    fig.update_layout(yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105],
                                  showgrid=False))
    return _style(fig, title, x_title=column, y_title="Number of stories")


def word_frequency_chart(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Horizontal bar of the most common words in Story Text (stop words removed)."""
    title = f"Top {top_n} Words in Story Text"
    words = analysis.word_frequencies(df, top_n)
    if words.empty:
        return empty_figure(title, "No story text available for the current filters.")
    fig = px.bar(words.iloc[::-1], x="Count", y="Word", orientation="h", color_discrete_sequence=[ORANGE])
    return _style(fig, title, height=460, x_title="Occurrences", y_title="Word")


def story_length_histogram(df: pd.DataFrame) -> go.Figure:
    """Histogram of story word counts (text analysis)."""
    title = "Story Length (Words)"
    data = _valid(df, ["Story Word Count"])
    if data.empty:
        return empty_figure(title, "No story text available for the current filters.")
    fig = px.histogram(data, x="Story Word Count", color="Language", nbins=15,
                       color_discrete_map=_color_map(data["Language"].unique(), LANGUAGE_COLORS))
    fig.update_layout(barmode="overlay")
    fig.update_traces(opacity=0.75)
    return _style(fig, title, x_title="Words per story", y_title="Number of stories", legend_title="Language")


ALL_VISUALIZATIONS = [
    "bar_language", "donut_emotion", "line_trend", "histogram_confidence", "box_confidence_language",
    "scatter_temperature_confidence", "heatmap_correlation", "treemap_language_emotion", "area_monthly",
    "violin_confidence_emotion", "stacked_bar_media_by_language", "scatter_matrix_numeric",
]
