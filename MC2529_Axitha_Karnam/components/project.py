import os
import streamlit as st


def get_pdf_count():
    """Return number of PDFs in the knowledge base."""

    pdf_folder = "data/pdfs"

    if not os.path.exists(pdf_folder):

        return 0

    return len(
        [
            file
            for file in os.listdir(pdf_folder)
            if file.lower().endswith(".pdf")
        ]
    )


def render_project():
    """Render project information."""

    st.header(
        "📘 Finance AI Project"
    )

    st.write(
        "An AI-powered Personal Finance Assistant "
        "using Retrieval-Augmented Generation."
    )

    # --------------------------------------------------------
    # Project Statistics
    # --------------------------------------------------------

    pdf_count = get_pdf_count()

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Finance PDFs",
            pdf_count
        )

    with col2:

        st.metric(
            "LLM",
            "Gemma 3"
        )

    with col3:

        st.metric(
            "Vector Database",
            "ChromaDB"
        )

    st.divider()

    # --------------------------------------------------------
    # Project Overview
    # --------------------------------------------------------

    st.subheader(
        "🎯 Project Objective"
    )

    st.write(
        """
        Finance AI is an intelligent personal finance
        assistant designed to help users understand
        financial concepts, manage savings and receive
        AI-powered financial guidance.

        The application combines Large Language Models,
        Retrieval-Augmented Generation, vector databases
        and financial calculations.
        """
    )

    # --------------------------------------------------------
    # Architecture
    # --------------------------------------------------------

    st.subheader(
        "🏗️ System Architecture"
    )

    st.code(
        """
User
 │
 ▼
Streamlit Interface
 │
 ▼
Finance AI Application
 │
 ├── Financial Calculator
 │
 ├── RAG Pipeline
 │      │
 │      ├── PDF Documents
 │      ├── Text Chunking
 │      ├── MiniLM Embeddings
 │      └── ChromaDB
 │
 ▼
Gemma 3 LLM
 │
 ▼
AI Financial Response
        """,
        language="text"
    )

    # --------------------------------------------------------
    # Technologies
    # --------------------------------------------------------

    st.subheader(
        "🛠️ Technologies Used"
    )

    technologies = [
        "Python",
        "Streamlit",
        "LangChain",
        "ChromaDB",
        "Ollama",
        "Gemma 3",
        "HuggingFace Embeddings",
        "Retrieval-Augmented Generation (RAG)"
    ]

    for technology in technologies:

        st.write(
            f"• {technology}"
        )

    # --------------------------------------------------------
    # Current Features
    # --------------------------------------------------------

    st.subheader(
        "✨ Current Features"
    )

    features = [
        "AI Personal Finance Q&A",
        "PDF-based Knowledge Retrieval",
        "Retrieval-Augmented Generation",
        "ChromaDB Vector Search",
        "Gemma 3 LLM",
        "Text-to-Speech",
        "Download AI Answers",
        "PDF Upload",
        "Reference Document Display",
        "Conversation History",
        "Suggested Finance Questions",
        "Monthly Savings Calculator"
    ]

    for feature in features:

        st.write(
            f"✅ {feature}"
        )

    # --------------------------------------------------------
    # Future Features
    # --------------------------------------------------------

    st.subheader(
        "🚀 Planned Advanced Features"
    )

    future_features = [
        "Expense Tracker",
        "Budget Planner",
        "SIP Calculator",
        "EMI Calculator",
        "FD Calculator",
        "Financial Goal Planner",
        "Financial Health Score",
        "Stock Market API",
        "Currency Exchange API",
        "Gold Price API",
        "Financial News API",
        "AI Expense Categorization",
        "Personalized Financial Dashboard"
    ]

    for feature in future_features:

        st.write(
            f"🔹 {feature}"
        )