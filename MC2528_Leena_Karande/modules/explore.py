import math

import streamlit as st

from utils.dance_data import categories, filter_forms, load_dance_forms
from utils.merged_data import get_enrichment, merged_data_available, musicbrainz_link, openlibrary_link, youtube_link

_DISAMBIGUATION_MARKERS = ("topics referred to by the same term", "may refer to")


def _clean(value) -> str:
    """Merged-CSV cells come back as NaN (float) for missing values."""
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def _is_disambiguation_junk(description: str, extract: str) -> bool:
    """Defensive check: if the merged CSV still has an un-refreshed
    disambiguation-page match (see scripts/refresh_enrichment.py), don't
    show it -- it's not useful to the person and it's not really about
    the dance form."""
    combined = f"{description} {extract}".lower()
    return any(marker in combined for marker in _DISAMBIGUATION_MARKERS)


def _render_enrichment(dance_id: str) -> None:
    if not merged_data_available():
        return
    row = get_enrichment(dance_id)
    if not row:
        return

    thumb = _clean(row.get("wikipedia_thumbnail_url"))
    extract = _clean(row.get("wikipedia_extract"))
    wiki_url = _clean(row.get("wikipedia_url"))
    wikidata_desc = _clean(row.get("wikidata_description"))
    wikidata_url = _clean(row.get("wikidata_url"))
    location = _clean(row.get("location_display_name")) or _clean(row.get("country"))

    # Guard against un-refreshed disambiguation-page matches (e.g. "Manipuri
    # may refer to..."). See scripts/refresh_enrichment.py.
    if _is_disambiguation_junk(wikidata_desc, extract):
        thumb, extract, wikidata_desc = "", "", ""

    if not any([thumb, extract, wikidata_desc, location, _clean(row.get("book_1_title")), _clean(row.get("music_recording_1_title"))]):
        return

    st.markdown("---")
    st.markdown("**🌐 From open data sources**")

    img_col, text_col = st.columns([1, 2]) if thumb else (None, st.container())
    if thumb:
        with img_col:
            st.image(thumb, use_container_width=True)
    with text_col:
        if extract:
            st.write(extract)
        if wikidata_desc:
            st.caption(f"Wikidata: {wikidata_desc}")
        links = []
        if wiki_url:
            links.append(f"[Wikipedia]({wiki_url})")
        if wikidata_url:
            links.append(f"[Wikidata]({wikidata_url})")
        if links:
            st.markdown(" · ".join(links))
        if location:
            st.markdown(f"📍 **Origin (geocoded):** {location}")

    book_col, music_col = st.columns(2)
    with book_col:
        books = []
        for i in (1, 2, 3):
            title = _clean(row.get(f"book_{i}_title"))
            if title:
                author = _clean(row.get(f"book_{i}_author"))
                year = _clean(row.get(f"book_{i}_year"))
                meta = " · ".join(v for v in (author, year) if v)
                link = openlibrary_link(row, i)
                label = f"{title}" + (f" ({meta})" if meta else "")
                books.append(f"- [{label}]({link})" if link else f"- {label}")
        if books:
            st.markdown("📚 **Further reading** *(links open Open Library)*")
            st.markdown("\n".join(books))

    with music_col:
        tracks = []
        for i in (1, 2, 3):
            title = _clean(row.get(f"music_recording_{i}_title"))
            if title:
                artist = _clean(row.get(f"music_recording_{i}_artist"))
                label = f"{title}" + (f" — {artist}" if artist else "")
                mb_link, yt_link = musicbrainz_link(row, i), youtube_link(row, i)
                line = f"- {label}"
                link_bits = []
                if mb_link:
                    link_bits.append(f"[MusicBrainz]({mb_link})")
                if yt_link:
                    link_bits.append(f"[Listen on YouTube]({yt_link})")
                if link_bits:
                    line += "  " + " · ".join(link_bits)
                tracks.append(line)
        if tracks:
            st.markdown("🎵 **Reference recordings**")
            st.markdown("\n".join(tracks))

    st.caption("Sourced live from Wikidata, Wikipedia, Nominatim, Open Library, MusicBrainz, and Kaggle via data/dancecompass_final_fused_allsources.csv.")


def render():
    st.markdown("## 🗂️ Explore Dance Forms")
    st.write("")

    dance_forms = load_dance_forms()

    col1, col2, col3 = st.columns(3)
    with col1:
        category = st.selectbox("Category", ["All"] + categories(dance_forms))
    with col2:
        energy = st.selectbox("Energy level", ["All", "Low-Medium", "Medium", "Medium-High", "High"])
    with col3:
        solo_partner = st.selectbox("Solo / Partner", ["All", "Solo", "Partner", "Group"])

    filtered = filter_forms(dance_forms, category, energy, solo_partner)
    st.caption(f"{len(filtered)} of {len(dance_forms)} dance forms match your filters.")
    st.write("")

    for d in filtered:
        with st.expander(f"{d['name']}  ·  {d['category']}  ·  {d['origin_region']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Origin:** {d['origin_region']}")
                st.markdown(f"**History:** {d['era_origin']}")
                st.markdown(f"**Music:** {d['music_style']}")
                st.markdown(f"**Instruments:** {', '.join(d['instruments'])}")
                st.markdown(f"**Costume:** {d['costume']}")
            with col2:
                st.markdown(f"**Energy level:** {d['energy_level']}")
                st.markdown(f"**Solo/Partner:** {d['solo_or_partner']}")
                st.markdown(f"**Mood/style:** {', '.join(d['mood_style'])}")
                st.markdown(f"**Difficulty:** {d['learning_difficulty']}")
                st.markdown(f"**Famous for:** {d['famous_for']}")
            st.markdown(f"**Key movements:** {d['key_movements']}")
            st.info(f"✨ Fun fact: {d['fun_fact']}")

            _render_enrichment(d["id"])
