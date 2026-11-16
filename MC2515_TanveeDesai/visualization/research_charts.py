"""
visualization/research_charts.py — Research analytics visualizations.
"""

from typing import Any, Dict, List, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def chart_publications_by_year(research_eda: Dict, drug_name: str = "") -> go.Figure:
    """Bar chart of publications per year."""
    year_dist = research_eda.get("year_distribution", {})
    if not year_dist:
        fig = go.Figure()
        fig.add_annotation(text="No publication year data available", showarrow=False)
        return fig

    years = sorted(year_dist.keys())
    counts = [year_dist[y] for y in years]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years, y=counts,
        marker_color="#42a5f5",
        name="Publications",
    ))
    fig.update_layout(
        title=f"PubMed Publications by Year — {drug_name}",
        xaxis_title="Publication Year",
        yaxis_title="Number of Articles",
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def chart_top_journals(research_eda: Dict, drug_name: str = "") -> go.Figure:
    """Horizontal bar chart of top journals."""
    journals = research_eda.get("top_journals", {})
    if not journals:
        fig = go.Figure()
        fig.add_annotation(text="No journal data available", showarrow=False)
        return fig

    df = pd.DataFrame(list(journals.items()), columns=["journal", "count"])
    df = df.sort_values("count", ascending=True).head(10)

    # Truncate long journal names
    df["journal_short"] = df["journal"].str[:50]

    fig = px.bar(
        df, x="count", y="journal_short", orientation="h",
        title=f"Top Publication Journals — {drug_name}",
        labels={"count": "Articles", "journal_short": "Journal"},
        color="count",
        color_continuous_scale="Blues",
    )
    fig.update_layout(
        height=400,
        coloraxis_showscale=False,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def chart_research_keywords(keywords: List[Tuple[str, float]], drug_name: str = "") -> go.Figure:
    """Word/bar chart of research keywords."""
    if not keywords:
        fig = go.Figure()
        fig.add_annotation(text="No keywords extracted", showarrow=False)
        return fig

    df = pd.DataFrame(keywords[:20], columns=["keyword", "tfidf_score"])
    df = df.sort_values("tfidf_score", ascending=True)

    fig = px.bar(
        df, x="tfidf_score", y="keyword", orientation="h",
        title=f"Top Research Keywords (TF-IDF) — {drug_name}",
        labels={"tfidf_score": "TF-IDF Score", "keyword": "Keyword/Phrase"},
        color="tfidf_score",
        color_continuous_scale="Greens",
    )
    fig.update_layout(
        height=450,
        coloraxis_showscale=False,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def chart_pub_types(research_eda: Dict, drug_name: str = "") -> go.Figure:
    """Pie chart of publication types."""
    pub_types = research_eda.get("pub_type_distribution", {})
    if not pub_types:
        fig = go.Figure()
        fig.add_annotation(text="No publication type data", showarrow=False)
        return fig

    fig = px.pie(
        values=list(pub_types.values()),
        names=list(pub_types.keys()),
        title=f"Publication Types — {drug_name}",
    )
    fig.update_layout(height=350)
    return fig
