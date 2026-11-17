import re
import textwrap
from datetime import datetime

import streamlit as st
import pandas as pd
from src.search_engine import search_movies
from src.rag_engine import generate_recommendation
from src.tmdb_api import search_tmdb_movie
from src.youtube_api import search_movie_trailer
from src.watchmode_api import search_watchmode_movie
from src.analytics_dashboard import render_analytics_dashboard

# ==================================================
# Page Configuration
# ==================================================

st.set_page_config(
    page_title="MovieMind AI",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================================================
# Session State Defaults
# ==================================================


if "nav" not in st.session_state:
    st.session_state.nav = "Home"
if "favorites" not in st.session_state:
    st.session_state.favorites = {}
if "recent_searches" not in st.session_state:
    st.session_state.recent_searches = []     # most-recent-first list of queries
if "last_query" not in st.session_state:
    st.session_state.last_query = ""
if "last_movies" not in st.session_state:
    st.session_state.last_movies = []
if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""

IS_DARK = True

# ==================================================
# Theme tokens
# ==================================================


TOKENS = {
    "bg": "#0F1117",
    "bg-elevated": "#14161F",
    "card": "#1A1D29",
    "card-border": "rgba(255,255,255,0.08)",
    "glass": "rgba(26,29,41,0.55)",
    "text": "#FFFFFF",
    "muted": "#A6A9B8",
}

PRIMARY = "#FF6B00"
SECONDARY = "#6C63FF"
ACCENT = "#FF3D71"

# ==================================================
# CSS
# ==================================================

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&family=Inter:wght@400;500;600&display=swap');

:root {{
    --bg: {TOKENS['bg']};
    --bg-elevated: {TOKENS['bg-elevated']};
    --card: {TOKENS['card']};
    --card-border: {TOKENS['card-border']};
    --glass: {TOKENS['glass']};
    --text: {TOKENS['text']};
    --muted: {TOKENS['muted']};
    --primary: {PRIMARY};
    --secondary: {SECONDARY};
    --accent: {ACCENT};
    --gradient: linear-gradient(120deg, {PRIMARY} 0%, {ACCENT} 55%, {SECONDARY} 100%);
}}

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}
h1, h2, h3, .brand-font {{
    font-family: 'Poppins', sans-serif;
}}

.stApp {{
    background:
        radial-gradient(ellipse 90% 50% at 15% -10%, rgba(255,107,0,0.14), transparent 60%),
        radial-gradient(ellipse 80% 50% at 100% 0%, rgba(108,99,255,0.14), transparent 55%),
        var(--bg);
    color: var(--text);
}}
#MainMenu, footer {{ visibility: hidden; }}

/* ---------- Top Nav ---------- */
.mm-nav {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    background: var(--glass);
    backdrop-filter: blur(16px);
    border: 1px solid var(--card-border);
    border-radius: 18px;
    padding: 8px;
    margin-bottom: 1.6rem;
}}
div[data-testid="stHorizontalBlock"] .stButton button {{
    border-radius: 12px !important;
}}
.nav-btn button {{
    background: transparent !important;
    border: none !important;
    color: var(--muted) !important;
    font-weight: 600 !important;
    font-family: 'Poppins', sans-serif !important;
    transition: all 0.2s ease;
}}
.nav-btn button:hover {{
    color: var(--text) !important;
    background: rgba(255,255,255,0.06) !important;
}}
.nav-btn-active button {{
    background: var(--gradient) !important;
    color: #fff !important;
}}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {{
    background: var(--bg-elevated);
    border-right: 1px solid var(--card-border);
}}
section[data-testid="stSidebar"] .stButton button {{
    width: 100%;
    text-align: left;
    background: var(--card);
    color: var(--text);
    border: 1px solid var(--card-border);
    border-radius: 14px;
    padding: 0.6rem 0.9rem;
    margin-bottom: 6px;
    font-weight: 500;
    transition: all 0.2s ease;
}}
section[data-testid="stSidebar"] .stButton button:hover {{
    border-color: var(--primary);
    color: var(--primary);
    transform: translateX(3px);
    box-shadow: 0 0 16px rgba(255,107,0,0.25);
}}
.sidebar-tagline {{
    color: var(--muted);
    font-size: 0.85rem;
    margin-top: -6px;
    margin-bottom: 1rem;
}}
.sidebar-section-title {{
    font-family: 'Poppins', sans-serif;
    font-weight: 700;
    font-size: 0.95rem;
    margin: 1.2rem 0 0.6rem 0;
    color: var(--text);
}}

/* ---------- Hero ---------- */
.hero-title {{
    font-family: 'Poppins', sans-serif;
    font-weight: 800;
    font-size: 3.4rem;
    line-height: 1.05;
    background: var(--gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem;
}}
.hero-sub {{
    color: var(--muted);
    font-size: 1.05rem;
    margin-bottom: 1.6rem;
}}

/* ---------- Search bar ---------- */
.search-shell {{
    position: relative;
}}
div[data-testid="stTextInput"] {{
    position: relative;
}}
div[data-testid="stTextInput"]::before {{
    content: "🔍";
    position: absolute;
    left: 22px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 1.1rem;
    z-index: 2;
    opacity: 0.6;
}}
div[data-testid="stTextInput"] input {{
    background: var(--glass) !important;
    backdrop-filter: blur(16px);
    border: 1px solid var(--card-border) !important;
    border-radius: 20px !important;
    color: var(--text) !important;
    padding: 1.1rem 1.4rem 1.1rem 3rem !important;
    font-size: 1.05rem !important;
}}
div[data-testid="stTextInput"] input:focus {{
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 4px rgba(255,107,0,0.15) !important;
}}
div[data-testid="stTextInput"] input::placeholder {{
    color: var(--muted) !important;
}}

.stButton>button[kind="primary"] {{
    background: var(--gradient) !important;
    background-size: 200% auto !important;
    color: #fff !important;
    border: none !important;
    border-radius: 20px !important;
    font-weight: 700 !important;
    font-family: 'Poppins', sans-serif !important;
    letter-spacing: 0.01em;
    padding: 0.85rem 1rem !important;
    transition: all 0.25s ease;
    box-shadow: 0 8px 24px rgba(255,61,113,0.25);
}}
.stButton>button[kind="primary"]:hover {{
    background-position: right center !important;
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 12px 30px rgba(255,61,113,0.4);
}}

/* ---------- AI Recommendation ---------- */
.ai-chat-wrap {{
    position: relative;
    padding: 2px;
    border-radius: 22px;
    background: var(--gradient);
    margin: 1.6rem 0 2.2rem 0;
    animation: fadeIn 0.6s ease;
}}
.ai-chat-inner {{
    background: var(--glass);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 1.5rem 1.7rem;
}}
.ai-chat-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 0.8rem;
}}
.ai-chat-icon {{
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: var(--gradient);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
}}
.ai-chat-label {{
    font-family: 'Poppins', sans-serif;
    font-weight: 700;
    font-size: 0.95rem;
    color: var(--text);
}}
.ai-chat-bubble {{
    color: var(--text);
    font-size: 1.02rem;
    line-height: 1.7;
}}
.ai-chat-bubble b {{
    color: var(--primary);
    font-weight: 700;
}}

/* ---------- Section label ---------- */
.section-label {{
    font-family: 'Poppins', sans-serif;
    font-weight: 700;
    font-size: 1.5rem;
    color: var(--text);
    margin: 1.4rem 0 1.2rem 0;
}}
.section-label span {{
    background: var(--gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}

/* ---------- Skeleton loaders ---------- */
@keyframes shimmer {{
    0% {{ background-position: -400px 0; }}
    100% {{ background-position: 400px 0; }}
}}
.skeleton-card {{
    height: 260px;
    border-radius: 20px;
    background: var(--card);
    border: 1px solid var(--card-border);
    background-image: linear-gradient(90deg, var(--card) 0px, rgba(255,255,255,0.06) 40px, var(--card) 80px);
    background-size: 800px 100%;
    animation: shimmer 1.4s infinite linear;
    margin-bottom: 22px;
}}

@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

/* ---------- Movie Cards ---------- */
.movie-card {{
    position: relative;
    background: var(--glass);
    backdrop-filter: blur(16px);
    border: 1px solid var(--card-border);
    border-radius: 20px;
    overflow: hidden;
    margin-bottom: 14px;
    padding: 20px;
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
    animation: fadeIn 0.5s ease;
}}
.movie-card:hover {{
    transform: translateY(-6px) scale(1.01);
    border-color: rgba(255,107,0,0.5);
    box-shadow: 0 18px 40px rgba(255,61,113,0.18), 0 0 0 1px rgba(255,107,0,0.15);
}}
.card-header {{
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 6px;
}}
.card-title {{
    font-family: 'Poppins', sans-serif;
    font-size: 1.12rem;
    font-weight: 700;
    color: var(--text);
    line-height: 1.3;
    flex: 1;
}}
.rating-chip {{
    flex-shrink: 0;
    background: var(--gradient);
    color: #fff;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 20px;
    white-space: nowrap;
}}
.card-meta-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    font-size: 0.75rem;
    color: var(--muted);
    margin-bottom: 10px;
}}
.genre-pills {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 10px;
}}
.genre-pill {{
    background: rgba(108,99,255,0.12);
    color: var(--secondary);
    font-size: 0.7rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    border: 1px solid rgba(108,99,255,0.25);
}}
.card-director {{
    font-size: 0.82rem;
    color: var(--muted);
    margin-bottom: 8px;
}}
.card-director b {{ color: var(--text); font-weight: 600; }}
.card-overview {{
    font-size: 0.85rem;
    color: var(--muted);
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    margin-bottom: 4px;
}}

/* card action buttons (real Streamlit buttons rendered under the card) */
.card-btn-row {{ margin-top: -8px; margin-bottom: 18px; }}
.card-btn-row .stButton button {{
    width: 100%;
    border-radius: 12px !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    padding: 0.5rem !important;
}}
.card-btn-row div[data-testid="column"]:nth-child(1) .stButton button {{
    background: rgba(108,99,255,0.12) !important;
    color: var(--secondary) !important;
    border: 1px solid rgba(108,99,255,0.3) !important;
}}
.card-btn-row div[data-testid="column"]:nth-child(2) .stButton button {{
    background: rgba(255,61,113,0.12) !important;
    color: var(--accent) !important;
    border: 1px solid rgba(255,61,113,0.3) !important;
}}


/* ---------- Streaming Availability ---------- */

.stream-card {{
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 14px;
    padding: 14px 16px;
    margin-top: 8px;
    margin-bottom: 6px;
    transition: all 0.2s ease;
}}

.stream-card:hover {{
    border-color: rgba(255,107,0,0.45);
    background: rgba(255,255,255,0.055);
}}

.stream-title {{
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 7px;
}}

.stream-info {{
    font-size: 0.78rem;
    color: var(--muted);
    margin-bottom: 6px;
}}

.stream-quality {{
    font-size: 0.75rem;
    color: var(--primary);
    font-weight: 600;
}}
/* ---------- Footer ---------- */
.mm-footer {{
    text-align: center;
    color: var(--muted);
    font-size: 0.78rem;
    padding: 2rem 0 0.5rem 0;
    opacity: 0.6;
}}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==================================================
# Helpers
# ==================================================

QUICK_PICKS = {
    "🚀 Space Movies": "space movies",
    "🤖 Artificial Intelligence": "artificial intelligence movies",
    "😂 Comedy Movies": "comedy movies",
    "👻 Horror Movies": "horror movies",
    "🕵️ Thriller Movies": "thriller movies",
    "❤️ Romantic Movies": "romantic movies",
}


def highlight_titles(text, movies):
    """Bold movie titles inside the AI recommendation text."""
    for m in movies:
        title = m.get("title")
        if title and title in text:
            text = text.replace(title, f"<b>{title}</b>")
    return text


def year_from_date(date_str):
    if not date_str:
        return "Unknown"
    match = re.match(r"(\d{4})", str(date_str))
    return match.group(1) if match else "Unknown"


def run_search(query):
    st.session_state.last_query = query
    ph = st.empty()
    ph.markdown(
        '<div class="skeleton-card"></div><div class="skeleton-card"></div>',
        unsafe_allow_html=True,
    )
    movies = search_movies(query)
    answer = generate_recommendation(query, movies)
    ph.empty()

    st.session_state.last_movies = movies
    st.session_state.last_answer = answer

    if query not in st.session_state.recent_searches:
        st.session_state.recent_searches.insert(0, query)
        st.session_state.recent_searches = st.session_state.recent_searches[:6]


def render_movie_grid(movies, key_prefix=""):
    if not movies:
        st.warning("No matching movies found. Try a different query.")
        return

    cols_per_row = 3
    for i in range(0, len(movies), cols_per_row):
        row_movies = movies[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for col_idx, (col, movie) in enumerate(zip(cols, row_movies)):
            with col:
                title = movie.get("title", "Untitled")
                # Get additional information from TMDB
                tmdb_data = search_tmdb_movie(title)
                tmdb_poster = None
                tmdb_rating = None
                tmdb_overview = None

                if tmdb_data:
                    tmdb_poster = tmdb_data.get("poster_url")
                    tmdb_rating = tmdb_data.get("rating")
                    tmdb_overview = tmdb_data.get("overview")

                rating = movie.get("vote_average", "N/A")
                year = year_from_date(movie.get("release_date"))
                runtime = movie.get("runtime", "N/A")
                popularity = movie.get("popularity", "N/A")
                director = movie.get("director") or "Unknown"
                if str(director).lower() == "nan":
                    director = "Unknown"
                genres = movie.get("genres_clean", "") or ""
                genre_pills = "".join(
                    f'<span class="genre-pill">{g.strip()}</span>'
                    for g in genres.split(",") if g.strip()
                )
                overview = movie.get("overview", "No overview available.")

               
                poster_html = ""
                if tmdb_poster:
                    poster_html = (
                        f'<img src="{tmdb_poster}" '
                        f'style="width:100%;height:420px;object-fit:cover;'
                        f'border-radius:14px;margin-bottom:15px;">'
                    )

                card_html = f"""
<div class="movie-card">
{poster_html}
<div class="card-header">
<div class="card-title">🎬 {title}</div>
<div class="rating-chip">⭐ {rating}</div>
</div>
<div class="card-meta-row">
<span>📅 {year}</span>
<span>⏱ {runtime} min</span>
<span>🔥 {popularity}</span>
</div>
<div class="genre-pills">{genre_pills}</div>
<div class="card-director">🎥 Director: <b>{director}</b></div>
<div class="card-overview">{overview}</div>
</div>
"""
                st.markdown(textwrap.dedent(card_html), unsafe_allow_html=True)

                st.markdown('<div class="card-btn-row">', unsafe_allow_html=True)
                btn_cols = st.columns(2)
                unique_key = f"{key_prefix}_{i}_{col_idx}_{title}"
                with btn_cols[0]:
                    if st.button("View Details", key=f"details_{unique_key}", use_container_width=True):
                        st.session_state[f"expanded_{unique_key}"] = not st.session_state.get(
                            f"expanded_{unique_key}", False
                        )
                with btn_cols[1]:
                    is_fav = title in st.session_state.favorites
                    label = "★ Saved" if is_fav else "☆ Favorite"
                    if st.button(label, key=f"fav_{unique_key}", use_container_width=True):
                        if is_fav:
                            st.session_state.favorites.pop(title, None)
                        else:
                            st.session_state.favorites[title] = movie
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

                if st.session_state.get(f"expanded_{unique_key}", False):
                    with st.expander("Full details", expanded=True):
                        st.write(f"**Overview:** {overview}")
                        st.write(f"**Director:** {director}")
                        st.write(f"**Genres:** {genres or 'Unknown'}")
                        st.write(f"**Rating:** {rating}")
                        st.write(f"**Release Year:** {year}")

                        # YouTube Trailer
                        trailer = search_movie_trailer(title)
                        if trailer:
                            st.markdown("### 🎬 Official Trailer")
                            st.video(trailer["youtube_url"])
                        else:
                            st.info("Trailer not available.")


                        # Watchmode
                        streaming_data = search_watchmode_movie(
                            title,
                            country="IN"
                        )
                        if streaming_data and streaming_data.get("sources"):
                            st.markdown("### 📺 Where to Watch in India")
                            sources = streaming_data["sources"]
                            for i in range(0, len(sources), 2):
                                cols = st.columns(2)
                                for j, col in enumerate(cols):
                                    index = i + j
                                    if index >= len(sources):
                                        break
                                    source = sources[index]
                                    name = source.get("name", "Unknown")
                                    source_type = source.get("type", "").lower()
                                    price = source.get("price")
                                    qualities = source.get("qualities", [])
                                    url = source.get("url")


                                    if source_type == "sub":
                                        watch_type = "Subscription"
                                    elif source_type == "rent":
                                        watch_type = "Rent"
                                    elif source_type == "buy":
                                        watch_type = "Buy"
                                    else:
                                        watch_type = source_type.title()

                                    price_text = (
                                        f"₹{price}"
                                        if price is not None
                                        else "Included"
                                    )

                                    quality_text = (
                                        ", ".join(qualities)
                                        if qualities
                                        else "N/A"
                                    )

                                    with col:
                                        st.markdown(
                                            f"""
                                            <div class="stream-card">
                                            <div class="stream-title">
                                            📺 {name}
                                            </div>

                                            <div class="stream-info">
                                            {watch_type} • {price_text}
                                            </div>
                                            
                                            <div class="stream-quality">
                                            🎞 {quality_text}
                                            </div>
                                            
                                            </div>
                                            """,
                                            unsafe_allow_html=True
                                        )

                                        if url:
                                            st.link_button(
                                                "Watch Now →",
                                                url,
                                                use_container_width=True
                                                )
                        else:
                            st.info(
                                "📺 Streaming availability is not currently "
                                "available for this movie in India."
            )

# ==================================================
# Sidebar
# ==================================================

with st.sidebar:
    st.markdown(
        "<div class='brand-font' style='font-size:1.7rem;font-weight:800;"
        "background:linear-gradient(120deg,#FF6B00,#FF3D71,#6C63FF);"
        "-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>"
        "🎬 MovieMind AI</div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sidebar-tagline">Your AI Movie Discovery Assistant</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-title">🔥 Popular Searches</div>', unsafe_allow_html=True)
    quick_query = None
    for label, value in QUICK_PICKS.items():
        if st.button(label, use_container_width=True, key=f"quick_{value}"):
            quick_query = value

    st.markdown('<div class="sidebar-section-title">💡 Example Questions</div>', unsafe_allow_html=True)
    st.info(
        "• Recommend movies like Interstellar\n\n"
        "• I want emotional space movies\n\n"
        "• Funny family movies\n\n"
        "• Christopher Nolan movies\n\n"
        "• Movies about AI\n\n"
        "• Time travel movies\n\n"
        "• Recommend a suspense thriller"
    )

    if st.session_state.recent_searches:
        st.markdown('<div class="sidebar-section-title">🕘 Recent Searches</div>', unsafe_allow_html=True)
        for rq in st.session_state.recent_searches:
            if st.button(rq, use_container_width=True, key=f"recent_{rq}"):
                quick_query = rq

    st.markdown("---")
    st.caption("MovieMind AI · Glass Edition")

# ==================================================
# Top Navigation
# ==================================================

st.markdown('<div class="mm-nav">', unsafe_allow_html=True)
nav_cols = st.columns(5)
nav_items = ["Home", "Discover", "Favorites", "Analytics", "About"]
for nc, item in zip(nav_cols, nav_items):
    with nc:
        active = st.session_state.nav == item
        st.markdown(f'<div class="nav-btn{" nav-btn-active" if active else ""}">', unsafe_allow_html=True)
        if st.button(item, key=f"nav_{item}", use_container_width=True):
            st.session_state.nav = item
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ==================================================
# Page: Home / Discover (same search experience)
# ==================================================

if st.session_state.nav in ("Home", "Discover"):

    st.markdown('<div class="hero-title">MovieMind AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">Your AI-powered movie discovery assistant — tell it a mood, '
        'a director, or a story, and it finds the film.</div>',
        unsafe_allow_html=True,
    )

    col_input, col_btn = st.columns([5, 1])
    with col_input:
        query = st.text_input(
            "search",
            value=quick_query if quick_query else "",
            placeholder="Ask anything… e.g. Recommend emotional space movies",
            label_visibility="collapsed",
        )
    with col_btn:
        search = st.button("Discover Movies", use_container_width=True, type="primary")

    if quick_query:
        search = True
        query = quick_query

    if search:
        if query.strip():
            run_search(query.strip())
        else:
            st.warning("⚠ Please enter a movie query.")

    if st.session_state.last_answer:
        answer_html = highlight_titles(st.session_state.last_answer, st.session_state.last_movies)
        st.markdown(
            f"""
            <div class="ai-chat-wrap">
                <div class="ai-chat-inner">
                    <div class="ai-chat-header">
                        <div class="ai-chat-icon">✨</div>
                        <div class="ai-chat-label">AI Recommendation</div>
                    </div>
                    <div class="ai-chat-bubble">{answer_html}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-label">🎬 Recommended <span>Movies</span></div>',
            unsafe_allow_html=True,
        )
        render_movie_grid(st.session_state.last_movies, key_prefix="home")

# ==================================================
# Page: Favorites
# ==================================================

elif st.session_state.nav == "Favorites":
    st.markdown('<div class="hero-title">Your Favorites</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">Movies you\'ve saved for later.</div>',
        unsafe_allow_html=True,
    )
    fav_movies = list(st.session_state.favorites.values())
    if not fav_movies:
        st.info("You haven't saved any favorites yet. Click ☆ Favorite on a movie card to add it here.")
    else:
        render_movie_grid(fav_movies, key_prefix="fav")


elif st.session_state.nav == "Analytics":
    render_analytics_dashboard()


# ==================================================
# Page: About
# ==================================================

elif st.session_state.nav == "About":
    st.markdown('<div class="hero-title">About MovieMind AI</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="ai-chat-wrap">
            <div class="ai-chat-inner">
                <div class="ai-chat-bubble">
                MovieMind AI is an intelligent movie discovery assistant. Describe a mood, a director,
                or a story you're in the mind for, and it searches a semantic movie database to find
                and recommend films that fit — complete with genres, ratings, and an AI-written summary
                explaining why each pick matches your search.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ==================================================
# Footer
# ==================================================

st.markdown(
    f'<div class="mm-footer">MovieMind AI · AI-driven semantic search · Built {datetime.now().year}</div>',
    unsafe_allow_html=True,
)