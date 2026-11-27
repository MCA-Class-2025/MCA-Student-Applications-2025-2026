import streamlit as st

def inject_custom_css():
    st.markdown("""
    <style>
    .metric-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 16px 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 15px;
    }
    .metric-card h4 {
        margin: 0;
        font-size: 14px;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-card h2 {
        margin: 6px 0 0 0;
        font-size: 28px;
        font-weight: 700;
        color: #1e293b;
    }
    .metric-card p {
        margin: 4px 0 0 0;
        font-size: 12px;
        color: #94a3b8;
    }
    .badge-safe {
        background-color: #d1fae5;
        color: #065f46;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
    }
    .badge-unsafe {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

def metric_card(title, value, subtitle="", border_color="#3b82f6"):
    st.markdown(f"""
    <div class="metric-card" style="border-top: 4px solid {border_color};">
        <h4>{title}</h4>
        <h2>{value}</h2>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)
