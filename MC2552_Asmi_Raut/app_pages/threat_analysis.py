import streamlit as st

from modules.rag.hybrid_retriever import HybridRetriever
from modules.rag.prompt_template import build_prompt
from modules.llm.threat_assistant import generate_answer


# ---------------------------------------------------
# Load Fused Retriever Only Once
# ---------------------------------------------------

def load_retriever():
    return HybridRetriever()


retriever = load_retriever()


# ---------------------------------------------------
# Welcome Message
# ---------------------------------------------------

WELCOME_MESSAGE = (
    "Hello! 👋 I am your **AI Threat Analysis Assistant**.\n\n"
    "I answer questions using the fused cybersecurity knowledge base "
    "containing network records and external threat-intelligence data.\n\n"
)


# ---------------------------------------------------
# Main Page
# ---------------------------------------------------

def show():

    st.title("🛡️ AI Threat Analysis Assistant")

    st.markdown("""
Ask questions about the project's fused cybersecurity knowledge base.

The assistant uses a Retrieval-Augmented Generation (RAG) pipeline
to retrieve relevant network and external threat-intelligence records.

#### You can ask about:

- Network traffic and attack records
- NSL-KDD / CIC network attributes
- VirusTotal information
- AbuseIPDB information
- AlienVault OTX information
- Shodan information
- ThreatFox information
- IP reputation and threat intelligence
- Network activity and cybersecurity observations
""")

    st.markdown("---")

    # ---------------------------------------------------
    # Initialize Chat History
    # ---------------------------------------------------

    if "messages" not in st.session_state:

        st.session_state.messages = [
            {
                "role": "assistant",
                "content": WELCOME_MESSAGE
            }
        ]

    # ---------------------------------------------------
    # Clear Chat Button
    # ---------------------------------------------------

    col1, col2 = st.columns([6, 1])

    with col2:

        if st.button("🗑️ Clear Chat"):

            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": WELCOME_MESSAGE
                }
            ]

            st.rerun()

    # ---------------------------------------------------
    # Display Chat History
    # ---------------------------------------------------

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

    # ---------------------------------------------------
    # User Input
    # ---------------------------------------------------

    question = st.chat_input(
        "Ask about network traffic, IPs, or threat intelligence..."
    )

    if question:

        # ---------------- User ----------------

        st.session_state.messages.append(
            {
                "role": "user",
                "content": question
            }
        )

        with st.chat_message("user"):

            st.markdown(question)

        # ---------------- AI ----------------

        with st.spinner("🧠 Retrieving fused data and generating response..."):

            try:

                # Retrieve relevant fused records
                context = retriever.retrieve(question)

                # Build prompt
                prompt = build_prompt(
                    context,
                    question
                )

                # Generate answer
                answer = generate_answer(prompt)

            except Exception as e:

                answer = f"❌ Error:\n\n{str(e)}"

                context = []

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        with st.chat_message("assistant"):

            st.markdown("## Answer")

            st.write(answer)

            # ---------------------------------------------------
            # Optional Retrieved Knowledge
            # ---------------------------------------------------

            if context:

                st.markdown("---")

                st.markdown("### 📚 Retrieved Fused Records")

                for i, record in enumerate(context, start=1):

                    with st.expander(f"Source {i}"):

                        st.write(record)