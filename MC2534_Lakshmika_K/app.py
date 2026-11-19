import streamlit as st
from llm.rag_chat import generate_answer
from predict_waste import predict_waste


def render_html(content):
    """Render multiline HTML as real HTML, not a Markdown code block."""
    cleaned = "\n".join(line.strip() for line in content.strip().splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="EcoMind AI | Smart Waste Assistant",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Main background */
.stApp {
    background:
        radial-gradient(circle at 10% 10%, rgba(20, 184, 166, 0.12), transparent 25%),
        radial-gradient(circle at 90% 15%, rgba(34, 197, 94, 0.10), transparent 25%),
        linear-gradient(135deg, #071512 0%, #0a211c 45%, #06110e 100%);
    color: #ecfdf5;
}

/* Hide Streamlit default */
#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    visibility: hidden;
}

/* Main content */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1450px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #071512, #0b1f1a);
    border-right: 1px solid rgba(255,255,255,0.08);
}

section[data-testid="stSidebar"] * {
    color: #eafff7 !important;
}

/* Hero */
.hero {
    padding: 35px 40px;
    border-radius: 28px;
    background:
        linear-gradient(135deg,
        rgba(16,185,129,0.20),
        rgba(6,78,59,0.35));
    border: 1px solid rgba(52,211,153,0.22);
    box-shadow: 0 20px 60px rgba(0,0,0,0.25);
    margin-bottom: 25px;
}

.hero-badge {
    display: inline-block;
    padding: 7px 14px;
    border-radius: 999px;
    background: rgba(52,211,153,0.13);
    border: 1px solid rgba(52,211,153,0.25);
    color: #6ee7b7;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

.hero-title {
    font-size: 46px;
    font-weight: 800;
    line-height: 1.1;
    margin-top: 18px;
    margin-bottom: 12px;
    color: #f0fdf4;
}

.hero-title span {
    color: #34d399;
}

.hero-subtitle {
    color: #a7c7bc;
    font-size: 16px;
    line-height: 1.7;
    max-width: 850px;
}

/* Cards */
.card {
    background: rgba(10, 31, 26, 0.78);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 22px;
    height: 100%;
    box-shadow: 0 10px 35px rgba(0,0,0,0.18);
}

.card:hover {
    border-color: rgba(52,211,153,0.25);
}

.card-title {
    font-size: 15px;
    color: #9fbdb2;
    margin-bottom: 8px;
}

.card-value {
    font-size: 30px;
    font-weight: 800;
    color: #f0fdf4;
}

.card-small {
    color: #6ee7b7;
    font-size: 12px;
    margin-top: 5px;
}

/* Section titles */
.section-title {
    font-size: 25px;
    font-weight: 800;
    color: #ecfdf5;
    margin-top: 35px;
    margin-bottom: 15px;
}

/* Assistant */
.assistant-box {
    background: linear-gradient(
        145deg,
        rgba(6,78,59,0.48),
        rgba(10,31,26,0.80)
    );
    border: 1px solid rgba(52,211,153,0.18);
    border-radius: 24px;
    padding: 25px;
    margin-top: 10px;
}

.answer-box {
    background: rgba(3, 20, 16, 0.85);
    border-left: 4px solid #34d399;
    border-radius: 14px;
    padding: 22px;
    color: #d9fbe9;
    line-height: 1.75;
}

/* Category cards */
.category {
    text-align: center;
    padding: 20px 10px;
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 18px;
}

.category-icon {
    font-size: 34px;
}

.category-name {
    margin-top: 8px;
    font-weight: 700;
    color: #ecfdf5;
}

.category-desc {
    color: #8eaaa1;
    font-size: 12px;
    margin-top: 4px;
}

/* Status */
.status {
    display: flex;
    align-items: center;
    gap: 9px;
    margin: 10px 0;
    color: #cde9df;
}

.dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #34d399;
    display: inline-block;
    box-shadow: 0 0 10px rgba(52,211,153,0.8);
}

.dot-yellow {
    background: #fbbf24;
    box-shadow: 0 0 10px rgba(251,191,36,0.7);
}

/* Buttons */
.stButton > button {
    border-radius: 13px;
    border: 1px solid rgba(52,211,153,0.35);
    background: linear-gradient(135deg, #059669, #10b981);
    color: white;
    font-weight: 700;
    padding: 11px 20px;
    transition: 0.2s;
}

.stButton > button:hover {
    border-color: #6ee7b7;
    transform: translateY(-1px);
}

/* Text area */
textarea {
    background-color: rgba(3,20,16,0.85) !important;
    color: #ecfdf5 !important;
    border: 1px solid rgba(52,211,153,0.20) !important;
    border-radius: 15px !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: rgba(255,255,255,0.035);
    border-radius: 12px;
}

/* Footer */
.footer {
    text-align: center;
    margin-top: 50px;
    padding: 20px;
    color: #6f8d83;
    font-size: 12px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    render_html("""
        <div style="text-align:center; padding:15px 0 25px;">
            <div style="font-size:55px;">♻️</div>
            <h2 style="margin:5px 0;">EcoMind AI</h2>
            <p style="color:#86a99d;">Smart Waste Intelligence</p>
        </div>
        """)

    st.markdown("### 🧠 System Status")

    render_html('<div class="status"><span class="dot"></span> RAG Knowledge Base Ready</div>')

    render_html('<div class="status"><span class="dot"></span> FAISS Vector Search Ready</div>')

    render_html('<div class="status"><span class="dot"></span> Gemini LLM Connected</div>')

    render_html('<div class="status"><span class="dot-yellow"></span> API Fusion — Coming Next</div>')

    st.divider()

    st.markdown("### 📊 Knowledge Base")

    st.metric(
        "Knowledge Records",
        "26,183"
    )

    st.caption(
        "3 Kaggle datasets processed using RAG"
    )

    st.divider()

    st.markdown("""
    **Technology Stack**

    🧠 Gemini LLM  
    🔎 RAG  
    📚 FAISS  
    🔢 Sentence Transformers  
    🐍 Python  
    🎨 Streamlit  
    📊 Kaggle Datasets
    """)


# =========================================================
# HERO SECTION
# =========================================================

render_html("""
<div class="hero">

        <div class="hero-badge">
            ✦ AI-POWERED WASTE MANAGEMENT
        </div>

        <div class="hero-title">
            Smarter Waste Decisions.<br>
            <span>Cleaner Cities.</span>
        </div>

        <div class="hero-subtitle">
            An intelligent waste-management assistant powered by
            Retrieval-Augmented Generation. Ask questions about
            waste segregation, recycling, disposal and collection
            using knowledge retrieved from real waste-management datasets.
        </div>

    </div>
    """)
# =========================================================
# AI WASTE SCANNER
# =========================================================

render_html('<div class="section-title">📷 AI Waste Scanner</div>')

render_html("""
    <div class="assistant-box">

    <b style="font-size:20px;">
        Identify your waste with AI
    </b>

    <p style="color:#91afa5;">
        Upload an image of your waste and our trained
        image-classification model will identify its category.
    </p>

    </div>
    """)

uploaded_image = st.file_uploader(
    "Upload Waste Image",
    type=["jpg", "jpeg", "png"],
    help="Upload a clear image of cardboard, glass, metal, paper, plastic or trash."
)

if uploaded_image is not None:

    col1, col2 = st.columns([1, 1])

    with col1:

        st.image(
            uploaded_image,
            caption="Uploaded Waste Image",
            use_container_width=True
        )

    with col2:

        if st.button(
            "🔍 Identify Waste",
            use_container_width=True
        ):

            with st.spinner(
                "AI is analyzing the waste image..."
            ):

                try:

                    predicted_class, confidence = predict_waste(
                        uploaded_image
                    )

                    st.session_state["detected_waste"] = predicted_class
                    st.session_state["confidence"] = confidence

                except Exception as e:

                    st.error(
                        f"Prediction error: {e}"
                    )


# Show prediction
if "detected_waste" in st.session_state:

    waste = st.session_state["detected_waste"]
    confidence = st.session_state["confidence"]

    render_html(f"""
        <div class="answer-box">

        <div style="font-size:14px;color:#8eaaa1;">
            AI DETECTION RESULT
        </div>

        <div style="
            font-size:32px;
            font-weight:800;
            margin-top:8px;
            color:#34d399;
        ">
            ♻️ {waste.upper()}
        </div>

        <div style="
            font-size:16px;
            margin-top:8px;
        ">
            Confidence: <b>{confidence:.2f}%</b>
        </div>

        </div>
        """)

    # Automatic recommendation
    recommendations = {
        "cardboard": "Flatten and send to paper/cardboard recycling.",
        "glass": "Keep glass separate and send it to a glass recycling facility.",
        "metal": "Separate metal items and send them for recycling.",
        "paper": "Keep paper dry and place it in paper recycling.",
        "plastic": "Separate recyclable plastic and send it to plastic recycling.",
        "trash": "Dispose of non-recyclable waste through the appropriate municipal collection system."
    }

    recommendation = recommendations.get(
        waste.lower(),
        "Follow the appropriate local waste-disposal guidelines."
    )

    render_html(f"""
        <div class="card" style="margin-top:15px;">

            <div class="card-title">
                💡 Recommended Action
            </div>

            <div style="
                font-size:16px;
                line-height:1.6;
                color:#d9fbe9;
            ">
                {recommendation}
            </div>

        </div>
        """)

# =========================================================
# STATS
# =========================================================

cols = st.columns(4)

stats = [
    ("26,183", "Knowledge Records", "RAG indexed"),
    ("3", "Kaggle Datasets", "Domain knowledge"),
    ("384", "Embedding Size", "Vector representation"),
    ("RAG", "AI Architecture", "Context-aware")
]

for col, (value, title, small) in zip(cols, stats):

    with col:

        render_html(f"""
            <div class="card">
                <div class="card-title">{title}</div>
                <div class="card-value">{value}</div>
                <div class="card-small">● {small}</div>
            </div>
            """)


# =========================================================
# ASSISTANT
# =========================================================

render_html('<div class="section-title">🤖 Ask the Waste Intelligence Assistant</div>')

render_html("""
    <div class="assistant-box">

    <b style="font-size:18px;">What would you like to know?</b>

    <p style="color:#91afa5;">
    Ask about recycling, waste generation, disposal methods,
    city-level waste management or environmental conditions.
    </p>

    </div>
    """)


# =========================================================
# SAMPLE QUESTIONS
# =========================================================

st.markdown("##### 💡 Try asking")

sample_questions = [
    "What is the recycling rate of plastic waste in Mumbai?",
    "What waste management information is available for Delhi?",
    "Which disposal methods are used for organic waste?",
    "How does recycling help in waste management?"
]

sample_cols = st.columns(2)

for i, question in enumerate(sample_questions):

    with sample_cols[i % 2]:

        if st.button(
            question,
            key=f"sample_{i}",
            use_container_width=True
        ):

            st.session_state["question"] = question


# =========================================================
# QUESTION INPUT
# =========================================================

question = st.text_area(
    "Your Question",
    value=st.session_state.get("question", ""),
    placeholder="Example: What is the recycling rate of plastic waste in Mumbai?",
    height=110
)


# =========================================================
# ASK BUTTON
# =========================================================

if st.button(
    "♻️ Generate Intelligent Recommendation",
    use_container_width=True
):

    if not question.strip():

        st.warning(
            "Please enter a waste-management question first."
        )

    else:

        with st.spinner(
            "🔎 Retrieving relevant knowledge and consulting the AI..."
        ):

            try:

                retrieved, answer = generate_answer(
                    question
                )

                # -----------------------------------------
                # ANSWER
                # -----------------------------------------

                render_html('<div class="section-title">🤖 AI Recommendation</div>')

                render_html(f"""
                    <div class="answer-box">
                    {answer}
                    </div>
                    """)

                # -----------------------------------------
                # RAG SOURCES
                # -----------------------------------------

                render_html('<div class="section-title">🔎 RAG Retrieved Knowledge</div>')

                st.caption(
                    "These records were retrieved from the project knowledge base "
                    "before generating the response."
                )

                for i, item in enumerate(
                    retrieved,
                    start=1
                ):

                    with st.expander(
                        f"Knowledge Source {i}  •  Similarity {item['score']:.4f}"
                    ):

                        st.code(
                            item["document"][:1800],
                            language="text"
                        )

            except Exception as e:

                st.error(
                    f"Unable to generate response: {e}"
                )


# =========================================================
# WASTE CATEGORIES
# =========================================================

render_html('<div class="section-title">🗑️ Waste Categories</div>')

categories = [
    ("🥬", "Organic", "Food & biodegradable waste"),
    ("♻️", "Plastic", "Recyclable plastic materials"),
    ("📦", "Paper", "Paper and cardboard waste"),
    ("🍾", "Glass", "Glass bottles and containers"),
    ("⚙️", "Metal", "Metal and recyclable scrap"),
    ("🔌", "E-Waste", "Electronic waste materials")
]

category_cols = st.columns(6)

for col, (icon, name, desc) in zip(
    category_cols,
    categories
):

    with col:

        render_html(f"""
            <div class="category">
                <div class="category-icon">{icon}</div>
                <div class="category-name">{name}</div>
                <div class="category-desc">{desc}</div>
            </div>
            """)


# =========================================================
# HOW SYSTEM WORKS
# =========================================================

render_html('<div class="section-title">⚡ How EcoMind AI Works</div>')

steps = st.columns(5)

workflow = [
    ("01", "User Query", "Question entered through the interface"),
    ("02", "Embedding", "Question converted into a vector"),
    ("03", "RAG Search", "Relevant dataset records retrieved"),
    ("04", "LLM", "Gemini understands the retrieved context"),
    ("05", "Answer", "Context-aware recommendation generated")
]

for col, (number, title, description) in zip(
    steps,
    workflow
):

    with col:

        render_html(f"""
            <div class="card">
                <div style="
                    color:#34d399;
                    font-size:13px;
                    font-weight:800;
                ">
                    STEP {number}
                </div>

                <div style="
                    font-size:18px;
                    font-weight:800;
                    margin-top:8px;
                ">
                    {title}
                </div>

                <div style="
                    color:#8eaaa1;
                    font-size:12px;
                    margin-top:8px;
                    line-height:1.5;
                ">
                    {description}
                </div>
            </div>
            """)


# =========================================================
# UPCOMING DATA FUSION
# =========================================================

render_html('<div class="section-title">🔌 Multi-Source Intelligence</div>')

api_cols = st.columns(5)

api_data = [
    ("🌦️", "Weather API", "Weather & rainfall"),
    ("📍", "Location API", "Address & coordinates"),
    ("🌫️", "Air Quality API", "AQI information"),
    ("🛣️", "Route API", "Distance & route"),
    ("👤", "User Data", "Waste reports")
]

for col, (icon, title, desc) in zip(
    api_cols,
    api_data
):

    with col:

        render_html(f"""
            <div class="card">
                <div style="font-size:30px;">{icon}</div>
                <div style="
                    font-weight:800;
                    margin-top:10px;
                ">
                    {title}
                </div>
                <div style="
                    color:#8eaaa1;
                    font-size:12px;
                    margin-top:5px;
                ">
                    {desc}
                </div>
                <div style="
                    color:#fbbf24;
                    font-size:11px;
                    margin-top:12px;
                ">
                    ● Integration Phase
                </div>
            </div>
            """)


# =========================================================
# FOOTER
# =========================================================

render_html("""
    <div class="footer">
        ♻️ <b>EcoMind AI</b> — Smart Waste Segregation & Collection Assistant
        <br><br>
        Powered by RAG • FAISS • Sentence Transformers • Gemini LLM
        <br>
        Multi-source Data Fusion & Real-Time APIs coming next
    </div>
    """)