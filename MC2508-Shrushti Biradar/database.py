import streamlit as st

from database import create_tables, create_user, authenticate_user

st.set_page_config(
    page_title="AI Event Planner",
    page_icon="🎉"
)

create_tables()

st.title("🎉 AI Event Planner")
st.write("Database Login Test")

st.divider()

email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Login"):

    user = authenticate_user(email, password)

    if user:
        st.success(f"Login successful! Welcome {user[1]} 🎉")
    else:
        st.error("Invalid email or password.")