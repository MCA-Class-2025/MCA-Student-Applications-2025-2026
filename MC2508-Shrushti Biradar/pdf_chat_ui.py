
"""
pdf_chat_ui.py

Streamlit interface for the AI Event Planner PDF QA Chatbot.
Supports multiple PDFs and chat history.
"""

import streamlit as st

from pdf_processor import process_pdfs
from vector_store import create_vector_store
from pdf_qa import answer_pdf_question


st.set_page_config(
    page_title="Event Planner PDF Assistant",
    page_icon="📄",
    layout="wide",
)

st.title("📄 AI Event Planner — PDF Assistant")
st.write(
    "Upload event documents and ask questions about budgets, "
    "venues, schedules, guests, and more."
)

# Store uploaded PDF search index and conversation in session
if "pdf_vector_store" not in st.session_state:
    st.session_state.pdf_vector_store = None

if "pdf_chat_history" not in st.session_state:
    st.session_state.pdf_chat_history = []

uploaded_files = st.file_uploader(
    "Upload one or more PDF documents",
    type=["pdf"],
    accept_multiple_files=True,
)

if st.button("Process PDFs", type="primary"):
    if not uploaded_files:
        st.warning("Please upload at least one PDF.")
    else:
        try:
            with st.spinner("Reading PDFs and building search index..."):
                chunks = process_pdfs(uploaded_files)
                st.session_state.pdf_vector_store = create_vector_store(chunks)
                st.session_state.pdf_chat_history = []

            st.success(
                f"Successfully processed {len(uploaded_files)} PDF file(s)."
            )

        except Exception as e:
            st.error(f"Could not process the PDFs: {e}")

st.divider()

if st.session_state.pdf_vector_store is not None:
    st.subheader("💬 Ask your event documents")

    # Display previous messages
    for message in st.session_state.pdf_chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input("Example: What is the event budget?")

    if question:
        st.session_state.pdf_chat_history.append(
            {"role": "user", "content": question}
        )

        with st.chat_message("user"):
            st.markdown(question)

        # Pass only previous messages as context, excluding the current question
        previous_history = st.session_state.pdf_chat_history[:-1]

        with st.chat_message("assistant"):
            with st.spinner("Searching PDFs and generating an answer..."):
                answer = answer_pdf_question(
                    question,
                    st.session_state.pdf_vector_store,
                    previous_history,
                )

            st.markdown(answer)

        st.session_state.pdf_chat_history.append(
            {"role": "assistant", "content": answer}
        )

else:
    st.info("Upload your PDFs and click Process PDFs to begin.")
