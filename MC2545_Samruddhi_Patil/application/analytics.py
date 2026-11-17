import streamlit as st
import pandas as pd


@st.cache_data
def load_fused_data():

    df = pd.read_csv(
        "data/fused_movies.csv",
        encoding="latin1"
    )

    return df


def show_analytics():

    st.title("📊 MovieMind AI Analytics")

    df = load_fused_data()

    st.write("Dataset loaded successfully!")

    st.write("Rows:", df.shape[0])
    st.write("Columns:", df.shape[1])

    st.dataframe(
        df.head(10),
        use_container_width=True
    )


# Run the dashboard
show_analytics()