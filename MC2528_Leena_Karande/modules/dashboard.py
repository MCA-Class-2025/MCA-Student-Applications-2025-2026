"""Premium, content-first landing page for DanceCompass AI."""

import streamlit as st

from utils.dance_data import load_dance_forms


def _featured_card(dance: dict) -> None:
    st.markdown(
        f"<div class='fd-card featured-card'><p class='eyebrow'>{dance['category'].upper()}</p>"
        f"<h3>{dance['name']}</h3><p class='card-place'>{dance['origin_region']}</p>"
        f"<p>{dance['famous_for']}</p><span class='tag'>{dance['energy_level']} energy</span> "
        f"<span class='tag'>{dance['learning_difficulty']}</span></div>",
        unsafe_allow_html=True,
    )


def render() -> None:
    forms = load_dance_forms()
    st.markdown("<section class='home-hero'><div><p class='eyebrow'>CULTURE IN MOTION</p><h1>Find the rhythm<br>that moves you.</h1><p>Discover, compare, and learn from a curated collection of global dance heritage.</p></div><div class='hero-orb'>💃</div></section>", unsafe_allow_html=True)
    st.markdown("### Begin your journey")
    action1, action2, action3 = st.columns(3)
    action1.markdown("<div class='fd-card action-card'><h3>🧭 Explore</h3><p>Browse living traditions by place, style, and energy.</p></div>", unsafe_allow_html=True)
    action2.markdown("<div class='fd-card action-card'><h3>🤖 Ask the Guide</h3><p>Search the cultural knowledge library with grounded RAG.</p></div>", unsafe_allow_html=True)
    action3.markdown("<div class='fd-card action-card'><h3>🎯 Find your fit</h3><p>Take the recommender quiz and discover a matching form.</p></div>", unsafe_allow_html=True)
    st.markdown("### Featured traditions")
    picks = [next(d for d in forms if d["id"] == item) for item in ("bharatanatyam", "flamenco", "tango")]
    for column, dance in zip(st.columns(3), picks):
        with column:
            _featured_card(dance)
    st.markdown("<div class='fd-footer'>DanceCompass AI · A local-first cultural heritage platform</div>", unsafe_allow_html=True)
