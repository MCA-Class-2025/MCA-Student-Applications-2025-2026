"""
app.py
------
AI Fish Identification Assistant — Streamlit app.

Flow (single continuous page):
    1. User uploads a fish photo.
    2. CNN (MobileNetV2) classifies the species.
    3. LangChain + Gemini generates a fact sheet about that fish.
    4. The fact sheet is read aloud via text-to-speech.
    5. Directly below: user can ask follow-up questions by TYPING or SPEAKING;
       speech is transcribed, answered by the LLM (with conversation memory),
       and read back aloud.

Run:
    cd src
    streamlit run app.py
"""

import hashlib
import os
import re
import sys

import streamlit as st
from streamlit_mic_recorder import mic_recorder

sys.path.append(os.path.dirname(__file__))


from noaa_utils import get_ocean_environment_for_occurrences
from noaa_utils import (
    get_ocean_environment_for_occurrences
)
from predict import FishClassifier
from llm_chain import generate_fish_info, ask_followup, LANGUAGE_NAMES
from speech_utils import speech_to_text_from_bytes, text_to_speech_bytes
from report_utils import generate_fact_sheet_pdf
from species_mapping import get_species_info
from gbif_utils import verify_species, get_distribution, get_available_countries
from nutrition_utils import get_nutrition_facts
from weather_utils import get_weather, get_weather_by_coords, get_forecast_by_coords, is_favorable, find_next_favorable_window, fishing_condition_note
from market_finder import find_nearby_seafood_places, reverse_geocode
from context_reasoning import generate_context_reasoning
from services.noaa_ocean import (
    get_ocean_environment_for_occurrences
)


st.set_page_config(
    page_title="AI Fish Identification Assistant",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="expanded",
)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "fish_classifier.h5")
CLASS_INDICES_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "class_indices.json")

FACT_ICONS = {
    "Fish Name": "🐟",
    "Scientific Name": "🔬",
    "Habitat": "🌊",
    "Nutrition": "🥗",
    "Average Weight": "⚖️",
    "Cooking Uses": "🍳",
    "Health Benefits": "💪",
}

CUSTOM_CSS = """
<style>
.stApp {
    background: linear-gradient(180deg, #071c2c 0%, #0b2f45 45%, #0e3b52 100%);
}
[data-testid="stSidebar"] {
    background: #05141f;
}
.hero {
    padding: 1.6rem 1.8rem;
    border-radius: 18px;
    background: linear-gradient(120deg, #0f4c6b 0%, #147d92 100%);
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 1.4rem;
}
.hero h1 { margin: 0; font-size: 2rem; color: #ffffff; }
.hero p { margin: 0.3rem 0 0 0; color: #d7f2f7; font-size: 1rem; }
.result-badge {
    display: inline-block;
    padding: 0.5rem 1.1rem;
    border-radius: 999px;
    background: linear-gradient(120deg, #1fb17a, #17a389);
    color: white;
    font-weight: 600;
    font-size: 1.05rem;
    margin-bottom: 0.6rem;
}
.fact-card {
    background: rgba(255,255,255,0.045);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 14px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.7rem;
}
.fact-label {
    color: #7fd8e8;
    font-weight: 700;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.15rem;
}
.fact-value { color: #f2fbfd; font-size: 1rem; line-height: 1.4; }
.qa-bubble-q {
    background: rgba(20,125,146,0.25);
    border-radius: 12px 12px 2px 12px;
    padding: 0.6rem 0.9rem;
    margin: 0.3rem 0;
    color: #eafcff;
}
.qa-bubble-a {
    background: rgba(31,177,122,0.18);
    border-radius: 12px 12px 12px 2px;
    padding: 0.6rem 0.9rem;
    margin: 0.3rem 0 0.9rem 0;
    color: #eafcff;
}
.section-divider { margin: 1.6rem 0 1rem 0; border-top: 1px solid rgba(255,255,255,0.12); }
.sidebar-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 0.7rem 0.9rem;
    margin-bottom: 0.55rem;
}
.sidebar-card-title {
    color: #ffffff;
    font-weight: 700;
    font-size: 0.92rem;
    margin-bottom: 0.15rem;
}
.sidebar-card-desc {
    color: #a9c9d4;
    font-size: 0.8rem;
    line-height: 1.35;
}
.sidebar-header {
    color: #7fd8e8;
    font-weight: 700;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0.4rem 0 0.5rem 0;
}
.sidebar-step {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 0.35rem;
    color: #dff3f7;
    font-size: 0.85rem;
    line-height: 1.4;
}
.sidebar-step-num {
    background: linear-gradient(120deg, #147d92, #1fb17a);
    color: white;
    border-radius: 50%;
    width: 18px;
    height: 18px;
    min-width: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    font-weight: 700;
}
</style>
"""


def parse_fact_sheet(text: str) -> dict:
    facts = {}
    pattern = r"(Fish Name|Scientific Name|Habitat|Nutrition|Average Weight|Cooking Uses|Health Benefits):\s*"
    parts = re.split(pattern, text)
    for i in range(1, len(parts) - 1, 2):
        label = parts[i].strip()
        value = parts[i + 1].strip()
        facts[label] = value
    return facts


def render_fact_sheet(text: str):
    facts = parse_fact_sheet(text)
    if not facts:
        st.markdown(text)
        return
    cols = st.columns(2)
    for idx, (label, value) in enumerate(facts.items()):
        icon = FACT_ICONS.get(label, "📌")
        with cols[idx % 2]:
            st.markdown(
                f"""<div class="fact-card">
                        <div class="fact-label">{icon} {label}</div>
                        <div class="fact-value">{value}</div>
                    </div>""",
                unsafe_allow_html=True,
            )


@st.cache_resource
def load_classifier():
    return FishClassifier(MODEL_PATH, CLASS_INDICES_PATH)


def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    st.markdown(
        """<div class="hero">
                <h1>🐟 AI Fish Identification Assistant</h1>
                <p>Upload a photo of an Indian seafood fish — a CNN identifies the species,
                Gemini writes a fact sheet, and you can ask follow-up questions by voice or text.</p>
            </div>""",
        unsafe_allow_html=True,
    )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "current_fish" not in st.session_state:
        st.session_state.current_fish = None

    with st.sidebar:
        st.markdown(
            """<div style="text-align:center; padding: 0.4rem 0 1rem 0;">
                    <span style="font-size:1.8rem;">🐟</span><br>
                    <span style="color:#fff; font-weight:700; font-size:1.05rem;">Fish AI Assistant</span>
                </div>""",
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-header">🌐 Output Language</div>', unsafe_allow_html=True)
        language_label = st.selectbox(
            "Fact sheets and answers will be generated in:",
            options=["English", "Hindi (हिन्दी)", "Marathi (मराठी)"],
            index=0,
            label_visibility="collapsed",
        )
        language_code = {"English": "en", "Hindi (हिन्दी)": "hi", "Marathi (मराठी)": "mr"}[language_label]
        st.session_state.language = language_code

        st.markdown('<div class="sidebar-header">🧭 How It Works</div>', unsafe_allow_html=True)
        steps = [
            "Upload a fish photo",
            "CNN predicts the species",
            "RAG + Gemini writes a grounded fact sheet",
            "Text-to-speech reads it aloud",
            "Ask anything, by typing or speaking",
        ]
        for i, step in enumerate(steps, 1):
            st.markdown(
                f'<div class="sidebar-step"><span class="sidebar-step-num">{i}</span><span>{step}</span></div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="sidebar-header">🐠 Supported Species</div>', unsafe_allow_html=True)
        species_list = ["Pomfret", "Black Pomfret", "Rohu", "Mackerel", "Tilapia", "Prawn", "Rani Fish", "Bhetki"]
        pills_html = "".join(f'<span class="species-pill">{s}</span>' for s in species_list)
        st.markdown(pills_html, unsafe_allow_html=True)

        st.markdown('<div class="sidebar-header">🔌 External APIs Used</div>', unsafe_allow_html=True)
        api_cards = [
            ("Google Gemini", "Generates fact sheets & answers, via LangChain"),
            ("FAISS + Google Embeddings", "Retrieves grounding facts (RAG) before generation"),
            ("GBIF", "Verifies taxonomy & shows real catch/sighting locations — no key needed"),
            ("USDA FoodData Central", "Real, verified nutrition data per 100g"),
            ("OpenWeatherMap", "Live weather + go/no-go fishing conditions"),
            ("OpenStreetMap", "Finds nearby seafood markets — no key needed"),
        ]
        for name, desc in api_cards:
            st.markdown(
                f'<div class="sidebar-card"><div class="sidebar-card-title">{name}</div>'
                f'<div class="sidebar-card-desc">{desc}</div></div>',
                unsafe_allow_html=True,
            )

        if st.session_state.chat_history:
            st.markdown('<div class="sidebar-header">💬 Conversation</div>', unsafe_allow_html=True)
            if st.button("🗑️ Clear conversation", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

    # ----------------------------------------------------------------- #
    # SECTION 1 — Identify
    # ----------------------------------------------------------------- #
    try:
        classifier = load_classifier()
        model_ready = True
    except FileNotFoundError:
        model_ready = False
        st.warning(
            "⚠️ No trained model found yet. Run `split_dataset.py` then "
            "`train_cnn.py` first (see README). You can still try the LLM "
            "explanation below by typing a fish name manually."
        )

    st.markdown("### 1️⃣ Identify a fish")
    col_upload, col_result = st.columns([1, 1.3], gap="large")
    label = None  # tracked across both branches below, used by the "Explore More" section afterward

    with col_upload:
        uploaded_file = st.file_uploader("Upload a fish image", type=["jpg", "jpeg", "png"])
        manual_fish_name = None
        if not model_ready:
            manual_fish_name = st.text_input("Or type a fish name to test the LLM explanation:")
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Uploaded image", width="stretch")

    info_text = None
    with col_result:
        if uploaded_file is not None and model_ready:
            # Streamlit reruns this whole script on every interaction (e.g. typing
            # a follow-up question). Without caching, that would re-run the CNN
            # AND call Gemini again on every keystroke, burning API quota fast.
            # We cache results per (image, language) so they're computed once.
            cache_key = (uploaded_file.file_id, st.session_state.language)

            if st.session_state.get("cache_key") != cache_key:
                tmp_path = os.path.join(os.path.dirname(__file__), "_tmp_upload.jpg")
                with open(tmp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                with st.spinner("🔍 Classifying fish species..."):
                    label, confidence, top3 = classifier.predict(tmp_path)
                os.remove(tmp_path)

                st.session_state.current_fish = label

                try:
                    with st.spinner("✍️ Asking Gemini to write a fact sheet..."):
                        info_text = generate_fish_info(label, confidence, language=st.session_state.language)
                except Exception as e:
                    st.error(
                        f"⚠️ Couldn't reach Gemini ({type(e).__name__}: {e}). "
                        "Check your `.env` API key, your internet connection, "
                        "or you may have hit the free-tier daily quota — see "
                        "https://ai.google.dev/gemini-api/docs/rate-limits"
                    )
                    info_text = None

                # Cache everything for this image so later reruns (e.g. asking
                # a follow-up question) reuse it instead of calling the API again.
                st.session_state.cache_key = cache_key
                st.session_state.cached_label = label
                st.session_state.cached_confidence = confidence
                st.session_state.cached_top3 = top3
                st.session_state.cached_info_text = info_text

                cached_audio = None
                if info_text:
                    try:
                        with st.spinner("🔊 Generating audio..."):
                            cached_audio = text_to_speech_bytes(info_text, lang=st.session_state.language)
                    except Exception as e:
                        st.warning(f"⚠️ Fact sheet generated, but audio failed: {e}")
                st.session_state.cached_audio = cached_audio
            else:
                # Same image + language as last run — reuse cached results, no API call.
                label = st.session_state.cached_label
                confidence = st.session_state.cached_confidence
                top3 = st.session_state.cached_top3
                info_text = st.session_state.cached_info_text

            st.markdown(
                f'<div class="result-badge">🐟 {label} · {confidence:.1%} confidence</div>',
                unsafe_allow_html=True,
            )
            with st.expander("See top 3 predictions"):
                for cls, conf in top3:
                    st.progress(conf, text=f"{cls} — {conf:.1%}")

            if info_text:
                st.markdown("#### 📋 Fish Fact Sheet")
                render_fact_sheet(info_text)

                if st.session_state.get("cached_audio"):
                    st.audio(st.session_state.cached_audio, format="audio/mp3")

                dl_col1, dl_col2 = st.columns(2)
                with dl_col1:
                    st.download_button(
                        "⬇️ Download as .txt",
                        data=info_text,
                        file_name=f"{label.replace(' ', '_')}_fact_sheet.txt",
                        mime="text/plain",
                    )
                with dl_col2:
                    pdf_bytes = generate_fact_sheet_pdf(f"{label} — Fish Fact Sheet", info_text)
                    st.download_button(
                        "⬇️ Download as PDF",
                        data=pdf_bytes,
                        file_name=f"{label.replace(' ', '_')}_fact_sheet.pdf",
                        mime="application/pdf",
                    )

        elif manual_fish_name:
            label = manual_fish_name
            st.session_state.current_fish = manual_fish_name
            try:
                with st.spinner("✍️ Asking Gemini..."):
                    info_text = generate_fish_info(manual_fish_name, 1.0, language=st.session_state.language)
                st.markdown("#### 📋 Fish Fact Sheet")
                render_fact_sheet(info_text)
                audio_bytes = text_to_speech_bytes(info_text, lang=st.session_state.language)
                st.audio(audio_bytes, format="audio/mp3")
            except Exception as e:
                st.error(f"⚠️ Couldn't reach Gemini ({type(e).__name__}: {e}).")
        else:
            st.info("👈 Upload a fish photo to get started.")

    # ----------------------------------------------------------------- #
    # SECTION 1.5 — Explore More (lazy-loaded external data APIs)
    # ----------------------------------------------------------------- #
    # IMPORTANT:
    # _cached_distribution MUST be defined before both the
    # "Distribution" and "Fishing Grounds" branches.
    # Otherwise selecting Fishing Grounds directly causes:
    # UnboundLocalError: _cached_distribution
    # ----------------------------------------------------------------- #
    if label:
        species_info = get_species_info(label)

        if species_info:
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            st.markdown("### 🔎 Explore More")
            st.caption(
                f"Real-world data for **{species_info['common_name']}** "
                f"(*{species_info['scientific_name']}*) from external sources — "
                "not generated by the LLM."
            )

            sci_name = species_info["scientific_name"]
            common_name = species_info["common_name"]

            explore_options = [
                "🧬 Taxonomy",
                "🥗 USDA Nutrition",
                "🗺️ Distribution",
                "🎣 Fishing Grounds",
                "📍 Nearby Markets",
                "☁️ Weather",
            ]

            if "explore_section" not in st.session_state:
                st.session_state.explore_section = explore_options[0]

            if st.session_state.explore_section not in explore_options:
                st.session_state.explore_section = explore_options[0]

            selected_explore = st.radio(
                "Explore More section",
                explore_options,
                horizontal=True,
                key="explore_section",
                label_visibility="collapsed",
            )

            # ==========================================================
            # ALL SHARED CACHED FUNCTIONS
            # ==========================================================
            # Define these BEFORE the branch that uses them.
            # In particular, _cached_distribution is shared by both
            # Distribution and Fishing Grounds.
            # ==========================================================

            @st.cache_data(ttl=3600, show_spinner=False)
            def _cached_taxonomy(scientific_name):
                return verify_species(scientific_name)

            @st.cache_data(ttl=3600, show_spinner=False)
            def _cached_nutrition(name, common_name_value):
                return get_nutrition_facts(
                    name,
                    common_name=common_name_value,
                )

            @st.cache_data(ttl=3600, show_spinner=False)
            def _cached_distribution(scientific_name, country=None):
                return get_distribution(
                    scientific_name,
                    limit=100,
                    country=country,
                )

            @st.cache_data(ttl=3600, show_spinner=False)
            def _cached_countries(scientific_name):
                return get_available_countries(
                    scientific_name,
                    top_n=15,
                )

            @st.cache_data(ttl=900, show_spinner=False)
            def _cached_weather_coords(lat, lon):
                return get_weather_by_coords(lat, lon)

            @st.cache_data(ttl=900, show_spinner=False)
            def _cached_forecast_coords(lat, lon):
                return get_forecast_by_coords(lat, lon)

            @st.cache_data(ttl=86400, show_spinner=False)
            def _cached_reverse_geocode(lat, lon):
                return reverse_geocode(lat, lon)

            @st.cache_data(ttl=1800, show_spinner=False)
            def _cached_markets(city):
                return find_nearby_seafood_places(
                    city,
                    radius_km=5,
                )

            @st.cache_data(ttl=900, show_spinner=False)
            def _cached_weather(city):
                return get_weather(city)

            # ==========================================================
            # TAXONOMY
            # ==========================================================

            if selected_explore == "🧬 Taxonomy":

                with st.spinner("Verifying with GBIF..."):
                    taxonomy = _cached_taxonomy(sci_name)

                if taxonomy:
                    st.success(
                        f"✅ Verified: **{taxonomy['canonical_name']}** — a recognized "
                        "species in GBIF's global biodiversity taxonomy."
                    )

                    tcols = st.columns(3)
                    tcols[0].metric(
                        "Family",
                        taxonomy.get("family") or "—",
                    )
                    tcols[1].metric(
                        "Order",
                        taxonomy.get("order") or "—",
                    )
                    tcols[2].metric(
                        "Class",
                        taxonomy.get("class") or "—",
                    )

                    st.caption(
                        f"GBIF match confidence: {taxonomy.get('confidence')}% · "
                        f"Taxonomic status: {taxonomy.get('status')}"
                    )

                else:
                    st.info(
                        "Couldn't verify against GBIF right now "
                        "(species not found, or a connection issue)."
                    )

            # ==========================================================
            # USDA NUTRITION
            # ==========================================================

            elif selected_explore == "🥗 USDA Nutrition":

                with st.spinner("Fetching USDA nutrition data..."):
                    nutrition = _cached_nutrition(
                        common_name,
                        common_name,
                    )

                if nutrition:

                    if nutrition.get("used_generic_fallback"):
                        st.caption(
                            f"⚠️ USDA doesn't stock '{common_name}' by name — "
                            f"showing the closest equivalent: "
                            f"*{nutrition['matched_food_name']}*"
                        )
                    else:
                        st.caption(
                            f"Matched USDA entry: *{nutrition['matched_food_name']}*"
                        )

                    items = list(
                        nutrition["nutrients_per_100g"].items()
                    )

                    ncols = st.columns(3)

                    for i, (nut_name, nut_val) in enumerate(items):
                        ncols[i % 3].metric(
                            nut_name,
                            nut_val,
                        )

                    st.caption(
                        "Values per 100g, raw — sourced from USDA FoodData Central."
                    )

                elif not os.getenv("USDA_API_KEY"):
                    st.info(
                        "Add a free USDA_API_KEY to your .env to enable real "
                        "nutrition data (see README)."
                    )

                else:
                    st.info(
                        "No USDA nutrition match found for this species, "
                        "even with the fallback."
                    )

            # ==========================================================
            # GLOBAL DISTRIBUTION
            # ==========================================================

            elif selected_explore == "🗺️ Distribution":

                with st.spinner(
                    "Fetching real occurrence records from GBIF..."
                ):
                    distribution = _cached_distribution(
                        sci_name,
                        None,
                    )

                if distribution:
                    st.caption(
                        f"{distribution['total_records']} real occurrence records "
                        "found worldwide (showing up to 100 on the map)."
                    )

                    map_points = [
                        {
                            "lat": p["lat"],
                            "lon": p["lon"],
                        }
                        for p in distribution["points"]
                    ]

                    if map_points:
                        st.map(
                            map_points,
                            size=6,
                        )

                    st.markdown("**Most commonly recorded in:**")

                    for country_name, count in distribution["countries"][:5]:
                        st.write(
                            f"- {country_name} — {count} records"
                        )

                else:
                    st.info(
                        "No distribution records found on GBIF for this species."
                    )

            # ==========================================================
            # FISHING GROUNDS
            # ==========================================================

            elif selected_explore == "🎣 Fishing Grounds":

                st.caption(
                    "Real recorded sighting/catch locations for this species, "
                    "from GBIF's global biodiversity database. Pick a country "
                    "below to see only where GBIF actually has records for this "
                    "species — each location checked against current weather "
                    "for a go/no-go read. This reflects recorded sightings, not "
                    "official fishing-zone regulations — always follow local "
                    "fishing laws and coast guard guidance."
                )

                with st.spinner(
                    "Checking which countries have records of this species..."
                ):
                    available_countries = _cached_countries(
                        sci_name
                    )

                if not available_countries:
                    st.info(
                        "Couldn't determine which countries have GBIF records "
                        "for this species right now."
                    )

                else:
                    country_options = [
                        f"{c['name']} ({c['count']} records)"
                        for c in available_countries
                    ]

                    default_idx = next(
                        (
                            i
                            for i, c in enumerate(available_countries)
                            if c["code"] == "IN"
                        ),
                        0,
                    )

                    selected_label = st.selectbox(
                        "Country (only showing countries where this species has real GBIF records):",
                        options=country_options,
                        index=default_idx,
                        key="fishing_country",
                    )

                    selected_country = available_countries[
                        country_options.index(selected_label)
                    ]

                    with st.spinner(
                        f"Fetching catch locations in {selected_country['name']}..."
                    ):
                        grounds = _cached_distribution(
                            sci_name,
                            selected_country["code"],
                        )

                    if not grounds:
                        st.info(
                            f"No detailed occurrence points found for "
                            f"{selected_country['name']} right now."
                        )

                    else:
                        st.success(
                            f"{grounds['total_records']} recorded locations "
                            f"found in {selected_country['name']}."
                        )

                        all_points = [
                            {
                                "lat": p["lat"],
                                "lon": p["lon"],
                            }
                            for p in grounds["points"]
                        ]

                        if all_points:
                            st.map(
                                all_points,
                                size=8,
                                color="#ff4b4b",
                            )

                        if not os.getenv("OPENWEATHER_API_KEY"):
                            st.info(
                                "Add a free OPENWEATHER_API_KEY to your .env "
                                "to see live weather and go/no-go advice for "
                                "these locations (see README)."
                            )

                        else:
                            seen_clusters = set()
                            representative_points = []

                            for point in grounds["points"]:
                                cluster_key = (
                                    round(point["lat"]),
                                    round(point["lon"]),
                                )

                                if cluster_key not in seen_clusters:
                                    seen_clusters.add(cluster_key)
                                    representative_points.append(point)

                                if len(representative_points) >= 5:
                                    break

                            st.markdown(
                                f"**Conditions at {len(representative_points)} "
                                "representative locations:**"
                            )

                            for point in representative_points:
                                lat = point["lat"]
                                lon = point["lon"]

                                with st.spinner(
                                    f"Checking conditions near "
                                    f"({lat:.2f}, {lon:.2f})..."
                                ):
                                    place_name = (
                                        _cached_reverse_geocode(
                                            lat,
                                            lon,
                                        )
                                        or f"({lat:.2f}, {lon:.2f})"
                                    )

                                    current = _cached_weather_coords(
                                        lat,
                                        lon,
                                    )

                                with st.container(border=True):
                                    st.markdown(
                                        f"**📍 {place_name}**"
                                    )

                                    if not current:
                                        st.caption(
                                            "Couldn't fetch weather for this "
                                            "location right now."
                                        )
                                        continue

                                    wcols = st.columns(3)

                                    wcols[0].metric(
                                        "Temp",
                                        f"{current['temperature_c']}°C",
                                    )

                                    wcols[1].metric(
                                        "Condition",
                                        current["description"],
                                    )

                                    wcols[2].metric(
                                        "Wind",
                                        f"{current['wind_speed_mps']} m/s",
                                    )

                                    if is_favorable(current):
                                        st.success(
                                            "✅ Favorable conditions right now "
                                            "— a reasonable time to go out."
                                        )

                                    else:
                                        st.warning(
                                            "⚠️ Not ideal right now "
                                            "(rain/storm or high wind)."
                                        )

                                    with st.spinner(
                                        "Checking the 5-day forecast for "
                                        "the next favorable window..."
                                    ):
                                        forecast = _cached_forecast_coords(
                                            lat,
                                            lon,
                                        )

                                    next_window = (
                                        find_next_favorable_window(
                                            forecast
                                        )
                                        if forecast
                                        else None
                                    )

                                    if next_window:
                                        st.caption(
                                            f"🕒 Next likely favorable window: "
                                            f"**{next_window['datetime']}** — "
                                            f"{next_window['description']}, "
                                            f"wind {next_window['wind_speed_mps']} m/s."
                                        )
                                    else:
                                        st.caption(
                                            "No clearly favorable window found "
                                            "in the next 5 days — check back "
                                            "closer to the time."
                                        )

            # ==========================================================
            # NEARBY MARKETS
            # ==========================================================

            elif selected_explore == "📍 Nearby Markets":

                st.caption(
                    "Note: OpenStreetMap doesn't track which specific fish "
                    "species each market sells — this shows general seafood "
                    "markets/shops nearby, not verified "
                    f"{common_name} sellers specifically."
                )

                location = st.text_input(
                    "Enter your city/area:",
                    key="market_location",
                    placeholder="e.g. Mumbai, Pune, Chennai",
                )

                if location:
                    with st.spinner(
                        "Searching OpenStreetMap for nearby seafood shops..."
                    ):
                        places = _cached_markets(location)

                    if places:
                        for place in places:
                            st.write(
                                f"🐟 **{place['name']}** "
                                f"({place['type']})"
                            )

                        market_points = [
                            {
                                "lat": place["lat"],
                                "lon": place["lon"],
                            }
                            for place in places
                            if place.get("lat") is not None
                            and place.get("lon") is not None
                        ]

                        if market_points:
                            st.map(
                                market_points,
                                size=8,
                            )

                    else:
                        st.info(
                            "No seafood shops/markets found nearby, even after "
                            "widening the search radius. This can mean the area "
                            "genuinely has sparse OpenStreetMap coverage, or the "
                            "free Overpass service was briefly slow — try again, "
                            "or try a bigger nearby city."
                        )

            # ==========================================================
            # WEATHER
            # ==========================================================

            elif selected_explore == "☁️ Weather":

                weather_location = st.text_input(
                    "Enter your city:",
                    key="weather_location",
                    placeholder="e.g. Mumbai, Pune, Chennai",
                )

                if weather_location:
                    with st.spinner("Fetching weather..."):
                        weather = _cached_weather(
                            weather_location
                        )

                    if weather:
                        wcols = st.columns(3)

                        wcols[0].metric(
                            "Temperature",
                            f"{weather['temperature_c']}°C",
                        )

                        wcols[1].metric(
                            "Condition",
                            weather["description"],
                        )

                        wcols[2].metric(
                            "Humidity",
                            f"{weather['humidity_pct']}%",
                        )

                        st.caption(
                            fishing_condition_note(weather)
                        )

                    elif not os.getenv("OPENWEATHER_API_KEY"):
                        st.info(
                            "Add a free OPENWEATHER_API_KEY to your .env "
                            "to enable weather data (see README)."
                        )

                    else:
                        st.info(
                            "Couldn't find weather for that location."
                        )

    # ----------------------------------------------------------------- #
    # SECTION 2 — Ask (directly below, same page, same flow)
    # ----------------------------------------------------------------- #
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("### 2️⃣ Ask a follow-up question")
    if st.session_state.current_fish:
        st.caption(f"Currently discussing: **{st.session_state.current_fish}**")
    else:
        st.caption("Type a question, or record your voice and it will be transcribed automatically.")

    col_type, col_mic = st.columns([3, 1])
    with col_type:
        typed_question = st.text_input(
            "Type your question", key="typed_q",
            placeholder="e.g. Is this fish good for weight loss?"
        )
        ask_clicked = st.button("💬 Ask")
    with col_mic:
        st.write("")
        audio = mic_recorder(start_prompt="🎤 Record", stop_prompt="⏹ Stop", key="recorder")

    # A question can come from two independent sources — typing + clicking "Ask",
    # or recording a new voice clip. We handle them separately instead of one
    # "question" variable with an if/elif, because that let a stale typed
    # question silently keep winning over a freshly recorded voice question.
    question = None

    if ask_clicked and typed_question.strip():
        # st.button() only returns True on the exact rerun it was clicked —
        # never on unrelated reruns — so this naturally fires once per click.
        question = typed_question.strip()

    elif audio and audio.get("bytes"):
        # mic_recorder keeps returning the SAME last recording on every rerun
        # until you record again, so we hash the audio bytes and only process
        # it when the hash actually changes (i.e. a genuinely new recording).
        audio_hash = hashlib.md5(audio["bytes"]).hexdigest()
        if audio_hash != st.session_state.get("last_audio_hash"):
            st.session_state.last_audio_hash = audio_hash
            with st.spinner("🎙️ Transcribing your voice..."):
                question = speech_to_text_from_bytes(audio["bytes"], suffix=".wav")
            st.info(f'You said: "{question}"')

    if question:
        context_note = (
            f" (regarding the {st.session_state.current_fish})"
            if st.session_state.current_fish else ""
        )
        try:
            with st.spinner("🤔 Thinking..."):
                answer = ask_followup(question + context_note, language=st.session_state.language)
        except Exception as e:
            st.error(
                f"⚠️ Couldn't get an answer from Gemini ({type(e).__name__}: {e}). "
                "This is usually a rate limit, network timeout, or an invalid API key — "
                "check your `.env` file and try again in a moment."
            )
            answer = None

        if answer:
            st.session_state.chat_history.append((question, answer))
            st.session_state.last_answered_question = question
            st.session_state.last_answer = answer

            try:
                st.session_state.last_answer_audio = text_to_speech_bytes(answer, lang=st.session_state.language)
            except Exception as e:
                st.warning(f"⚠️ Got the answer, but couldn't generate audio: {e}")
                st.session_state.last_answer_audio = None

    # Show the most recent Q&A even on reruns that weren't triggered by a new
    # question (e.g. you switched the language dropdown) — otherwise the
    # answer would vanish from view even though it's still the current one.
    if st.session_state.get("last_answer"):
        st.markdown(f'<div class="qa-bubble-q">🧑 {st.session_state.last_answered_question}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="qa-bubble-a">🤖 {st.session_state.last_answer}</div>', unsafe_allow_html=True)
        if st.session_state.get("last_answer_audio"):
            st.audio(st.session_state.last_answer_audio, format="audio/mp3")

    if st.session_state.chat_history:
        with st.expander(f"📜 Full conversation ({len(st.session_state.chat_history)} messages)"):
            for q, a in st.session_state.chat_history:
                st.markdown(f'<div class="qa-bubble-q">🧑 {q}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="qa-bubble-a">🤖 {a}</div>', unsafe_allow_html=True)




if __name__ == "__main__":
    main()