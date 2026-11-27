import streamlit as st
from api.watchmode_api import search_watchmode

st.title("🎬 Watchmode API Test")

movie_name = st.text_input("Enter movie name", "Inception")

if st.button("Search"):

    if movie_name:

        result = search_watchmode(movie_name)

        if result:
            st.success("Watchmode API is working!")

            st.json(result)

        else:
            st.error("Watchmode API failed.")