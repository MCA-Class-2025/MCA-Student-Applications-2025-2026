"""
visualization/clinical_trial_charts.py — Clinical trial analytics visualizations.
"""

from typing import Any, Dict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def chart_trials_by_status(trial_eda: Dict, drug_name: str = "") -> go.Figure:
    """Pie chart of trials by status."""
    status_dist = trial_eda.get("status_distribution", {})
    if not status_dist:
        fig = go.Figure()
        fig.add_annotation(text="No trial status data", showarrow=False)
        return fig

    color_map = {
        "Active": "#4caf50",
        "Completed": "#2196f3",
        "Planned": "#ff9800",
        "Terminated": "#f44336",
        "Withdrawn": "#9e9e9e",
        "Suspended": "#ff5722",
        "Unknown": "#bdbdbd",
    }

    fig = px.pie(
        values=list(status_dist.values()),
        names=list(status_dist.keys()),
        title=f"Clinical Trials by Status — {drug_name}",
        color=list(status_dist.keys()),
        color_discrete_map=color_map,
    )
    fig.update_layout(height=380)
    return fig


def chart_trials_by_phase(trial_eda: Dict, drug_name: str = "") -> go.Figure:
    """Bar chart of trials by phase."""
    phase_dist = trial_eda.get("phase_distribution", {})
    if not phase_dist:
        fig = go.Figure()
        fig.add_annotation(text="No trial phase data", showarrow=False)
        return fig

    df = pd.DataFrame(list(phase_dist.items()), columns=["phase", "count"])
    df = df.sort_values("count", ascending=False)

    fig = px.bar(
        df, x="phase", y="count",
        title=f"Clinical Trials by Phase — {drug_name}",
        labels={"phase": "Phase", "count": "Number of Trials"},
        color="count",
        color_continuous_scale="Purples",
    )
    fig.update_layout(
        height=380,
        coloraxis_showscale=False,
        xaxis_tickangle=-30,
        margin=dict(l=20, r=20, t=50, b=60),
    )
    return fig


def chart_trials_over_time(trial_eda: Dict, drug_name: str = "") -> go.Figure:
    """Line chart of trial starts over time."""
    year_dist = trial_eda.get("start_year_distribution", {})
    if not year_dist:
        fig = go.Figure()
        fig.add_annotation(text="No trial start year data", showarrow=False)
        return fig

    years = sorted(year_dist.keys())
    counts = [year_dist[y] for y in years]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years, y=counts, mode="lines+markers",
        line=dict(color="#9c27b0", width=2),
        marker=dict(size=7),
        fill="tozeroy",
        fillcolor="rgba(156,39,176,0.1)",
    ))
    fig.update_layout(
        title=f"Clinical Trial Starts by Year — {drug_name}",
        xaxis_title="Year",
        yaxis_title="Trials Started",
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def chart_enrollment_distribution(trials_df: pd.DataFrame, drug_name: str = "") -> go.Figure:
    """Histogram of trial enrollment counts."""
    if trials_df is None or trials_df.empty or "enrollment" not in trials_df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No enrollment data available", showarrow=False)
        return fig

    enroll = trials_df["enrollment"].dropna()
    enroll = enroll[enroll > 0]

    if enroll.empty:
        fig = go.Figure()
        fig.add_annotation(text="No valid enrollment data", showarrow=False)
        return fig

    fig = px.histogram(
        enroll, nbins=30,
        title=f"Trial Enrollment Distribution — {drug_name}",
        labels={"value": "Enrollment Count", "count": "Number of Trials"},
        color_discrete_sequence=["#7b1fa2"],
    )
    fig.update_layout(
        height=350,
        showlegend=False,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def chart_top_sponsors(trial_eda: Dict, drug_name: str = "") -> go.Figure:
    """Horizontal bar chart of top trial sponsors."""
    sponsors = trial_eda.get("top_sponsors", {})
    if not sponsors:
        fig = go.Figure()
        fig.add_annotation(text="No sponsor data", showarrow=False)
        return fig

    df = pd.DataFrame(list(sponsors.items()), columns=["sponsor", "count"])
    df = df.sort_values("count", ascending=True).head(10)
    df["sponsor_short"] = df["sponsor"].str[:50]

    fig = px.bar(
        df, x="count", y="sponsor_short", orientation="h",
        title=f"Top Trial Sponsors — {drug_name}",
        labels={"count": "Trials", "sponsor_short": "Sponsor"},
        color="count",
        color_continuous_scale="Purples",
    )
    fig.update_layout(
        height=400,
        coloraxis_showscale=False,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig
