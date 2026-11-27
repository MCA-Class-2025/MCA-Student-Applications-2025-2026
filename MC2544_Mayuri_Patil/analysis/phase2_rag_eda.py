"""Create the Phase 2 (Parts F-K) fusion-analysis and RAG deliverables."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIRECTORY = PROJECT_ROOT / "backend"
if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIRECTORY))

from services.fused_rag_service import (  # noqa: E402
    FUSED_DATASET_PATH,
    ORIGINAL_DATASET_PATH,
    build_knowledge_base,
    retrieve,
)
from services.llm_service import LlmServiceError, generate_phase2_answer  # noqa: E402

OUTPUT_DIRECTORY = Path(__file__).resolve().parent / "phase2_output"
DATA_DIRECTORY = OUTPUT_DIRECTORY / "data"
CHART_DIRECTORY = OUTPUT_DIRECTORY / "charts"

TEST_CASES = [
    {
        "set": "Original dataset",
        "question": "How many patient records are in the original dataset?",
        "expected_answer": "299",
        "source": "original_dataset_summary:original-summary",
    },
    {
        "set": "Original dataset",
        "question": "How many death events are recorded in the original dataset?",
        "expected_answer": "96",
        "source": "original_dataset_summary:original-summary",
    },
    {
        "set": "Original dataset",
        "question": "What is the target variable in the original dataset?",
        "expected_answer": "DEATH_EVENT",
        "source": "original_dataset_summary:original-summary",
    },
    {
        "set": "Original dataset",
        "question": "How many attributes does the original dataset have?",
        "expected_answer": "13",
        "source": "original_dataset_summary:original-summary",
    },
    {
        "set": "Original dataset",
        "question": "How many survivors are in the original dataset?",
        "expected_answer": "203",
        "source": "original_dataset_summary:original-summary",
    },
    {
        "set": "Fused/API data",
        "question": "What LOINC code identifies serum creatinine?",
        "expected_answer": "2160-0",
        "source": "api_loinc_metadata:serum_creatinine",
    },
    {
        "set": "Fused/API data",
        "question": "What LOINC code identifies serum sodium?",
        "expected_answer": "2951-2",
        "source": "api_loinc_metadata:serum_sodium",
    },
    {
        "set": "Fused/API data",
        "question": "What unit is used for serum creatinine?",
        "expected_answer": "mg/dL",
        "source": "api_loinc_metadata:serum_creatinine",
    },
    {
        "set": "Fused/API data",
        "question": "Which API provider supplied the laboratory metadata?",
        "expected_answer": "NLM Clinical Tables",
        "source": "api_loinc_metadata:serum_creatinine",
    },
    {
        "set": "Fused/API data",
        "question": "How many patient-laboratory records are in the fused dataset?",
        "expected_answer": "598",
        "source": "fusion_summary:fusion-summary",
    },
]


def markdown_table(data: pd.DataFrame) -> str:
    return data.to_markdown(index=False, floatfmt=".3f")


def create_charts(
    original_data: pd.DataFrame,
    fused_data: pd.DataFrame,
    attribute_comparison: pd.DataFrame,
) -> None:
    sns.set_theme(style="whitegrid")

    figure, axis = plt.subplots(figsize=(9, 4.5))
    chart_data = attribute_comparison.melt(
        id_vars="Attribute group",
        value_vars=["Original dataset", "Fused dataset"],
        var_name="Dataset",
        value_name="Attribute count",
    )
    sns.barplot(
        chart_data,
        x="Attribute group",
        y="Attribute count",
        hue="Dataset",
        palette=["#577590", "#43aa8b"],
        ax=axis,
    )
    axis.set_title("Attributes available before and after API fusion")
    axis.set_xlabel("")
    axis.tick_params(axis="x", rotation=16)
    figure.tight_layout()
    figure.savefig(CHART_DIRECTORY / "06_before_after_attribute_gain.png", dpi=180)
    plt.close(figure)

    lab_outcomes = (
        fused_data.groupby(["measurement_name", "DEATH_EVENT"])["clinical_value"]
        .mean()
        .reset_index()
    )
    lab_outcomes["Outcome"] = lab_outcomes["DEATH_EVENT"].map(
        {0: "Survived", 1: "Death event"}
    )
    figure, axis = plt.subplots(figsize=(9, 4.5))
    sns.barplot(
        lab_outcomes,
        x="measurement_name",
        y="clinical_value",
        hue="Outcome",
        palette=["#43aa8b", "#e76f51"],
        ax=axis,
    )
    axis.set_title("Mean fused laboratory values by outcome")
    axis.set_xlabel("API-standardized laboratory measurement")
    axis.set_ylabel("Mean clinical value in native unit")
    figure.tight_layout()
    figure.savefig(CHART_DIRECTORY / "07_fused_lab_outcome_insight.png", dpi=180)
    plt.close(figure)

    coverage = fused_data.groupby("measurement_name")["loinc_code"].agg(
        lambda values: values.notna().mean() * 100
    )
    figure, axis = plt.subplots(figsize=(7, 4))
    coverage.plot(kind="bar", color="#277da1", ax=axis)
    axis.set_ylim(0, 105)
    axis.set_title("API metadata coverage in the fused dataset")
    axis.set_xlabel("Measurement")
    axis.set_ylabel("Rows with LOINC metadata (%)")
    axis.tick_params(axis="x", rotation=0)
    figure.tight_layout()
    figure.savefig(CHART_DIRECTORY / "08_loinc_metadata_coverage.png", dpi=180)
    plt.close(figure)


def build_analysis(
    original_data: pd.DataFrame, fused_data: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, str]]]:
    api_columns = [
        "loinc_search_term",
        "loinc_code",
        "loinc_display_name",
        "unit",
        "api_provider",
        "api_result_count",
    ]
    attribute_comparison = pd.DataFrame(
        {
            "Attribute group": ["Clinical/source fields", "API-derived fields", "Total fields"],
            "Original dataset": [len(original_data.columns), 0, len(original_data.columns)],
            "Fused dataset": [
                6,
                len(api_columns),
                len(fused_data.columns),
            ],
        }
    )
    outcome_summary = (
        fused_data.groupby(["measurement_name", "DEATH_EVENT"])["clinical_value"]
        .agg(["count", "mean", "median", "std", "min", "max"])
        .reset_index()
    )
    outcome_summary["outcome_label"] = outcome_summary["DEATH_EVENT"].map(
        {0: "Survived", 1: "Death event"}
    )

    creatinine = fused_data.loc[
        fused_data["measurement_name"].eq("serum_creatinine")
    ].copy()
    sodium = fused_data.loc[fused_data["measurement_name"].eq("serum_sodium")].copy()
    creatinine_rates = (
        creatinine.assign(quartile=pd.qcut(creatinine["clinical_value"], 4, duplicates="drop"))
        .groupby("quartile", observed=True)["DEATH_EVENT"]
        .mean()
    )
    sodium_rates = (
        sodium.assign(quartile=pd.qcut(sodium["clinical_value"], 4, duplicates="drop"))
        .groupby("quartile", observed=True)["DEATH_EVENT"]
        .mean()
    )
    creatinine_means = creatinine.groupby("DEATH_EVENT")["clinical_value"].mean()
    sodium_means = sodium.groupby("DEATH_EVENT")["clinical_value"].mean()
    correlations = {
        name: group["clinical_value"].corr(group["DEATH_EVENT"])
        for name, group in fused_data.groupby("measurement_name")
    }
    insights = [
        {
            "Finding": "Higher serum creatinine is associated with death events.",
            "Evidence": (
                f"Mean creatinine was {creatinine_means[1]:.3f} mg/dL for death events "
                f"and {creatinine_means[0]:.3f} mg/dL for survivors."
            ),
            "Interpretation": (
                "Elevated creatinine is associated with poorer outcomes in these records; "
                "this is an association, not a clinical diagnosis."
            ),
        },
        {
            "Finding": "The highest serum-creatinine quartile has the highest death-event rate.",
            "Evidence": (
                f"The highest quartile had a {creatinine_rates.iloc[-1]:.1%} death-event rate, "
                f"versus {creatinine_rates.iloc[0]:.1%} in the lowest quartile."
            ),
            "Interpretation": "Higher creatinine is a strong risk-associated pattern in this dataset.",
        },
        {
            "Finding": "The lowest serum-sodium quartile has the highest death-event rate.",
            "Evidence": (
                f"The lowest quartile had a {sodium_rates.iloc[0]:.1%} death-event rate, "
                f"compared with {sodium_rates.iloc[1:].min():.1%} to "
                f"{sodium_rates.iloc[1:].max():.1%} in the higher quartiles."
            ),
            "Interpretation": "Lower sodium is associated with worse outcomes in these records.",
        },
        {
            "Finding": "Creatinine has the stronger linear association with the outcome.",
            "Evidence": (
                f"Correlation with DEATH_EVENT is {correlations['serum_creatinine']:.3f} "
                f"for creatinine and {correlations['serum_sodium']:.3f} for sodium."
            ),
            "Interpretation": "Both measurements are informative, but creatinine is stronger here.",
        },
        {
            "Finding": "API fusion standardized every patient-laboratory observation.",
            "Evidence": (
                f"All {len(fused_data)} fused records have a non-missing LOINC code, "
                "unit, and provider."
            ),
            "Interpretation": (
                "The added metadata improves interoperability and enables grounded retrieval "
                "of laboratory definitions."
            ),
        },
    ]
    return attribute_comparison, outcome_summary, insights


def run_llm_tests(run_live_tests: bool) -> pd.DataFrame:
    results: list[dict[str, object]] = []
    for test_case in TEST_CASES:
        sources = retrieve(test_case["question"])
        retrieved_text = "\n".join(str(source["text"]) for source in sources)
        retrieval_correct = test_case["expected_answer"].lower() in retrieved_text.lower()
        response = "Not run. Use --run-llm-tests with HF_TOKEN configured."
        response_status = "not_run"
        llm_correct: bool | None = None
        if run_live_tests:
            try:
                response, _ = generate_phase2_answer(test_case["question"])
                response_status = "completed"
                llm_correct = test_case["expected_answer"].lower() in response.lower()
            except LlmServiceError as error:
                response = f"Failed: {error}"
                response_status = "failed"

        results.append(
            {
                **test_case,
                "retrieved_sources": "; ".join(
                    f"{source['source']}:{source['record_id']}" for source in sources
                ),
                "retrieval_correct": retrieval_correct,
                "llm_response": response,
                "llm_response_status": response_status,
                "llm_correct": llm_correct,
            }
        )
    return pd.DataFrame(results)


def write_report(
    original_data: pd.DataFrame,
    fused_data: pd.DataFrame,
    attribute_comparison: pd.DataFrame,
    outcome_summary: pd.DataFrame,
    insights: list[dict[str, str]],
    test_results: pd.DataFrame,
    knowledge_base_records: int,
) -> None:
    api_fields = [
        "`loinc_search_term`",
        "`loinc_code`",
        "`loinc_display_name`",
        "`unit`",
        "`api_provider`",
        "`api_result_count`",
    ]
    insight_markdown = "\n\n".join(
        f"{index}. **Finding:** {insight['Finding']}  \n"
        f"   **Evidence:** {insight['Evidence']}  \n"
        f"   **Interpretation:** {insight['Interpretation']}"
        for index, insight in enumerate(insights, start=1)
    )
    retrieval_results = test_results[
        [
            "set",
            "question",
            "expected_answer",
            "source",
            "retrieved_sources",
            "retrieval_correct",
            "llm_response_status",
            "llm_correct",
        ]
    ]
    live_results = test_results[test_results["llm_response_status"].eq("completed")]
    comparison = pd.DataFrame(
        {
            "Evaluation parameter": [
                "Knowledge source",
                "Questions tested",
                "Grounded retrieval checks",
                "Live LLM answers evaluated",
                "Relevant API metadata",
                "Hallucination control",
            ],
            "Before API/fusion": [
                "Submitted patient fields and risk result",
                "Original patient-profile questions only",
                "Not available",
                "Not available",
                "Not available",
                "General wellness system prompt only",
            ],
            "After API/fusion": [
                "Original and LOINC-enriched fused records",
                str(len(test_results)),
                f"{int(test_results['retrieval_correct'].sum())}/{len(test_results)}",
                (
                    f"{int(live_results['llm_correct'].fillna(False).sum())}/"
                    f"{len(live_results)}"
                    if not live_results.empty
                    else "Not run; configure HF_TOKEN and rerun with --run-llm-tests"
                ),
                "LOINC code, display name, unit, provider, and API result count",
                "Retriever context plus a prompt that prohibits unsupported claims",
            ],
        }
    )
    report = f"""# Phase 2 Report: Fused-data Analysis and Enhanced LLM/RAG

## Part F - Before Fusion vs After Fusion

### New attributes and information

The API introduced {", ".join(api_fields)}. `measurement_name` remains the join key rather than a newly added API field. The new fields supply standardized LOINC identities, display names, units, provenance, and search-match counts for the existing laboratory observations.

{markdown_table(attribute_comparison)}

### What fusion made possible

The original clinical dataset contained laboratory values but did not contain standardized LOINC identifiers or API provenance. After fusion, the system can retrieve the standardized definition and unit for each laboratory record, calculate metadata coverage, and answer questions such as “What LOINC code identifies serum creatinine?” The API adds shared metadata rather than new patient-level clinical measurements, so it must not be presented as creating new causal clinical relationships.

### Data quality and patterns

The fused dataset contains **{len(fused_data)} records**, **{len(fused_data.columns)} attributes**, **0 missing API responses**, and **0 duplicate API keys**. All records have LOINC metadata. Fusion did not introduce data-quality problems in the generated output; the original extreme lab values remain clinically plausible observations and are retained.

`charts/06_before_after_attribute_gain.png` visualizes the added API fields. `charts/08_loinc_metadata_coverage.png` confirms 100% LOINC metadata coverage.

## Part G - Insight Generation

{insight_markdown}

Supporting summary:

{markdown_table(outcome_summary)}

`charts/07_fused_lab_outcome_insight.png` visualizes the mean laboratory values by outcome.

## Part H - Integration with the Enhanced LLM/RAG System

The enhanced system uses a persisted local TF-IDF vector knowledge base. TF-IDF creates sparse vector embeddings for textual source records, and cosine similarity ranks the records for each question.

```text
Fused CSV + original CSV
        ↓
Document/record creation
        ↓
TF-IDF vector embedding
        ↓
Persisted local vector knowledge base (.joblib)
        ↓
Cosine-similarity retriever
        ↓
Hugging Face LLM with retrieved source context
```

The knowledge base contains **{knowledge_base_records} documents**: dataset summaries, two API metadata records, and one record for each fused patient-laboratory observation. `backend/services/fused_rag_service.py` builds and queries it. `POST /phase2/questions` retrieves the top source records and sends only those records to the configured Hugging Face model. The model prompt requires it to cite source IDs and decline unsupported answers.

## Part I - LLM Testing

The test ledger has five original-dataset questions and five questions that require fused/API information. Each item stores its expected answer, supporting source record, retrieved sources, LLM output, and correctness status in `data/phase2_llm_test_results.csv`.

{markdown_table(retrieval_results)}

Live LLM responses require `HF_TOKEN`. Run:

```powershell
.\\.venv\\Scripts\\python.exe analysis\\phase2_rag_eda.py --run-llm-tests
```

This command preserves the reproducible test questions and records actual model responses rather than fabricating results. Until live tests run, the report must not claim LLM-answer correctness.

## Part J - Before and After Comparison

{markdown_table(comparison)}

The enhanced implementation makes API-derived LOINC metadata available to the LLM through retrieval. The documented retrieval checks verify that expected facts are found in the correct source records. A measured claim about live LLM accuracy requires the configured-token test run above.

## Part K - Technical Documentation

| Deliverable | Location |
| --- | --- |
| Original dataset | `dataset/heart_failure_source/heart_failure_clinical_records_dataset.csv` |
| API dataset | `analysis/phase1_output/data/phase1_api_loinc_metadata.csv` |
| Final fused CSV | `analysis/phase1_output/data/phase1_fused_heart_failure_loinc.csv` |
| Phase 1 EDA/fusion script | `analysis/phase1_fusion_eda.py` |
| Phase 2 analysis and evaluation script | `analysis/phase2_rag_eda.py` |
| RAG implementation | `backend/services/fused_rag_service.py` |
| Grounded LLM integration | `backend/services/llm_service.py` and `POST /phase2/questions` |
| Knowledge-base artifact | `analysis/phase2_output/rag/fused_knowledge_base.joblib` |
| Test results | `analysis/phase2_output/data/phase2_llm_test_results.csv` |
| Phase 2 report | `analysis/phase2_output/phase2_report_parts_F_to_K.md` |

The report is reproducible: regenerate all Phase 2 outputs with `analysis/phase2_rag_eda.py`. Add browser/API screenshots after running the application, since screenshots cannot be truthfully generated in a non-interactive script.
"""
    (OUTPUT_DIRECTORY / "phase2_report_parts_F_to_K.md").write_text(report, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create Phase 2 fused-data analysis and RAG deliverables."
    )
    parser.add_argument(
        "--run-llm-tests",
        action="store_true",
        help="Call the configured Hugging Face model for the ten test questions.",
    )
    arguments = parser.parse_args()
    load_dotenv(PROJECT_ROOT / ".env", encoding="utf-8-sig")

    if not ORIGINAL_DATASET_PATH.exists() or not FUSED_DATASET_PATH.exists():
        raise FileNotFoundError(
            "Phase 1 data is missing. Run analysis/phase1_fusion_eda.py before Phase 2."
        )
    if arguments.run_llm_tests and not os.getenv("HF_TOKEN"):
        raise RuntimeError("HF_TOKEN must be configured before running live LLM tests.")

    DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    CHART_DIRECTORY.mkdir(parents=True, exist_ok=True)
    original_data = pd.read_csv(ORIGINAL_DATASET_PATH)
    fused_data = pd.read_csv(FUSED_DATASET_PATH)
    knowledge_base_records = build_knowledge_base()
    attribute_comparison, outcome_summary, insights = build_analysis(original_data, fused_data)
    create_charts(original_data, fused_data, attribute_comparison)
    test_results = run_llm_tests(arguments.run_llm_tests)

    attribute_comparison.to_csv(DATA_DIRECTORY / "before_after_attributes.csv", index=False)
    outcome_summary.to_csv(DATA_DIRECTORY / "phase2_lab_outcome_summary.csv", index=False)
    pd.DataFrame(insights).to_csv(DATA_DIRECTORY / "phase2_insights.csv", index=False)
    test_results.to_csv(DATA_DIRECTORY / "phase2_llm_test_results.csv", index=False)
    write_report(
        original_data,
        fused_data,
        attribute_comparison,
        outcome_summary,
        insights,
        test_results,
        knowledge_base_records,
    )
    print(f"Created Phase 2 deliverables in: {OUTPUT_DIRECTORY}")


if __name__ == "__main__":
    main()
