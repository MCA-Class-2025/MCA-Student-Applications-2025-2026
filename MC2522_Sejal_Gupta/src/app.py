
import io
import re
import json

import pandas as pd
import streamlit as st
from PIL import Image
from gtts import gTTS

from api.vision_api import detect_safe_search
from src.moderator import analyze_comment
from api.ocr_api import extract_text_from_image
from api.translation_api import translate_text


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Social Media Moderator",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #eef4ff, #dbeafe, #bfdbfe);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0B1120, #1E3A8A);
}

[data-testid="stSidebar"] * {
    color: white !important;
}

h1, h2, h3, h4, h5, h6 {
    color: #111827 !important;
    font-weight: 700;
}

p, label {
    color: #1F2937;
}

[data-testid="stMetric"] {
    background: rgba(255,255,255,0.85);
    padding: 18px;
    border-radius: 16px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.08);
}

[data-testid="stMetricValue"] {
    color: #111827 !important;
    font-size: 30px !important;
    font-weight: 700 !important;
}

textarea {
    background: white !important;
    color: #111827 !important;
    border-radius: 12px !important;
    border: 2px solid #2563EB !important;
    font-size: 16px !important;
}

[data-testid="stFileUploader"] {
    background: white;
    padding: 15px;
    border-radius: 15px;
    border: 2px dashed #2563EB;
}

.stButton > button {
    width: 100%;
    background: #2563EB;
    color: white;
    border: none;
    border-radius: 12px;
    padding: 12px;
    font-size: 16px;
    font-weight: 700;
}

.stButton > button:hover {
    background: #1D4ED8;
    color: white;
}

.card {
    background: white;
    padding: 20px;
    border-radius: 16px;
    margin-top: 12px;
    margin-bottom: 12px;
    box-shadow: 0 5px 18px rgba(0,0,0,0.08);
}

.success-card {
    background: #ecfdf5;
    border-left: 5px solid #10b981;
    padding: 16px;
    border-radius: 12px;
    margin: 10px 0;
}

.translation-card {
    background: #eff6ff;
    border-left: 5px solid #2563eb;
    padding: 16px;
    border-radius: 12px;
    margin: 10px 0;
}

.warning-card {
    background: #fff7ed;
    border-left: 5px solid #f97316;
    padding: 16px;
    border-radius: 12px;
    margin: 10px 0;
}

.vision-card {
    background: #f5f3ff;
    border-left: 5px solid #7c3aed;
    padding: 16px;
    border-radius: 12px;
    margin: 10px 0;
}

.footer {
    text-align: center;
    color: #374151;
    font-size: 14px;
    margin-top: 40px;
    padding-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# RESULT INTERPRETATION HELPERS
# ============================================================

def result_to_text(result):
    """Convert a model result into searchable text."""
    if result is None:
        return ""

    if isinstance(result, str):
        return result

    try:
        return json.dumps(result, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return str(result)


def get_toxicity_status(result):
    """
    Interpret recognizable labels from the existing result.
    This does not generate a model confidence score.
    """

    if result is None:
        return "Unknown"

    # Read common structured prediction fields when available.
    if isinstance(result, dict):
        for key in (
            "label",
            "status",
            "toxicity",
            "prediction",
            "classification"
        ):
            value = result.get(key)

            if isinstance(value, str):
                status = get_toxicity_status(value)
                if status != "Unknown":
                    return status

    text = result_to_text(result).lower()
    text = re.sub(r"[_-]+", " ", text)
    text = re.sub(r"\s+", " ", text)

    # Check safe phrases first.
    safe_phrases = [
        "non toxic",
        "not toxic",
        "safe content",
        "clean content",
        "no toxicity detected",
        "no toxic content",
        "status: safe",
        "status: clean"
    ]

    if any(phrase in text for phrase in safe_phrases):
        return "Non-Toxic"

    toxic_phrases = [
        "potentially toxic",
        "toxic content",
        "toxic comment",
        "toxicity detected",
        "status: toxic",
        "severe toxic",
        "severely toxic",
        "offensive content",
        "threat detected",
        "identity hate",
        "obscene content",
        "insult detected"
    ]

    if any(phrase in text for phrase in toxic_phrases):
        return "Toxic"

    return "Unknown"


def get_detected_categories(result):
    """
    Find category labels explicitly mentioned by the model.
    Missing categories are not assumed to be negative predictions.
    """

    text = result_to_text(result).lower()
    text = re.sub(r"[_-]+", " ", text)

    category_patterns = {
        "Toxic": [
            r"\btoxic\b",
            r"\btoxicity\b"
        ],
        "Severe Toxic": [
            r"\bsevere toxic\b",
            r"\bseverely toxic\b"
        ],
        "Obscene": [
            r"\bobscene\b",
            r"\bobscenity\b"
        ],
        "Threat": [
            r"\bthreat\b",
            r"\bthreatening\b"
        ],
        "Insult": [
            r"\binsult\b",
            r"\binsulting\b"
        ],
        "Identity Hate": [
            r"\bidentity hate\b"
        ],
        "Non-Toxic": [
            r"\bnon toxic\b",
            r"\bnot toxic\b",
            r"\bsafe content\b",
            r"\bclean content\b"
        ]
    }

    detected = []

    for category, patterns in category_patterns.items():
        if any(re.search(pattern, text) for pattern in patterns):
            detected.append(category)

    # Remove the general Toxic label when it appears only as part
    # of a more specific label such as "Severe Toxic".
    if "Severe Toxic" in detected:
        text_without_severe = re.sub(
            r"\bsevere(?:ly)?\s+toxic\b",
            "",
            text
        )

        if not re.search(r"\btoxic\b|\btoxicity\b", text_without_severe):
            detected.remove("Toxic")

    # A clearly safe result should not also be classified as Toxic
    # just because the word "toxic" appears in "non-toxic".
    status = get_toxicity_status(result)

    if status == "Non-Toxic":
        detected = [
            category for category in detected
            if category == "Non-Toxic"
        ]

    return detected


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "image_text": "",
    "translated_text": "",
    "analysis_result": None,
    "vision_result": None,
    "last_comment": "",
    "analysis_mode": "Not analyzed",
    "audio_bytes": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("🛡️ AI Moderator")
    st.success("✅ Application Ready")

    st.markdown("---")

    st.subheader("👩‍💻 Developer")
    st.write("Sejal Gupta")

    st.subheader("🎓 Course")
    st.write("MCA")

    st.subheader("🤖 AI Moderation")
    st.write("Hugging Face / Existing model")

    st.subheader("🌐 Translation")
    st.write("MyMemory API")

    st.subheader("📷 OCR")
    st.write("OCR API")

    st.subheader("🛡️ Image Safety")
    st.write("Google Vision SafeSearch")

    st.markdown("---")

    st.info(
        "Analyze social media comments and screenshots "
        "using AI-based moderation."
    )

    if st.button("🧹 Clear Current Results"):
        st.session_state.analysis_result = None
        st.session_state.last_comment = ""
        st.session_state.analysis_mode = "Not analyzed"
        st.session_state.audio_bytes = None
        st.session_state.translated_text = ""
        st.session_state.vision_result = None
        st.rerun()


# ============================================================
# HEADER
# ============================================================

st.markdown("""
<h1 style="text-align:center; font-size:42px;">
🛡️ AI Social Media Content Moderator
</h1>

<h3 style="text-align:center; color:#374151;">
AI-powered Toxic Comment Detection
</h3>

<p style="text-align:center; font-size:16px;">
Analyze social media comments and screenshots using OCR,
translation, image safety checks, and AI moderation.
</p>
""", unsafe_allow_html=True)

st.divider()


# ============================================================
# STATUS DASHBOARD
# ============================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🤖 AI Moderation", "Ready")

with col2:
    st.metric("📷 OCR", "Available")

with col3:
    st.metric("🛡️ Image Safety", "Available")

with col4:
    st.metric("📊 Analysis", st.session_state.analysis_mode)

st.divider()


# ============================================================
# IMAGE UPLOAD AND SAFETY CHECK
# ============================================================

st.subheader("📷 Upload Social Media Screenshot")

st.write(
    "Upload a screenshot containing social media comments. "
    "OCR will extract readable text and Google Vision will "
    "check the image for potentially unsafe visual content."
)

uploaded_file = st.file_uploader(
    "Choose an image",
    type=["png", "jpg", "jpeg"],
    help="Supported formats: PNG, JPG, JPEG"
)

image_comment = ""

if uploaded_file is not None:

    try:
        image = Image.open(uploaded_file)
        st.image(
            image,
            caption="Uploaded Screenshot",
            use_container_width=True
        )
    except Exception as image_error:
        st.error(f"Could not open image: {image_error}")

    # --------------------------------------------------------
    # GOOGLE VISION SAFESEARCH
    # --------------------------------------------------------

    if st.button("🛡️ Check Image Safety"):
        try:
            with st.spinner("Checking image safety..."):
                uploaded_file.seek(0)
                image_bytes = uploaded_file.getvalue()

                vision_response = detect_safe_search(image_bytes)
                st.session_state.vision_result = vision_response

            if vision_response.get("success"):
                safe = vision_response["result"]

                st.subheader("🛡️ Google Vision SafeSearch")

                v1, v2, v3 = st.columns(3)

                with v1:
                    st.write(f"🔞 **Adult:** {safe.get('adult', 'Unknown')}")
                    st.write(f"🩺 **Medical:** {safe.get('medical', 'Unknown')}")

                with v2:
                    st.write(f"⚠️ **Violence:** {safe.get('violence', 'Unknown')}")
                    st.write(f"🔥 **Racy:** {safe.get('racy', 'Unknown')}")

                with v3:
                    st.write(f"🎭 **Spoof:** {safe.get('spoof', 'Unknown')}")

                unsafe_levels = {"LIKELY", "VERY_LIKELY"}

                image_unsafe = any(
                    safe.get(category) in unsafe_levels
                    for category in ("adult", "violence", "racy")
                )

                if image_unsafe:
                    st.error("🚨 Potentially unsafe visual content detected.")
                else:
                    st.success("✅ No high-risk level detected in the checked categories.")

            else:
                st.error(
                    "Google Vision API error: "
                    + str(vision_response.get("error", "Unknown error"))
                )

        except Exception as vision_error:
            st.error(f"Image safety check failed: {vision_error}")

    # --------------------------------------------------------
    # OCR TEXT EXTRACTION
    # --------------------------------------------------------

    if st.button("🔍 Extract Text from Image"):
        try:
            with st.spinner("Extracting text using OCR..."):
                uploaded_file.seek(0)
                extracted_text = extract_text_from_image(uploaded_file)

            if extracted_text and extracted_text.strip():
                st.session_state.image_text = extracted_text.strip()
                st.success("Text extracted successfully!")
            else:
                st.session_state.image_text = ""
                st.warning("No readable text was found.")

        except Exception as ocr_error:
            st.error(f"OCR processing failed: {ocr_error}")

    if st.session_state.image_text:
        st.subheader("📝 Extracted Text")

        edited_text = st.text_area(
            "Review or edit extracted text",
            value=st.session_state.image_text,
            height=120,
            key="edited_image_text"
        )

        image_comment = edited_text.strip()


# ============================================================
# LANGUAGE SELECTION AND TRANSLATION
# ============================================================

st.divider()
st.subheader("🌐 Comment Language")

language_options = {
    "English": "en",
    "Hindi": "hi",
    "Gujarati": "gu"
}

selected_language = st.selectbox(
    "Select the language of your comment",
    list(language_options.keys())
)

source_language = language_options[selected_language]

if image_comment and source_language != "en":

    if st.button("🌐 Translate Extracted Text to English"):
        try:
            with st.spinner("Translating text..."):
                translated = translate_text(
                    image_comment,
                    source_language=source_language,
                    target_language="en"
                )

            if translated and translated.strip():
                st.session_state.translated_text = translated.strip()
                st.success("Translation completed.")
            else:
                st.warning("The translation returned empty text.")

        except Exception as translation_error:
            st.error(f"Translation failed: {translation_error}")

if st.session_state.translated_text:
    st.markdown(
        "<div class='translation-card'>"
        "<b>🌐 English Translation</b>"
        "</div>",
        unsafe_allow_html=True
    )

    st.text_area(
        "Translated text",
        value=st.session_state.translated_text,
        height=100,
        disabled=True
    )


# ============================================================
# COMMENT INPUT
# ============================================================

st.divider()
st.subheader("💬 Analyze a Social Media Comment")

if st.session_state.translated_text:
    default_comment = st.session_state.translated_text
elif image_comment:
    default_comment = image_comment
else:
    default_comment = ""

comment = st.text_area(
    "Enter the comment to analyze",
    value=default_comment,
    height=140,
    placeholder="Example: You are such an idiot..."
)

st.caption(
    "For an uploaded screenshot, review the extracted text before analysis."
)


# ============================================================
# ANALYZE COMMENT
# ============================================================

if st.button("🚀 Analyze Comment", type="primary"):

    if not comment.strip():
        st.warning("Please enter a comment or extract text from an image.")

    else:
        try:
            with st.spinner("🤖 AI is analyzing your comment..."):
                result = analyze_comment(comment.strip())

            st.session_state.analysis_result = result
            st.session_state.last_comment = comment.strip()
            st.session_state.analysis_mode = "Completed"
            st.session_state.audio_bytes = None

            st.success("✅ Comment analysis completed!")

        except Exception as analysis_error:

            error_msg = str(analysis_error)

            if (
                "402" in error_msg
                or "credits" in error_msg.lower()
            ):
                st.warning(
                    "Hugging Face credits may be exhausted. "
                    "Using the basic keyword fallback."
                )

                lower_comment = comment.lower()

                toxic_keywords = [
                    "idiot",
                    "stupid",
                    "hate",
                    "dumb",
                    "kill",
                    "worst",
                    "shut up"
                ]

                is_toxic = any(
                    word in lower_comment
                    for word in toxic_keywords
                )

                if is_toxic:
                    fallback_result = (
                        "Toxicity Warning (Fallback Analysis)\n"
                        "Status: Potentially Toxic / Offensive\n"
                        "Recommendation: Consider reviewing this comment."
                    )
                else:
                    fallback_result = (
                        "Safe Content (Fallback Analysis)\n"
                        "Status: Clean / Non-Toxic\n"
                        "Recommendation: No matching toxic keywords were found."
                    )

                st.session_state.analysis_result = fallback_result
                st.session_state.last_comment = comment.strip()
                st.session_state.analysis_mode = "Fallback"
                st.session_state.audio_bytes = None

                st.info(
                    "This fallback uses simple keyword matching. "
                    "It is not equivalent to a trained toxicity model."
                )
                st.success("Analysis completed using fallback mode.")

            else:
                st.error(f"AI analysis failed: {analysis_error}")


# ============================================================
# DISPLAY THE LATEST ANALYSIS RESULT
# ============================================================

if st.session_state.analysis_result is not None:

    result = st.session_state.analysis_result
    status = get_toxicity_status(result)
    detected_categories = get_detected_categories(result)

    st.divider()
    st.subheader("📋 AI Analysis Report")

    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.markdown("**Comment analyzed:**")
    st.write(st.session_state.last_comment)

    st.markdown("**Model result:**")
    if isinstance(result, (dict, list)):
        st.json(result)
    else:
        st.write(result)

    st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # TOXICITY STATUS
    # --------------------------------------------------------

    st.subheader("🔎 Moderation Status")

    if status == "Toxic":
        st.error("🚨 Toxic or potentially harmful content indicated by the result.")

    elif status == "Non-Toxic":
        st.success("✅ The result indicates non-toxic or safe content.")

    else:
        st.warning(
            "The result could not be classified automatically. "
            "Review the model output below."
        )

    # --------------------------------------------------------
    # TOXICITY GRAPH
    # --------------------------------------------------------

    st.divider()
    st.subheader("📊 Toxicity Level Graph")

    st.write(
        "This graph shows the recognized classification of the current "
        "comment. It is a count of one analyzed comment, not a confidence score."
    )

    if status == "Toxic":
        graph_data = pd.DataFrame({
            "Comments": [1, 0, 0]
        }, index=["Toxic", "Non-Toxic", "Unknown"])

    elif status == "Non-Toxic":
        graph_data = pd.DataFrame({
            "Comments": [0, 1, 0]
        }, index=["Toxic", "Non-Toxic", "Unknown"])

    else:
        graph_data = pd.DataFrame({
            "Comments": [0, 0, 1]
        }, index=["Toxic", "Non-Toxic", "Unknown"])

    st.bar_chart(
        graph_data,
        y_label="Number of comments",
        color="#2563EB"
    )

    # --------------------------------------------------------
    # CATEGORY GRAPH
    # --------------------------------------------------------

    st.subheader("📈 Detected Toxicity Categories")

    if detected_categories:
        category_data = pd.DataFrame({
            "Detected": [1] * len(detected_categories)
        }, index=detected_categories)

        st.bar_chart(
            category_data,
            y_label="Category detected (1 = identified)",
            color="#DC2626"
        )

        st.caption(
            "Only categories explicitly recognized in the model's output "
            "are shown. Categories not shown have not been confirmed absent."
        )

    else:
        st.info(
            "No specific toxicity categories could be extracted from the "
            "current result. Your model may return only an overall text report."
        )

    # --------------------------------------------------------
    # VOICE REPORT
    # --------------------------------------------------------

    st.divider()
    st.subheader("🔊 Voice Report")

    if st.button("🎙️ Generate Voice Report"):
        try:
            with st.spinner("Generating voice report..."):
                speech_text = result_to_text(result)

                speech = gTTS(
                    text=speech_text[:4500],
                    lang="en"
                )

                audio_buffer = io.BytesIO()
                speech.write_to_fp(audio_buffer)
                audio_buffer.seek(0)

                st.session_state.audio_bytes = audio_buffer.getvalue()

        except Exception as voice_error:
            st.warning(f"Voice output unavailable: {voice_error}")

    if st.session_state.audio_bytes:
        st.audio(
            st.session_state.audio_bytes,
            format="audio/mp3"
        )


# ============================================================
# IMAGE SAFETY SUMMARY
# ============================================================

if st.session_state.vision_result is not None:

    vision_data = st.session_state.vision_result

    if vision_data.get("success"):
        safe = vision_data.get("result", {})

        st.divider()
        st.subheader("🛡️ Image Moderation Summary")

        unsafe_levels = {"LIKELY", "VERY_LIKELY"}

        image_unsafe = any(
            safe.get(category) in unsafe_levels
            for category in ("adult", "violence", "racy")
        )

        if image_unsafe:
            st.error("🚨 Potentially unsafe visual content detected.")
        else:
            st.success(
                "✅ No high-risk level detected in the checked image categories."
            )


# ============================================================
# MODERATION PIPELINE
# ============================================================

st.divider()
st.subheader("🔄 Moderation Pipeline")

pipeline = st.columns(5)

pipeline_items = [
    ("📷 OCR API", "Image → Text"),
    ("🌐 Translation API", "Language → English"),
    ("🛡️ Google Vision", "Image → Safety"),
    ("🤖 AI Moderation", "Comment → Analysis"),
    ("🔊 gTTS", "Report → Audio")
]

for column, (heading, description) in zip(pipeline, pipeline_items):
    with column:
        st.info(f"**{heading}**\n\n{description}")


# ============================================================
# FOOTER
# ============================================================

st.markdown("""
<div class="footer">
<hr>
❤️ <b>Developed by Sejal Gupta</b> | MCA
<br><br>
Python • Streamlit • Hugging Face • OCR • Translation
<br>
Google Vision SafeSearch • gTTS
</div>
""", unsafe_allow_html=True)
