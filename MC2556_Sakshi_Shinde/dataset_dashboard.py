"""
FundFlow fused-dataset dashboard for DocuMind AI.

This dashboard is connected directly to FundFlow_fused_dataset.csv.
The fused file contains 4,269 loan-application records enriched with
aggregated financial-risk segment features.
"""

import os

import pandas as pd
import streamlit as st

try:
    import plotly.express as px
    USE_PLOTLY = True
except ImportError:
    USE_PLOTLY = False
    import matplotlib.pyplot as plt


FUSED_DATASET_FILENAME = "FundFlow_fused_dataset.csv"


@st.cache_data(show_spinner="Loading FundFlow fused dataset...")
def load_fused_dataset(csv_path: str) -> pd.DataFrame:
    """Load and normalize the FundFlow fused CSV."""
    df = pd.read_csv(csv_path)

    # Normalize column names and string values so filtering is reliable.
    df.columns = [str(col).strip() for col in df.columns]
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()

    # Convert numeric columns safely.
    numeric_columns = [
        "loan_id", "no_of_dependents", "income_annum", "loan_amount",
        "loan_term", "cibil_score", "residential_assets_value",
        "commercial_assets_value", "luxury_assets_value", "bank_asset_value",
        "risk_segment_records", "risk_avg_score", "risk_avg_credit_score",
        "risk_avg_annual_income", "risk_avg_loan_amount",
        "risk_avg_loan_duration_months", "risk_avg_interest_rate",
        "risk_avg_debt_to_income", "risk_avg_total_debt_to_income",
        "risk_loan_approval_rate", "risk_avg_net_worth", "risk_avg_savings",
    ]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def _compute_statistics(df: pd.DataFrame) -> dict:
    approved = int((df["loan_status"] == "Approved").sum()) if "loan_status" in df else 0
    rejected = int((df["loan_status"] == "Rejected").sum()) if "loan_status" in df else 0
    return {
        "total_records": len(df),
        "approved_loans": approved,
        "rejected_loans": rejected,
        "approval_rate": (approved / len(df) * 100) if len(df) else 0,
        "avg_credit_score": float(df["cibil_score"].mean()) if "cibil_score" in df else 0.0,
        "avg_annual_income": float(df["income_annum"].mean()) if "income_annum" in df else 0.0,
        "avg_loan_amount": float(df["loan_amount"].mean()) if "loan_amount" in df else 0.0,
        "avg_risk_score": float(df["risk_avg_score"].mean()) if "risk_avg_score" in df else 0.0,
    }


def _histogram(df, x, title, x_label=None):
    if x not in df.columns:
        st.info(f"{x} is not available in the fused dataset.")
        return
    if USE_PLOTLY:
        fig = px.histogram(df, x=x, nbins=30, title=title)
        if x_label:
            fig.update_xaxes(title=x_label)
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig, ax = plt.subplots()
        ax.hist(df[x].dropna(), bins=30)
        ax.set_title(title)
        if x_label:
            ax.set_xlabel(x_label)
        st.pyplot(fig)
        plt.close(fig)


def render_dataset_fusion_dashboard(workspace_dir: str):
    """
    Render the FundFlow fused dataset section inside Streamlit.
    """
    csv_path = os.path.join(workspace_dir, FUSED_DATASET_FILENAME)

    if not os.path.exists(csv_path):
        st.error(
            f"FundFlow fused dataset not found at `{csv_path}`. "
            f"Expected `{FUSED_DATASET_FILENAME}` in the project root."
        )
        return

    df = load_fused_dataset(csv_path)

    required_columns = {
        "loan_id", "education_group", "no_of_dependents", "education",
        "self_employed", "income_annum", "loan_amount", "loan_term",
        "cibil_score", "loan_status", "risk_avg_score",
    }
    missing = sorted(required_columns - set(df.columns))
    if missing:
        st.error(
            "The FundFlow fused file is missing required columns: "
            + ", ".join(missing)
        )
        return

    stats = _compute_statistics(df)

    st.markdown("### 📊 FundFlow Dataset Fusion")
    st.markdown(
        f"**FundFlow_fused_dataset.csv** contains **{len(df):,} loan records** "
        f"with the original loan-approval fields plus aggregated financial-risk "
        f"features. The current file has **{len(df.columns)} columns**."
    )

    # Overview
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Fused Records", f"{len(df):,}")
    c2.metric("Features", str(len(df.columns)))
    c3.metric("Approved", f"{stats['approved_loans']:,}")
    c4.metric("Rejected", f"{stats['rejected_loans']:,}")
    c5.metric("Approval Rate", f"{stats['approval_rate']:.1f}%")

    st.markdown("---")

    # Filters
    st.markdown("#### 🔎 Interactive Filters")
    f1, f2, f3, f4 = st.columns(4)

    with f1:
        status_filter = st.selectbox(
            "Loan Status",
            ["All"] + sorted(df["loan_status"].dropna().unique().tolist()),
        )
    with f2:
        education_filter = st.selectbox(
            "Education",
            ["All"] + sorted(df["education"].dropna().unique().tolist()),
        )
    with f3:
        self_employed_filter = st.selectbox(
            "Self Employed",
            ["All"] + sorted(df["self_employed"].dropna().unique().tolist()),
        )
    with f4:
        cs_min = int(df["cibil_score"].min())
        cs_max = int(df["cibil_score"].max())
        credit_range = st.slider(
            "CIBIL Score Range",
            min_value=cs_min,
            max_value=cs_max,
            value=(cs_min, cs_max),
        )

    filtered = df.copy()

    if status_filter != "All":
        filtered = filtered[filtered["loan_status"] == status_filter]
    if education_filter != "All":
        filtered = filtered[filtered["education"] == education_filter]
    if self_employed_filter != "All":
        filtered = filtered[filtered["self_employed"] == self_employed_filter]

    filtered = filtered[
        filtered["cibil_score"].between(credit_range[0], credit_range[1])
    ]

    # Statistics after filters
    stats = _compute_statistics(filtered)
    st.markdown("#### 📈 Filtered Statistics")
    s1, s2, s3, s4, s5, s6 = st.columns(6)
    s1.metric("Records", f"{stats['total_records']:,}")
    s2.metric("Approved", f"{stats['approved_loans']:,}")
    s3.metric("Rejected", f"{stats['rejected_loans']:,}")
    s4.metric("Approval Rate", f"{stats['approval_rate']:.1f}%")
    s5.metric("Avg CIBIL", f"{stats['avg_credit_score']:.1f}")
    s6.metric("Avg Risk Score", f"{stats['avg_risk_score']:.2f}")

    st.markdown("#### 👁️ Dataset Preview (All Records)")
    st.caption(f"Displaying all **{len(filtered):,}** filtered records with **{len(filtered.columns)}** columns.")
    st.dataframe(filtered, use_container_width=True, height=600)

    # Charts
    st.markdown("#### 📉 Visualizations")
    v1, v2 = st.columns(2)

    with v1:
        st.markdown("**Loan Status Distribution**")
        status_counts = filtered["loan_status"].value_counts().reset_index()
        status_counts.columns = ["loan_status", "count"]
        if USE_PLOTLY:
            fig = px.pie(
                status_counts,
                names="loan_status",
                values="count",
                hole=0.35,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            fig, ax = plt.subplots()
            ax.pie(
                status_counts["count"],
                labels=status_counts["loan_status"],
                autopct="%1.1f%%",
            )
            st.pyplot(fig)
            plt.close(fig)

        _histogram(filtered, "cibil_score", "CIBIL Score Distribution", "CIBIL Score")
        _histogram(filtered, "loan_amount", "Loan Amount Distribution", "Loan Amount (₹)")

    with v2:
        _histogram(
            filtered,
            "income_annum",
            "Annual Income Distribution",
            "Annual Income (₹)",
        )

        st.markdown("**Education Distribution**")
        edu_counts = filtered["education"].value_counts().reset_index()
        edu_counts.columns = ["education", "count"]
        if USE_PLOTLY:
            fig = px.bar(edu_counts, x="education", y="count")
            st.plotly_chart(fig, use_container_width=True)
        else:
            fig, ax = plt.subplots()
            ax.bar(edu_counts["education"], edu_counts["count"])
            ax.tick_params(axis="x", rotation=30)
            st.pyplot(fig)
            plt.close(fig)

    # Risk section
    st.markdown("#### 🛡️ Financial Risk Insights")
    r1, r2, r3 = st.columns(3)
    r1.metric(
        "Avg Risk-Segment Score",
        f"{filtered['risk_avg_score'].mean():.2f}" if len(filtered) else "0.00",
    )
    r2.metric(
        "Avg Risk Approval Rate",
        f"{filtered['risk_loan_approval_rate'].mean():.2f}%"
        if len(filtered) else "0.00%",
    )
    r3.metric(
        "Avg Risk DTI",
        f"{filtered['risk_avg_debt_to_income'].mean():.2f}"
        if len(filtered) else "0.00",
    )

    st.caption(
        f"Showing **{len(filtered):,}** of **{len(df):,}** FundFlow fused records "
        f"with **{len(df.columns)}** features."
    )
