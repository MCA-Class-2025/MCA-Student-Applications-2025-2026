import io
from datetime import datetime

import streamlit as st
import pandas as pd
from pathlib import Path
from analytics.dashboard import (
    get_metrics,
    load_data,
)
from analytics.dashboard_page import render_analytics_dashboard

from rag.chat_service import respond_to_question
from utils.chat_history import (
    delete_chat,
    get_chat_info,
    get_history,
    load_chat,
    rename_chat,
    save_chat,
)

from utils.healthcare_finder import render_healthcare_finder
from utils.app_settings import apply_app_settings, render_settings
from utils.menocare_page import render_menocare
from utils.nutrition_guide import render_nutrition_guide
from utils.ui_shell import inject_ui_shell, render_home, render_sidebar_brand

# -----------------------------------------------------------------------------
# 1. PAGE CONFIG & CUSTOM CSS STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="FemCare AI",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_ui_shell()

# Apply user-selected appearance and accessibility preferences after base CSS.
apply_app_settings()

# -----------------------------------------------------------------------------
# 2. DATA LOADING & METRICS
# -----------------------------------------------------------------------------
df = load_data()
metrics = get_metrics(df)

# -----------------------------------------------------------------------------
# 3. SIDEBAR NAVIGATION & SYSTEM STATUS
# -----------------------------------------------------------------------------
with st.sidebar:
    render_sidebar_brand()

    page = st.radio(
    "Navigation",
    [
        "🏠 Home",
        "💬 Chat",
        "🕒 History",
        "📊 EDA & Analytics",
        "🔗 Data Fusion",
        "🗃️ Complete Dataset",
        "🌙 MenoCare",
        "🏥 Healthcare Finder",
        "🍎 Nutrition Guide",
        "⚙️ Settings",
        "ℹ️ About",
    ],
    label_visibility="collapsed",
    key="main_navigation",
)

    st.divider()

    st.markdown('<div class="fc-side-label">System</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div>
            <div class="status-badge">🤖 <b>LLM:</b> Llama 3.2</div>
            <div class="status-badge">🔍 <b>Vectorizer:</b> TF-IDF</div>
            <div class="status-badge">⚡ <b>Knowledge Base:</b> Fused Index</div>
            <div class="status-badge">📚 <b>RAG:</b> Enabled</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# 4. PAGE ROUTING & UI LAYOUT
# -----------------------------------------------------------------------------

# --- PAGE 1: HOME ---
if page == "🏠 Home":
    render_home(metrics)


# --- PAGE 2: CHAT ---
elif page == "💬 Chat":
    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">🌸 FemCare AI Assistant</div>
            <p class="hero-subtitle">
                Ask questions about menstrual cycles, PCOS, pain management, hormonal health, and wellness.
            </p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = datetime.now().strftime(
            "Chat_%d-%m-%Y_%H-%M-%S"
        )

    def generate_chat_text(messages):
        text = []
        text.append("FemCare AI Conversation")
        text.append("=" * 40)
        text.append(f"Generated: {datetime.now()}")
        text.append("")

        for msg in messages:
            role = msg["role"].capitalize()
            text.append(f"{role}:")
            text.append(msg["content"])
            text.append("-" * 40)

        return "\n".join(text)

    # Collapsible / Expressive Guide Card
    with st.expander("💬 **How to interact with FemCare AI**", expanded=False):
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown(
                """
                **Ask General Knowledge Questions:**
                - *What is PCOS?*
                - *Why do menstrual cramps happen?*
                - *How does stress affect periods?*
                """
            )
        with col_g2:
            st.markdown(
                """
                **Describe Symptoms for Analysis:**
                ```text
                Pain: 6/10 | Stress: 4/10 | Sleep: 5 hours | Flow: Heavy | PCOS: Yes
                ```
                *Or as text:* "My pain is 6/10, stress is 4/10, I slept 5 hours and my flow is heavy. What can you infer?"
                """
            )

    st.write("")

    # Chat Actions Header Bar
    c_act1, c_act2, _ = st.columns([1, 1, 2])
    with c_act1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conversation_id = datetime.now().strftime(
                "Chat_%d-%m-%Y_%H-%M-%S"
            )
            st.rerun()

    with c_act2:
        if st.session_state.messages:
            chat_text = generate_chat_text(st.session_state.messages)
            st.download_button(
                label="📥 Download Chat",
                data=chat_text,
                file_name=f"FemCare_Chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
            )

    st.divider()

    # Chat Input Box
    question = st.chat_input("Ask anything about menstrual health...")

    if question:
        st.session_state.messages.append({"role": "user", "content": question})

        with st.spinner("Analyzing and retrieving context..."):
            result = respond_to_question(question)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": result["answer"],
                "context": result["context"],
                "assessment": result["assessment"],
                "sources": [
                    {"name": document.get("source", "unknown source"),
                     "text": document.get("text", "")}
                    for document in result["documents"]
                ],
            }
        )
        save_chat(
            st.session_state.messages, st.session_state.conversation_id
        )
        st.rerun()

    # Display Chat History Messages
    for msg in st.session_state.messages:
        avatar = "👤" if msg["role"] == "user" else "🌸"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                assessment = msg.get("assessment")
                if assessment:
                    if any(
                        [
                            assessment["pain"],
                            assessment["stress"],
                            assessment["sleep"],
                            assessment["flow"],
                            assessment["pcos"],
                            assessment.get("urgency") != "none",
                        ]
                    ):
                        st.divider()
                        st.markdown("### 📋 Reported Symptoms and Safety Check")

                        mc1, mc2, mc3, mc4, mc5, mc6 = st.columns(6)

                        with mc1:
                            val = assessment["pain"] or "N/A"
                            st.markdown(
                                f"""<div class="metric-card">
                                    <div class="metric-card-label">Pain</div>
                                    <div class="metric-card-value">{val}</div>
                                </div>""",
                                unsafe_allow_html=True,
                            )

                        with mc2:
                            val = assessment["stress"] or "N/A"
                            st.markdown(
                                f"""<div class="metric-card">
                                    <div class="metric-card-label">Stress</div>
                                    <div class="metric-card-value">{val}</div>
                                </div>""",
                                unsafe_allow_html=True,
                            )

                        with mc3:
                            val = assessment["sleep"] or "N/A"
                            st.markdown(
                                f"""<div class="metric-card">
                                    <div class="metric-card-label">Sleep</div>
                                    <div class="metric-card-value">{val}</div>
                                </div>""",
                                unsafe_allow_html=True,
                            )

                        with mc4:
                            val = assessment["flow"] or "N/A"
                            st.markdown(
                                f"""<div class="metric-card">
                                    <div class="metric-card-label">Flow</div>
                                    <div class="metric-card-value">{val}</div>
                                </div>""",
                                unsafe_allow_html=True,
                            )

                        with mc5:
                            val = "Reported" if assessment["pcos"] else "Not reported"
                            st.markdown(
                                f"""<div class="metric-card">
                                    <div class="metric-card-label">PCOS</div>
                                    <div class="metric-card-value">{val}</div>
                                </div>""",
                                unsafe_allow_html=True,
                            )

                        with mc6:
                            val = str(assessment["risk"])
                            st.markdown(
                                f"""<div class="metric-card" style="border-color: #fbb6ce;">
                                    <div class="metric-card-label">Safety check</div>
                                    <div class="metric-card-value" style="color: #e53e3e;">{val}</div>
                                </div>""",
                                unsafe_allow_html=True,
                            )

                if msg.get("context"):
                    with st.expander("📚 Sources and evidence used"):
                        sources = msg.get("sources", [])
                        if sources:
                            for source in sources:
                                st.markdown(f"**{source['name']}**")
                                st.markdown(source["text"])
                        else:
                            st.markdown(msg["context"])


# --- PAGE 2: HISTORY ---
elif page == "🕒 History":
    st.title("🕒 Conversation History")
    st.caption("Review, edit, or delete past session transcripts.")
    st.divider()

    history = get_history()

    if not history:
        st.info("No saved conversations found.")
    else:
        chat_map = {}
        for file in history:
            info = get_chat_info(file)
            display = f"{info['title']}    ({info['created_at']})"
            chat_map[display] = file

        selected_display = st.selectbox(
            "Select a conversation", list(chat_map.keys())
        )
        selected_file = chat_map[selected_display]
        info = get_chat_info(selected_file)

        st.markdown(f"## 📝 {info['title']}")
        st.caption(f"Created: {info['created_at']}")
        st.divider()

        # Action Buttons Layout
        col1, col2 = st.columns(2)
        with col1:
            new_title = st.text_input(
                "Rename Conversation", value=info["title"]
            )
            if st.button("💾 Save Title", use_container_width=True):
                rename_chat(selected_file, new_title)
                st.success("Conversation renamed.")
                st.rerun()

        with col2:
            st.write("")
            st.write("")
            if st.button(
                "🗑️ Delete Conversation",
                type="primary",
                use_container_width=True,
            ):
                delete_chat(selected_file)
                st.success("Conversation deleted.")
                st.rerun()

        st.divider()

        # Show Messages Transcript
        messages = load_chat(selected_file)
        for msg in messages:
            avatar = "👤" if msg["role"] == "user" else "🌸"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])


# --- PAGE 3: EDA & ANALYTICS ---

elif page == "📊 EDA & Analytics":

    render_analytics_dashboard(df)
    st.stop()

# --- PAGE 4: DATA FUSION  ---

elif page == "🔗 Data Fusion":

    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">🔗 FemCare Data Fusion</div>
            <p class="hero-subtitle">
                Integration of menstrual, demographic, public-health,
                environmental and nutritional data.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "External APIs are collected separately and stored locally. "
        "The application reads the processed datasets rather than repeatedly "
        "calling external services."
    )

    # FUSION PIPELINE

    st.subheader("🔄 Fusion Pipeline")

    pipeline = pd.DataFrame({
        "Stage": [
            "Base Menstrual Dataset",
            "Census ACS",
            "CDC PLACES",
            "Open-Meteo",
            "USDA FoodData Central",
            "OpenStreetMap / Overpass",
            "Final Fusion",
            "Final Cleaning",
        ],
        "Purpose": [
            "Primary menstrual-cycle records",
            "Population and demographic context",
            "Public-health indicators",
            "Weather and environmental context",
            "Nutrition reference data",
            "Healthcare accessibility reference",
            "Combine contextual features",
            "Prepare ML-ready dataset",
        ],
        "Status": [
            "✓ Complete",
            "✓ Complete",
            "✓ Complete",
            "✓ Complete",
            "✓ Complete",
            "✓ Implemented",
            "✓ Complete",
            "✓ Complete",
        ],
    })

    st.dataframe(
        pipeline,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # FINAL DATASET

    final_path = Path(
        "data/api_fusion/final/femcare_final_cleaned.csv"
    )

    if final_path.exists():

        @st.cache_data
        def load_final_fusion(path):
            return pd.read_csv(path)

        fusion_df = load_final_fusion(final_path)

        rows, cols = fusion_df.shape

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Final Records", f"{rows:,}")
        c2.metric("Final Features", cols)
        c3.metric("Users", f"{fusion_df['user_id'].nunique():,}")
        c4.metric("States", fusion_df["state"].nunique())

        st.divider()

        st.subheader("📊 Final Dataset Composition")

        category_counts = {
            "Menstrual / Clinical": 34,
            "Census ACS": 8,
            "CDC PLACES": 7,
            "Open-Meteo": 6,
        }

        fusion_summary = pd.DataFrame(
            {
                "Source": list(category_counts.keys()),
                "Features": list(category_counts.values()),
            }
        )

        st.bar_chart(
            fusion_summary.set_index("Source")
        )

        st.divider()

        st.subheader("👀 Final Fused Dataset Preview")

        st.dataframe(
            fusion_df.head(20),
            use_container_width=True,
            height=500,
        )

        st.download_button(
            "📥 Download Final Fused Dataset",
            data=fusion_df.to_csv(index=False).encode("utf-8"),
            file_name="femcare_final_cleaned.csv",
            mime="text/csv",
            use_container_width=True,
        )

    else:
        st.error(
            "Final fused dataset not found."
        )

# --- PAGE 5: COMPLETE DATASET ---

elif page == "🗃️ Complete Dataset":

    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">📋 Complete FemCare Dataset</div>
            <p class="hero-subtitle">
                Explore the cleaned and fully fused menstrual-health dataset.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    dataset_path = Path(
        "data/api_fusion/final/femcare_final_cleaned.csv"
    )

    if not dataset_path.exists():
        st.error(f"Dataset not found: {dataset_path}")
        st.stop()

    @st.cache_data
    def load_complete_dataset(path):
        return pd.read_csv(path)

    complete_df = load_complete_dataset(dataset_path)

    # OVERVIEW

    rows, cols = complete_df.shape
    users = complete_df["user_id"].nunique()
    states = complete_df["state"].nunique()
    missing = int(complete_df.isna().sum().sum())

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Records", f"{rows:,}")
    c2.metric("Users", f"{users:,}")
    c3.metric("States", states)
    c4.metric("Columns", cols)

    st.divider()

    # DATA QUALITY

    st.subheader("🔎 Data Quality")

    missing_df = (
        complete_df.isna()
        .sum()
        .reset_index()
    )

    missing_df.columns = ["Feature", "Missing"]

    missing_df["Percentage"] = (
        missing_df["Missing"] / len(complete_df) * 100
    ).round(2)

    missing_df = missing_df[
        missing_df["Missing"] > 0
    ].sort_values(
        "Missing",
        ascending=False
    )

    if missing_df.empty:
        st.success("✓ No missing values found.")
    else:
        st.dataframe(
            missing_df,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # FILTERS

    st.subheader("🔍 Explore Dataset")

    f1, f2, f3 = st.columns(3)

    with f1:
        state_options = ["All States"] + sorted(
            complete_df["state"].dropna().unique().tolist()
        )

        selected_state = st.selectbox(
            "State",
            state_options,
            key="dataset_state_filter",
        )

    with f2:
        selected_pain = st.selectbox(
            "Pain Level",
            ["All"] + list(range(1, 11)),
            key="dataset_pain_filter",
        )

    with f3:
        selected_pcos = st.selectbox(
            "PCOS Diagnosed",
            ["All", "Yes", "No"],
            key="dataset_pcos_filter",
        )

    filtered_df = complete_df.copy()

    if selected_state != "All States":
        filtered_df = filtered_df[
            filtered_df["state"] == selected_state
        ]

    if selected_pain != "All":
        filtered_df = filtered_df[
            filtered_df["pain_level"] == selected_pain
        ]

    if selected_pcos != "All":
        pcos_value = 1 if selected_pcos == "Yes" else 0

        filtered_df = filtered_df[
            filtered_df["pcos_diagnosed"] == pcos_value
        ]

    st.caption(
        f"Showing {len(filtered_df):,} of {len(complete_df):,} records."
    )

    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=600,
    )

    # DOWNLOAD

    st.divider()

    st.download_button(
        "📥 Download Complete Dataset",
        data=complete_df.to_csv(index=False).encode("utf-8"),
        file_name="femcare_final_cleaned.csv",
        mime="text/csv",
        use_container_width=True,
    )

# --- PAGE 6: MENOCARE ---

elif page == "🌙 MenoCare":

    render_menocare()
    st.stop()

# --- PAGE 7: HEALTHCARE FINDER ---

elif page == "🏥 Healthcare Finder":

    render_healthcare_finder()
    st.stop()


# --- PAGE 8: NUTRITION GUIDE ---

elif page == "🍎 Nutrition Guide":

    render_nutrition_guide()
    st.stop()


# --- PAGE 9: SETTINGS ---

elif page == "⚙️ Settings":

    render_settings()
    st.stop()


# --- PAGE 10: ABOUT ---

elif page == "ℹ️ About":

    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">🌸 About FemCare AI</div>
            <p class="hero-subtitle">
                AI-powered menstrual and menopause-transition support,
                analytics and contextual health information.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("🎯 Project Objective")

    st.write(
        """
        FemCare AI is an educational women's-health prototype. It combines
        menstrual-health information and analytics with MenoCare, a
        session-only menopause-transition symptom tracker. The tracker
        summarizes self-reported entries and does not diagnose or recommend
        treatment.
        """
    )

    st.divider()

    st.subheader("🧠 AI Architecture")

    architecture = pd.DataFrame({
        "Component": [
            "User Interface",
            "Intent Router",
            "Clinical Engine",
            "MenoCare Tracker",
            "RAG Retriever",
            "Embedding Model",
            "Vector Database",
            "LLM",
            "Analytics",
            "Data Fusion",
        ],
        "Technology": [
            "Streamlit",
            "Python",
            "Python",
            "Streamlit session state / Pandas",
            "LangChain / Retriever",
            "MiniLM",
            "FAISS",
            "Llama 3.2 via Ollama",
            "Pandas / Plotly",
            "Python / Pandas",
        ],
    })

    st.dataframe(
        architecture,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.subheader("📊 Data Sources")

    st.markdown(
        """
        - 🩸 Menstrual health dataset
        - 🏛️ Census ACS
        - 🏥 CDC PLACES
        - 🌦️ Open-Meteo
        - 🥗 USDA FoodData Central
        - 🗺️ OpenStreetMap / Overpass
        - 🌙 SWAN data-collection schedule (design reference only; no participant data is loaded)
        """
    )

    st.divider()

    st.subheader("⚠️ Important Disclaimer")

    st.warning(
        "FemCare AI is an educational and analytical system. "
        "It does not replace professional medical diagnosis, treatment "
        "or consultation with a qualified healthcare professional."
    )

    st.divider()

    st.subheader("🚀 Future Scope")

    st.markdown(
        """
        - Machine-learning based prediction
        - Private accounts and consent-based symptom history
        - Clinician-reviewed MenoCare questionnaires and reports
        - Multilingual support
        - Voice interaction
        - Healthcare appointment integration
        - Expanded healthcare accessibility data
        """
    )
