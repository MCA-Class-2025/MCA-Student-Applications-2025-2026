# Phase 2 Report: Fused-data Analysis and Enhanced LLM/RAG

## Part F - Before Fusion vs After Fusion

### New attributes and information

The API introduced `loinc_search_term`, `loinc_code`, `loinc_display_name`, `unit`, `api_provider`, `api_result_count`. `measurement_name` remains the join key rather than a newly added API field. The new fields supply standardized LOINC identities, display names, units, provenance, and search-match counts for the existing laboratory observations.

| Attribute group        |   Original dataset |   Fused dataset |
|:-----------------------|-------------------:|----------------:|
| Clinical/source fields |                 13 |               6 |
| API-derived fields     |                  0 |               6 |
| Total fields           |                 13 |              12 |

### What fusion made possible

The original clinical dataset contained laboratory values but did not contain standardized LOINC identifiers or API provenance. After fusion, the system can retrieve the standardized definition and unit for each laboratory record, calculate metadata coverage, and answer questions such as “What LOINC code identifies serum creatinine?” The API adds shared metadata rather than new patient-level clinical measurements, so it must not be presented as creating new causal clinical relationships.

### Data quality and patterns

The fused dataset contains **598 records**, **12 attributes**, **0 missing API responses**, and **0 duplicate API keys**. All records have LOINC metadata. Fusion did not introduce data-quality problems in the generated output; the original extreme lab values remain clinically plausible observations and are retained.

`charts/06_before_after_attribute_gain.png` visualizes the added API fields. `charts/08_loinc_metadata_coverage.png` confirms 100% LOINC metadata coverage.

## Part G - Insight Generation

1. **Finding:** Higher serum creatinine is associated with death events.  
   **Evidence:** Mean creatinine was 1.836 mg/dL for death events and 1.185 mg/dL for survivors.  
   **Interpretation:** Elevated creatinine is associated with poorer outcomes in these records; this is an association, not a clinical diagnosis.

2. **Finding:** The highest serum-creatinine quartile has the highest death-event rate.  
   **Evidence:** The highest quartile had a 62.5% death-event rate, versus 11.1% in the lowest quartile.  
   **Interpretation:** Higher creatinine is a strong risk-associated pattern in this dataset.

3. **Finding:** The lowest serum-sodium quartile has the highest death-event rate.  
   **Evidence:** The lowest quartile had a 50.6% death-event rate, compared with 23.8% to 26.2% in the higher quartiles.  
   **Interpretation:** Lower sodium is associated with worse outcomes in these records.

4. **Finding:** Creatinine has the stronger linear association with the outcome.  
   **Evidence:** Correlation with DEATH_EVENT is 0.294 for creatinine and -0.195 for sodium.  
   **Interpretation:** Both measurements are informative, but creatinine is stronger here.

5. **Finding:** API fusion standardized every patient-laboratory observation.  
   **Evidence:** All 598 fused records have a non-missing LOINC code, unit, and provider.  
   **Interpretation:** The added metadata improves interoperability and enables grounded retrieval of laboratory definitions.

Supporting summary:

| measurement_name   |   DEATH_EVENT |   count |    mean |   median |   std |     min |     max | outcome_label   |
|:-------------------|--------------:|--------:|--------:|---------:|------:|--------:|--------:|:----------------|
| serum_creatinine   |             0 |     203 |   1.185 |    1.000 | 0.654 |   0.500 |   6.100 | Survived        |
| serum_creatinine   |             1 |      96 |   1.836 |    1.300 | 1.469 |   0.600 |   9.400 | Death event     |
| serum_sodium       |             0 |     203 | 137.217 |  137.000 | 3.983 | 113.000 | 148.000 | Survived        |
| serum_sodium       |             1 |      96 | 135.375 |  135.500 | 5.002 | 116.000 | 146.000 | Death event     |

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

The knowledge base contains **602 documents**: dataset summaries, two API metadata records, and one record for each fused patient-laboratory observation. `backend/services/fused_rag_service.py` builds and queries it. `POST /phase2/questions` retrieves the top source records and sends only those records to the configured Hugging Face model. The model prompt requires it to cite source IDs and decline unsupported answers.

## Part I - LLM Testing

The test ledger has five original-dataset questions and five questions that require fused/API information. Each item stores its expected answer, supporting source record, retrieved sources, LLM output, and correctness status in `data/phase2_llm_test_results.csv`.

| set              | question                                                      | expected_answer     | source                                    | retrieved_sources                                                                                                     | retrieval_correct   | llm_response_status   | llm_correct   |
|:-----------------|:--------------------------------------------------------------|:--------------------|:------------------------------------------|:----------------------------------------------------------------------------------------------------------------------|:--------------------|:----------------------|:--------------|
| Original dataset | How many patient records are in the original dataset?         | 299                 | original_dataset_summary:original-summary | original_dataset_summary:original-summary; fusion_summary:fusion-summary; fused_patient_lab_record:8-serum_creatinine | True                | completed             | True          |
| Original dataset | How many death events are recorded in the original dataset?   | 96                  | original_dataset_summary:original-summary | original_dataset_summary:original-summary; fusion_summary:fusion-summary; fused_patient_lab_record:8-serum_creatinine | True                | completed             | True          |
| Original dataset | What is the target variable in the original dataset?          | DEATH_EVENT         | original_dataset_summary:original-summary | original_dataset_summary:original-summary; fusion_summary:fusion-summary; fused_patient_lab_record:299-serum_sodium   | True                | completed             | True          |
| Original dataset | How many attributes does the original dataset have?           | 13                  | original_dataset_summary:original-summary | original_dataset_summary:original-summary; fusion_summary:fusion-summary; fused_patient_lab_record:299-serum_sodium   | True                | completed             | True          |
| Original dataset | How many survivors are in the original dataset?               | 203                 | original_dataset_summary:original-summary | original_dataset_summary:original-summary; fusion_summary:fusion-summary; fused_patient_lab_record:299-serum_sodium   | True                | completed             | True          |
| Fused/API data   | What LOINC code identifies serum creatinine?                  | 2160-0              | api_loinc_metadata:serum_creatinine       | api_loinc_metadata:serum_creatinine; api_loinc_metadata:serum_sodium; fused_patient_lab_record:8-serum_creatinine     | True                | completed             | True          |
| Fused/API data   | What LOINC code identifies serum sodium?                      | 2951-2              | api_loinc_metadata:serum_sodium           | api_loinc_metadata:serum_sodium; api_loinc_metadata:serum_creatinine; fused_patient_lab_record:2-serum_sodium         | True                | completed             | True          |
| Fused/API data   | What unit is used for serum creatinine?                       | mg/dL               | api_loinc_metadata:serum_creatinine       | api_loinc_metadata:serum_creatinine; api_loinc_metadata:serum_sodium; fused_patient_lab_record:299-serum_sodium       | True                | completed             | True          |
| Fused/API data   | Which API provider supplied the laboratory metadata?          | NLM Clinical Tables | api_loinc_metadata:serum_creatinine       | api_loinc_metadata:serum_sodium; api_loinc_metadata:serum_creatinine; fusion_summary:fusion-summary                   | True                | completed             | True          |
| Fused/API data   | How many patient-laboratory records are in the fused dataset? | 598                 | fusion_summary:fusion-summary             | fusion_summary:fusion-summary; original_dataset_summary:original-summary; fused_patient_lab_record:8-serum_creatinine | True                | completed             | True          |

Live LLM responses require `HF_TOKEN`. Run:

```powershell
.\.venv\Scripts\python.exe analysis\phase2_rag_eda.py --run-llm-tests
```

This command preserves the reproducible test questions and records actual model responses rather than fabricating results. Until live tests run, the report must not claim LLM-answer correctness.

## Part J - Before and After Comparison

| Evaluation parameter       | Before API/fusion                        | After API/fusion                                                  |
|:---------------------------|:-----------------------------------------|:------------------------------------------------------------------|
| Knowledge source           | Submitted patient fields and risk result | Original and LOINC-enriched fused records                         |
| Questions tested           | Original patient-profile questions only  | 10                                                                |
| Grounded retrieval checks  | Not available                            | 10/10                                                             |
| Live LLM answers evaluated | Not available                            | 10/10                                                             |
| Relevant API metadata      | Not available                            | LOINC code, display name, unit, provider, and API result count    |
| Hallucination control      | General wellness system prompt only      | Retriever context plus a prompt that prohibits unsupported claims |

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
