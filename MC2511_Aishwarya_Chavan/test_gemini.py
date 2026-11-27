import streamlit as st
from api.gemini_api import ask_gemini

st.set_page_config(
    page_title="Gemini Movie Chatbot",
    page_icon="🎬"
)

st.title("🎬 Gemini Movie Chatbot")

st.write("Ask Gemini anything about movies.")

question = st.text_area(
    "Enter your question",
    placeholder="Example: Explain the story of Inception"
)

if st.button("🤖 Ask Gemini"):

    if question.strip():

        with st.spinner("Gemini is thinking..."):

            try:
                answer = ask_gemini(question)

                st.success("Gemini answered!")

                st.markdown("### 🤖 Gemini Answer")

                st.write(answer)

            except Exception as e:

                st.error("Gemini API Error")

                st.write(str(e))

    else:

        st.warning("Please enter a question.")