import os
import pandas as pd
import streamlit as st

DATASETS = {
    "Static Books": ("data/static_books.csv", "Static"),
    "Dynamic Books": ("data/dynamic_books.csv", "Dynamic"),
    "Fusion Books": ("data/fusion_books.csv", "Fusion"),
    "API Records": ("data/api_records.csv", "API Data"),
    "Book Features": ("data/book_features.csv", "Derived")
}


def show_dataset_dashboard():
    st.markdown("### 📊 BookMuse Dataset Dashboard")

    st.write(
        "BookMuse uses multiple datasets for static data, "
        "live API data, fusion and derived features."
    )

    summary = []

    for name, (path, dataset_type) in DATASETS.items():
        if os.path.exists(path):
            df = pd.read_csv(path)

            summary.append({
                "Dataset": name,
                "Type": dataset_type,
                "Records": len(df),
                "Columns": len(df.columns)
            })

    if summary:
        st.dataframe(
            pd.DataFrame(summary),
            use_container_width=True,
            hide_index=True
        )

    st.markdown("#### 📁 Dataset Preview")

    selected = st.selectbox(
        "Select dataset",
        list(DATASETS.keys())
    )

    path = DATASETS[selected][0]

    if os.path.exists(path):
        df = pd.read_csv(path)

        st.write(
            f"**{selected}:** {len(df)} records"
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("Dataset file not found.")