
import time
import streamlit as st

from rag.qa_chain import ask_food_question


st.set_page_config(
    page_title="Rasoi AI | Food Assistant",
    page_icon="🍲",
    layout="wide"
)


# ---------------- DESIGN ----------------

st.markdown("""
<style>
.stApp {
    background: #fffaf4;
}

.main .block-container {
    max-width: 1050px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.hero {
    background: linear-gradient(120deg, #7d241b, #c65a2e);
    padding: 35px;
    border-radius: 20px;
    color: white;
    margin-bottom: 25px;
}

.hero h1 {
    color: white;
    font-size: 38px;
}

.hero p {
    color: #fff0e5;
    font-size: 16px;
}

.answer-box {
    background: white;
    padding: 25px;
    border-radius: 16px;
    border: 1px solid #f0dfd1;
    margin-top: 20px;
}

.stButton button {
    background: #a83c27;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 10px 20px;
}

.stButton button:hover {
    background: #7d241b;
    color: white;
}
</style>
""", unsafe_allow_html=True)


# ---------------- SIDEBAR ----------------

with st.sidebar:

    st.markdown("## 🍲 Rasoi AI")

    st.write(
        "Your intelligent Indian food and nutrition assistant."
    )

    st.divider()

    st.markdown("### Knowledge Sources")

    st.write("📖 Indian Recipe PDF")
    st.write("📊 Food Nutrition Dataset")

    st.divider()

    st.markdown("### Technology")

    st.write("✨ Google Gemini")
    st.write("🔎 RAG Retrieval")
    st.write("🧠 FAISS")
    st.write("📚 Sentence Transformers")

    st.divider()

    st.caption(
        "Nutrition values are based on the available food dataset."
    )


# ---------------- HERO ----------------

st.markdown("""
<div class="hero">
    <h1>🍛 Discover the Taste of India</h1>
    <p>
        Ask about Indian recipes, ingredients, nutrition
        and seasonal food recommendations.
    </p>
</div>
""", unsafe_allow_html=True)


# ---------------- SUGGESTIONS ----------------

st.markdown("### What would you like to know?")

suggestions = [
    "How to prepare Rajma Masala?",
    "Suggest a healthy Indian breakfast.",
    "Which foods are suitable for rainy season?",
    "Show me high-protein vegetarian foods."
]

if "question_input" not in st.session_state:
    st.session_state.question_input = ""

columns = st.columns(2)

for index, suggestion in enumerate(suggestions):

    with columns[index % 2]:

        if st.button(
            suggestion,
            key=f"suggestion_{index}",
            use_container_width=True
        ):
            st.session_state.question_input = suggestion
            st.rerun()


# ---------------- QUESTION FORM ----------------

with st.form("food_question_form"):

    question = st.text_input(
        "Ask your food question",
        key="question_input",
        placeholder="Example: Tell me about Paneer Tikka and its nutrition"
    )

    submitted = st.form_submit_button(
        "✨ Get Food Recommendation",
        use_container_width=True
    )


# ---------------- ANSWER ----------------

if submitted:

    if not question.strip():

        st.warning("Please enter a food-related question.")

    else:

        start_time = time.perf_counter()

        with st.spinner(
            "🍲 Rasoi AI is preparing your answer..."
        ):

            result = ask_food_question(
                question,
                top_k=6
            )

        elapsed = time.perf_counter() - start_time

        st.markdown("### 🍽️ Your Food Answer")

        st.markdown(
            '<div class="answer-box">',
            unsafe_allow_html=True
        )

        st.markdown(
            result.get("answer", "No answer available.")
        )

        st.markdown("</div>", unsafe_allow_html=True)

        st.caption(
            f"Response time: {elapsed:.2f} seconds"
        )


# ---------------- FOOTER ----------------

st.divider()

st.markdown(
    "<center style='color:#98796a;'>"
    "Made with ❤️ for Indian food lovers | Rasoi AI"
    "</center>",
    unsafe_allow_html=True
)
