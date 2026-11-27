import os
import streamlit as st

from rag import ask_question
from utils import text_to_speech

from components.sidebar import render_sidebar
from components.dashboard import render_dashboard
from components.chat import render_chat
from components.calculators import render_calculators
from components.project import render_project
from components.data_fusion import render_data_fusion

from database import initialize_database
from chat_history import save_chat_message


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Finance AI",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# INITIALIZE DATABASE
# ============================================================

initialize_database()


# ============================================================
# INITIALIZE CHAT HISTORY
# ============================================================

# The chat_history.py file will automatically create
# chat_history.csv when the first message is saved.


# ============================================================
# LOAD CSS
# ============================================================

def load_css(file_name):
    """Load custom CSS file."""

    if os.path.exists(file_name):

        with open(
            file_name,
            "r",
            encoding="utf-8"
        ) as file:

            css = file.read()

        st.markdown(
            f"<style>{css}</style>",
            unsafe_allow_html=True
        )


load_css("style.css")


# ============================================================
# SESSION STATE
# ============================================================

def initialize_session_state():
    """Initialize Streamlit session variables."""

    if "messages" not in st.session_state:

        st.session_state.messages = []

    if "suggested_question" not in st.session_state:

        st.session_state.suggested_question = None


initialize_session_state()


# ============================================================
# CHAT HISTORY WRAPPER
# ============================================================

def ask_question_with_history(question):
    """
    Call the existing ask_question() function and
    automatically save the conversation to CSV.

    This wrapper does NOT change the existing ask_question()
    function or its features.
    """

    # --------------------------------------------------------
    # CALL EXISTING FINANCE AI
    # --------------------------------------------------------

    answer, docs = ask_question(question)

    # --------------------------------------------------------
    # DETERMINE CHAT TYPE AND SOURCE
    # --------------------------------------------------------

    if docs:

        chat_type = "rag"
        source = "PDF / Uploaded Documents"

    else:

        chat_type = "general"
        source = "Finance AI"

    # --------------------------------------------------------
    # SAVE CHAT HISTORY
    # --------------------------------------------------------

    save_chat_message(
        user_message=question,
        assistant_message=answer,
        chat_type=chat_type,
        source=source
    )

    # --------------------------------------------------------
    # RETURN EXACT SAME FORMAT AS ask_question()
    # --------------------------------------------------------

    return answer, docs


# ============================================================
# SIDEBAR
# ============================================================

render_sidebar()


# ============================================================
# MAIN PAGE HEADER
# ============================================================

st.markdown(
    """
    <div class="main-title">
        💰 Finance AI
    </div>

    <div class="subtitle">
        Intelligent Personal Finance Assistant powered by
        RAG, LangChain, ChromaDB and Gemma 3
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# MAIN PAGE FINANCE CATEGORIES
# ============================================================

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.markdown(
        """
<div class="card">
<div class="card-title">💵</div>
<h4>Saving</h4>
<div class="card-text">Smart Saving Tips</div>
</div>
""",
        unsafe_allow_html=True
    )


with col2:

    st.markdown(
        """
<div class="card">
<div class="card-title">📊</div>
<h4>Budget</h4>
<div class="card-text">Budget Planning</div>
</div>
""",
        unsafe_allow_html=True
    )


with col3:

    st.markdown(
        """
<div class="card">
<div class="card-title">📈</div>
<h4>Investment</h4>
<div class="card-text">SIP & Mutual Funds</div>
</div>
""",
        unsafe_allow_html=True
    )


with col4:

    st.markdown(
        """
<div class="card">
<div class="card-title">🏦</div>
<h4>Banking</h4>
<div class="card-text">Financial Knowledge</div>
</div>
""",
        unsafe_allow_html=True
    )


st.divider()


# ============================================================
# MAIN NAVIGATION
# ============================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💬 Chat",
    "📊 Dashboard",
    "🧮 Finance Tools",
    "🔗 Data Fusion",
    "📘 Project"
])


# ============================================================
# TAB 1 - AI CHAT
# ============================================================

with tab1:

    render_chat(
        ask_question=ask_question_with_history,
        text_to_speech=text_to_speech
    )


# ============================================================
# TAB 2 - DASHBOARD
# ============================================================

with tab2:

    render_dashboard()


# ============================================================
# TAB 3 - FINANCE TOOLS
# ============================================================

with tab3:

    render_calculators(
        ask_question=ask_question
    )


# ============================================================
# TAB 4 - DATA FUSION
# ============================================================

with tab4:

    render_data_fusion()


# ============================================================
# TAB 5 - PROJECT
# ============================================================

with tab5:

    render_project()


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    """
<div class="footer">
<h4>💰 Finance AI</h4>
<p>Intelligent Personal Finance Assistant</p>
<p>Python • Streamlit • LangChain • ChromaDB • Ollama</p>
<strong>MCA Project</strong>
</div>
""",
    unsafe_allow_html=True
)