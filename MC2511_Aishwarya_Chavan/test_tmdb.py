import requests
import streamlit as st

API_KEY = st.secrets["TMDB_API_KEY"]

url = "https://api.themoviedb.org/3/search/movie"

params = {
    "api_key": API_KEY,
    "query": "Inception"
}

response = requests.get(url, params=params)

print("Status Code:", response.status_code)

if response.status_code == 200:
    data = response.json()

    print("TMDB API is working!")

    for movie in data["results"][:5]:
        print(movie["title"])

else:
    print("TMDB API Error:")
    print(response.text)