import streamlit as st
import pandas as pd
from modules.anomaly_detection.predictor import predict


def show():

    st.title("🚨 Threat Detection")

    st.markdown("""
    Analyze network traffic using the trained **Isolation Forest** model.

    ### Supported Dataset

    - NSL-KDD Train+
    - NSL-KDD Test+
    - CSV files
    - TXT files

    Upload a dataset and the model will classify each record as:

    - ✅ Normal
    - ⚠️ Anomaly
    """)

    st.markdown("---")

    uploaded_file = st.file_uploader(
        "Upload NSL-KDD File",
        type=["txt", "csv"]
    )

    if uploaded_file is not None:

        try:

            columns = [
                "duration","protocol_type","service","flag","src_bytes","dst_bytes",
                "land","wrong_fragment","urgent","hot","num_failed_logins",
                "logged_in","num_compromised","root_shell","su_attempted",
                "num_root","num_file_creations","num_shells","num_access_files",
                "num_outbound_cmds","is_host_login","is_guest_login","count",
                "srv_count","serror_rate","srv_serror_rate","rerror_rate",
                "srv_rerror_rate","same_srv_rate","diff_srv_rate",
                "srv_diff_host_rate","dst_host_count","dst_host_srv_count",
                "dst_host_same_srv_rate","dst_host_diff_srv_rate",
                "dst_host_same_src_port_rate","dst_host_srv_diff_host_rate",
                "dst_host_serror_rate","dst_host_srv_serror_rate",
                "dst_host_rerror_rate","dst_host_srv_rerror_rate",
                "label","difficulty_level"
            ]

            df = pd.read_csv(uploaded_file, header=None)
            df.columns = columns

            st.subheader("📂 Uploaded Dataset Preview")
            st.dataframe(df.head())

            input_df = df.drop(columns=["label", "difficulty_level"])

            predictions = predict(input_df)

            result_df = df.copy()
            result_df["Prediction"] = predictions

            total = len(result_df)
            normal = (result_df["Prediction"] == "Normal").sum()
            anomaly = (result_df["Prediction"] == "Anomaly").sum()

            st.subheader("📊 Detection Summary")

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "📄 Total Records",
                total
            )

            c2.metric(
                "✅ Normal Traffic",
                normal
            )

            c3.metric(
                "🚨 Threats Detected",
                anomaly
            )

            if anomaly > 0:

                st.error(
                    f"⚠️ {anomaly} anomalous records detected."
                )

            else:

                st.success(
                    "✅ No anomalies detected."
                )

            st.subheader("📈 Prediction Distribution")

            chart_data = pd.DataFrame(
                {
                    "Category": ["Normal", "Anomaly"],
                    "Count": [normal, anomaly]
                }
            )

            st.bar_chart(chart_data.set_index("Category"))

            st.subheader("📋 Prediction Results")

            def highlight_prediction(value):

                if value == "Anomaly":
                    return "background-color:#ff4b4b;color:white;font-weight:bold"

                return "background-color:#00b050;color:white;font-weight:bold"

            display_df = result_df.head(100)

            styled_df = display_df.style.map(
                highlight_prediction,
                subset=["Prediction"]
            )

            st.dataframe(styled_df, use_container_width=True)

            st.info(f"Displaying the first 100 rows out of {len(result_df)} predictions.")

            csv = result_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                "📥 Download Detection Report",
                csv,
                "prediction_results.csv",
                "text/csv"
            )

        except Exception as e:
            st.error(f"Error: {e}")