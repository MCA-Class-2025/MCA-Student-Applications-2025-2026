"""Streamlit composition for the FemCare analytics dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from analytics.dashboard import (
    algorithm_comparison_chart,
    cycle_chart,
    flow_profile_chart,
    lifestyle_boxplot,
    monthly_health_trend,
    pain_driver_chart,
    pain_severity_donut,
    state_choropleth,
    stress_sleep_scatter,
)


STATIC_CONFIG = {
    "staticPlot": True,
    "displayModeBar": False,
    "responsive": True,
}

DYNAMIC_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}


def _filtered_data(data: pd.DataFrame) -> pd.DataFrame:
    """Render compact controls and return the requested analytical slice."""
    min_age = int(data["age"].min())
    max_age = int(data["age"].max())

    with st.container(border=True):
        st.markdown("#### 🎛️ Interactive filters")
        state_col, age_col, pcos_col, flow_col = st.columns([1.35, 1.1, 1, 1])
        with state_col:
            states = st.multiselect(
                "States",
                sorted(data["state"].dropna().unique()),
                placeholder="All states",
                help="Leave empty to include every state.",
            )
        with age_col:
            age_range = st.slider(
                "Age range", min_age, max_age, (min_age, max_age)
            )
        with pcos_col:
            pcos = st.selectbox("PCOS status", ["All", "Diagnosed", "Not diagnosed"])
        with flow_col:
            flow = st.selectbox("Flow level", ["All", "Light", "Medium", "Heavy"])

    mask = data["age"].between(*age_range)
    if states:
        mask &= data["state"].isin(states)
    if pcos != "All":
        mask &= data["pcos_diagnosed"].eq(1 if pcos == "Diagnosed" else 0)
    if flow != "All":
        mask &= data["flow_level"].eq(flow)
    return data.loc[mask].copy()


def render_analytics_dashboard(data: pd.DataFrame) -> None:
    """Render static storytelling charts and filterable Plotly exploration."""
    st.markdown(
        """
        <div class="analytics-hero">
            <div class="analytics-kicker">FUSED DATA · VISUAL ANALYTICS</div>
            <div class="analytics-title">Women's Health Intelligence Studio</div>
            <div class="analytics-subtitle">
                A visual journey from cycle patterns to lifestyle, environment and state context.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <style>
        .analytics-hero {
            background: linear-gradient(120deg, #7b1e63 0%, #d63384 46%, #f783ac 100%);
            border-radius: 22px;
            padding: 30px 34px;
            margin-bottom: 22px;
            box-shadow: 0 18px 42px rgba(141, 35, 102, 0.18);
            color: white;
        }
        .analytics-kicker {
            font-size: 0.78rem;
            font-weight: 750;
            letter-spacing: 0.15em;
            opacity: 0.88;
            margin-bottom: 8px;
        }
        .analytics-title {
            font-size: 2.25rem;
            line-height: 1.08;
            font-weight: 800;
            margin-bottom: 9px;
        }
        .analytics-subtitle { font-size: 1.03rem; opacity: 0.92; }
        .insight-strip {
            border-left: 5px solid #d63384;
            background: linear-gradient(90deg, #fff0f6, rgba(255,255,255,0));
            padding: 12px 16px;
            border-radius: 0 12px 12px 0;
            color: #5f244c;
            margin: 4px 0 18px 0;
        }
        [data-testid="stMetric"] {
            background: linear-gradient(145deg, #ffffff, #fff7fb);
            border: 1px solid #f2cee0;
            padding: 14px 16px;
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(128, 40, 92, 0.07);
        }
        [data-testid="stMetricValue"] { color: #9f236d; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    overview = st.columns(4)
    overview[0].metric("Cycle records", f"{len(data):,}")
    overview[1].metric("People represented", f"{data['user_id'].nunique():,}")
    overview[2].metric("States", f"{data['state'].nunique():,}")
    overview[3].metric("Fused features", f"{len(data.columns):,}")

    st.markdown("### 🖼️ Static visual story")
    st.caption("Presentation-ready snapshots with fixed scales and labels.")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            pain_severity_donut(data), width="stretch",
            config=STATIC_CONFIG, key="static_pain_severity",
        )
    with right:
        st.plotly_chart(
            flow_profile_chart(data), width="stretch",
            config=STATIC_CONFIG, key="static_flow_profile",
        )

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            cycle_chart(data), width="stretch",
            config=STATIC_CONFIG, key="static_cycle_distribution",
        )
    with right:
        st.plotly_chart(
            pain_driver_chart(data), width="stretch",
            config=STATIC_CONFIG, key="static_pain_associations",
        )

    st.markdown(
        """
        <div class="insight-strip">
            <b>How to read this section:</b> the charts describe patterns in this dataset.
            Correlation is association—not proof that a feature causes pain.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### ✨ Dynamic exploration")
    st.caption("Filter the population, hover for exact values, zoom, and change the metric.")
    filtered = _filtered_data(data)

    if filtered.empty:
        st.warning("No records match this combination. Broaden one or more filters.")
        return

    high_pain_rate = filtered["pain_level"].ge(7).mean() * 100
    filtered_metrics = st.columns(4)
    filtered_metrics[0].metric("Visible records", f"{len(filtered):,}")
    filtered_metrics[1].metric("Average pain", f"{filtered['pain_level'].mean():.2f} / 10")
    filtered_metrics[2].metric("High-pain rate", f"{high_pain_rate:.1f}%")
    filtered_metrics[3].metric("Average stress", f"{filtered['stress_score_cycle'].mean():.2f} / 10")

    map_metric = st.selectbox(
        "Colour the state map by",
        ["Average pain", "High-pain rate", "Average stress", "Average cycle length"],
    )
    st.plotly_chart(
        state_choropleth(filtered, map_metric), width="stretch",
        config=DYNAMIC_CONFIG, key="dynamic_state_map",
    )
    st.caption(
        "State colours summarize records in the selected slice. State-level API values "
        "are contextual and should not be interpreted as individual or causal effects."
    )

    left, right = st.columns([1.08, 0.92])
    with left:
        st.plotly_chart(
            stress_sleep_scatter(filtered), width="stretch",
            config=DYNAMIC_CONFIG, key="dynamic_stress_sleep",
        )
    with right:
        lifestyle_choice = st.selectbox(
            "Compare pain by",
            [
                "exercise_frequency", "diet_quality",
                "alcohol_consumption", "smoking_status",
            ],
            format_func=lambda value: value.replace("_", " ").title(),
        )
        st.plotly_chart(
            lifestyle_boxplot(filtered, lifestyle_choice), width="stretch",
            config=DYNAMIC_CONFIG, key="dynamic_lifestyle",
        )

    st.plotly_chart(
        monthly_health_trend(filtered), width="stretch",
        config=DYNAMIC_CONFIG, key="dynamic_monthly_trend",
    )
    st.caption(
        "The range slider changes the visible time window. Hover over a line to compare "
        "pain, stress and mood for the same month."
    )

    score_path = Path("report/algorithm_comparison/seven_algorithm_scores.csv")
    if score_path.exists():
        st.markdown("### 🤖 Seven-algorithm comparison")
        st.caption(
            "Classification predicts high pain (7–10); regression predicts the exact pain score. "
            "Only compare algorithms within the same task."
        )
        scores = pd.read_csv(score_path)
        left, right = st.columns(2)
        with left:
            st.plotly_chart(
                algorithm_comparison_chart(scores, "classification", "f1"),
                width="stretch", config=STATIC_CONFIG, key="static_classifier_f1",
            )
        with right:
            st.plotly_chart(
                algorithm_comparison_chart(scores, "regression", "mae"),
                width="stretch", config=STATIC_CONFIG, key="static_regression_mae",
            )

        model_col, metric_col = st.columns(2)
        with model_col:
            model_task = st.selectbox(
                "Prediction task", ["classification", "regression"],
                format_func=lambda value: value.title(),
            )
        metric_options = (
            ["accuracy", "precision", "recall", "f1", "roc_auc"]
            if model_task == "classification"
            else ["mae", "rmse", "r2"]
        )
        with metric_col:
            model_metric = st.selectbox(
                "Evaluation measure", metric_options,
                format_func=lambda value: value.replace("_", "-").upper(),
            )
        st.plotly_chart(
            algorithm_comparison_chart(scores, model_task, model_metric),
            width="stretch", config=DYNAMIC_CONFIG, key="dynamic_model_comparison",
        )
        st.caption(
            "Pink marks the best observed value for the selected measure on this fixed test split. "
            "MAE and RMSE are better when lower; the other measures are better when higher."
        )

    with st.expander("Method and interpretation notes"):
        st.markdown(
            """
            - **Static charts** are fixed presentation views and intentionally disable chart controls.
            - **Dynamic charts** respond to state, age, PCOS and flow filters and retain hover/zoom controls.
            - **High pain** is defined here as a recorded score of 7–10 for descriptive analysis; it is not a clinical diagnosis.
            - Weather uses a representative state location, and Census/CDC measurements are state-level values repeated across cycle records.
            - Results describe this academic dataset and are not validated for medical decisions.
            """
        )
