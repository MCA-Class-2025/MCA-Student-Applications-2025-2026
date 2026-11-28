import streamlit as st


def upload_file():


    st.subheader(
        "📷 Upload Room Image / Document"
    )


    uploaded_file = st.file_uploader(

        "Choose File",

        type=[
            "png",
            "jpg",
            "jpeg",
            "pdf"
        ]

    )


    return uploaded_file