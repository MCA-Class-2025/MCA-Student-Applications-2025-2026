import os

import pandas as pd
import streamlit as st

OUTPUT_DIR = os.path.join("data", "api_results")

API_FILES = {
    "MITRE ATT&CK": "mitre_attack_data.csv",
    "NVD (CVE)": "nvd_data.csv",
    "URLhaus": "urlhaus_data.csv",
    "VirusTotal": "virustotal_data.csv",
    "AbuseIPDB": "abuseipdb_data.csv",
}

FUSED_FILE = "fused_threat_dataset.csv"


def _file_status(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path)
        return df
    except Exception:
        return None


def show():
    st.title("🌐 Threat Intelligence — API Integration")

    st.markdown("""
    This module enriches the existing NSL-KDD threat-detection pipeline with
    **5 external threat-intelligence APIs**, fused into one final dataset.

    - **MITRE ATT&CK** and **NVD** are joined onto the 23 NSL-KDD attack
      categories using `attack` as the join key.
    - **URLhaus**, **VirusTotal**, and **AbuseIPDB** have no matching field
      in NSL-KDD (no URLs/hashes/IPs exist in the dataset), so they're kept
      as independent, clearly-labeled threat-intel IOC records rather than
      forced into a fake join.
    """)

    st.markdown("---")

    if st.button("▶️ Run Pipeline Now (calls all 5 live APIs)"):
        with st.spinner("Running dataset load → 5 API calls → fusion... this can take a minute or two."):
            try:
                from modules.threat_enrichment.pipeline import run_all
                from modules.threat_enrichment.fusion import fuse

                results = run_all()
                fuse(
                    results["base_summary"], results["mitre"], results["nvd"],
                    results["urlhaus"], results["virustotal"], results["abuseipdb"],
                )
                st.success("Pipeline completed. Scroll down for results.")
            except Exception as e:
                st.error(f"Pipeline failed: {e}")
                st.info("Check logs/api_pipeline.log for details, and confirm your .env API keys and internet connection.")

    st.markdown("---")
    st.subheader("📡 API Integration Status")

    cols = st.columns(5)

    for i, (label, filename) in enumerate(API_FILES.items()):
        df = _file_status(filename)
        with cols[i]:
            if df is not None:
                st.success(f"✅ {label}")
                st.caption(f"{len(df)} records")
            else:
                st.warning(f"⏳ {label}")
                st.caption("Not run yet")

    st.markdown("---")
    st.subheader("🔗 Fused Threat Dataset")

    fused_df = _file_status(FUSED_FILE)

    if fused_df is None:
        st.info("Run the pipeline above to generate the fused dataset.")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Rows", len(fused_df))
    c2.metric("Total Columns", len(fused_df.columns))

    if "record_type" in fused_df.columns:
        n_traffic = (fused_df["record_type"] == "network_traffic_category").sum()
        c3.metric("Attack Categories Enriched", n_traffic)

        st.markdown("**Record type breakdown**")
        st.bar_chart(fused_df["record_type"].value_counts())

    st.markdown("**Preview**")
    st.dataframe(fused_df, use_container_width=True)

    csv_bytes = fused_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download fused_threat_dataset.csv",
        csv_bytes,
        "fused_threat_dataset.csv",
        "text/csv",
    )

    st.markdown("---")
    st.subheader("📄 Individual API CSVs")

    for label, filename in API_FILES.items():
        df = _file_status(filename)
        if df is None:
            continue
        with st.expander(f"{label} — {filename} ({len(df)} rows)"):
            st.dataframe(df, use_container_width=True)
            st.download_button(
                f"📥 Download {filename}",
                df.to_csv(index=False).encode("utf-8"),
                filename,
                "text/csv",
                key=f"dl_{filename}",
            )
