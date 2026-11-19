import os
import streamlit as st

from ingest import create_vector_database


def render_sidebar():
    """Render the Finance AI sidebar."""

    # ========================================================
    # SIDEBAR
    # ========================================================

    with st.sidebar:

        # ----------------------------------------------------
        # LOGO
        # ----------------------------------------------------

        st.image(
            "https://cdn-icons-png.flaticon.com/512/3135/3135706.png",
            width=80
        )

        st.title("💰 Finance AI")

        st.markdown("---")

        # ----------------------------------------------------
        # ABOUT
        # ----------------------------------------------------

        st.subheader("📘 About")

        st.write(
            """
            Finance AI is an AI-powered personal finance
            assistant that uses RAG, ChromaDB and Gemma 3
            to answer finance-related questions.
            """
        )

        st.markdown("---")

        # ----------------------------------------------------
        # PDF KNOWLEDGE BASE
        # ----------------------------------------------------

        st.subheader("📂 Finance Knowledge")

        st.caption(
            "Upload a finance PDF to add it to the AI knowledge base."
        )

        uploaded_file = st.file_uploader(
            "Upload Finance PDF",
            type=["pdf"],
            key="finance_pdf_uploader"
        )

        if uploaded_file is not None:

            os.makedirs(
                "data/pdfs",
                exist_ok=True
            )

            pdf_path = os.path.join(
                "data/pdfs",
                uploaded_file.name
            )

            # Save PDF
            with open(
                pdf_path,
                "wb"
            ) as file:

                file.write(
                    uploaded_file.getbuffer()
                )

            st.success(
                f"📄 {uploaded_file.name} uploaded!"
            )

            # ------------------------------------------------
            # PROCESS PDF
            # ------------------------------------------------

            if st.button(
                "🔄 Add PDF to AI Knowledge",
                key="process_pdf_button"
            ):

                with st.spinner(
                    "Processing PDF..."
                ):

                    try:

                        success = create_vector_database()

                        if success:

                            st.success(
                                "✅ PDF added to Finance AI!"
                            )

                            st.info(
                                "You can now ask questions about this PDF."
                            )

                        else:

                            st.error(
                                "❌ No documents were found."
                            )

                    except Exception as error:

                        st.error(
                            f"❌ Error processing PDF: {error}"
                        )

        st.markdown("---")

        # ----------------------------------------------------
        # SAMPLE QUESTIONS
        # ----------------------------------------------------

        st.subheader("💡 Sample Questions")

        st.write(
            """
            • What is SIP?

            • How can I save money?

            • What is budgeting?

            • What is EMI?

            • What is an emergency fund?
            """
        )

        st.markdown("---")

        # ----------------------------------------------------
        # CLEAR CHAT
        # ----------------------------------------------------

        if st.button(
            "🗑️ Clear Chat",
            key="clear_chat_button"
        ):

            st.session_state.messages = []

            st.rerun()

        st.markdown("---")

        # ----------------------------------------------------
        # SYSTEM STATUS
        # ----------------------------------------------------

        st.subheader("⚙️ System")

        st.success("🟢 Finance AI Ready")

        st.info("🧠 LLM: Gemma 3")

        st.info("🔎 Embedding: MiniLM-L6-v2")

        st.info("🗄️ Database: ChromaDB")