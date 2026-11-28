import os
import time
import shutil
import streamlit as st
import numpy as np
from dotenv import load_dotenv

load_dotenv()

def clean_api_key(value):
    if not value:
        return ""
    value = value.strip()
    if "=" in value:
        value = value.split("=")[-1].strip()
    return value.replace('"', '').replace("'", "")

# Automatically fetch and clean all 5 API keys from environment
env_news = clean_api_key(os.getenv("NEWS_API_KEY") or "")
env_fred = clean_api_key(os.getenv("FRED_API_KEY") or "")
env_exchangerate = clean_api_key(os.getenv("EXCHANGERATE_API_KEY") or "")
env_alphavantage = clean_api_key(os.getenv("ALPHAVANTAGE_API_KEY") or "")

# Page configuration - Set tab title and layout
st.set_page_config(
    page_title="FundFlow AI - FundFlow Loan Intelligence",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import local modules
from rag_engine import EmbeddingService, FAISSIndex, LLMQueryService
from utils import apply_custom_css, render_metric_card, convert_history_to_text
from api_helpers import (
    fetch_news_articles,
    fetch_fred_series,
    fetch_exchange_rates,
    convert_currency,
    fetch_world_bank_indicator,
    fetch_alpha_vantage_quote,
)
from api_router import route_api, format_api_status_sidebar, build_combined_response, fetch_external_context
from entity_extractor import extract_entities
from dataset_dashboard import render_dataset_fusion_dashboard, load_fused_dataset
from dataset_config import FUSED_DATASET_FILENAME
from loan_intelligence import assess_applicant, dataset_risk_label, fusion_validation, fusion_validation_details

# 1. Apply Custom styling
apply_custom_css()

# 2. Setup paths
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(WORKSPACE_DIR, "temp_docs")
INDEX_PATH = os.path.join(WORKSPACE_DIR, "faiss_index")
os.makedirs(TEMP_DIR, exist_ok=True)

# 3. Initialize Session States
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "faiss_index" not in st.session_state:
    st.session_state.faiss_index = None
if "processed_files" not in st.session_state:
    st.session_state.processed_files = []
if "total_chunks" not in st.session_state:
    st.session_state.total_chunks = 0
if "search_latency" not in st.session_state:
    st.session_state.search_latency = 0.0
if "active_embed_config" not in st.session_state:
    st.session_state.active_embed_config = {}
# --- NEW: session state for intelligent routing & document features ---
if "last_routing" not in st.session_state:
    st.session_state.last_routing = None
if "generated_questions" not in st.session_state:
    st.session_state.generated_questions = []
if "document_full_text" not in st.session_state:
    st.session_state.document_full_text = ""
if "doc_summary" not in st.session_state:
    st.session_state.doc_summary = ""
if "answer_evaluation" not in st.session_state:
    st.session_state.answer_evaluation = ""

# --- SIDEBAR CONFIGURATION ---
st.sidebar.markdown("## ⚙️ Configuration Portal")
st.sidebar.caption(f"Dataset: `{FUSED_DATASET_FILENAME}`")

# MAJOR CHANGE: Manual LLM provider selection removed — APIs are auto-routed
st.sidebar.markdown("### 🤖 Intelligent API Router")
st.sidebar.info(
    "LLM and external APIs are **automatically selected** based on your "
    "query and uploaded document content. No manual API picking required."
)

# Exactly the seven APIs configured by the project owner.
key_status = []
for label, key in [
    ("NewsAPI", env_news),
    ("FRED", env_fred),
    ("ExchangeRate", env_exchangerate),
    ("WorldBank", "ok"),
    ("AlphaVantage", env_alphavantage),
]:
    if label == "WorldBank":
        key_status.append("✅ WorldBank (no key)")
    else:
        key_status.append(("✅ " if key else "❌ ") + label)
st.sidebar.caption("API Key Status: " + " | ".join(key_status))
st.sidebar.caption("💡 Cloud LLMs are not required. Local/offline answering is available, with optional Ollama support.")

# --- NEW: Sidebar Active APIs panel ---
st.sidebar.markdown("### 📡 Active APIs")
if st.session_state.last_routing:
    st.sidebar.markdown(format_api_status_sidebar(st.session_state.last_routing), unsafe_allow_html=False)
    with st.sidebar.expander("Routing Details", expanded=False):
        for api_key, info in st.session_state.last_routing["apis"].items():
            st.caption(f"**{api_key.title()}**: {info.get('reason', '')}")
else:
    st.sidebar.markdown(
        "**Automatically Selected APIs**\n\n"
        "⚪ NewsAPI: Not Needed\n"
        "⚪ FRED: Not Needed\n"
        "⚪ ExchangeRate: Not Needed\n"
        "⚪ World Bank: Not Needed\n"
        "⚪ Alpha Vantage: Not Needed"
    )
    st.sidebar.caption("Submit a query to see intelligent routing in action.")

# API keys are loaded from .env. Gemini/OpenAI remain configured for future optional integrations,
# but the chatbot and document answering stay local/offline.
news_api_key = env_news
fred_api_key = env_fred
exchangerate_api_key = env_exchangerate
alphavantage_api_key = env_alphavantage

with st.sidebar.expander("🔑 API Key Overrides (Optional)", expanded=False):
    news_api_key = st.text_input("NewsAPI Key", value=env_news, type="password")
    fred_api_key = st.text_input("FRED API Key", value=env_fred, type="password")
    exchangerate_api_key = st.text_input("ExchangeRate API Key", value=env_exchangerate, type="password")
    alphavantage_api_key = st.text_input("Alpha Vantage API Key", value=env_alphavantage, type="password")
    st.caption("World Bank Open Data API does not require an API key.")

st.sidebar.markdown("### 🧠 Answering Engine")
st.sidebar.success("Local RAG / Offline Synthesis — no cloud LLM quota is required. Optional Ollama/Qwen support is available.")
embed_provider = "Local (all-MiniLM-L6-v2)"
embed_api_key = None
embed_model = "all-MiniLM-L6-v2"

# RAG Hyperparameters Section
st.sidebar.markdown("### 🎛️ Retrieval Parameters")
chunk_size = st.sidebar.slider("Chunk Size (characters)", min_value=200, max_value=2000, value=800, step=100)
chunk_overlap = st.sidebar.slider("Chunk Overlap (characters)", min_value=0, max_value=500, value=150, step=50)
top_k = st.sidebar.slider("Top-K Retrieved Chunks", min_value=1, max_value=10, value=4)
temperature = st.sidebar.slider("LLM Temperature", min_value=0.0, max_value=1.0, value=0.3, step=0.1)

# Reset Button
st.sidebar.markdown("---")
if st.sidebar.button("🧹 Reset Database & Chat", use_container_width=True):
    # Clear temp files
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # Remove index files
    for ext in [".index", ".docs"]:
        fpath = INDEX_PATH + ext
        if os.path.exists(fpath):
            os.remove(fpath)
            
    # Reset Session state
    st.session_state.chat_history = []
    st.session_state.faiss_index = None
    st.session_state.processed_files = []
    st.session_state.total_chunks = 0
    st.session_state.search_latency = 0.0
    st.session_state.active_embed_config = {}
    st.session_state.last_routing = None
    st.session_state.generated_questions = []
    st.session_state.document_full_text = ""
    st.toast("Database and history cleared successfully!", icon="🗑️")
    st.rerun()

# --- MAIN APP LAYOUT ---
st.markdown(
    """
    <div class="main-title-container">
        <h1 class="main-title">FundFlow AI</h1>
        <div class="main-subtitle">Enterprise Multimodal RAG Assistant & Knowledge Base</div>
    </div>
    """,
    unsafe_allow_html=True
)

# --- FAISS index bootstrap (runs once, outside tabs — avoids rebuilding every run) ---
current_config = {
    "provider": embed_provider,
    "model": embed_model,
    "chunk_size": chunk_size,
    "chunk_overlap": chunk_overlap,
}

if st.session_state.faiss_index is None and os.path.exists(INDEX_PATH + ".index"):
    try:
        st.session_state.faiss_index = FAISSIndex.load(INDEX_PATH)
        st.session_state.processed_files = os.listdir(TEMP_DIR)
        st.session_state.total_chunks = len(st.session_state.faiss_index.documents)
        st.session_state.active_embed_config = current_config
        if not st.session_state.document_full_text and st.session_state.faiss_index.documents:
            st.session_state.document_full_text = " ".join(
                d["text"] for d in st.session_state.faiss_index.documents[:50]
            )
    except Exception as e:
        st.error(f"Error loading saved Vector Index: {e}")

# --- MAIN APP LAYOUT: top-level navigation tabs ---
main_tab_kb, main_tab_loan, main_tab_dataset = st.tabs(["📚 Knowledge Base & Chat", "🏦 Loan Intelligence", "📊 Dataset Fusion"])

with main_tab_loan:
    st.markdown("# 🏦 Loan Intelligence Center")
    st.caption("Transparent loan assessment, explainable risk, and interactive risk analytics.")
    fused_path = os.path.join(WORKSPACE_DIR, FUSED_DATASET_FILENAME)
    if not os.path.exists(fused_path):
        st.error(f"Missing {FUSED_DATASET_FILENAME} in the project root.")
    else:
        loan_df = load_fused_dataset(fused_path)
        # Add the analytical risk label once per dataset load.
        if "analytical_risk" not in loan_df.columns:
            loan_df = loan_df.copy()
            loan_df["analytical_risk"] = dataset_risk_label(loan_df)

        loan_tab1, loan_tab2, loan_tab3 = st.tabs([
            "🎯 Loan Assessment", "📊 Risk Dashboard", "🔐 Fusion Validation"
        ])

        with loan_tab1:
            st.markdown("### 🎯 Loan Approval / Risk Assessment")
            st.info("This is an analytical eligibility estimator based on transparent project rules. It is not a bank's final lending decision.")
            a1,a2,a3 = st.columns(3)
            with a1:
                in_cibil = st.number_input("CIBIL Score", 300, 900, 750, step=1)
                in_income = st.number_input("Annual Income (₹)", 0.0, 100000000.0, 800000.0, step=10000.0)
                in_loan = st.number_input("Loan Amount (₹)", 0.0, 100000000.0, 300000.0, step=10000.0)
            with a2:
                in_term = st.number_input("Loan Term (years)", 1.0, 40.0, 10.0, step=1.0)
                in_dep = st.number_input("Number of Dependents", 0, 20, 2, step=1)
                in_assets = st.number_input("Total Assets (₹)", 0.0, 500000000.0, 500000.0, step=10000.0)
            with a3:
                in_edu = st.selectbox("Education", ["Graduate", "Not Graduate"])
                in_emp = st.selectbox("Self Employed", ["No", "Yes"])
                st.markdown("**Assessment uses:** CIBIL, income, loan burden, assets, term and dependents.")
            if st.button("🔎 Assess Loan", type="primary", use_container_width=True):
                result=assess_applicant(in_cibil,in_income,in_loan,in_term,in_dep,in_edu,in_emp,in_assets)
                c1,c2,c3=st.columns(3)
                c1.metric("Eligibility Score", f"{result['score']:.1f}/100")
                c2.metric("Risk Level", result["risk_level"])
                c3.metric("Estimated Status", result["decision"])
                st.progress(result["score"]/100)
                x,y=st.columns(2)
                with x:
                    st.markdown("#### ✅ Positive Factors")
                    for item in result["positive"] or ["No major positive factor identified."]: st.write("• "+item)
                with y:
                    st.markdown("#### ⚠️ Risk Factors")
                    for item in result["risks"] or ["No major risk factor identified."]: st.write("• "+item)
                st.markdown(f"**Loan-to-income ratio:** {result['loan_to_income']:.2f}")
                st.caption("The score is a transparent project heuristic, not a regulated credit score or guaranteed approval.")

        with loan_tab2:
            st.markdown("### 📊 Interactive Risk Dashboard")
            risk_filter=st.multiselect("Risk Levels", ["LOW","MEDIUM","HIGH"], default=["LOW","MEDIUM","HIGH"])
            view=loan_df[loan_df["analytical_risk"].isin(risk_filter)].copy()
            k1,k2,k3,k4=st.columns(4)
            k1.metric("Records",f"{len(view):,}")
            k2.metric("Low Risk",f"{(view.analytical_risk=='LOW').sum():,}")
            k3.metric("Medium Risk",f"{(view.analytical_risk=='MEDIUM').sum():,}")
            k4.metric("High Risk",f"{(view.analytical_risk=='HIGH').sum():,}")
            if len(view):
                c1,c2=st.columns(2)
                with c1:
                    if 'plotly.express' in globals() and False: pass
                    import plotly.express as px
                    fig=px.scatter(view,x="cibil_score",y="loan_amount",color="analytical_risk",hover_data=["loan_id","loan_status","income_annum"])
                    fig.update_layout(title="CIBIL vs Loan Amount")
                    st.plotly_chart(fig,use_container_width=True)
                with c2:
                    import plotly.express as px
                    counts=view["analytical_risk"].value_counts().rename_axis("risk").reset_index(name="count")
                    fig=px.bar(counts,x="risk",y="count",title="Risk Distribution")
                    st.plotly_chart(fig,use_container_width=True)
                import plotly.express as px
                grouped=(view.assign(_approved=(view["loan_status"]=="Approved").astype(int))
                         .groupby("analytical_risk",as_index=False)["_approved"].mean()
                         .rename(columns={"_approved":"approval_rate"}))
                grouped["approval_rate"]*=100
                fig=px.bar(grouped,x="analytical_risk",y="approval_rate",title="Observed Approval Rate by Analytical Risk")
                fig.update_yaxes(title="Approval Rate (%)")
                st.plotly_chart(fig,use_container_width=True)
                st.dataframe(view[[c for c in ["loan_id","cibil_score","income_annum","loan_amount","loan_status","analytical_risk","fusion_key"] if c in view.columns]].head(50),use_container_width=True)
            else: st.warning("Select at least one risk level.")

        with loan_tab3:
            st.markdown("### 🔐 Fusion Validation — Complete Dataset Fusion Report")
            st.info(
                "This page explains **exactly how the two source datasets were fused** into "
                "`FundFlow_fused_dataset.csv`. Use this report to demonstrate the fusion methodology to your teacher."
            )

            v = fusion_validation(loan_df)
            details = fusion_validation_details(loan_df)

            q1, q2, q3, q4 = st.columns(4)
            q1.metric("Fused Records", f"{v['rows']:,}")
            q2.metric("Columns", v["columns"])
            q3.metric("Unique Fusion Keys", f"{v['unique_keys']:,}")
            q4.metric("Duplicate Rows", f"{v['duplicate_rows']:,}")

            if v["status"] == "PASS":
                st.success("✅ Key-based fusion validation passed — dataset is ready for analysis.")
            else:
                st.warning("⚠️ Fusion validation needs review.")

            st.markdown("---")
            st.markdown("#### 📋 Source Datasets")
            src1, src2 = st.columns(2)
            with src1:
                st.markdown(f"**Primary Dataset:** `{details['source_primary']}`")
                st.write(details["source_primary_desc"])
                st.metric("Rows in fused output (from primary)", f"{details['source_primary_rows']:,}")
            with src2:
                st.markdown(f"**Secondary Dataset:** `{details['source_secondary']}`")
                st.write(details["source_secondary_desc"])
                st.metric("Approx. rows in secondary dataset", details["source_secondary_rows"])

            st.markdown("---")
            st.markdown("#### 🔗 Fusion Methodology")
            st.markdown(
                f"""
| Property | Value |
|---|---|
| **Fusion Type** | {details.get('fusion_method', 'Key-based LEFT JOIN with pre-aggregation')} |
| **Join Type** | {details['join_type']} |
| **Fusion Key Formula** | `{details['fusion_key_formula']}` |
| **Fusion Key Description** | {details['fusion_key_description']} |
| **Example Fusion Key** | `{details['fusion_key_example']}` |
| **Aggregation Rule** | {details['aggregation_rule']} |
| **Why rows don't multiply** | {details['why_no_row_explosion']} |
"""
            )

            st.markdown("---")
            st.markdown("#### 🔄 Step-by-Step Fusion Process")
            for step in details["steps"]:
                with st.expander(f"Step {step['step']}: {step['title']}", expanded=(step["step"] <= 2)):
                    st.write(step["detail"])

            st.markdown("---")
            st.markdown("#### 📊 Column Groups in the Fused Dataset")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Meta / Fusion Columns**")
                for c in details["meta_columns"]:
                    st.write(f"• `{c}`")
            with col2:
                st.markdown("**Original Loan Columns (from Dataset A)**")
                for c in details["loan_columns"]:
                    st.write(f"• `{c}`")
            with col3:
                st.markdown("**Aggregated Risk Columns (from Dataset B)**")
                for c in details["risk_columns"]:
                    st.write(f"• `{c}`")

            st.markdown("---")
            st.markdown("#### 🧪 Validation Checks")
            st.markdown(
                f"""
| Check | Result | Meaning |
|---|---|---|
| Null fusion keys | **{v['null_keys']:,}** | Every row must have a valid segment key |
| Duplicate full rows | **{v['duplicate_rows']:,}** | No identical duplicate records |
| Duplicate key rows | **{v['key_duplicates']:,}** | Multiple applicants can share the same segment key (expected) |
| Fusion key description present | **{v['has_description']}** | Human-readable key explanation included |
| Total unique segments | **{details['segment_count']:,}** | Distinct dependent+education groups |
| Largest segment | **`{details['largest_segment']}`** ({details['largest_segment_count']:,} loan applications) |
"""
            )

            st.markdown("---")
            st.markdown("#### 👁️ Sample: Same Fusion Key, Different Applicants")
            st.caption(
                f"These rows share fusion key `{details['fusion_key_example']}`. "
                "They keep their individual loan details but receive the **same aggregated risk statistics** "
                "from Loan.csv because they belong to the same segment."
            )
            if len(details["sample_rows"]):
                st.dataframe(details["sample_rows"], use_container_width=True)

            st.markdown("---")
            st.markdown("#### 📐 Fusion Diagram")
            st.markdown(
                """
```mermaid
flowchart LR
    A["loan_approval_dataset.csv<br/>4,269 loan applications"] --> C["Create fusion_key<br/>DEP_n_EDU_GROUP"]
    B["Loan.csv<br/>~20,000 risk records"] --> D["Create same fusion_key"]
    D --> E["GROUP BY fusion_key<br/>Compute averages"]
    E --> F["Aggregated risk features<br/>risk_avg_score, risk_avg_dti, etc."]
    C --> G["LEFT JOIN on fusion_key"]
    F --> G
    G --> H["FundFlow_fused_dataset.csv<br/>4,269 enriched rows"]
```
"""
            )

with main_tab_dataset:
    render_dataset_fusion_dashboard(WORKSPACE_DIR)

with main_tab_kb:
    if st.session_state.faiss_index is not None and st.session_state.active_embed_config != current_config:
        st.warning(
            "⚠️ Embedding settings changed! The current Vector Index dimensions or chunking parameters do "
            "not match your selection. Please rebuild the Vector Database."
        )

    # Metric Dashboard Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card(
            "Documents Ingested",
            str(len(st.session_state.processed_files)),
            ", ".join(st.session_state.processed_files) if st.session_state.processed_files else "None",
            "",
        )
    with col2:
        render_metric_card(
            "Vector Index Status",
            "READY" if st.session_state.faiss_index is not None else "EMPTY",
            "Database is offline" if st.session_state.faiss_index is None else f"Dimension: {st.session_state.faiss_index.dimension}",
            "green" if st.session_state.faiss_index is not None else "purple",
        )
    with col3:
        render_metric_card(
            "Total Chunks",
            str(st.session_state.total_chunks),
            f"Avg. {chunk_size} chars per chunk",
            "purple",
        )
    with col4:
        render_metric_card(
            "Query Retrieval Speed",
            f"{st.session_state.search_latency:.4f}s",
            "Vector search response time",
            "green",
        )

    # Section: Live API Ingestion Portals
    st.markdown("### 🌐 1. Ingest Live Knowledge (Configured APIs)")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📰 NewsAPI", "📈 FRED", "💱 ExchangeRate", "🌍 World Bank", "📊 Alpha Vantage"
    ])

    with tab1:
        news_query = st.text_input("News Search Topic", placeholder="e.g. AI, banking, stock market")
        if st.button("📰 Fetch and Save News", use_container_width=True):
            if not news_query.strip(): st.error("Please enter a search topic.")
            else:
                with st.spinner("Fetching news..."):
                    ok, content = fetch_news_articles(news_query, news_api_key)
                if ok:
                    path=os.path.join(TEMP_DIR, f"news_{news_query.lower().replace(' ','_')}.txt")
                    open(path,"w",encoding="utf-8").write(content); st.success("News saved. Build the vector database to index it.")
                else: st.error(content)

    with tab2:
        fred_series = st.text_input("FRED Series ID", value="GDP", help="Examples: GDP, CPIAUCSL, UNRATE")
        if st.button("📈 Fetch FRED Data", use_container_width=True):
            with st.spinner("Fetching FRED observations..."):
                ok, content = fetch_fred_series(fred_series, fred_api_key)
            if ok:
                path=os.path.join(TEMP_DIR, f"fred_{fred_series.upper()}.txt")
                open(path,"w",encoding="utf-8").write(content); st.success("FRED data saved. Build the vector database to index it.")
            else: st.error(content)

    with tab3:
        st.markdown("#### 💱 Live Currency Converter")
        c1,c2,c3=st.columns(3)
        with c1: amount=st.number_input("Amount", min_value=0.0, value=1000.0, step=100.0)
        with c2: base_currency=st.selectbox("From", ["INR","USD","EUR","GBP","AED","JPY"], index=0)
        with c3: target_currency=st.selectbox("To", ["USD","INR","EUR","GBP","AED","JPY"], index=0)
        if st.button("💱 Convert Amount", type="primary", use_container_width=True):
            with st.spinner("Getting live exchange rate..."):
                ok, content, converted = convert_currency(amount, base_currency, target_currency, exchangerate_api_key)
            if ok:
                st.success(content)
                st.metric("Converted Amount", f"{converted:,.2f} {target_currency}")
            else: st.error(content)
        st.caption("Conversion uses the live ExchangeRate-API rate. Change either currency to convert in the opposite direction.")

    with tab4:
        st.markdown("#### 🌍 World Bank Development Indicators")
        wb1, wb2 = st.columns(2)
        with wb1:
            wb_country = st.text_input("Country Code", value="IND", help="Examples: IND, USA, GBR, CHN")
        with wb2:
            wb_indicator = st.text_input(
                "Indicator Code",
                value="NY.GDP.MKTP.CD",
                help="Examples: NY.GDP.MKTP.CD (GDP), SL.UEM.TOTL.ZS (Unemployment), FP.CPI.TOTL.ZG (Inflation)",
            )
        if st.button("🌍 Fetch World Bank Data", use_container_width=True):
            with st.spinner("Fetching World Bank indicator..."):
                ok, content = fetch_world_bank_indicator(wb_country, wb_indicator)
            if ok:
                path = os.path.join(TEMP_DIR, f"worldbank_{wb_country.upper()}_{wb_indicator.upper()}.txt")
                open(path, "w", encoding="utf-8").write(content)
                st.success("World Bank data saved. Build the vector database to index it.")
                st.text(content)
            else:
                st.error(content)
        st.caption("World Bank Open Data API is free and does not require an API key.")

    with tab5:
        st.markdown("#### 📊 Alpha Vantage Stock Quote")
        av_symbol = st.text_input("Stock Symbol", value="IBM", help="Examples: IBM, AAPL, MSFT, TSLA, INFY")
        if st.button("📊 Fetch Stock Quote", use_container_width=True):
            with st.spinner("Fetching Alpha Vantage quote..."):
                ok, content = fetch_alpha_vantage_quote(av_symbol, alphavantage_api_key)
            if ok:
                path = os.path.join(TEMP_DIR, f"alphavantage_{av_symbol.upper()}.txt")
                open(path, "w", encoding="utf-8").write(content)
                st.success("Alpha Vantage quote saved. Build the vector database to index it.")
                st.text(content)
            else:
                st.error(content)
        st.caption("Requires ALPHAVANTAGE_API_KEY in your .env file (free tier: 25 requests/day).")

    # Section: Chat Interface with automatic API routing
    st.markdown("### 💬 2. Chat with your Knowledge Base")

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and message.get("citations"):
                with st.expander("🔍 View References"):
                    for idx, cit in enumerate(message["citations"]):
                        src = cit["metadata"]["source"]
                        page = cit["metadata"]["page"]
                        score = cit["score"]
                        text = cit["text"]
                        st.markdown(f"**[{idx+1}] File: {src} | Page: {page}** (Similarity: `{score:.3f}`)")
                        st.info(text)

    if user_query := st.chat_input("Ask a question about your ingested knowledge..."):
        with st.chat_message("user"):
            st.markdown(user_query)
        st.session_state.chat_history.append({"role": "user", "content": user_query})

        if st.session_state.faiss_index is None:
            with st.chat_message("assistant"):
                fallback_ans = "⚠️ The Vector Database is empty. Please ingest live knowledge from the API tabs above and build the vector database first."
                st.markdown(fallback_ans)
            st.session_state.chat_history.append({"role": "assistant", "content": fallback_ans})
        else:
            with st.spinner("Routing APIs, retrieving context, and generating answer..."):
                try:
                    prov_embed = "local" if embed_provider.startswith("Local") else ("gemini" if "Gemini" in embed_provider else "openai")
                    embedding_svc = EmbeddingService(provider=prov_embed, api_key=embed_api_key, model_name=embed_model)

                    start_time = time.time()
                    query_vector = embedding_svc.get_embeddings([user_query], is_query=True)
                    retrieved_docs = st.session_state.faiss_index.search(query_vector, k=top_k)
                    st.session_state.search_latency = time.time() - start_time

                    doc_text = st.session_state.document_full_text or " ".join(d["text"] for d in retrieved_docs)

                    # MAJOR CHANGE: Automatic API routing replaces manual LLM selection
                    routing = route_api(doc_text, user_query)
                    st.session_state.last_routing = routing

                    # Chatbot answering is always local/offline. Gemini/OpenAI are not used here.
                    llm_svc = LLMQueryService(provider="local", api_key=None, model_name=None)

                    document_answer = llm_svc.generate_response(user_query, retrieved_docs, temperature=temperature)

                    external = fetch_external_context(
                        routing, news_api_key, fred_api_key, exchangerate_api_key, alphavantage_api_key
                    )
                    response_text = build_combined_response(
                        document_answer=document_answer,
                        external_insights=external.get("external_insights", ""),
                        news_section=external.get("news", ""),
                        sources=[f"FAISS retrieval ({len(retrieved_docs)} chunks)"],
                        routing=routing,
                    )

                    with st.chat_message("assistant"):
                        st.markdown(response_text)
                        if retrieved_docs:
                            with st.expander("🔍 View References"):
                                for idx, cit in enumerate(retrieved_docs):
                                    src = cit["metadata"]["source"]
                                    page = cit["metadata"]["page"]
                                    score = cit["score"]
                                    text = cit["text"]
                                    st.markdown(f"**[{idx+1}] File: {src} | Page: {page}** (Similarity: `{score:.3f}`)")
                                    st.info(text)

                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response_text,
                        "citations": retrieved_docs,
                    })
                    st.rerun()

                except Exception as e:
                    with st.chat_message("assistant"):
                        err_msg = f"❌ An error occurred during retrieval: {str(e)}"
                        st.markdown(err_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": err_msg})

    if st.session_state.chat_history:
        st.markdown("---")
        chat_log = convert_history_to_text(st.session_state.chat_history)
        st.download_button(
            label="📥 Download Chat Transcript",
            data=chat_log,
            file_name=f"documind_chat_history_{int(time.time())}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.markdown(
        """
        <div class="custom-footer">
            DocuMind AI • Built for LLMs & RAG Final Assignment • Powered by Streamlit, FAISS & Sentence Transformers
        </div>
        """,
        unsafe_allow_html=True,
    )
