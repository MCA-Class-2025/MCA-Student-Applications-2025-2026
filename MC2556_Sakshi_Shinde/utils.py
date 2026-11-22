import streamlit as st

def apply_custom_css():
    """
    Applies custom high-end styles to the Streamlit app.
    Uses glassmorphic styling, subtle linear gradients, and responsive layouts.
    """
    st.markdown(
        """
        <style>
        /* Modern Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
        
        /* Root container */
        .stApp {
            background: radial-gradient(circle at 10% 20%, rgba(13, 20, 35, 1) 0%, rgba(8, 10, 16, 1) 90%);
            color: #f1f5f9;
            font-family: 'Plus Jakarta Sans', sans-serif;
        }

        /* Top Header */
        h1, h2, h3 {
            font-family: 'Outfit', sans-serif;
            color: #ffffff;
            font-weight: 700;
        }

        .main-title-container {
            text-align: center;
            padding: 1.5rem 0 2rem 0;
            background: linear-gradient(180deg, rgba(56, 189, 248, 0.05) 0%, rgba(0, 0, 0, 0) 100%);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            margin-bottom: 2rem;
        }

        .main-title {
            font-size: 3.2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
            padding: 0;
            letter-spacing: -0.02em;
        }

        .main-subtitle {
            font-size: 1.1rem;
            color: #94a3b8;
            margin-top: 0.5rem;
            font-weight: 300;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: rgba(9, 14, 25, 0.98) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.06);
        }

        [data-testid="stSidebar"] .stMarkdown h2 {
            font-size: 1.4rem;
            color: #38bdf8;
            border-bottom: 1px solid rgba(56, 189, 248, 0.2);
            padding-bottom: 0.5rem;
            margin-bottom: 1rem;
        }

        /* Premium Glass Card Containers */
        .glass-card {
            background: rgba(255, 255, 255, 0.025);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 16px;
            padding: 1.25rem 1.5rem;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            margin-bottom: 1.25rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .glass-card:hover {
            border-color: rgba(56, 189, 248, 0.3);
            transform: translateY(-2px);
            box-shadow: 0 12px 40px 0 rgba(56, 189, 248, 0.1);
        }

        .card-header {
            font-family: 'Outfit', sans-serif;
            font-size: 1.1rem;
            font-weight: 600;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }

        /* Customized Metric Layouts */
        .metric-container {
            display: flex;
            flex-direction: column;
        }

        .metric-value {
            font-family: 'Outfit', sans-serif;
            font-size: 2rem;
            font-weight: 800;
            color: #38bdf8;
            margin: 0.25rem 0;
            text-shadow: 0 0 15px rgba(56, 189, 248, 0.2);
        }

        .metric-value.purple {
            color: #c084fc;
            text-shadow: 0 0 15px rgba(192, 132, 252, 0.2);
        }

        .metric-value.green {
            color: #34d399;
            text-shadow: 0 0 15px rgba(52, 211, 153, 0.2);
        }

        .metric-desc {
            font-size: 0.85rem;
            color: #64748b;
        }

        /* Source Document Citation Expanders */
        .citation-box {
            background: rgba(15, 23, 42, 0.6);
            border-left: 3px solid #6366f1;
            border-radius: 4px;
            padding: 0.75rem 1rem;
            margin: 0.5rem 0;
            font-size: 0.9rem;
            color: #cbd5e1;
        }

        .citation-badge {
            background: rgba(99, 102, 241, 0.15);
            color: #818cf8;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-right: 0.5rem;
            display: inline-block;
        }

        /* Custom buttons styling */
        .stButton>button {
            background: linear-gradient(135deg, #38bdf8 0%, #6366f1 100%) !important;
            color: white !important;
            border: none !important;
            padding: 0.5rem 1.5rem !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
        }

        .stButton>button:hover {
            transform: scale(1.02) !important;
            box-shadow: 0 6px 18px rgba(99, 102, 241, 0.5) !important;
        }

        /* Streamlit overrides */
        .stChatMessage {
            background-color: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.04) !important;
            border-radius: 12px !important;
            padding: 1rem !important;
            margin-bottom: 0.75rem !important;
        }
        
        .stChatMessage[data-testid="stChatMessageUser"] {
            background-color: rgba(56, 189, 248, 0.04) !important;
            border-color: rgba(56, 189, 248, 0.1) !important;
        }

        /* Custom footer */
        .custom-footer {
            text-align: center;
            color: #475569;
            font-size: 0.8rem;
            margin-top: 3rem;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            padding-top: 1.5rem;
            letter-spacing: 0.05em;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def render_metric_card(label: str, value: str, description: str, color_class: str = ""):
    """Renders a responsive metric card using custom HTML."""
    st.markdown(
        f"""
        <div class="glass-card metric-container">
            <div class="card-header">{label}</div>
            <div class="metric-value {color_class}">{value}</div>
            <div class="metric-desc">{description}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def convert_history_to_text(chat_history: list[dict]) -> str:
    """Converts Streamlit chat history list into a clean text file format."""
    text_out = "DOCUMIND AI - RAG SESSION CONVERSATION LOG\n"
    text_out += "="*50 + "\n"
    for msg in chat_history:
        role = "USER" if msg["role"] == "user" else "ASSISTANT"
        text_out += f"\n[{role}]:\n{msg['content']}\n"
        if role == "ASSISTANT" and msg.get("citations"):
            text_out += "\n--- Citations ---\n"
            for c_idx, cit in enumerate(msg["citations"]):
                src = cit["metadata"]["source"]
                page = cit["metadata"]["page"]
                text_out += f"  [{c_idx+1}] File: {src} (Page {page}) [Similarity: {cit.get('score', 0.0):.3f}]\n"
        text_out += "-" * 50 + "\n"
    return text_out
