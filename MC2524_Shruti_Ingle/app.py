import os
import tempfile
import traceback

import streamlit as st
from streamlit_mic_recorder import mic_recorder

from src.voice_input import speech_to_text
from src.text_to_speech import text_to_audio
from src.translator import translate_text

from src.pdf_handler import load_pdfs, split_documents
from src.vector_store import create_vector_store
from src.qa_chain import build_qa_chain
from src.query_handler import ask_chatbot

# Google Drive
from src.google_drive_api import (
    export_google_drive_dataset,
    load_google_drive_documents
)

# GitHub
from src.github_api import (
    export_github_dataset,
    load_github_documents
)


# =======================================================
# PAGE CONFIGURATION
# =======================================================

st.set_page_config(
    page_title="DocuMind AI - Intelligent Document Assistant",
    page_icon="📚",
    layout="wide"
)


# =======================================================
# HEADER
# =======================================================

st.title("🤖 DocuMind AI")

st.subheader("Your Personal AI Document Assistant")

st.markdown(
    """
    Upload documents, import Google Drive files, import GitHub
    repositories, and ask questions using Retrieval-Augmented
    Generation (RAG).
    """
)


# =======================================================
# SESSION STATE
# =======================================================

if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None

if "messages" not in st.session_state:
    st.session_state.messages = []


# =======================================================
# SIDEBAR
# =======================================================

st.sidebar.header("📂 Document Upload")


uploaded_files = st.sidebar.file_uploader(
    "Upload Documents",
    type=[
        "pdf",
        "docx",
        "txt",
        "csv",
        "json",
        "md",
        "png",
        "jpg",
        "jpeg"
    ],
    accept_multiple_files=True
)


# =======================================================
# GOOGLE DRIVE IMPORT
# =======================================================

st.sidebar.markdown("---")

st.sidebar.header("☁️ Google Drive")


if st.sidebar.button("Import Google Drive Files"):

    try:

        with st.spinner(
            "Fetching Google Drive files..."
        ):

            files = export_google_drive_dataset()

        st.sidebar.success(
            f"Imported {len(files)} Google Drive files."
        )

        st.info(
            "Google Drive metadata saved to: "
            "datasets/google_drive_dataset.csv"
        )

    except Exception as e:

        st.sidebar.error(
            f"Google Drive import failed: {e}"
        )

        st.code(
            traceback.format_exc()
        )


# =======================================================
# GITHUB IMPORT
# =======================================================

st.sidebar.markdown("---")

st.sidebar.header("🐙 GitHub")


if st.sidebar.button("Import GitHub Repositories"):

    try:

        with st.spinner(
            "Fetching GitHub repositories..."
        ):

            repos = export_github_dataset()

        st.sidebar.success(
            f"Imported {len(repos)} GitHub repositories."
        )

        st.info(
            "GitHub dataset saved to: "
            "datasets/github_dataset.csv"
        )

    except Exception as e:

        st.sidebar.error(
            f"GitHub import failed: {e}"
        )

        st.code(
            traceback.format_exc()
        )


# =======================================================
# PROCESS KNOWLEDGE BASE
# =======================================================

st.sidebar.markdown("---")


if st.sidebar.button(
    "⚙️ Process Knowledge Base"
):

    # ---------------------------------------------------
    # Check whether there is anything to process
    # ---------------------------------------------------

    has_uploaded_files = bool(uploaded_files)

    has_google_drive = os.path.exists(
        "datasets/google_drive_dataset.csv"
    )

    has_github = os.path.exists(
        "datasets/github_dataset.csv"
    )


    if not (
        has_uploaded_files
        or has_google_drive
        or has_github
    ):

        st.sidebar.warning(
            "Please upload a document or import "
            "Google Drive/GitHub data first."
        )

    else:

        with st.spinner(
            "Building DocuMind knowledge base..."
        ):

            temp_paths = []

            try:

                # ===================================================
                # MASTER DOCUMENT LIST
                # ===================================================

                docs = []


                # ===================================================
                # 1. LOCAL UPLOADED DOCUMENTS
                # ===================================================

                if uploaded_files:

                    st.write(
                        "### 📁 Processing uploaded files"
                    )


                    for file in uploaded_files:

                        extension = os.path.splitext(
                            file.name
                        )[1]

                        tmp = tempfile.NamedTemporaryFile(
                            delete=False,
                            suffix=extension
                        )

                        tmp.write(
                            file.read()
                        )

                        tmp.close()

                        temp_paths.append(
                            tmp.name
                        )


                    st.write(
                        f"Uploaded files: "
                        f"{len(temp_paths)}"
                    )


                    uploaded_docs = load_pdfs(
                        temp_paths
                    )


                    st.write(
                        f"Uploaded documents loaded: "
                        f"{len(uploaded_docs)}"
                    )


                    docs.extend(
                        uploaded_docs
                    )


                # ===================================================
                # 2. GOOGLE DRIVE DOCUMENTS
                # ===================================================

                if has_google_drive:

                    st.write(
                        "### ☁️ Processing Google Drive"
                    )


                    # IMPORTANT:
                    # For now we process only ONE file.
                    # Once testing is successful we can increase this.

                    drive_docs = load_google_drive_documents(
                        limit=1
                    )


                    st.write(
                        f"Google Drive documents added: "
                        f"{len(drive_docs)}"
                    )


                    docs.extend(
                        drive_docs
                    )


                # ===================================================
                # 3. GITHUB DOCUMENTS
                # ===================================================

                if has_github:

                    st.write(
                        "### 🐙 Processing GitHub"
                    )


                    github_docs = load_github_documents()


                    st.write(
                        f"GitHub documents added: "
                        f"{len(github_docs)}"
                    )


                    docs.extend(
                        github_docs
                    )


                # ===================================================
                # CHECK DOCUMENTS
                # ===================================================

                st.write(
                    f"### 📚 Total documents loaded: "
                    f"{len(docs)}"
                )


                if len(docs) == 0:

                    raise ValueError(
                        "No documents were successfully loaded."
                    )


                # ===================================================
                # SPLIT INTO CHUNKS
                # ===================================================

                st.write(
                    "### ✂️ Creating document chunks..."
                )


                chunks = split_documents(
                    docs
                )


                st.write(
                    f"Chunks created: "
                    f"{len(chunks)}"
                )


                if len(chunks) == 0:

                    raise ValueError(
                        "No text chunks were created."
                    )


                # ===================================================
                # CREATE VECTOR DATABASE
                # ===================================================

                st.write(
                    "### 🧠 Creating FAISS vector database..."
                )


                db = create_vector_store(
                    chunks
                )


                # ===================================================
                # BUILD QA CHAIN
                # ===================================================

                st.write(
                    "### 🤖 Building RAG QA chain..."
                )


                st.session_state.qa_chain = (
                    build_qa_chain(db)
                )


                # ===================================================
                # SUCCESS
                # ===================================================

                st.sidebar.success(
                    "Knowledge base created successfully!"
                )


                st.success(
                    f"""
                    Knowledge base ready!

                    Documents: {len(docs)}

                    Chunks: {len(chunks)}
                    """
                )


            except Exception as e:

                st.sidebar.error(
                    f"Processing failed: {e}"
                )

                st.error(
                    "An error occurred while "
                    "building the knowledge base."
                )

                st.code(
                    traceback.format_exc()
                )


            finally:

                # ===================================================
                # DELETE TEMPORARY FILES
                # ===================================================

                for path in temp_paths:

                    if os.path.exists(path):

                        os.remove(path)


# =======================================================
# SIDEBAR INFORMATION
# =======================================================

st.sidebar.markdown("---")

st.sidebar.markdown(
    "**Embedding Model:** all-MiniLM-L6-v2"
)

st.sidebar.markdown(
    "**Vector Database:** FAISS"
)

st.sidebar.markdown(
    "**LLM:** google/flan-t5-large"
)


# =======================================================
# LANGUAGE SELECTION
# =======================================================

st.sidebar.markdown("---")

st.sidebar.header("🌍 Language")


selected_language = st.sidebar.selectbox(
    "Choose response language",
    [
        "English",
        "Hindi",
        "Marathi",
        "Gujarati",
        "Tamil",
        "Telugu",
        "Kannada",
        "Bengali"
    ]
)


# =======================================================
# CHAT HISTORY
# =======================================================

for msg in st.session_state.messages:

    with st.chat_message(
        msg["role"]
    ):

        st.markdown(
            msg["content"]
        )


# =======================================================
# VOICE INPUT
# =======================================================

st.subheader("🎤 Ask by Voice")


audio = mic_recorder(
    start_prompt="🎙️ Start Recording",
    stop_prompt="⏹️ Stop Recording",
    key="voice_recorder"
)


question = None


if audio is not None:

    try:

        question = speech_to_text(
            audio["bytes"]
        )


        if question:

            st.success(
                f"You said: {question}"
            )


    except Exception as e:

        st.error(
            f"Speech recognition failed: {e}"
        )


# =======================================================
# TEXT INPUT
# =======================================================

typed_question = st.chat_input(
    "Ask a question about your documents, Google Drive, or GitHub"
)


if typed_question:

    question = typed_question


# =======================================================
# PROCESS QUESTION
# =======================================================

if question:

    # ---------------------------------------------------
    # Add user message
    # ---------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )


    with st.chat_message(
        "user"
    ):

        st.markdown(
            question
        )


    # ---------------------------------------------------
    # Check QA Chain
    # ---------------------------------------------------

    if st.session_state.qa_chain is None:

        answer = (
            "Please build the knowledge base first "
            "by clicking '⚙️ Process Knowledge Base'."
        )

        sources = []


    else:

        try:

            # ---------------------------------------------------
            # Ask RAG chatbot
            # ---------------------------------------------------

            answer = ask_chatbot(
                st.session_state.qa_chain,
                question
            )


            # ---------------------------------------------------
            # Translation
            # ---------------------------------------------------

            answer = translate_text(
                answer,
                selected_language
            )


            # ---------------------------------------------------
            # Retrieve source documents
            # ---------------------------------------------------

            result = (
                st.session_state.qa_chain.invoke(
                    {
                        "question": question
                    }
                )
            )


            sources = result.get(
                "source_documents",
                []
            )


        except Exception as e:

            answer = (
                f"Error while generating answer: {e}"
            )

            sources = []


    # ===================================================
    # ASSISTANT RESPONSE
    # ===================================================

    with st.chat_message(
        "assistant"
    ):

        st.markdown(
            answer
        )


        # ===================================================
        # TEXT TO SPEECH
        # ===================================================

        try:

            audio_file = text_to_audio(
                answer
            )


            if audio_file:

                with open(
                    audio_file,
                    "rb"
                ) as f:

                    audio_bytes = f.read()


                st.audio(
                    audio_bytes,
                    format="audio/mp3"
                )


                os.remove(
                    audio_file
                )


        except Exception as e:

            st.warning(
                f"Audio generation failed: {e}"
            )


        # ===================================================
        # SOURCE DOCUMENTS
        # ===================================================

        if sources:

            st.markdown(
                "### 📄 Source Documents"
            )


            displayed = set()


            for doc in sources:

                file_name = os.path.basename(
                    doc.metadata.get(
                        "source_file",
                        "Unknown"
                    )
                )


                page = doc.metadata.get(
                    "page",
                    None
                )


                source_type = doc.metadata.get(
                    "source",
                    ""
                )


                key = (
                    file_name,
                    page,
                    source_type
                )


                if key in displayed:

                    continue


                displayed.add(
                    key
                )


                # ------------------------------------------------
                # PDF with page number
                # ------------------------------------------------

                if page is not None:

                    st.markdown(
                        f"- **{file_name}** — "
                        f"Page **{page + 1}**"
                    )


                else:

                    # ------------------------------------------------
                    # Google Drive / GitHub / other documents
                    # ------------------------------------------------

                    if source_type:

                        st.markdown(
                            f"- **{file_name}** "
                            f"({source_type})"
                        )

                    else:

                        st.markdown(
                            f"- **{file_name}**"
                        )


        # ===================================================
        # DOWNLOAD ANSWER
        # ===================================================

        st.download_button(
            label="⬇️ Download Answer",
            data=answer,
            file_name="answer.txt",
            mime="text/plain"
        )


    # ---------------------------------------------------
    # Save assistant message
    # ---------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )