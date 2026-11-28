import streamlit as st


def sidebar():

    st.sidebar.image(
        "https://cdn-icons-png.flaticon.com/512/3064/3064197.png",
        width=100
    )


    st.sidebar.title(
        "🏠 Design Settings"
    )


    room = st.sidebar.selectbox(
        "Room Type",
        [
            "Luxury Bedroom",
            "Living Room",
            "Modern Kitchen",
            "Home Office",
            "Studio Apartment"
        ]
    )


    style = st.sidebar.selectbox(
        "Interior Style",
        [
            "Modern Luxury",
            "Minimalist",
            "Traditional Indian",
            "Scandinavian",
            "Royal Theme"
        ]
    )


    budget = st.sidebar.number_input(
        "Budget ₹",
        min_value=10000,
        value=50000
    )


    return room, style, budget

with st.sidebar:

    st.markdown("## 🏠 Interior Preferences")

    uploaded_image = st.file_uploader(
        "📷 Upload Room Image",
        type=["jpg","jpeg","png"]
    )

    uploaded_pdf = st.file_uploader(
        "📄 Upload Design PDF",
        type=["pdf"]
    )

    room = st.selectbox(...)

    style = st.selectbox(...)

    ...

    generate = st.button("✨ Generate Design")

# ===========================
# ADD STEP 3 HERE
# ===========================

import os

os.makedirs("uploads", exist_ok=True)

pdf_path = None

if uploaded_pdf:

    pdf_path = os.path.join(
        "uploads",
        uploaded_pdf.name
    )

    with open(pdf_path, "wb") as f:
        f.write(uploaded_pdf.getbuffer())