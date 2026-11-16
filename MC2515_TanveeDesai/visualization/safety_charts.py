"""
visualization/safety_charts.py — Safety analytics visualizations using Plotly.
"""

from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def chart_top_adverse_reactions(top_ae: List[Dict], drug_name: str = "") -> go.Figure:
    """Horizontal bar chart of top adverse reactions."""
    if not top_ae:
        fig = go.Figure()
        fig.add_annotation(text="No adverse reaction data available", showarrow=False, font=dict(size=14))
        return fig

    df = pd.DataFrame(top_ae[:20])
    df = df.sort_values("count", ascending=True)

    fig = px.bar(
        df, x="count", y="term", orientation="h",
        title=f"Top Adverse Reactions — {drug_name}",
        labels={"count": "Report Count", "term": "Adverse Reaction (MedDRA)"},
        color="count",
        color_continuous_scale="Reds",
    )
    fig.update_layout(
        height=500,
        coloraxis_showscale=False,
        xaxis_title="Number of Reports in FDA FAERS",
        yaxis_title="",
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def chart_recall_timeline(recalls_df: pd.DataFrame, drug_name: str = "") -> go.Figure:
    """Timeline of recall events."""
    if recalls_df is None or recalls_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No recall data found for this drug", showarrow=False, font=dict(size=14))
        fig.update_layout(title=f"Recall History — {drug_name}")
        return fig

    date_col = "recall_initiation_date" if "recall_initiation_date" in recalls_df.columns else "report_date"

    df = recalls_df.copy()
    df["date"] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=["date"])

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Recall dates unavailable", showarrow=False)
        return fig

    df["year"] = df["date"].dt.year
    yearly = df.groupby(["year", "classification"]).size().reset_index(name="count")

    fig = px.bar(
        yearly, x="year", y="count", color="classification",
        title=f"Recall Timeline — {drug_name}",
        labels={"year": "Year", "count": "Recalls", "classification": "Classification"},
        color_discrete_map={
            "CLASS I": "#d32f2f",
            "CLASS II": "#f57c00",
            "CLASS III": "#388e3c",
        },
    )
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def chart_recall_classification(recalls_df: pd.DataFrame, drug_name: str = "") -> go.Figure:
    """Pie chart of recall classifications."""
    if recalls_df is None or recalls_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No recall data", showarrow=False)
        return fig

    class_counts = recalls_df["classification"].value_counts()
    fig = px.pie(
        values=class_counts.values,
        names=class_counts.index,
        title=f"Recall Classification Distribution — {drug_name}",
        color_discrete_map={
            "CLASS I": "#d32f2f",
            "CLASS II": "#f57c00",
            "CLASS III": "#388e3c",
        },
    )
    fig.update_layout(height=400)
    return fig


def chart_safety_score_gauge(score_data: Dict[str, Any]) -> go.Figure:
    """Gauge chart for Drug Safety Intelligence Score."""
    score = score_data.get("score", 0)
    category = score_data.get("category", "")

    color_map = {"green": "#4caf50", "orange": "#ff9800", "red": "#f44336"}
    bar_color = color_map.get(score_data.get("color", "green"), "#4caf50")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": f"Safety Intelligence Score<br><sub>{category}</sub>", "font": {"size": 14}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": bar_color},
            "steps": [
                {"range": [0, 33], "color": "#e8f5e9"},
                {"range": [33, 66], "color": "#fff8e1"},
                {"range": [66, 100], "color": "#ffebee"},
            ],
            "threshold": {
                "line": {"color": "black", "width": 2},
                "thickness": 0.75,
                "value": score,
            },
        },
        number={"suffix": "/100"},
    ))
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=80, b=20),
        annotations=[{
            "text": "Analytical indicator only — not a clinical risk assessment",
            "showarrow": False,
            "xref": "paper", "yref": "paper",
            "x": 0.5, "y": -0.1,
            "font": {"size": 10, "color": "gray"},
        }],
    )
    return fig


def chart_safety_score_components(score_data: Dict[str, Any]) -> go.Figure:
    """Radar/bar chart of safety score components."""
    components = score_data.get("components", {})
    if not components:
        return go.Figure()

    labels = list(components.keys())
    values = list(components.values())

    # Clean up labels
    label_map = {
        "adverse_event_reporting": "AE Reporting",
        "recall_activity": "Recall Activity",
        "boxed_warning_presence": "Boxed Warning",
        "research_activity": "Research Activity",
        "trial_activity": "Trial Activity",
    }
    labels = [label_map.get(l, l) for l in labels]

    weights = score_data.get("weights", {})
    weight_values = [
        weights.get(list(score_data["components"].keys())[i].replace("_reporting", "").replace("_presence", "").replace("_activity", ""), 0)
        for i in range(len(labels))
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels, y=values,
        name="Component Score",
        marker_color=["#ef5350", "#ff7043", "#ffa726", "#66bb6a", "#42a5f5"],
        text=[f"{v:.1f}" for v in values],
        textposition="outside",
    ))
    fig.update_layout(
        title="Safety Score Components (0–100 each)",
        xaxis_title="",
        yaxis_title="Score",
        yaxis=dict(range=[0, 110]),
        height=350,
        showlegend=False,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def chart_ae_year_trend(ae_eda: Dict[str, Any], drug_name: str = "") -> go.Figure:
    """Line chart of adverse event reports by year."""
    year_dist = ae_eda.get("year_distribution", {})
    if not year_dist:
        fig = go.Figure()
        fig.add_annotation(text="No year data available", showarrow=False)
        return fig

    years = sorted(year_dist.keys())
    counts = [year_dist[y] for y in years]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years, y=counts, mode="lines+markers",
        line=dict(color="#ef5350", width=2),
        marker=dict(size=6),
        fill="tozeroy",
        fillcolor="rgba(239,83,80,0.1)",
        name="AE Reports",
    ))
    fig.update_layout(
        title=f"Adverse Event Reports by Year — {drug_name}",
        xaxis_title="Year",
        yaxis_title="Reports Retrieved",
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig
