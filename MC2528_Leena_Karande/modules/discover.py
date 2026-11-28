import random
import plotly.express as px
import streamlit as st

from utils.dance_data import load_dance_forms


def _saved():
    return st.session_state.setdefault("favourite_dance_ids", set())


def _show(d, prefix):
    saved = _saved()
    head, action = st.columns([5, 1])
    head.markdown(f"### {d['name']}\n{d['category']} · {d['origin_region']}")
    if action.button("♥ Saved" if d["id"] in saved else "♡ Save", key=f"{prefix}_{d['id']}"):
        saved.symmetric_difference_update({d["id"]})
        st.rerun()
    st.markdown(f"**Known for:** {d['famous_for']}  \n**Energy:** {d['energy_level']} · **Difficulty:** {d['learning_difficulty']}")
    with st.expander("Cultural details"):
        st.markdown(f"**Music:** {d['music_style']} — {', '.join(d['instruments'])}\n\n**Costume:** {d['costume']}\n\n**Movements:** {d['key_movements']}")
        st.info(f"Did you know? {d['fun_fact']}")


def render():
    st.markdown("## Discover")
    st.markdown("<div class='fd-card'><b>Explore a curated collection, not a global census.</b> These tools navigate the dance forms included in DanceCompass; they do not measure the full diversity or popularity of world dance.</div>", unsafe_allow_html=True)
    forms = load_dance_forms()
    by_place = {}
    for d in forms:
        by_place.setdefault(d["origin_region"].split(",")[-1].strip(), []).append(d)
    tab1, tab2, tab3 = st.tabs(["Explore by place", "Surprise me", "My collection"])
    with tab1:
        points = [{"place": p, "count": len(ds)} for p, ds in by_place.items()]
        fig = px.scatter_geo(points, locations="place", locationmode="country names", size="count", hover_name="place", color="count", color_continuous_scale="Plasma")
        fig.update_layout(height=410, paper_bgcolor="rgba(0,0,0,0)", font_color="#E2E8F0", margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
        place = st.selectbox("Place represented in this collection", list(by_place))
        for d in by_place[place]: _show(d, "place")
    with tab2:
        if st.button("Show me a dance form", type="primary"): st.session_state["surprise"] = random.choice(forms)["id"]
        if choice := st.session_state.get("surprise"):
            _show(next(d for d in forms if d["id"] == choice), "surprise")
    with tab3:
        chosen = [d for d in forms if d["id"] in _saved()]
        if not chosen: st.info("No saved dance forms yet. Save one while exploring.")
        for d in chosen: _show(d, "saved")
