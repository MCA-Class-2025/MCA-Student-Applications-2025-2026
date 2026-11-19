import streamlit as st
from api.news_api import search_movie_news

st.title("📰 News API Test")

movie_name = st.text_input(
    "Enter movie name",
    "Inception"
)

if st.button("Search News"):

    if movie_name:

        try:
            result = search_movie_news(movie_name)

            if result.get("status") == "ok":

                st.success("News API is working!")

                st.write(
                    f"Found {result.get('totalResults', 0)} articles."
                )

                for article in result.get("articles", []):

                    st.subheader(article.get("title"))

                    st.write(
                        article.get("description")
                    )

                    st.write(
                        "Source:",
                        article.get("source", {}).get("name")
                    )

                    st.write(
                        "Published:",
                        article.get("publishedAt")
                    )

                    st.write(
                        "URL:",
                        article.get("url")
                    )

                    st.divider()

            else:
                st.error(result)

        except Exception as e:
            st.error(str(e))