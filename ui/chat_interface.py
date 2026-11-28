import streamlit as st


def chat_interface(answer):


    st.markdown(
        """
        <div class="result-box">
        <h2>✨ AI Design Plan</h2>
        </div>
        """,
        unsafe_allow_html=True
    )


    st.write(answer)