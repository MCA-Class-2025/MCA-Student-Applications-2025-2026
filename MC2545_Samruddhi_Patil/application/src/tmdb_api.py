"""
MovieMind AI
TMDB API Integration
"""

import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

BASE_URL = "https://api.themoviedb.org/3"

@st.cache_data(ttl=86400)

def search_tmdb_movie(title):

    if not TMDB_API_KEY:
        return None

    url = f"{BASE_URL}/search/movie"

    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "language": "en-US"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("results", [])

        if not results:
            return None

        movie = results[0]

        poster_path = movie.get("poster_path")

        poster_url = None

        if poster_path:
            poster_url = (
                "https://image.tmdb.org/t/p/w500"
                + poster_path
            )

        return {
            "tmdb_id": movie.get("id"),
            "title": movie.get("title"),
            "overview": movie.get("overview"),
            "poster_url": poster_url,
            "rating": movie.get("vote_average"),
            "release_date": movie.get("release_date")
        }

    except requests.RequestException as e:

        print("TMDB API Error:", e)

        return None