import pandas as pd
import streamlit as st

from utils.dance_data import load_dance_forms


def render():
    st.markdown("## Compare Dance Forms")
    st.caption("Compare facts from DanceCompass's curated collection; it does not claim global coverage.")
    forms = load_dance_forms()
    by_name = {d["name"]: d for d in forms}
    names = list(by_name)
    a, b = st.columns(2)
    with a:
        left_name = st.selectbox("First dance form", names, index=names.index("Kathak"))
    with b:
        choices = [n for n in names if n != left_name]
        right_name = st.selectbox("Second dance form", choices, index=choices.index("Flamenco") if "Flamenco" in choices else 0)
    left, right = by_name[left_name], by_name[right_name]
    fields = [
        ("Category", "category"), ("Origin", "origin_region"), ("Era / history", "era_origin"),
        ("Music", "music_style"), ("Costume", "costume"), ("Key movements", "key_movements"),
        ("Energy", "energy_level"), ("Formation", "solo_or_partner"),
        ("Difficulty", "learning_difficulty"), ("Known for", "famous_for"),
    ]
    rows = [(label, left[key], right[key]) for label, key in fields]
    rows.insert(4, ("Instruments", ", ".join(left["instruments"]), ", ".join(right["instruments"])))
    rows.insert(9, ("Mood / style", ", ".join(left["mood_style"]), ", ".join(right["mood_style"])))
    st.dataframe(pd.DataFrame(rows, columns=["Feature", left_name, right_name]), hide_index=True, use_container_width=True)
    x, y = st.columns(2)
    x.info(f"Did you know? {left['fun_fact']}")
    y.info(f"Did you know? {right['fun_fact']}")
