import streamlit as st


# ============================================================
# CHAT
# ============================================================

def render_chat(
    ask_question,
    text_to_speech=None
):
    """
    Render the Finance AI Chat interface.
    """

    st.header(
        "💬 Finance AI Chat"
    )

    st.write(
        "Ask questions about finance, "
        "income, expenses, savings and budgeting."
    )


    # ========================================================
    # SUGGESTED QUESTIONS
    # ========================================================

    st.subheader(
        "💡 Suggested Questions"
    )

    st.caption(
        "Choose a question or type your own question below."
    )


    # ========================================================
    # OLD / GENERAL QUESTIONS
    # ========================================================

    st.write(
        "**📚 Finance Knowledge**"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        if st.button(
            "💳 What is a loan?",
            key="old_loan_question"
        ):

            st.session_state.suggested_question = (
                "What is a loan?"
            )


    with col2:

        if st.button(
            "📈 What is SIP?",
            key="old_sip_question"
        ):

            st.session_state.suggested_question = (
                "What is SIP?"
            )


    with col3:

        if st.button(
            "📊 What is budgeting?",
            key="old_budget_question"
        ):

            st.session_state.suggested_question = (
                "What is budgeting?"
            )


    # ========================================================
    # USER FINANCIAL QUESTIONS
    # ========================================================

    st.write(
        "**💰 My Financial Data**"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        if st.button(
            "💰 How much am I saving?",
            key="income_saving_question"
        ):

            st.session_state.suggested_question = (
                "How much am I saving from my "
                "current recorded income?"
            )


    with col2:

        if st.button(
            "💸 Where am I spending the most?",
            key="highest_expense_question"
        ):

            st.session_state.suggested_question = (
                "Where am I spending the most "
                "based on my actual recorded expenses?"
            )


    with col3:

        if st.button(
            "📉 How can I reduce my expenses?",
            key="reduce_expense_question"
        ):

            st.session_state.suggested_question = (
                "How can I reduce my expenses "
                "based on my actual recorded income "
                "and expenses?"
            )


    st.divider()


    # ========================================================
    # CHAT HISTORY
    # ========================================================

    if "messages" not in st.session_state:

        st.session_state.messages = []


    for message in st.session_state.messages:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )


    # ========================================================
    # HANDLE SUGGESTED QUESTION
    # ========================================================

    suggested_question = st.session_state.get(
        "suggested_question"
    )


    if suggested_question:

        st.session_state.suggested_question = None


        # ----------------------------------------------------
        # USER MESSAGE
        # ----------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "user",
                "content": suggested_question
            }
        )


        with st.chat_message(
            "user"
        ):

            st.markdown(
                suggested_question
            )


        # ----------------------------------------------------
        # AI RESPONSE
        # ----------------------------------------------------

        with st.chat_message(
            "assistant"
        ):

            with st.spinner(
                "🤖 Thinking..."
            ):

                try:

                    answer, docs = ask_question(
                        suggested_question
                    )

                    st.markdown(
                        answer
                    )


                    # ----------------------------------------
                    # TEXT TO SPEECH
                    # ----------------------------------------

                    if text_to_speech:

                        try:

                            audio = text_to_speech(
                                answer
                            )

                            if audio:

                                st.audio(
                                    audio
                                )

                        except Exception:

                            pass


                    # ----------------------------------------
                    # SAVE RESPONSE
                    # ----------------------------------------

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer
                        }
                    )


                except Exception as error:

                    st.error(
                        "Unable to generate an AI response."
                    )

                    st.exception(error)


        st.rerun()


    # ========================================================
    # CHAT INPUT
    # ========================================================

    question = st.chat_input(
        "Ask your finance question..."
    )


    if question:

        # ----------------------------------------------------
        # USER MESSAGE
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # AI RESPONSE
        # ----------------------------------------------------

        with st.chat_message(
            "assistant"
        ):

            with st.spinner(
                "🤖 Analyzing your question..."
            ):

                try:

                    answer, docs = ask_question(
                        question
                    )

                    st.markdown(
                        answer
                    )


                    # ----------------------------------------
                    # TEXT TO SPEECH
                    # ----------------------------------------

                    if text_to_speech:

                        try:

                            audio = text_to_speech(
                                answer
                            )

                            if audio:

                                st.audio(
                                    audio
                                )

                        except Exception:

                            pass


                    # ----------------------------------------
                    # SAVE RESPONSE
                    # ----------------------------------------

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer
                        }
                    )


                except Exception as error:

                    st.error(
                        "Unable to generate an AI response."
                    )

                    st.exception(error)