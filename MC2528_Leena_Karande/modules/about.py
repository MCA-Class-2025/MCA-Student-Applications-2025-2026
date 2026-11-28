#"""Project story and transparent technical architecture."""

import streamlit as st


def render() -> None:
    st.markdown("## About DanceCompass AI")
    st.markdown("<div class='fd-card'><p class='eyebrow'>CULTURAL HERITAGE PLATFORM</p><h3>Built to make dance traditions easier to discover—with care.</h3><p>DanceCompass is a local-first exploration platform for a curated collection of dance forms. It does not claim that the collection represents every dance tradition in the world.</p></div>", unsafe_allow_html=True)
    st.markdown("### How the guide works")
    st.markdown("<div class='fd-card'><b>Global Dance Dataset</b> → <b>Data Processing</b> → <b>Vector Embeddings</b> → <b>FAISS Knowledge Base</b> → <b>AI Retrieval (RAG)</b> → <b>Gemini AI</b> → <b>Multilingual Response</br>→<b>Text-to-Speech</b><br><p>Every response is generated using Retrieval-Augmented Generation (RAG), ensuring answers are based on the curated dance knowledge base and uploaded PDF documents rather than relying solely on the language model.</p></div>", unsafe_allow_html=True)
    st.markdown("### Technology, with purpose")
    left, right = st.columns(2)
    left.markdown("<div class='fd-card'><h4>Knowledge layer</h4><p>Curated Global Dance Dataset<br>PDF Knowledge Upload<br>RAG-based Information Retrieval<br>FAISS Vector Database</p></div>", unsafe_allow_html=True)
    right.markdown("<div class='fd-card'><h4>Experience layer</h4><p>Interactive Streamlit Interface<br>Gemini AI-powered Responses<br>Multilingual Translation<br>Browser Text-to-Speech<br>Dance Image Recognition<br>Personalized Dance Recommendation</p></div>", unsafe_allow_html=True)
    st.markdown("### Privacy & future scope")
    st.markdown("<div class='fd-card'>DanceCompass AI combines Retrieval-Augmented Generation (RAG) with Gemini AI to provide reliable, multilingual answers. Users can expand the knowledge base by uploading PDF documents, while text-to-speech enhances accessibility across supported languages.</div>", unsafe_allow_html=True)



