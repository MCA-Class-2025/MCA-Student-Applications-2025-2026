"""Cautious visual description: never identifies a person or dance from a photo."""

import streamlit as st

from utils.translate import translate_text

try:
    from utils.llm import ask_llm, gemini_available
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

def render():
    st.markdown("## Image Guide")
    st.markdown("<div class='fd-card'><b>A safe visual companion—not dance recognition.</b> Ask about visible costume, pose, instruments, or setting. The guide never claims to identify a dance form, person, ethnicity, nationality, or religion from a photograph.</div>", unsafe_allow_html=True)
    image = st.file_uploader("Upload a JPG, PNG, or WebP image", type=["jpg", "jpeg", "png", "webp"])
    if not image:
        return
    st.image(image, caption=image.name, use_container_width=True)
    question = st.text_area("What visible details would you like described?", placeholder="Describe the costume, pose, setting, and any instruments you can see.")
    if not (AVAILABLE and gemini_available()):
        st.info("Add a Gemini API key in the sidebar to enable visual descriptions.")
        return
    if st.button("Describe visible details", type="primary"):
        system = ("You are a careful cultural-image guide. Describe only visibly supported clothing, posture, objects, colours, setting, and performance context. Do not identify a specific dance form or infer a person's identity, ethnicity, nationality, religion, or cultural background. If asked to identify a dance, say a photo alone is insufficient and explain which observable details could be compared with a documented dance profile.")
        prompt = question or "Describe visible costume, pose, setting, and any performance-related objects."
        with st.spinner("Looking at visible details..."):
            try:
                answer = ask_llm(system, prompt, max_tokens=450, image_bytes=image.getvalue(), image_mime_type=image.type or "image/jpeg")
                target_language = st.session_state.get("target_language", "English")
                if target_language != "English":
                    answer = translate_text(answer, target_language)
                st.session_state["image_answer"] = answer
            except Exception as exc:
                st.error(f"Image description failed: {exc}")
    if answer := st.session_state.get("image_answer"):
        st.markdown("### Visual notes")
        st.write(answer)
