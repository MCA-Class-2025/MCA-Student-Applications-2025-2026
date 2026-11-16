import streamlit as st


def show():

    st.title("🛡️ SecureSense AI")
    st.subheader("AI-Powered Threat Detection & Analysis System")

    st.markdown("---")

    st.markdown("""


The platform enables users to:

- 🚨 Detect anomalous network traffic using Isolation Forest
- 🤖 Analyze cybersecurity concepts using an AI assistant
- 📚 Query multiple cybersecurity documents using RAG
- 🔐 Understand Zero Trust Network Access (ZTNA)
- 📄 Explore research papers and technical documentation
""")

    st.markdown("---")

    st.subheader("📊 System Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Research PDFs", "3")
    col2.metric("Knowledge Chunks", "599")
    col3.metric("Embedding Model", "MiniLM")
    col4.metric("Vector DB", "FAISS")

    st.markdown("---")

    st.subheader("🛠 Technologies Used")

    c1, c2 = st.columns(2)

    with c1:

        st.info("""
### Machine Learning

- Isolation Forest
- Scikit-Learn
- NSL-KDD Dataset
- Label Encoding
- Standard Scaling
""")

        st.info("""
### Large Language Model

- Gemma 3 1B
- Ollama
""")

    with c2:

        st.info("""
### Retrieval-Augmented Generation

- Sentence Transformers
- all-MiniLM-L6-v2
- FAISS
- Prompt Engineering
""")

        st.info("""
### Application

- Streamlit
- Python
- Pandas
- NumPy
""")

    st.markdown("---")

    st.subheader("🏗 Project Workflow")

    st.code("""
Network Traffic
        │
        ▼
Isolation Forest
        │
        ▼
Threat Detection
        │
        ▼
Threat Analysis Assistant
        │
        ▼
Retriever (FAISS)
        │
        ▼
Gemma 3
        │
        ▼
AI Response
""")

