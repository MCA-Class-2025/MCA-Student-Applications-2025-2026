import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

COLOR_MAP = {
    "Safe": "#10B981",
    "Unsafe": "#EF4444",
    "Needs Review": "#F59E0B",
    "Low": "#10B981",
    "Medium": "#F59E0B",
    "High": "#EF4444",
    "Positive": "#10B981",
    "Negative": "#EF4444",
    "Neutral": "#6B7280"
}

def toxicity_distribution_donut(df):
    toxic_counts = df["toxic"].value_counts().reset_index()
    toxic_counts.columns = ["Status", "Count"]
    toxic_counts["Status"] = toxic_counts["Status"].map({1: "Toxic", 0: "Non-Toxic"})
    fig = px.pie(
        toxic_counts, values="Count", names="Status",
        color="Status",
        color_discrete_map={"Toxic": "#EF4444", "Non-Toxic": "#10B981"},
        hole=0.45,
        title="Toxicity Status Breakdown"
    )
    fig.update_layout(margin=dict(t=40, b=20, l=20, r=20), height=320)
    return fig

def gemini_risk_donut(df):
    counts = df["gemini_risk_level"].value_counts().reset_index()
    counts.columns = ["Risk Level", "Count"]
    fig = px.pie(
        counts, values="Count", names="Risk Level",
        color="Risk Level",
        color_discrete_map=COLOR_MAP,
        hole=0.45,
        title="Gemini LLM Risk Level Assessment"
    )
    fig.update_layout(margin=dict(t=40, b=20, l=20, r=20), height=320)
    return fig

def toxicity_categories_bar(df):
    cats = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]
    existing = [c for c in cats if c in df.columns]
    sums = df[existing].sum().reset_index()
    sums.columns = ["Category", "Count"]
    sums["Category"] = sums["Category"].str.replace("_", " ").str.title()
    fig = px.bar(
        sums, x="Category", y="Count",
        color="Count",
        color_continuous_scale="Reds",
        title="Toxicity Subcategory Occurrence"
    )
    fig.update_layout(margin=dict(t=40, b=20, l=20, r=20), height=350, showlegend=False)
    return fig

def sentiment_vs_toxic_scatter(df):
    fig = px.scatter(
        df,
        x="hf_sentiment_score",
        y="hf_toxic_score",
        color="gemini_risk_level",
        color_discrete_map=COLOR_MAP,
        hover_data=["comment_text", "gemini_decision"],
        labels={"hf_sentiment_score": "Sentiment Score", "hf_toxic_score": "Toxicity Confidence"},
        title="Hugging Face Sentiment Score vs Toxicity Confidence"
    )
    fig.update_layout(margin=dict(t=40, b=20, l=20, r=20), height=380)
    return fig

def safesearch_summary_bar(df):
    cats = ["adult_content", "violence_content", "racy_content", "medical_content", "spoof_content"]
    data = []
    for c in cats:
        if c in df.columns:
            counts = df[c].value_counts().to_dict()
            for level, cnt in counts.items():
                data.append({"Category": c.replace("_content", "").title(), "Likelihood": str(level), "Count": cnt})
    res_df = pd.DataFrame(data)
    if res_df.empty:
        return go.Figure()
    fig = px.bar(
        res_df,
        x="Category",
        y="Count",
        color="Likelihood",
        barmode="stack",
        title="Google Vision SafeSearch Content Likelihood Across Dataset"
    )
    fig.update_layout(margin=dict(t=40, b=20, l=20, r=20), height=360)
    return fig
