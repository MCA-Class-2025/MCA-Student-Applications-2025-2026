"""
Phase 4: evaluation of the RAG pipeline.

Every question you ask on the AI Assistant tab (in Phase 3 "rag" mode)
gets logged to st.session_state["eval_log"] with its question, answer,
and retrieved contexts. This page lets you:
  1. Review that log and optionally add a ground-truth reference answer
     for questions where you know the correct answer.
  2. Export the log as CSV/JSON -- the most reliable path, since you can
     run a full RAGAS evaluation in a notebook with more control over
     versions and the judge LLM.
  3. Optionally try an in-app RAGAS evaluation. This needs
     requirements-phase4.txt installed and a Groq key, and RAGAS's exact
     API has changed across versions -- if it errors, the CSV export
     path above will always work.
"""

import json

import pandas as pd
import streamlit as st


def render():
    st.markdown("## 🧪 Evaluation")
    st.markdown(
        "<span class='badge-upcoming'>Phase 4 · RAGAS-based evaluation</span>",
        unsafe_allow_html=True,
    )
    st.write("")

    log = st.session_state.get("eval_log", [])
    rag_entries = [e for e in log if e.get("mode") == "rag"]

    if not rag_entries:
        st.info(
            "No RAG interactions logged yet. Ask a few questions on the "
            "**AI Assistant** tab (with a document indexed and a Groq key "
            "set) to build up an evaluation set here."
        )
        return

    st.markdown(
        f"<div class='fd-card'>{len(rag_entries)} logged RAG interaction(s). "
        "Add a ground-truth answer to any you want RAGAS to score against "
        "(needed for context recall; the other metrics work without it).</div>",
        unsafe_allow_html=True,
    )

    for i, entry in enumerate(rag_entries):
        with st.expander(f"Q{i+1}: {entry['question'][:80]}"):
            st.markdown(f"**Answer:** {entry['answer']}")
            st.markdown(f"**Retrieved contexts:** {len(entry['contexts'])}")
            entry["ground_truth"] = st.text_area(
                "Ground truth (optional)",
                value=entry.get("ground_truth", ""),
                key=f"gt_{i}",
            )

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Export (always works)")
        export_df = pd.DataFrame(
            [
                {
                    "question": e["question"],
                    "answer": e["answer"],
                    "contexts": " ||| ".join(e["contexts"]),
                    "ground_truth": e.get("ground_truth", ""),
                }
                for e in rag_entries
            ]
        )
        st.download_button(
            "⬇️ Download CSV",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name="findocqa_eval_set.csv",
            mime="text/csv",
        )
        st.download_button(
            "⬇️ Download JSON",
            data=json.dumps(rag_entries, indent=2).encode("utf-8"),
            file_name="findocqa_eval_set.json",
            mime="application/json",
        )
        st.caption(
            "Load either file into a notebook and run RAGAS there for full "
            "control over versions and the judge model — this is the most "
            "reliable path for a graded submission."
        )

    with col2:
        st.markdown("#### Try in-app RAGAS")
        run_it = st.button("▶️ Run RAGAS evaluation here")
        if run_it:
            _run_ragas(rag_entries)


def _run_ragas(entries):
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_precision
    except ImportError:
        st.error(
            "RAGAS isn't installed. Run `pip install -r requirements-phase4.txt` "
            "and try again."
        )
        return

    from utils.llm import get_api_key

    if not get_api_key():
        st.error("Add a Groq API key in the sidebar first — RAGAS needs an LLM judge.")
        return

    data = {
        "question": [e["question"] for e in entries],
        "answer": [e["answer"] for e in entries],
        "contexts": [e["contexts"] for e in entries],
    }
    ground_truths = [e.get("ground_truth", "") for e in entries]
    metrics = [faithfulness, answer_relevancy, context_precision]
    if all(ground_truths):
        data["ground_truth"] = ground_truths

    dataset = Dataset.from_dict(data)

    with st.spinner("Running RAGAS (this calls the LLM judge multiple times per row)..."):
        try:
            result = evaluate(dataset, metrics=metrics)
            st.success("Evaluation complete.")
            st.dataframe(result.to_pandas())
        except Exception as e:
            st.error(
                f"RAGAS evaluation failed: {e}\n\n"
                "RAGAS's API changes between versions — if this keeps failing, "
                "use the CSV/JSON export instead and run the evaluation in a "
                "notebook where you can pin a known-working ragas version."
            )
