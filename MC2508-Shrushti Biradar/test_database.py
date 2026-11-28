import streamlit as st

from database import create_tables

create_tables()

st.title("🎉 Database Test")
st.write("Database is working correctly!")