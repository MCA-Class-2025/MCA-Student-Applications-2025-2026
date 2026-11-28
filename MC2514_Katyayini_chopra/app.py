import os
import streamlit as st

from services.gemini_service import analyze_household_image
from services.fusion_service import build_fusion_data
from services.final_reasoning_service import generate_final_diagnosis
from services.tts_service import text_to_speech
from services.excel_service import create_excel_report


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="FixAI Maharashtra",
    page_icon="🔧",
    layout="wide"
)
if "final_result" not in st.session_state:
    st.session_state.final_result = None

if "fused_data" not in st.session_state:
    st.session_state.fused_data = None

if "diagnosed" not in st.session_state:
    st.session_state.diagnosed = False

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #fffaf2;
    }

    .block-container {
        padding-top: 1rem;
    }

    .main-title {
        font-size: 48px;
        font-weight: 800;
        color: white;
        background-color: #f28c28;
        padding: 18px 25px;
        border-radius: 0 0 18px 18px;
        margin-bottom: 0;
    }

    .subtitle {
        font-size: 20px;
        font-weight: 600;
        color: #008311;
        margin: 12px 0 28px;
    }

    .section-title {
        font-size: 25px;
        font-weight: 700;
        color: #aa6e00;
        margin: 24px 0 10px;
    }

    .diagnosis-hero {
        background: linear-gradient(135deg, #fff3df, #fffaf2);
        border-left: 7px solid #f28c28;
        border-radius: 15px;
        padding: 24px;
        margin: 12px 0 24px;
    }

    .diagnosis-hero-title {
        font-size: 30px;
        font-weight: 800;
        color: #873127;
    }

    .explanation-card {
        background: white;
        border: 2px solid #008311;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 18px;
    }

    .cause-card {
        background: #fff7e8;
        border-left: 5px solid #f28c28;
        border-radius: 10px;
        padding: 10px 15px;
        margin-bottom: 8px;
    }

    .environment-card {
        background: #edf8ee;
        border: 2px solid #008311;
        border-radius: 15px;
        padding: 18px;
        margin-bottom: 20px;
    }

    .action-card {
        background: #edf8ee;
        border-left: 6px solid #008311;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 20px;
    }

    .action-title {
        color: #008311;
        font-size: 20px;
        font-weight: 800;
        margin-bottom: 7px;
    }

    .professional-card {
        background: linear-gradient(135deg, #fff7e8, white);
        border: 2px solid #f28c28;
        border-radius: 18px;
        padding: 22px;
        margin-bottom: 20px;
    }

    .professional-name {
        font-size: 25px;
        font-weight: 800;
        color: #873127;
    }

    .safety-card {
        background: #fff0ed;
        border-left: 6px solid #873127;
        border-radius: 12px;
        padding: 16px;
        margin: 10px 0 22px;
    }

    .safety-title {
        color: #873127;
        font-size: 20px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .stButton > button {
        border-radius: 10px;
        font-weight: 700;
        border: 2px solid #f28c28;
        background-color: #fff7e8;
        color: #873127;
    }

    .stButton > button:hover {
        background-color: #f28c28;
        color: white;
    }

    .stButton > button[kind="primary"] {
        background-color: #f28c28;
        color: white;
        border: none;
        font-weight: 800;
    }

    .stButton > button[kind="primary"]:hover {
        background-color: #d96f10;
        color: white;
    }

    .stTextInput input,
    .stTextArea textarea {
        border-radius: 10px;
        border: 1.5px solid #f28c28;
        background-color: white;
        color: #333333;
    }

    [data-testid="stFileUploader"] {
        border: 2px dashed #f28c28;
        border-radius: 15px;
        padding: 10px;
        background-color: #fff7e8;
    }

    [data-testid="stMetric"] {
        background-color: white;
        border: 2px solid #f28c28;
        border-radius: 14px;
        padding: 14px;
    }

    [data-testid="stMetricLabel"] {
        color: #873127 !important;
    }

    [data-testid="stMetricValue"] {
        color: #008311 !important;
    }

    [data-testid="stChatInput"] {
        border: 2px solid #008311;
        border-radius: 15px;
    }

    .stDownloadButton > button {
        background-color: #008311;
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 700;
    }

    .stDownloadButton > button:hover {
        background-color: #006b0e;
        color: white;
    }

    h1, h2, h3 {
        color: #873127 !important;
    }

    p {
        color: #333333;
    }

    hr {
        border-color: #f28c28;
        opacity: 0.4;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "diagnosed": False,
    "fused_data": None,
    "final_result": None,
    "chat_history": [],
    "description": "",
    "location": ""
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# LOCATIONS
# =========================================================

LOCATIONS = [
    "Andheri, Mumbai, Maharashtra",
    "Borivali, Mumbai, Maharashtra",
    "Dadar, Mumbai, Maharashtra",
    "Bandra, Mumbai, Maharashtra",
    "Powai, Mumbai, Maharashtra",
    "Malad, Mumbai, Maharashtra",
    "Goregaon, Mumbai, Maharashtra",
    "Kandivali, Mumbai, Maharashtra",
    "Kurla, Mumbai, Maharashtra",
    "Vikhroli, Mumbai, Maharashtra",
    "Mulund, Mumbai, Maharashtra",
    "Chembur, Mumbai, Maharashtra",
    "Worli, Mumbai, Maharashtra",
    "Santacruz, Mumbai, Maharashtra",
    "Vile Parle, Mumbai, Maharashtra",

    "Thane West, Thane, Maharashtra",
    "Thane East, Thane, Maharashtra",
    "Ghodbunder, Thane, Maharashtra",
    "Majiwada, Thane, Maharashtra",
    "Kalyan, Thane, Maharashtra",
    "Dombivli, Thane, Maharashtra",

    "Vashi, Navi Mumbai, Maharashtra",
    "Nerul, Navi Mumbai, Maharashtra",
    "Belapur, Navi Mumbai, Maharashtra",
    "Kharghar, Navi Mumbai, Maharashtra",
    "Airoli, Navi Mumbai, Maharashtra",
    "Panvel, Navi Mumbai, Maharashtra",

    "Kothrud, Pune, Maharashtra",
    "Baner, Pune, Maharashtra",
    "Hinjewadi, Pune, Maharashtra",
    "Wakad, Pune, Maharashtra",
    "Viman Nagar, Pune, Maharashtra",
    "Hadapsar, Pune, Maharashtra",
    "Kharadi, Pune, Maharashtra",
    "Shivajinagar, Pune, Maharashtra",

    "Dharampeth, Nagpur, Maharashtra",
    "Sadar, Nagpur, Maharashtra",
    "Manish Nagar, Nagpur, Maharashtra",
    "Wardhaman Nagar, Nagpur, Maharashtra",
    "Hingna, Nagpur, Maharashtra",
    "Pratap Nagar, Nagpur, Maharashtra",

    "College Road, Nashik, Maharashtra",
    "Gangapur Road, Nashik, Maharashtra",
    "Indira Nagar, Nashik, Maharashtra",
    "Panchavati, Nashik, Maharashtra",
    "CIDCO, Nashik, Maharashtra",
    "Nashik Road, Nashik, Maharashtra",

    "CIDCO, Chhatrapati Sambhajinagar, Maharashtra",
    "Garkheda, Chhatrapati Sambhajinagar, Maharashtra",
    "Waluj, Chhatrapati Sambhajinagar, Maharashtra",
    "Satara Parisar, Chhatrapati Sambhajinagar, Maharashtra",

    "Vasai, Vasai-Virar, Maharashtra",
    "Nalasopara, Vasai-Virar, Maharashtra",
    "Virar, Vasai-Virar, Maharashtra",
    "Naigaon, Vasai-Virar, Maharashtra",

    "Mira Road, Mira-Bhayandar, Maharashtra",
    "Bhayandar, Mira-Bhayandar, Maharashtra",
    "Beverly Park, Mira-Bhayandar, Maharashtra",
    "Shanti Nagar, Mira-Bhayandar, Maharashtra"
]


# =========================================================
# HELPERS
# =========================================================

def reset_app():
    st.session_state.diagnosed = False
    st.session_state.fused_data = None
    st.session_state.final_result = None
    st.session_state.chat_history = []
    st.session_state.description = ""
    st.session_state.location = ""


def format_confidence(value):
    try:
        value = float(value)

        if value <= 1:
            value *= 100

        return f"{value:.0f}%"

    except (TypeError, ValueError):
        return str(value)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🔧 FixAI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AI-powered household problem diagnosis for Maharashtra'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# INPUT PAGE
# =========================================================

if not st.session_state.diagnosed:

    st.markdown(
        '<div class="section-title">'
        '📷 Show FixAI the problem'
        '</div>',
        unsafe_allow_html=True
    )

    uploaded_file = st.file_uploader(
        "Upload a photo of the household problem",
        type=["jpg", "jpeg", "png", "webp"]
    )

    if uploaded_file:
        st.image(
            uploaded_file,
            caption="Uploaded problem",
            width=500
        )

    st.markdown(
        '<div class="section-title">'
        '📝 Tell us what you are experiencing'
        '</div>',
        unsafe_allow_html=True
    )

    description = st.text_area(
        "Problem description",
        placeholder=(
            "Example: Water starts leaking from this wall "
            "whenever it rains and the paint has started peeling."
        ),
        height=120
    )

    st.markdown(
        '<div class="section-title">'
        '📍 Where is the problem?'
        '</div>',
        unsafe_allow_html=True
    )

    location = st.selectbox(
        "Select your location",
        LOCATIONS,
        help="Select the area where the problem is located."
    )

    st.caption(
        "Location is used to retrieve environmental conditions "
        "and nearby professionals."
    )

    diagnose_button = st.button(
        "🔍 Diagnose My Problem",
        type="primary",
        use_container_width=True
    )

    # =====================================================
    # DIAGNOSIS
    # =====================================================

    if diagnose_button:

        if not uploaded_file:
            st.error(
                "Please upload an image first."
            )
            st.stop()

        # -------------------------------------------------
        # SAVE IMAGE
        # -------------------------------------------------

        os.makedirs(
            "test_images",
            exist_ok=True
        )

        image_path = os.path.join(
            "test_images",
            uploaded_file.name
        )

        with open(
            image_path,
            "wb"
        ) as file:

            file.write(
                uploaded_file.getbuffer()
            )

        # -------------------------------------------------
        # GEMINI IMAGE ANALYSIS
        # -------------------------------------------------

        with st.spinner(
            "🤖 Gemini is examining the image..."
        ):

            try:

                image_analysis = analyze_household_image(
                    image_path,
                    description=description
                )

            except TypeError:

                image_analysis = analyze_household_image(
                    image_path
                )

            except Exception as exc:

                st.error(
                    f"Gemini analysis failed: {exc}"
                )

                st.stop()

        # -------------------------------------------------
        # LIVE DATA FUSION
        # -------------------------------------------------

        with st.spinner(
            "🔗 Fusing environmental and defect data..."
        ):

            try:

                fused_data = build_fusion_data(
                    image_analysis,
                    location
                )

            except Exception as exc:

                st.error(
                    f"Data fusion failed: {exc}"
                )

                st.stop()

        # -------------------------------------------------
        # FINAL REASONING
        # -------------------------------------------------

        with st.spinner(
            "🧠 Generating final diagnosis..."
        ):

            try:

                final_result = generate_final_diagnosis(
                    fused_data
                )

            except Exception as exc:

                st.error(
                    f"Final reasoning failed: {exc}"
                )

                st.stop()


        # -------------------------------------------------
        # SAVE RESULTS
        # -------------------------------------------------

        st.session_state.fused_data = fused_data

        st.session_state.final_result = final_result

        st.session_state.description = description

        st.session_state.location = location

        st.session_state.chat_history = []

        st.session_state.diagnosed = True

        st.rerun()




# =========================================================
# RESULTS PAGE
# =========================================================

if st.session_state.diagnosed:

    # IMPORTANT:
    # These variables exist only inside the results page.

    final_result = (
        st.session_state.final_result or {}
    )

    fused_data = (
        st.session_state.fused_data or {}
    )

    # =====================================================
    # BACK BUTTON
    # =====================================================

    if st.button(
        "← Diagnose another problem"
    ):

        reset_app()
        st.rerun()

    st.divider()

    # =====================================================
    # DIAGNOSIS HEADER
    # =====================================================

    st.markdown(
        """
        <div class="diagnosis-hero">
            <div class="diagnosis-hero-title">
                🔍 FixAI Diagnosis
            </div>
            <div>
                Here is what FixAI found from your image,
                description and environmental conditions.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # =====================================================
    # METRICS
    # =====================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "🔧 Issue",
            final_result.get(
                "issue",
                "Unknown"
            )
        )

    with col2:

        st.metric(
            "⚠️ Severity",
            final_result.get(
                "severity",
                "Unknown"
            )
        )

    with col3:

        st.metric(
            "🎯 Confidence",
            format_confidence(
                final_result.get(
                    "confidence",
                    0
                )
            )
        )

    # =====================================================
    # WHAT IS HAPPENING
    # =====================================================

    st.markdown(
        '<div class="section-title">'
        '🧠 What is happening?'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="explanation-card">'
        + str(
            final_result.get(
                "explanation",
                ""
            )
        )
        + '</div>',
        unsafe_allow_html=True
    )

    # =====================================================
    # POSSIBLE CAUSES
    # =====================================================

    st.markdown(
        '<div class="section-title">'
        '⚠️ Possible Causes'
        '</div>',
        unsafe_allow_html=True
    )

    causes = final_result.get(
        "likely_causes",
        []
    )

    if causes:

        for cause in causes:

            st.markdown(
                f'<div class="cause-card">'
                f'🔸 {cause}'
                f'</div>',
                unsafe_allow_html=True
            )

    else:

        st.write(
            "No specific causes were identified."
        )

    # =====================================================
    # ENVIRONMENT
    # =====================================================

    st.markdown(
        '<div class="section-title">'
        '🌦 Environmental Conditions'
        '</div>',
        unsafe_allow_html=True
    )

    weather = fused_data.get(
        "weather",
        {}
    )

    air_quality = fused_data.get(
        "air_quality",
        {}
    )

    st.markdown(
        '<div class="environment-card">',
        unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "🌡 Temperature",
            f"{weather.get('temperature', 'N/A')} °C"
        )

    with c2:

        st.metric(
            "💧 Humidity",
            f"{weather.get('humidity', 'N/A')}%"
        )

    with c3:

        st.metric(
            "🌫 PM2.5",
            air_quality.get(
                "pm2_5",
                "N/A"
            )
        )

    with c4:

        st.metric(
            "🌍 AQI",
            air_quality.get(
                "us_aqi",
                "N/A"
            )
        )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    # =====================================================
    # RECOMMENDED ACTION
    # =====================================================

    st.markdown(
        '<div class="section-title">'
        '🔧 Recommended Action'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="action-card">'
        '<div class="action-title">'
        '✅ What you should do'
        '</div>'
        + str(
            final_result.get(
                "recommended_action",
                ""
            )
        )
        + '</div>',
        unsafe_allow_html=True
    )

    # =====================================================
    # PROFESSIONAL
    # =====================================================

    st.markdown(
        '<div class="section-title">'
        '👷 Recommended Professional'
        '</div>',
        unsafe_allow_html=True
    )

    professional = final_result.get(
        "professional"
    )

    if isinstance(
        professional,
        list
    ):

        professional = (
            professional[0]
            if professional
            else None
        )

    if professional:

        st.markdown(
            '<div class="professional-card">',
            unsafe_allow_html=True
        )

        c1, c2 = st.columns(2)

        with c1:

            st.markdown(
                '<div class="professional-name">'
                + str(
                    professional.get(
                        "name",
                        "Unknown"
                    )
                )
                + '</div>',
                unsafe_allow_html=True
            )

            st.write(
                "🔧 "
                + str(
                    professional.get(
                        "service_type",
                        "N/A"
                    )
                )
            )

            st.write(
                "📍 "
                + str(
                    professional.get(
                        "area",
                        "N/A"
                    )
                )
                + ", "
                + str(
                    professional.get(
                        "city",
                        "N/A"
                    )
                )
            )

            st.write(
                "📞 "
                + str(
                    professional.get(
                        "phone",
                        "N/A"
                    )
                )
            )

        with c2:

            st.write(
                "⭐ Rating: "
                + str(
                    professional.get(
                        "rating",
                        "N/A"
                    )
                )
            )

            st.write(
                "🛠 Experience: "
                + str(
                    professional.get(
                        "experience",
                        "N/A"
                    )
                )
                + " years"
            )

            st.write(
                "💰 Price: ₹"
                + str(
                    professional.get(
                        "price_range",
                        "N/A"
                    )
                )
            )

            distance = professional.get(
                "distance_km"
            )

            if distance is not None:

                try:

                    st.write(
                        f"📏 Distance: "
                        f"{float(distance):.2f} km"
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    pass

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    else:

        st.warning(
            "No suitable local professional was found."
        )

    # =====================================================
    # SAFETY WARNING
    # =====================================================

    st.markdown(
        '<div class="section-title">'
        '⚠️ Safety Warning'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="safety-card">'
        '<div class="safety-title">'
        '⚠️ Important'
        '</div>'
        + str(
            final_result.get(
                "warning",
                "Professional inspection may be required."
            )
        )
        + '</div>',
        unsafe_allow_html=True
    )

    # =====================================================
    # KNOWLEDGE SOURCES
    # =====================================================

    fused_knowledge_count = final_result.get(
        "_fused_knowledge_records",
        0
    )

    with st.expander(
        "🧠 How FixAI reached this result"
    ):

        st.write(
            "FixAI combines multiple knowledge and "
            "API sources to generate the diagnosis."
        )

        st.success(
            "✓ Gemini image analysis"
        )

        st.success(
            "✓ Original building-defect knowledge"
        )

        if fused_knowledge_count > 0:

            st.success(
                f"✓ Phase-1 fused dataset "
                f"({fused_knowledge_count} relevant records used)"
            )

        else:

            st.info(
                "Phase-1 fused dataset: "
                "no directly relevant records retrieved."
            )

        if weather:

            st.success(
                "✓ Current weather information"
            )

        if air_quality:

            st.success(
                "✓ Current air-quality information"
            )

        if fused_data.get(
            "local_services"
        ):

            st.success(
                "✓ Local professional REST API"
            )

    # =====================================================
    # CHATBOT
    # =====================================================

    st.divider()

    st.markdown(
        '<div class="section-title">'
        '💬 Ask FixAI'
        '</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Have questions about your diagnosis? "
        "Keep talking to FixAI using the information "
        "it has already analyzed."
    )

    q1, q2, q3, q4 = st.columns(4)

    if q1.button(
        "⚠️ Is it dangerous?",
        use_container_width=True
    ):

        st.session_state.chat_question = (
            "Is this problem dangerous right now?"
        )

    if q2.button(
        "💰 How much could it cost?",
        use_container_width=True
    ):

        st.session_state.chat_question = (
            "How much could repairing this problem cost?"
        )

    if q3.button(
        "🛠 Can I fix it myself?",
        use_container_width=True
    ):

        st.session_state.chat_question = (
            "Can I temporarily fix this myself?"
        )

    if q4.button(
        "🌧 Will rain make it worse?",
        use_container_width=True
    ):

        st.session_state.chat_question = (
            "Will rain and humidity make this problem worse?"
        )

    question = st.chat_input(
        "Ask FixAI anything about your problem..."
    )

    if "chat_question" in st.session_state:

        question = st.session_state.pop(
            "chat_question"
        )

    if question:

        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": question
            }
        )

        with st.spinner(
            "🤖 FixAI is thinking..."
        ):

            try:

                from services.chat_service import (
                    ask_fixai
                )

                answer = ask_fixai(
                    question=question,
                    fused_data=fused_data,
                    final_result=final_result,
                    chat_history=st.session_state.chat_history
                )

            except Exception as exc:

                answer = (
                    f"Unable to generate a response: {exc}"
                )

        st.session_state.chat_history.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

    for message in st.session_state.chat_history:

        with st.chat_message(
            message["role"]
        ):

            st.write(
                message["content"]
            )

    # =====================================================
    # VOICE
    # =====================================================

    st.divider()

    st.markdown(
        '<div class="section-title">'
        '🔊 Listen to your diagnosis'
        '</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "🔊 Generate Voice Diagnosis",
        use_container_width=True
    ):

        speech_text = f"""
FixAI diagnosis.

The identified issue is
{final_result.get('issue', '')}.

The severity is
{final_result.get('severity', '')}.

The recommended action is:
{final_result.get('recommended_action', '')}.

{final_result.get('explanation', '')}
"""

        with st.spinner(
            "Generating voice..."
        ):

            try:

                audio_path = text_to_speech(
                    speech_text
                )

                with open(
                    audio_path,
                    "rb"
                ) as audio_file:

                    st.audio(
                        audio_file.read(),
                        format="audio/mp3"
                    )

            except Exception as exc:

                st.error(
                    f"Voice generation failed: {exc}"
                )

    # =====================================================
    # EXCEL REPORT
    # =====================================================

    st.divider()

    st.markdown(
        '<div class="section-title">'
        '📊 Diagnosis Report'
        '</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Download the diagnosis and fused information "
        "as an Excel report."
    )

    if st.button(
        "📊 Generate Excel Report",
        use_container_width=True
    ):

        with st.spinner(
            "Creating report..."
        ):

            try:

                excel_path = create_excel_report(
                    fused_data,
                    final_result
                )

                with open(
                    excel_path,
                    "rb"
                ) as file:

                    st.download_button(
                        "⬇️ Download FixAI Report",
                        data=file,
                        file_name="FixAI_Report.xlsx",
                        mime=(
                            "application/vnd.openxmlformats-officedocument"
                            ".spreadsheetml.sheet"
                        ),
                        use_container_width=True
                    )

            except Exception as exc:

                st.error(
                    f"Excel generation failed: {exc}"
                )