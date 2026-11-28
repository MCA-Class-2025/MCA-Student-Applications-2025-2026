"""
app.py - BugAssist AI with Fused Dataset Integration
"""
import streamlit as st
import pandas as pd
import os
import plotly.express as px
import torch

from src.utils import ensure_directories, save_report, get_logger
from src.pdf_loader import process_uploaded_pdfs, PDFLoadError
from src.preprocessing import clean_documents
from src.chunking import chunk_documents
from src.embedding import encode_documents, EMBEDDING_MODEL_NAME
from src.vector_store import build_faiss_index, save_faiss_index, index_exists, VectorStoreError
from src.search import semantic_search, SearchError
from src.llm import generate_response, LLMError, load_llm
from src.ui import inject_custom_css, render_header, render_sidebar, render_response, render_sources
from src.dataset_index import build_dataset_index, dataset_index_exists

logger = get_logger(__name__)

st.set_page_config(page_title="BugAssist AI", page_icon="🐞", layout="wide")

ensure_directories()
inject_custom_css()

# ---------------------------------------------------------------------------
# Load the fused dataset (cached)
# ---------------------------------------------------------------------------
@st.cache_data
def load_fused_dataset():
    import glob
    # Look for any Excel file in data/ (prefer one with "FINAL" in name)
    excel_files = glob.glob("data/*.xlsx")
    excel_path = None
    for f in excel_files:
        if "FINAL" in f or "COMPLETE" in f:
            excel_path = f
            break
    if not excel_path and excel_files:
        excel_path = excel_files[0]  # fallback to first Excel found
    
    csv_path = "data/bug_dataset_300.csv"
    df = None
    
    if excel_path and os.path.exists(excel_path):
        try:
            df = pd.read_excel(excel_path, sheet_name=0)
            print(f"✅ Loaded Excel: {os.path.basename(excel_path)} with {len(df)} rows.")
        except Exception as e:
            print(f"Excel read error: {e}")
    
    # Fallback to CSV if Excel fails or not found
    if df is None and os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            print(f"✅ Loaded CSV with {len(df)} rows.")
        except Exception as e:
            print(f"CSV read error: {e}")
    
    if df is None:
        print("❌ No dataset found.")
        return None
    
    # ---- Add derived columns (safe) ----
    if 'cve_top_id' in df.columns:
        df['has_cve'] = df['cve_top_id'].notna().astype(int)
    else:
        df['has_cve'] = 0
    
    if 'severity' in df.columns:
        severity_map = {'Critical': 'Critical', 'High': 'High', 'Medium': 'Medium', 'Low': 'Low'}
        df['risk_level'] = df['severity'].map(severity_map).fillna('Medium')
    elif 'gemini_priority_recommendation' in df.columns:
        priority_map = {'Critical': 'Critical', 'High': 'High', 'Medium': 'Medium', 'Low': 'Low'}
        df['risk_level'] = df['gemini_priority_recommendation'].map(priority_map).fillna('Medium')
    else:
        df['risk_level'] = 'Medium'
    
    print(f"✅ Added derived columns: has_cve, risk_level")
    return df
df_bugs = load_fused_dataset()

# If dataset exists, build its FAISS index if not already built
if df_bugs is not None and not dataset_index_exists():
    with st.spinner("Building index for the fused dataset..."):
        build_dataset_index(df_bugs)

# ---------------------------------------------------------------------------
# Tabs layout
# ---------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📄 PDF RAG", "🐞 Bug Data Explorer", "🔧 Bug Management"])

# ===========================================================================
# TAB 1: PDF RAG (ORIGINAL FUNCTIONALITY – UNCHANGED)
# ===========================================================================
with tab1:
    render_header()
    render_sidebar()  # You can keep this or move it to the sidebar as before

    st.markdown("## 1️⃣ Upload Bug Reports & Documentation")

    uploaded_files = st.file_uploader(
        "Upload one or more PDF files (bug reports, logs, manuals)",
        type=["pdf"],
        accept_multiple_files=True,
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        create_kb_clicked = st.button("📚 Create Knowledge Base", use_container_width=True)

    if create_kb_clicked:
        if not uploaded_files:
            st.error("⚠️ Please upload at least one PDF file before creating the knowledge base.")
        else:
            try:
                with st.spinner("Processing PDFs..."):
                    raw_documents = process_uploaded_pdfs(uploaded_files)
                    cleaned_documents = clean_documents(raw_documents)
                    if not cleaned_documents:
                        raise PDFLoadError("Text cleaning removed all content.")
                    chunks = chunk_documents(cleaned_documents)
                    if not chunks:
                        raise PDFLoadError("No chunks could be generated.")
                    texts = [c["text"] for c in chunks]
                    embeddings = encode_documents(texts)
                    index = build_faiss_index(embeddings)
                    save_faiss_index(index, chunks)
                st.success(f"✅ Knowledge base created! Indexed {len(chunks)} chunks from {len(uploaded_files)} document(s).")
            except PDFLoadError as exc:
                st.error(f"❌ PDF processing error: {exc}")
            except VectorStoreError as exc:
                st.error(f"❌ Vector store error: {exc}")
            except Exception as exc:
                logger.exception("Unexpected error while building knowledge base")
                st.error(f"❌ Unexpected error: {exc}")

    st.markdown("---")
    st.markdown("## 2️⃣ Ask a Question About Your Bugs")

    if not index_exists():
        st.info("ℹ️ No PDF knowledge base found yet. Upload PDFs and click **Create Knowledge Base** above.")

    query = st.text_area(
        "Enter your bug‑related question",
        placeholder="e.g. Why does the application crash when uploading large files?",
        height=100,
    )

    col_a, col_b = st.columns([1, 3])
    with col_a:
        search_clicked = st.button("🔍 Search & Analyze", use_container_width=True)

    if search_clicked:
        if not query or not query.strip():
            st.error("⚠️ Please enter a valid question.")
        elif not index_exists() and df_bugs is None:
            st.error("⚠️ No knowledge base (PDF or dataset) available.")
        else:
            try:
                with st.spinner("🔎 Searching knowledge base and dataset..."):
                    retrieved_chunks = semantic_search(query, top_k=3, include_dataset=(df_bugs is not None))

                with st.spinner("🤖 Generating AI bug analysis..."):
                    response = generate_response(query, retrieved_chunks)

                render_response(response)
                render_sources(retrieved_chunks)

                try:
                    report_path = save_report(query, response, retrieved_chunks)
                    st.caption(f"💾 Report saved to: `{report_path}`")
                except Exception as exc:
                    logger.warning(f"Failed to save report: {exc}")

            except SearchError as exc:
                st.error(f"❌ Search error: {exc}")
            except LLMError as exc:
                st.error(f"❌ LLM error: {exc}")
            except Exception as exc:
                logger.exception("Unexpected error during search/generation")
                st.error(f"❌ Unexpected error: {exc}")

    st.markdown("---")
    st.caption("BugAssist AI · RAG-powered Bug Analysis · Built with Streamlit, FAISS, Qwen2.5 & Sentence-Transformers")


# ===========================================================================
# TAB 2: BUG DATA EXPLORER
# ===========================================================================
with tab2:
    st.header("🐞 Bug Data Explorer – Base Dataset")

    if df_bugs is None:
        st.error("❌ Dataset not found. Please place `bug_dataset_300.csv` in the `data/` folder.")
        st.stop()

    # Check which enriched columns are available
    has_risk = 'risk_level' in df_bugs.columns
    has_priority = 'gemini_priority_recommendation' in df_bugs.columns
    has_cve = 'cve_top_id' in df_bugs.columns
    has_github = 'github_similar_issues_count' in df_bugs.columns
    has_confidence = 'gemini_fix_confidence_score' in df_bugs.columns

    st.subheader("📊 Overview Statistics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Bugs", len(df_bugs))
    if has_risk:
        col2.metric("Critical Risk", len(df_bugs[df_bugs['risk_level'] == 'Critical']))
    else:
        col2.metric("Critical Risk", "N/A (enrich dataset)")
    if has_priority:
        col3.metric("High Priority", len(df_bugs[df_bugs['gemini_priority_recommendation'] == 'High']))
    else:
        col3.metric("High Priority", "N/A")
    if has_cve:
        col4.metric("CVEs Present", df_bugs['has_cve'].sum() if 'has_cve' in df_bugs else "N/A")
    else:
        col4.metric("CVEs Present", "N/A")

    # Filters – only if columns exist
    st.subheader("🔍 Filter & Search")
    col1, col2, col3 = st.columns(3)
    with col1:
        search_term = st.text_input("Search by title / bug_id")
    with col2:
        if has_priority:
            priority_filter = st.selectbox("Priority", ["All"] + sorted(df_bugs['gemini_priority_recommendation'].unique().tolist()))
        else:
            priority_filter = "All"
            st.info("Priority column not available.")
    with col3:
        if has_risk:
            risk_filter = st.selectbox("Risk Level", ["All"] + sorted(df_bugs['risk_level'].unique().tolist()))
        else:
            risk_filter = "All"
            st.info("Risk column not available.")

    filtered_df = df_bugs.copy()
    if search_term:
        filtered_df = filtered_df[
            filtered_df['title'].str.contains(search_term, case=False) |
            filtered_df['bug_id'].str.contains(search_term, case=False)
        ]
    if priority_filter != "All" and has_priority:
        filtered_df = filtered_df[filtered_df['gemini_priority_recommendation'] == priority_filter]
    if risk_filter != "All" and has_risk:
        filtered_df = filtered_df[filtered_df['risk_level'] == risk_filter]

    st.write(f"Showing **{len(filtered_df)}** bugs")

    # Choose display columns that exist
    display_cols = ['bug_id', 'title']
    if 'severity' in df_bugs.columns:
        display_cols.append('severity')
    if has_priority:
        display_cols.append('gemini_priority_recommendation')
    if has_risk:
        display_cols.append('risk_level')
    if has_github:
        display_cols.append('github_similar_issues_count')
    if has_cve:
        display_cols.append('cve_top_id')
    # Ensure only existing columns
    display_cols = [c for c in display_cols if c in df_bugs.columns]

    st.dataframe(filtered_df[display_cols], use_container_width=True)

    # Detailed view
    if not filtered_df.empty:
        selected_bug = st.selectbox("Select a bug for full details", filtered_df['bug_id'].tolist())
        if selected_bug:
            bug_row = filtered_df[filtered_df['bug_id'] == selected_bug].iloc[0]
            st.json(bug_row.to_dict())

    # Analytics plots – only if columns exist
    st.subheader("📈 Bug Analytics")
    if has_priority:
        fig1 = px.pie(df_bugs, names='gemini_priority_recommendation', title='Priority Distribution')
        col1, col2 = st.columns(2)
        col1.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("Priority data not available – please fuse the dataset to see charts.")

    if has_risk:
        fig2 = px.pie(df_bugs, names='risk_level', title='Risk Level Distribution')
        col1, col2 = st.columns(2)
        col2.plotly_chart(fig2, use_container_width=True)

    if has_confidence and 'cve_top_severity_score' in df_bugs.columns:
        fig3 = px.scatter(df_bugs, x='cve_top_severity_score', y='gemini_fix_confidence_score',
                          color='risk_level' if has_risk else None,
                          title='Confidence vs Severity')
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Enriched columns not available – please fuse the dataset for advanced analytics.")

# ===========================================================================
# TAB 3: BUG MANAGEMENT (FUNCTIONAL APIs) – FULLY UPGRADED
# ===========================================================================
with tab3:
    st.header("🔧 Bug Management & Functional APIs")
    
    # --- Explanation box at the top ---
    st.info("""
    **How this works:**  
    Select a bug below. The same bug data is transformed into **three different API payloads** –  
    each formatted for a specific external service (GitHub, Jira, Slack).  
    This demonstrates how a single dataset can power multiple integrations.
    """)

    if df_bugs is None:
        st.warning("Dataset not loaded. Please ensure the dataset is available.")
    else:
        selected_bug_id = st.selectbox("Select a bug to manage", df_bugs['bug_id'].tolist())
        if selected_bug_id:
            bug = df_bugs[df_bugs['bug_id'] == selected_bug_id].iloc[0]

            # --- Smart fallback for column names (handles both base & fused) ---
            root_cause = bug.get('gemini_root_cause_analysis', bug.get('root_cause', 'N/A'))
            priority = bug.get('gemini_priority_recommendation', bug.get('severity', 'Medium'))
            risk = bug.get('risk_level', bug.get('severity', 'N/A'))
            tech_stack = bug.get('tech_stack', 'N/A')
            environment = bug.get('environment', 'N/A')
            severity = bug.get('severity', 'N/A')

            st.subheader(f"📋 Managing: {bug['bug_id']} - {bug['title']}")

            # ------------------------------------------------------------
            # --- Column 1: GitHub Issue (Markdown format) ---
            # ------------------------------------------------------------
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("#### 🐙 GitHub Issue")
                st.caption("📤 **Target:** GitHub REST API `/repos/.../issues`")
                st.caption("🎯 **Purpose:** Track the bug as a developer task in your repository.")
                if st.button("📝 Create GitHub Issue", use_container_width=True):
                    issue_title = f"Bug: {bug['title']}"
                    issue_body = f"""### Bug Report

| Field | Value |
|-------|-------|
| **Bug ID** | {bug['bug_id']} |
| **Severity** | {severity} |
| **Priority** | {priority} |
| **Tech Stack** | {tech_stack} |
| **Environment** | {environment} |

**Root Cause:**
{root_cause}

**Steps to Reproduce:**
1. Describe step 1
2. Describe step 2
3. Observe the error

**Expected Behavior:**
- What should happen

**Actual Behavior:**
- What actually happens
"""
                    st.success("✅ GitHub issue draft prepared!")
                    with st.expander("📄 Preview GitHub Issue (Markdown)", expanded=True):
                        st.markdown("**Title:**")
                        st.code(issue_title, language="markdown")
                        st.markdown("**Labels:** `bug`, `priority-high`, `needs-triage`")
                        st.markdown("**Body:**")
                        st.code(issue_body, language="markdown")

            # ------------------------------------------------------------
            # --- Column 2: Jira Ticket (JSON format) ---
            # ------------------------------------------------------------
            with col2:
                st.markdown("#### 📋 Jira Ticket")
                st.caption("📤 **Target:** Jira REST API `/rest/api/3/issue`")
                st.caption("🎯 **Purpose:** Manage the bug in a sprint-based project workflow.")
                if st.button("📋 Create Jira Ticket", use_container_width=True):
                    jira_payload = {
                        "fields": {
                            "project": {"key": "PROJ"},
                            "summary": f"[BUG] {bug['title']}",
                            "description": f"""
*Bug ID:* {bug['bug_id']}
*Severity:* {severity}
*Priority:* {priority}
*Tech Stack:* {tech_stack}
*Environment:* {environment}

*Root Cause:*
{root_cause}
""",
                            "issuetype": {"name": "Bug"},
                            "priority": {"name": priority if priority in ["High", "Medium", "Low", "Critical"] else "Medium"},
                        }
                    }
                    st.success("✅ Jira ticket payload generated!")
                    with st.expander("📄 Preview Jira Ticket (JSON)", expanded=True):
                        st.json(jira_payload)

            # ------------------------------------------------------------
            # --- Column 3: Slack Alert (Messaging format) ---
            # ------------------------------------------------------------
            with col3:
                st.markdown("#### 💬 Slack Alert")
                st.caption("📤 **Target:** Slack Incoming Webhook")
                st.caption("🎯 **Purpose:** Instantly notify the team about high-impact bugs.")
                if st.button("💬 Send Slack Alert", use_container_width=True):
                    slack_message = f"""
🚨 *BUG ALERT* 🚨
• *Bug ID:* {bug['bug_id']}
• *Title:* {bug['title']}
• *Severity:* {severity}
• *Priority:* {priority}
• *Tech Stack:* {tech_stack}
• *Environment:* {environment}
• *Root Cause:* {root_cause}
• *Risk Level:* {risk}

:warning: Please review as soon as possible.
"""
                    st.success("✅ Slack alert prepared!")
                    with st.expander("📄 Preview Slack Message", expanded=True):
                        st.code(slack_message, language="markdown")

            # ------------------------------------------------------------
            # --- Separator before AI Triage ---
            # ------------------------------------------------------------
            st.markdown("---")
            st.subheader("🤖 AI Triage Recommendation")
            st.caption("🎯 **Purpose:** Get an AI‑generated recommendation for assigning, prioritising, and fixing the bug.")

            if st.button("Get AI Triage for this bug", use_container_width=True):
                with st.spinner("🧠 AI is analysing the bug..."):
                    try:
                        # Try to use the Qwen LLM if available
                        from src.llm import load_llm
                        import torch
                        tokenizer, model = load_llm()
                        device = "cuda" if torch.cuda.is_available() else "cpu"

                        triage_prompt = f"""
You are a senior software engineering manager. Given the following bug details, provide a structured triage recommendation.

Bug Details:
- ID: {bug['bug_id']}
- Title: {bug['title']}
- Severity: {severity}
- Tech Stack: {tech_stack}
- Root Cause: {root_cause}
- Environment: {environment}

Provide a response with these sections:
1. Recommended Team (e.g., Backend, Frontend, DevOps)
2. Urgency (Critical, High, Medium, Low)
3. Suggested Next Steps
4. Estimated Effort (Small, Medium, Large)
5. Additional Notes

Be concise and specific.
"""
                        messages = [
                            {"role": "system", "content": "You are an expert software triage manager."},
                            {"role": "user", "content": triage_prompt},
                        ]
                        text_input = tokenizer.apply_chat_template(
                            messages, tokenize=False, add_generation_prompt=True
                        )
                        model_inputs = tokenizer([text_input], return_tensors="pt").to(device)
                        with torch.no_grad():
                            generated_ids = model.generate(
                                **model_inputs,
                                max_new_tokens=400,
                                temperature=0.3,
                                top_p=0.9,
                                do_sample=True,
                                pad_token_id=tokenizer.eos_token_id,
                            )
                        generated_ids = [
                            output_ids[len(input_ids):]
                            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
                        ]
                        response_text = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
                        st.success("✅ Triage recommendation generated!")
                        st.markdown(response_text)
                    except Exception as e:
                        # --- Fallback recommendation (if LLM fails) ---
                        st.warning(f"⚠️ Could not use LLM: {e}")
                        # Determine team based on tech stack
                        if 'backend' in tech_stack.lower() or 'api' in root_cause.lower():
                            team = "Backend"
                        elif 'frontend' in tech_stack.lower() or 'ui' in root_cause.lower():
                            team = "Frontend"
                        else:
                            team = "DevOps / Full-Stack"

                        urgency = "Critical" if priority.lower() == "critical" else "High" if priority.lower() == "high" else "Medium"
                        effort = "Large" if 'database' in root_cause.lower() or 'concurrency' in root_cause.lower() else "Medium"

                        fallback = f"""
**1. Recommended Team:** {team}

**2. Urgency:** {urgency}

**3. Suggested Next Steps:**
- Review the root cause: {root_cause}
- Reproduce the issue in the {environment} environment
- Prepare a hotfix if urgency is critical
- Schedule a code review for the affected module

**4. Estimated Effort:** {effort}

**5. Additional Notes:**
- Monitor error logs for similar issues
- Communicate with the team about the fix timeline
"""
                        st.info("💡 Fallback recommendation generated (LLM unavailable):")
                        st.markdown(fallback)
# ---------------------------------------------------------------------------
# Sidebar content (we keep it outside tabs for consistency)
# ---------------------------------------------------------------------------
# You can also move the render_sidebar() call to the sidebar itself.
# For simplicity, we keep it in tab1 but you can move it to st.sidebar.
# To have a consistent sidebar across all tabs, we can render it once.
# Let's add it to the sidebar:
with st.sidebar:
    st.markdown("## 📌 About BugAssist AI")
    st.write(
        "BugAssist AI is a RAG-based assistant that analyzes software bug "
        "reports, logs, and technical documentation to help engineers "
        "quickly understand issues and find fixes."
    )
    st.markdown("---")
    st.markdown("## 📤 Upload Instructions")
    st.write(
        "1. Upload one or more PDF files (bug reports, logs, manuals).\n"
        "2. Click **Create Knowledge Base** to process and index them.\n"
        "3. Ask a question in the query box below.\n"
        "4. Click **Search** to get an AI-generated bug analysis."
    )
    st.markdown("---")
    st.markdown("## 🛠️ Technology Stack")
    st.write(
        "- **Frontend:** Streamlit\n"
        "- **Embeddings:** Sentence-Transformers (all-MiniLM-L6-v2)\n"
        "- **LLM:** Qwen2.5-1.5B-Instruct\n"
        "- **Vector DB:** FAISS\n"
        "- **PDF Parsing:** PyMuPDF\n"
        "- **Core:** Python, NumPy, Pandas, Plotly"
    )
    st.markdown("---")
    st.caption("MCA Final Year Project · RAG Architecture + Fused Dataset")