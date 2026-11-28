import streamlit as st

from utils.dance_data import load_dance_forms, score_matches
from utils.translate import LANGUAGES, translate_text

try:
    from utils.llm import gemini_available, ask_llm
    _LLM_LIBS_AVAILABLE = True
except ImportError:
    _LLM_LIBS_AVAILABLE = False

    def gemini_available():
        return False

try:
    from utils.audio import tts_widget
    _AUDIO_AVAILABLE = True
except ImportError:
    _AUDIO_AVAILABLE = False


def _grounded_explanation(matches: list[dict], energy_label: str, wants_partner: bool,
                          wants_traditional: bool, wants_expressive: bool) -> str:
    """Reliable explanation built directly from the scored profile data."""
    format_preference = "partner-based" if wants_partner else "solo or independent"
    roots_preference = "traditional and cultural" if wants_traditional else "modern and global"
    movement_preference = "expressive storytelling" if wants_expressive else "free-flowing movement"
    lines = [
        f"Your choices point to **{energy_label.lower()}** energy, a **{format_preference}** format, "
        f"and **{roots_preference}** styles with **{movement_preference}**.",
    ]
    for dance in matches:
        lines.append(
            f"- **{dance['name']}** — Its **{dance['energy_level']}** energy and "
            f"**{dance['solo_or_partner'].lower()}** format make it a strong match. "
            f"You may enjoy its {', '.join(dance['mood_style'][:2])} character; it is known for {dance['famous_for'].lower()}."
        )
    lines.append(f"**Best first step:** Start by exploring **{matches[0]['name']}**, your highest-scoring match, and try a beginner introduction before committing to a class.")
    return "\n\n".join(lines)


def render():
    st.markdown("## 🎯 Find Your Dance Form")
    st.markdown(
        "<div class='fd-card'>Answer a few quick questions. Matching is done "
        "with a transparent scoring rule over the same dataset used by the "
        "AI Guide (not a black-box guess) -- then, if a Gemini key is set, "
        "the LLM writes up a friendly explanation grounded in the matched "
        "profiles.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    energy_label = st.select_slider(
        "How much energy do you want to bring?",
        options=["Calm & graceful", "Relaxed", "Balanced", "Energetic", "High-intensity & athletic"],
        value="Balanced",
    )
    energy_map = {
        "Calm & graceful": 1, "Relaxed": 2, "Balanced": 3,
        "Energetic": 4, "High-intensity & athletic": 5,
    }

    wants_partner = st.radio(
        "Do you want to dance with a partner, or on your own?",
        ["On my own", "With a partner"],
    ) == "With a partner"

    wants_traditional = st.radio(
        "Cultural/traditional roots, or a modern/global style?",
        ["Traditional / cultural", "Modern / global"],
    ) == "Traditional / cultural"

    wants_expressive = st.radio(
        "Storytelling & expression, or free-flowing movement?",
        ["Storytelling & expression", "Free-flowing movement"],
    ) == "Storytelling & expression"

    if st.button("✨ Find my matches"):
        dance_forms = load_dance_forms()
        matches = score_matches(
            dance_forms,
            desired_energy=energy_map[energy_label],
            wants_partner=wants_partner,
            wants_traditional=wants_traditional,
            wants_expressive=wants_expressive,
            top_n=3,
        )
        st.session_state["quiz_matches"] = matches

    matches = st.session_state.get("quiz_matches")
    if not matches:
        return

    st.markdown("### Your top matches")
    for i, d in enumerate(matches):
        st.markdown(
            f"<div class='fd-card'><b>{i+1}. {d['name']}</b> "
            f"<span style='color:#94A3B8;'>({d['category']}, {d['origin_region']})</span><br>"
            f"Energy: {d['energy_level']} · {d['solo_or_partner']} · {', '.join(d['mood_style'])}<br>"
            f"{d['famous_for']}</div>",
            unsafe_allow_html=True,
        )

    has_llm = _LLM_LIBS_AVAILABLE and gemini_available()
    target_language = st.session_state.get("target_language", "English")

    if has_llm:
        key = "quiz_explanation_" + "_".join(d["id"] for d in matches)
        if st.button("💬 Explain why these fit me"):
            context = "\n\n".join(
                f"{d['name']}: {d['famous_for']}. Energy {d['energy_level']}, "
                f"{d['solo_or_partner']}, mood: {', '.join(d['mood_style'])}. "
                f"{d['fun_fact']}"
                for d in matches
            )
            system_prompt = (
                "You are a warm, precise dance guide. Use ONLY the supplied "
                "matched profiles. Write a helpful recommendation with this exact "
                "format: a one-sentence opening, then three Markdown bullets—one "
                "for each named dance—explaining the specific match using its energy, "
                "formation, and mood/style. End with one short 'Best first step' sentence. "
                "Never answer with a single word, score, heading, or generic advice. "
                "Do not invent facts."
            )
            user_prompt = (
                f"User wants energy level '{energy_label}', "
                f"{'a partner' if wants_partner else 'to dance solo'}, "
                f"{'traditional/cultural' if wants_traditional else 'modern/global'} style, "
                f"{'storytelling/expressive' if wants_expressive else 'free-flowing'} movement.\n\n"
                f"Matched dance forms:\n{context}"
            )
            with st.spinner("Writing your explanation..."):
                try:
                    explanation = ask_llm(system_prompt, user_prompt, max_tokens=320)
                    if len(explanation.split()) < 35:
                        explanation = _grounded_explanation(matches, energy_label, wants_partner, wants_traditional, wants_expressive)
                except Exception as e:
                    st.session_state[key] = _grounded_explanation(matches, energy_label, wants_partner, wants_traditional, wants_expressive)
                    st.info("Showing a reliable explanation generated directly from your quiz matches.")
                final_explanation = st.session_state.get(key, explanation if 'explanation' in locals() else "")
                if target_language != "English":
                    try:
                        final_explanation = translate_text(final_explanation, target_language)
                    except Exception as translation_error:
                        st.warning(f"Translation is temporarily unavailable: {translation_error}")
                st.session_state[key] = final_explanation
        if key in st.session_state:
            st.markdown(f"<div class='fd-card'>{st.session_state[key]}</div>", unsafe_allow_html=True)
            if _AUDIO_AVAILABLE:
                lang_code = LANGUAGES.get(target_language, "en-US")
                tts_widget(st.session_state[key], lang_code=lang_code, key="tts_quiz_explanation")
    else:
        st.caption("Add a Gemini API key in the sidebar for a written explanation of your matches.")
