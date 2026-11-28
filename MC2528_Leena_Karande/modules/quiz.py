"""Small dataset-grounded cultural quiz for the discovery experience."""

import random
import streamlit as st

from utils.dance_data import load_dance_forms


def render() -> None:
    st.markdown("## Dance Quiz")
    st.caption("A playful knowledge check based only on the DanceCompass collection.")
    forms = load_dance_forms()
    if "quiz_item" not in st.session_state:
        st.session_state["quiz_item"] = random.choice(forms)
    dance = st.session_state["quiz_item"]
    choices = [dance["name"]] + [d["name"] for d in random.sample([d for d in forms if d["id"] != dance["id"]], 3)]
    random.shuffle(choices)
    st.markdown(f"<div class='fd-card'><p class='eyebrow'>CAN YOU GUESS IT?</p><h3>Which dance form is famous for {dance['famous_for'].lower()}?</h3></div>", unsafe_allow_html=True)
    answer = st.radio("Choose one", choices, key=f"quiz_choice_{dance['id']}")
    col1, col2 = st.columns(2)
    if col1.button("Check answer", type="primary"):
        if answer == dance["name"]:
            st.success(f"Correct! {dance['fun_fact']}")
        else:
            st.error(f"Not quite — it is {dance['name']}. {dance['fun_fact']}")
    if col2.button("New question"):
        st.session_state["quiz_item"] = random.choice(forms)
        st.rerun()
