import streamlit as st
from api.omdb_api import search_omdb

st.title("OMDb API Test")

movie_name = st.text_input("Enter movie name")

if st.button("Search"):

    if movie_name:

        result = search_omdb(movie_name)

        if result:
            st.success("OMDb API is working!")

            st.write("Title:", result.get("Title"))
            st.write("Year:", result.get("Year"))
            st.write("Genre:", result.get("Genre"))
            st.write("Director:", result.get("Director"))
            st.write("Actors:", result.get("Actors"))
            st.write("IMDb Rating:", result.get("imdbRating"))

        else:
            st.error("Movie not found or OMDb API failed.")