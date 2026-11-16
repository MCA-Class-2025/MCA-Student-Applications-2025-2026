import streamlit as st
import os
import shutil
import time

from modules.rag.knowledge_base_manager import build_knowledge_base


def show():

    st.title("📚 Knowledge Base")

    st.info("""
### 🔒 Administrator Panel

This application uses a **shared cybersecurity knowledge base**.

Only the administrator can upload research papers and rebuild the knowledge base.

End users can query the knowledge base but cannot modify it.
""")

    st.markdown("---")

    # ====================================================
    # Upload Section
    # ====================================================

    st.subheader("📤 Upload Research Paper")

    uploaded_file = st.file_uploader(
        "Choose a PDF or DOCX file",
        type=["pdf", "docx"]
    )

    if uploaded_file is not None:

        destination = os.path.join(
            "data",
            "documents",
            uploaded_file.name
        )

        # -------------------------
        # File already exists
        # -------------------------

        if os.path.exists(destination):

            st.warning(
                f"⚠️ '{uploaded_file.name}' already exists in the Knowledge Base."
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button("Replace Existing File"):

                    with open(destination, "wb") as f:
                        shutil.copyfileobj(uploaded_file, f)

                    st.success("✅ File replaced successfully.")

                    st.info(
                        "Click **Rebuild Knowledge Base** to update the AI Knowledge Base."
                    )

            with col2:

                st.button("Cancel Upload")

        # -------------------------
        # New File
        # -------------------------

        else:

            with open(destination, "wb") as f:
                shutil.copyfileobj(uploaded_file, f)

            st.success(f"✅ {uploaded_file.name} uploaded successfully.")

            st.info(
                "Click **Rebuild Knowledge Base** to update the AI Knowledge Base."
            )

    st.markdown("---")

    # ====================================================
    # Loaded Documents
    # ====================================================

    st.subheader("📂 Loaded Documents")

    document_folder = "data/documents"

    files = []

    if os.path.exists(document_folder):

        files = [
            file
            for file in os.listdir(document_folder)
            if file.endswith(".pdf") or file.endswith(".docx")
        ]

        if files:

            for file in files:
                st.success(file)

        else:

            st.warning("No documents found.")

    else:

        st.error("Document folder not found.")

    # ====================================================
    # Delete Document
    # ====================================================

    st.markdown("---")

    st.subheader("🗑️ Delete Document")

    if files:

        selected_file = st.selectbox(
            "Select a document to delete",
            files
        )

        if st.button("Delete Selected Document"):

            file_path = os.path.join(
                document_folder,
                selected_file
            )

            try:

                os.remove(file_path)

                st.success(
                    f"✅ '{selected_file}' deleted successfully."
                )

                st.info(
                    "Click 'Rebuild Knowledge Base' to update the AI."
                )

                time.sleep(1)

                st.rerun()

            except Exception as e:

                st.error(e)

    else:

        st.info("No documents available.")

    # ====================================================
    # Knowledge Base Builder
    # ====================================================

    st.subheader("🔄 Knowledge Base")

    if st.button("🔄 Rebuild Knowledge Base",use_container_width=True):

        with st.spinner("Updating Knowledge Base..."):

            info = build_knowledge_base()

        st.success("✅ Knowledge Base Updated Successfully!")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Documents", info["documents"])

        with col2:
            st.metric("Chunks", info["chunks"])

    st.markdown("---")

    # ====================================================
    # Information
    # ====================================================

    st.subheader("⚙️ Knowledge Base Information")

    col1, col2 = st.columns(2)

    with col1:

        st.info("""
### Embedding Model

all-MiniLM-L6-v2

Sentence Transformers
""")

        st.info("""
### Vector Database

FAISS
""")

    with col2:

        st.info("""
### Language Model

Gemma 3 1B

(Ollama)
""")

        st.info("""
### Supported Documents

• PDF

• DOCX
""")

    st.markdown("---")

    # ====================================================
    # Current Status
    # ====================================================

    st.subheader("📊 Current Status")

    st.success("Knowledge Base Ready")

    st.write(f"📄 Total Documents : **{len(files)}**")

    st.write("🤖 Embedding Model : **all-MiniLM-L6-v2**")

    st.write("🗄️ Vector Database : **FAISS**")

    st.write("🧠 Language Model : **Gemma 3 1B (Ollama)**")