import streamlit as st

from utils.text_utils import simple_keyword_search
from utils.translate import LANGUAGES, translate_text

try:
    from utils.llm import gemini_available, generate_rag_answer
    _LLM_LIBS_AVAILABLE = True
except ImportError:
    _LLM_LIBS_AVAILABLE = False

    def gemini_available():
        return False


try:
    from utils.audio import stt_available, transcribe_and_translate, tts_widget
    _AUDIO_AVAILABLE = True
except ImportError:
    _AUDIO_AVAILABLE = False

    def stt_available():
        return False

DOMAIN_PROMPT = (
    "You are DanceCompass, a friendly and knowledgeable guide to world "
    "dance forms. Answer the user's question using ONLY the provided "
    "dance-form profiles as context -- each profile combines curated "
    "reference data with, where marked, additional facts sourced from "
    "Wikipedia, Wikidata, geocoding, Open Library, and MusicBrainz. If "
    "the question is about a dance form not covered in the context, say "
    "clearly that it's not in your current dataset (20 dance forms) "
    "rather than guessing.\n\n"
    "Format every answer systematically:\n"
    "- Start with a one- or two-sentence direct answer.\n"
    "- If the question involves two or more dance forms (comparing, "
    "listing, recommending among options), give each one its own "
    "'### Name' heading with a short set of bullet points underneath -- "
    "never a single run-on paragraph mixing them together.\n"
    "- If the question is about one dance form, use short paragraphs or "
    "bullet points grouped by theme (origin & history, music & "
    "movement, what makes it notable), not one long block of prose.\n"
    "- Be specific and factual: mention concrete details like "
    "instruments, movements, or origin where relevant, and weave in any "
    "open-data facts (Wikipedia/Wikidata summaries, geographic origin) "
    "naturally into the prose.\n"
    "- If the context includes 'Recommended reading' or 'Reference "
    "recordings' lines with markdown links -- e.g. [Title](url) -- and "
    "they're relevant to the question, include them as their own short "
    "bullet list at the end of that dance form's section, using the "
    "markdown links exactly as given (don't rewrite or drop the URLs, "
    "and don't invent links that aren't in the context).\n"
    "- Keep it warm and conversational, but organized -- the person "
    "should be able to scan the answer, not have to read every word."
)


def _current_mode():
    has_index = st.session_state.get("doc_index") is not None
    has_llm = _LLM_LIBS_AVAILABLE and gemini_available()
    if has_index and has_llm:
        return "rag", "Grounded RAG · Gemini + FAISS"
    if has_index:
        return "retrieval_only", "Semantic retrieval (add Gemini key for generated answers)"
    return "keyword", "Keyword search (no Phase 2 libraries installed)"


def render():
    st.markdown("## 🤖 Ask the AI Guide")

    st.markdown("<section class='ai-hero'><p class='eyebrow'>DANCECOMPASS AI</p><h1>What are we discovering today?</h1><p>Ask, compare, translate, or find your next dance obsession.</p></section>", unsafe_allow_html=True)
    mode, badge_text = _current_mode()
    badge_class = "badge-phase1" if mode == "rag" else "badge-upcoming"
    st.markdown(f"<span class='{badge_class}'>{badge_text}</span>", unsafe_allow_html=True)

    target_language = st.session_state.get("target_language", "English")
    voice_note = " · 🎙️ voice input + 🔊 read-aloud available" if stt_available() else ""
    st.caption(f"Output language: {target_language}{voice_note}")
    st.write("")

    if mode == "keyword":
        st.info(
            "Running on plain keyword search over the dataset. Install "
            "`requirements-phase2.txt` for semantic search."
        )
    elif mode == "retrieval_only":
        st.info(
            "Semantic retrieval is active, but no Gemini key is set, so "
            "you'll see raw matching dance-form profiles instead of a generated answer."
        )

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "chat_contexts" not in st.session_state:
        st.session_state["chat_contexts"] = {}
    if "eval_log" not in st.session_state:
        st.session_state["eval_log"] = []

    st.markdown("<p class='prompt-label'>Try a conversation starter</p>", unsafe_allow_html=True)
    chip1, chip2, chip3, chip4 = st.columns(4)
    prompts = ["Compare Kathak and Flamenco", "Which dance is beginner-friendly?", "Tell me a surprising dance fact", "Recommend a high-energy group dance"]
    for column, text in zip((chip1, chip2, chip3, chip4), prompts):
        if column.button(text, key=f"quick_{text}", use_container_width=True):
            st.session_state["quick_prompt"] = text

    # Self-contained "chat window" panel (mac-style title bar + bounded,
    # scrollable message area + input docked to the panel's own bottom).
    st.markdown("<div class='chat-window-anchor'></div>", unsafe_allow_html=True)
    with st.container(height=620, border=True):
        status_label = "LIVE" if mode == "rag" else ("RETRIEVAL ONLY" if mode == "retrieval_only" else "KEYWORD MODE")
        st.markdown(
            "<div class='chat-window-titlebar'>"
            "<span class='dot red'></span><span class='dot yellow'></span><span class='dot green'></span>"
            "<span class='title'>💃 DanceCompass · AI Dance Guide</span>"
            f"<span class='status'><span class='pulse'></span>{status_label}</span>"
            "</div>",
            unsafe_allow_html=True,
        )

        # Every message (old and newly generated) is rendered ONLY here,
        # top to bottom, in one pass. This is what keeps chat_input pinned
        # after the last message instead of sandwiched mid-conversation --
        # new turns are appended to session_state and the page is rerun,
        # rather than rendered inline below the input on the same run.
        for i, (role, msg, lang_code) in enumerate(st.session_state["chat_history"]):
            with st.chat_message(role):
                st.markdown(msg)
                if role == "assistant":
                    contexts = st.session_state["chat_contexts"].get(i, [])
                    if contexts:
                        with st.expander(f"📚 Sources used ({len(contexts)} dance-form profiles)"):
                            for c in contexts:
                                name = c.get("name", "Unknown")
                                category = c.get("category", "")
                                badge = "🌐 curated + open-data" if c.get("has_enrichment") else "🗂️ curated dataset only"
                                st.markdown(f"**{name}** · {category} · relevance {c['score']:.2f} · {badge}")
                                st.markdown(c["text"])
                                st.markdown("---")
                    if _AUDIO_AVAILABLE:
                        tts_widget(msg, lang_code=lang_code, key=f"tts_{i}")

        try:
            prompt = st.chat_input(
                "Ask about any dance form, or record your voice...",
                accept_audio=True,
            )
            typed_text = prompt.text if prompt else st.session_state.pop("quick_prompt", None)
            audio_data = prompt.audio if prompt else None
        except TypeError:
            typed_text = st.chat_input("Ask about any dance form...") or st.session_state.pop("quick_prompt", None)
            audio_data = None

        query = None
        if audio_data is not None:
            if not stt_available():
                st.error("Speech-to-text is not enabled in this local-only build.")
            else:
                with st.spinner("Transcribing and translating your voice question to English..."):
                    try:
                        query = transcribe_and_translate(audio_data.read())
                    except Exception as e:
                        st.error(f"Voice transcription failed: {e}")
        elif typed_text:
            query = typed_text

        if query:
            st.session_state["chat_history"].append(("user", query, "en-US"))

            with st.spinner("DanceCompass is thinking..."):
                contexts = []
                if mode in ("rag", "retrieval_only"):
                    # k=5 (was 3): comparison / "which dance..." questions
                    # need more than 3 candidate profiles to answer completely.
                    contexts = st.session_state["doc_index"].search(query, k=5)

                if mode == "rag":
                    # Last few turns, so follow-ups ("what about that one",
                    # "and the beginner-friendly one from before") aren't
                    # answered as if the conversation just started.
                    history_turns = st.session_state["chat_history"][:-1][-6:]
                    conversation_history = "\n".join(
                        f"{'User' if role == 'user' else 'DanceCompass'}: {msg}" for role, msg, _ in history_turns
                    )
                    try:
                        answer = generate_rag_answer(query, contexts, domain_instructions=DOMAIN_PROMPT, conversation_history=conversation_history)
                    except Exception as e:
                        answer = f"⚠️ Gemini call failed: {e}"
                elif mode == "retrieval_only":
                    answer = "Closest matching dance-form profiles (add a Gemini key for a generated answer):\n\n" + "\n\n".join(
                        f"**{c.get('name', 'Match')}** *(score {c['score']:.2f})* — {c['text'][:280]}..." for c in contexts
                    )
                else:
                    corpus = st.session_state.get("corpus_full_text", "")
                    matches = simple_keyword_search(corpus, query)
                    answer = (
                        "Found matching passages:\n\n" + "\n\n".join(f"- {m}" for m in matches)
                        if matches
                        else "No direct keyword matches found. Try different wording, or "
                             "install Phase 2 for semantic search."
                    )

                display_answer = answer
                if mode == "rag" and target_language != "English":
                    try:
                        display_answer = translate_text(answer, target_language)
                    except Exception:
                        pass

                lang_code = LANGUAGES.get(target_language, "en-US")
                st.session_state["chat_history"].append(("assistant", display_answer, lang_code))
                st.session_state["chat_contexts"][len(st.session_state["chat_history"]) - 1] = contexts

                st.session_state["eval_log"].append(
                    {
                        "question": query,
                        "answer": answer,
                        "contexts": [c["text"] for c in contexts],
                        "mode": mode,
                        "ground_truth": "",
                    }
                )

            # Rerun so the history loop above renders this new turn in its
            # correct place, with chat_input naturally ending up after it.
            st.rerun()
