"""Reusable Plotly figures for the FemCare analytics dashboard."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


DATA_PATH = "Fusion/data/api_fusion/final/femcare_final_cleaned.csv"

# Meanings stay stable: pink=pain, purple=stress, teal=sleep/wellbeing.
PINK = "#D63384"
CORAL = "#F05D7B"
PURPLE = "#6F42C1"
TEAL = "#1F9D8A"
GOLD = "#F2B134"
INK = "#352B3A"
MUTED = "#776B7B"
GRID = "rgba(119,107,123,0.16)"
SEQUENTIAL = ["#FFF0F6", "#FCC2D7", "#F783AC", "#D63384", "#8C1D62"]


def load_data() -> pd.DataFrame:
    data = pd.read_csv(DATA_PATH)
    if "start_date" in data.columns:
        data["start_date"] = pd.to_datetime(data["start_date"], errors="coerce")
    return data


def get_metrics(df: pd.DataFrame) -> dict:
    return {
        "Total Records": len(df),
        "Unique Users": df["user_id"].nunique(),
        "Average Age": round(df["age"].mean(), 1),
        "Average BMI": round(df["bmi"].mean(), 1),
        "Average Cycle Length": round(df["cycle_length_days"].mean(), 1),
        "Average Pain": round(df["pain_level"].mean(), 1),
        "Average Stress": round(df["stress_score_cycle"].mean(), 1),
        "PCOS Cases": int(df["pcos_diagnosed"].sum()),
    }


def _style(fig: go.Figure, title: str, height: int = 390) -> go.Figure:
    fig.update_layout(
        title={"text": title, "x": 0.02, "xanchor": "left"},
        height=height,
        margin=dict(l=45, r=25, t=65, b=45),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=INK, family="Inter, Segoe UI, sans-serif", size=13),
        title_font=dict(size=19, color=INK),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1,
            title_text="",
        ),
        hoverlabel=dict(bgcolor="#FFFFFF", font_color=INK, bordercolor="#F2CEE0"),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, title_standoff=12)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, title_standoff=12)
    return fig


def cycle_chart(df: pd.DataFrame) -> go.Figure:
    counts = df["cycle_length_days"].value_counts().sort_index().reset_index()
    counts.columns = ["Cycle length", "Records"]
    fig = px.bar(counts, x="Cycle length", y="Records", color_discrete_sequence=[PURPLE])
    fig.update_traces(marker_line_width=0, hovertemplate="%{x} days<br>%{y:,} records<extra></extra>")
    return _style(fig, "Cycle length distribution")


def pain_chart(df: pd.DataFrame) -> go.Figure:
    counts = df["pain_level"].value_counts().sort_index().reset_index()
    counts.columns = ["Pain score", "Records"]
    fig = px.bar(
        counts, x="Pain score", y="Records", color="Pain score",
        color_continuous_scale=SEQUENTIAL,
    )
    fig.update_coloraxes(showscale=False)
    fig.update_traces(marker_line_width=0, hovertemplate="Pain %{x}<br>%{y:,} records<extra></extra>")
    return _style(fig, "Pain score distribution")


def stress_chart(df: pd.DataFrame) -> go.Figure:
    fig = px.histogram(df, x="stress_score_cycle", nbins=20, color_discrete_sequence=[PURPLE])
    fig.update_traces(marker_line_width=0, hovertemplate="Stress band %{x}<br>%{y:,} records<extra></extra>")
    return _style(fig, "Stress score distribution")


def flow_chart(df: pd.DataFrame) -> go.Figure:
    order = ["Light", "Medium", "Heavy"]
    counts = df["flow_level"].value_counts().reindex(order).dropna().reset_index()
    counts.columns = ["Flow level", "Records"]
    fig = px.bar(
        counts, x="Flow level", y="Records", color="Flow level",
        color_discrete_map={"Light": TEAL, "Medium": GOLD, "Heavy": CORAL},
    )
    fig.update_layout(showlegend=False)
    fig.update_traces(marker_line_width=0, texttemplate="%{y:,}", textposition="outside")
    return _style(fig, "Flow-level composition")


def pain_severity_donut(df: pd.DataFrame) -> go.Figure:
    severity = pd.cut(
        df["pain_level"], bins=[0, 3, 6, 10],
        labels=["Low (1–3)", "Moderate (4–6)", "High (7–10)"],
        include_lowest=True,
    )
    counts = severity.value_counts(sort=False).reset_index()
    counts.columns = ["Severity", "Records"]
    fig = px.pie(
        counts, names="Severity", values="Records", hole=0.63,
        color="Severity",
        color_discrete_map={
            "Low (1–3)": TEAL, "Moderate (4–6)": GOLD, "High (7–10)": CORAL,
        },
    )
    fig.update_traces(
        textinfo="percent+label", textposition="outside",
        marker=dict(line=dict(width=0)),
        hovertemplate="%{label}<br>%{value:,} records (%{percent})<extra></extra>",
    )
    fig.add_annotation(
        text=f"<b>{len(df):,}</b><br><span style='font-size:12px'>cycles</span>",
        x=0.5, y=0.5, showarrow=False, font=dict(color=INK, size=18),
    )
    return _style(fig, "Pain severity snapshot", 420)


def pain_driver_chart(df: pd.DataFrame) -> go.Figure:
    candidates = {
        "Stress": "stress_score_cycle", "Work hours lost": "work_hours_lost",
        "Baseline stress": "stress_score_baseline", "BMI": "bmi",
        "Cycle length": "cycle_length_days", "Temperature": "temperature_mean",
        "Humidity": "humidity_mean", "Sleep": "sleep_hours_cycle",
        "Mood": "mood_score", "Energy": "energy_level",
        "Overall health": "overall_health_score",
    }
    available = {label: column for label, column in candidates.items() if column in df.columns}
    corr = df[["pain_level", *available.values()]].corr(numeric_only=True)["pain_level"]
    values = pd.DataFrame(
        [{"Feature": label, "Correlation": corr[column]} for label, column in available.items()]
    )
    values["Strength"] = values["Correlation"].abs()
    values = values.nlargest(8, "Strength").sort_values("Correlation")
    values["Direction"] = np.where(values["Correlation"] >= 0, "Positive", "Negative")
    fig = px.bar(
        values, x="Correlation", y="Feature", orientation="h", color="Direction",
        color_discrete_map={"Positive": PINK, "Negative": TEAL}, text="Correlation",
    )
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside", cliponaxis=False)
    fig.update_layout(showlegend=False)
    fig.add_vline(x=0, line_width=1, line_color=MUTED)
    return _style(fig, "Strongest associations with pain", 420)


def flow_profile_chart(df: pd.DataFrame) -> go.Figure:
    order = ["Light", "Medium", "Heavy"]
    grouped = (
        df.groupby("flow_level", observed=True)
        .agg(Pain=("pain_level", "mean"), Stress=("stress_score_cycle", "mean"))
        .reindex(order).dropna().reset_index()
        .melt(id_vars="flow_level", var_name="Measure", value_name="Average score")
    )
    fig = px.bar(
        grouped, x="flow_level", y="Average score", color="Measure", barmode="group",
        color_discrete_map={"Pain": PINK, "Stress": PURPLE}, text="Average score",
    )
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_yaxes(range=[0, 10], title="Average score (0–10)")
    fig.update_xaxes(title="Flow level")
    return _style(fig, "Pain and stress by flow level", 420)


def state_choropleth(df: pd.DataFrame, metric: str) -> go.Figure:
    metric_map = {
        "Average pain": ("pain_level", "mean", "Average pain score"),
        "Average stress": ("stress_score_cycle", "mean", "Average stress score"),
        "Average cycle length": ("cycle_length_days", "mean", "Average cycle length (days)"),
        "High-pain rate": ("pain_level", lambda s: (s >= 7).mean() * 100, "High-pain records (%)"),
    }
    column, aggregation, label = metric_map[metric]
    state = (
        df.groupby(["state", "state_abbr"], as_index=False)
        .agg(value=(column, aggregation), records=("user_id", "size"))
    )
    fig = px.choropleth(
        state, locations="state_abbr", locationmode="USA-states", scope="usa",
        color="value", hover_name="state",
        hover_data={"records": ":,", "state_abbr": False},
        color_continuous_scale=SEQUENTIAL,
        labels={"value": label, "records": "Records"},
    )
    fig.update_traces(marker_line_color="#FFFFFF", marker_line_width=0.7)
    fig.update_coloraxes(colorbar_title=label)
    return _style(fig, f"{metric} across states", 520)


def stress_sleep_scatter(df: pd.DataFrame) -> go.Figure:
    plot_df = df.sample(min(len(df), 2500), random_state=42).copy()
    plot_df["PCOS"] = plot_df["pcos_diagnosed"].map({0: "No", 1: "Yes"})
    fig = px.scatter(
        plot_df, x="sleep_hours_cycle", y="stress_score_cycle", color="pain_level",
        symbol="PCOS", opacity=0.58, color_continuous_scale=SEQUENTIAL,
        hover_data={
            "state": True, "pain_level": ":.0f",
            "sleep_hours_cycle": ":.1f", "stress_score_cycle": ":.1f",
        },
        labels={
            "sleep_hours_cycle": "Cycle sleep (hours)",
            "stress_score_cycle": "Cycle stress score", "pain_level": "Pain score",
        },
    )
    fig.update_traces(marker=dict(size=8, line=dict(width=0)))
    return _style(fig, "How sleep, stress and pain move together", 520)


def monthly_health_trend(df: pd.DataFrame) -> go.Figure:
    dated = df.dropna(subset=["start_date"]).copy()
    dated["Month"] = dated["start_date"].dt.to_period("M").dt.to_timestamp()
    monthly = (
        dated.groupby("Month", as_index=False)
        .agg(Pain=("pain_level", "mean"), Stress=("stress_score_cycle", "mean"), Mood=("mood_score", "mean"))
        .melt(id_vars="Month", var_name="Measure", value_name="Average score")
    )
    fig = px.line(
        monthly, x="Month", y="Average score", color="Measure", markers=True,
        color_discrete_map={"Pain": PINK, "Stress": PURPLE, "Mood": TEAL},
    )
    fig.update_traces(line_width=3, marker_size=6)
    fig.update_xaxes(rangeslider_visible=True, title="Cycle start month")
    fig.update_yaxes(title="Average score (0–10)")
    return _style(fig, "Health signals over time", 480)


def quarterly_motion_bubbles(df: pd.DataFrame) -> go.Figure:
    """Animate state aggregates; bubble area represents sample size."""
    dated = df.dropna(subset=["start_date", "state", "pain_level", "stress_score_cycle", "sleep_hours_cycle"]).copy()
    dated["Quarter"] = dated["start_date"].dt.to_period("Q").astype(str)
    frame = dated.groupby(["Quarter", "state"], as_index=False).agg(
        pain=("pain_level", "mean"), stress=("stress_score_cycle", "mean"),
        sleep=("sleep_hours_cycle", "mean"), records=("user_id", "size"),
    )
    frame = frame.loc[frame["records"].ge(5)].copy()
    if frame.empty:
        return _style(go.Figure(), "State patterns over time", 530)
    fig = px.scatter(
        frame, x="stress", y="pain", size="records", color="sleep",
        animation_frame="Quarter", animation_group="state", hover_name="state",
        hover_data={"records": ":,", "stress": ":.2f", "pain": ":.2f", "sleep": ":.2f"},
        range_x=[0, 10], range_y=[0, 10], size_max=52,
        color_continuous_scale=["#F05D7B", "#F2B134", "#1F9D8A"],
        range_color=[4.5, 10],
        labels={"stress": "Average stress (0–10)", "pain": "Average pain (0–10)",
                "sleep": "Average sleep (hours)", "records": "Cycle records"},
    )
    fig.update_traces(marker_line_color="white", marker_line_width=1.5, opacity=0.78)
    fig = _style(fig, "State patterns through time · press Play", 550)
    fig.update_layout(coloraxis_colorbar=dict(title="Sleep (h)"))
    for control in fig.layout.updatemenus or []:
        control.update(x=0.02, y=-0.11, xanchor="left", yanchor="top")
    for slider in fig.layout.sliders or []:
        slider.update(y=-0.11, x=0.18, len=0.78)
    fig.update_layout(margin=dict(l=45, r=30, t=65, b=115))
    return fig


def lifestyle_boxplot(df: pd.DataFrame, category: str) -> go.Figure:
    labels = {
        "exercise_frequency": "Exercise frequency", "diet_quality": "Diet quality",
        "alcohol_consumption": "Alcohol consumption", "smoking_status": "Smoking status",
    }
    fig = px.box(
        df, x=category, y="pain_level", color=category, points="outliers",
        color_discrete_sequence=[TEAL, GOLD, PINK, PURPLE],
        labels={category: labels[category], "pain_level": "Pain score"},
    )
    fig.update_layout(showlegend=False)
    fig.update_traces(marker=dict(opacity=0.45), line_width=2)
    return _style(fig, f"Pain distribution by {labels[category].lower()}", 450)


def algorithm_comparison_chart(
    scores: pd.DataFrame, task: str, metric: str
) -> go.Figure:
    """Compare like-for-like algorithms and highlight the best observed score."""
    frame = scores.loc[scores["task"].eq(task), ["algorithm", metric]].dropna().copy()
    lower_is_better = metric in {"mae", "rmse"}
    frame = frame.sort_values(metric, ascending=not lower_is_better)
    best_index = frame[metric].idxmin() if lower_is_better else frame[metric].idxmax()
    frame["Result"] = np.where(frame.index == best_index, "Best observed", "Other model")
    metric_labels = {
        "accuracy": "Accuracy", "precision": "Precision", "recall": "Recall",
        "f1": "F1 score", "roc_auc": "ROC-AUC", "mae": "MAE (pain points)",
        "rmse": "RMSE (pain points)", "r2": "R²",
    }
    fig = px.bar(
        frame, x=metric, y="algorithm", orientation="h", color="Result", text=metric,
        color_discrete_map={"Best observed": PINK, "Other model": PURPLE},
        labels={metric: metric_labels[metric], "algorithm": "Algorithm"},
        category_orders={"Result": ["Best observed", "Other model"]},
    )
    fig.update_traces(texttemplate="%{text:.3f}", textposition="outside", cliponaxis=False)
    fig.update_layout(showlegend=False)
    title_task = "High-pain classification" if task == "classification" else "Pain-score regression"
    return _style(fig, f"{title_task}: {metric_labels[metric]}", 390)
