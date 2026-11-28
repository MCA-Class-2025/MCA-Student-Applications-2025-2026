import streamlit as st

st.title("🎉 Streamlit Test")
st.write("If you can see this, Streamlit is working correctly.")

name = st.text_input("Enter your name")

if st.button("Test"):
    st.success(f"Hello {name}!")