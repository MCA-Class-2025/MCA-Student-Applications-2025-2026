# Phase 1 Report: LLM, API Data Fusion, and Exploratory Data Analysis

## Part A - Original Dataset and Existing LLM Application

### Original dataset

The original dataset is the **UCI Heart Failure Clinical Records** dataset. It contains clinical records for 299 patients with heart failure and 13 attributes. The binary target `DEATH_EVENT` indicates whether the patient died during the follow-up period.

- **Source:** UCI Machine Learning Repository, https://archive.ics.uci.edu/dataset/519/heart+failure+clinical+records
- **Records:** 299
- **Attributes:** 13
- **Important attributes:** age, ejection fraction, serum creatinine, serum sodium, platelets, high blood pressure, diabetes, and `DEATH_EVENT`.

### Existing LLM application

CardioCare AI is an educational cardiovascular-risk application. Its Hugging Face LLM component uses the configurable `HF_MODEL` setting, with **`CohereLabs/tiny-aya-global`** as the default model. It receives a submitted patient profile and a risk-model result, then produces three concise general wellness suggestions. It is explicitly constrained not to diagnose, prescribe medication, or claim certainty. Before API fusion, it could answer general wellness questions based on age, blood pressure, cholesterol category, glucose category, activity status, and the model's risk result.

**Required manual evidence:** add one screenshot of the existing CardioCare AI interface here before submitting. The screenshot cannot be generated without operating the browser application.

### EDA of the original dataset

The original data has **0 missing values** and **0 duplicate records**. `DEATH_EVENT` has 203 survivors and 96 deaths. `charts/00_original_outcome_distribution.png` visualizes this moderate class imbalance, while `charts/04_correlation_heatmap.png` shows relationships among the key original clinical variables.

## Part B - API Data Collection

### API information

| Item | Details |
|---|---|
| API name | Clinical Tables Search Service - LOINC items |
| Provider | U.S. National Library of Medicine (NLM) |
| Purpose | Obtain standard LOINC codes and display names for laboratory measurements |
| Information obtained | LOINC code, display name, matching-record count, and source metadata |
| Request method | HTTPS GET |
| Response format | JSON array |
| Authentication | None |

The API dataset contains **2 records** and **7 attributes**. It stores metadata for the two original lab columns: `serum_creatinine` and `serum_sodium`.

### Important API fields

| Field              | Purpose                                     |
|:-------------------|:--------------------------------------------|
| measurement_name   | Normalized shared attribute used for fusion |
| loinc_search_term  | API search phrase                           |
| loinc_code         | Standard LOINC identifier                   |
| loinc_display_name | LOINC short display name                    |
| unit               | Measurement unit                            |
| api_provider       | External API provider                       |
| api_result_count   | Number of API matches for the query         |

### API request-response and collection process

For each measurement, the program sends `GET https://clinicaltables.nlm.nih.gov/api/loinc_items/v3/search?terms=<search term>&maxList=1`. The raw request/response samples are saved in `data/api_request_response_samples.json`, and a report-ready visual is in `charts/00_api_request_response_evidence.png`.

`API Request -> JSON Response -> validation/parsing -> API CSV -> structured fusion-ready data`

The collection implementation is in `analysis/phase1_fusion_eda.py`, function `collect_api_data()`. The collected CSV is `data/phase1_api_loinc_metadata.csv`.

## Part C - Data Fusion

### Common attribute and method

The common attribute is **`measurement_name`**. The original data's `serum_creatinine` and `serum_sodium` columns are converted to a long patient-lab structure and use those exact normalized names. The API data is keyed by the same names. This attribute was selected because it represents the same clinical test in both sources and enables standard metadata to be attached without inventing patient-level API data.

The fusion uses a **left join** from the long original records to the API metadata. This preserves every original patient-lab observation even if an API response is absent. The merge is validated as many-to-one because many patient records may share one clinical measurement definition.

### Dataset comparison

| Parameter          | Original Dataset                                                       | API Dataset      | Fused Dataset                       |
|:-------------------|:-----------------------------------------------------------------------|:-----------------|:------------------------------------|
| Records            | 299                                                                    | 2                | 598                                 |
| Attributes         | 13                                                                     | 7                | 12                                  |
| Unique identifiers | No supplied patient identifier; report row is used as source_record_id | measurement_name | source_record_id + measurement_name |
| Missing values     | 0                                                                      | 0                | 0                                   |
| Duplicate records  | 0                                                                      | 0                | 0                                   |

### Fusion validation

| Validation check             |   Result |
|:-----------------------------|---------:|
| Expected patient-lab records |      598 |
| Matching records             |      598 |
| Unmatched records            |        0 |
| Duplicate API keys           |        0 |
| Records lost during fusion   |        0 |
| Records added through API    |        0 |
| Conflicting values           |        0 |
| Missing API responses        |        0 |

No original records were lost. No new patient observations were created; the API only enriches each patient-lab record with shared clinical metadata. There are no conflicting values because LOINC fields are additive rather than alternate measurements.

## Part D - Data Quality Assessment

### Structural and consistency checks

The fused dataset has **598 rows** and **12 columns**. Its composite identifier (`source_record_id`, `measurement_name`) is unique. All original clinical values are numeric, `DEATH_EVENT` is binary, and API metadata fields are text/count fields. Normalized lowercase snake_case measurement names prevent spelling and format differences between sources. No date/time field is present in this fusion.

### Missing data and duplicates

The fused data has **0 missing values**, or **0.0%** of all cells, and **0 duplicate rows**. Since no values are missing, no imputation was applied.

### Outlier assessment

The IQR method was calculated separately for each clinical measurement because they have different units and scales.

| Measurement      |      Q1 |      Q3 |   IQR |   Lower bound |   Upper bound |   Outlier records |
|:-----------------|--------:|--------:|------:|--------------:|--------------:|------------------:|
| serum_creatinine |   0.900 |   1.400 | 0.500 |         0.150 |         2.150 |                29 |
| serum_sodium     | 134.000 | 140.000 | 6.000 |       125.000 |       149.000 |                 4 |

Outliers were retained because extreme creatinine or sodium values can be clinically valid observations. The source data does not provide evidence that they are entry errors.

## Part E - EDA of the Fused Dataset

### Univariate analysis

| measurement_name   |    mean |   median |   std |     min |     25% |     75% |     max |
|:-------------------|--------:|---------:|------:|--------:|--------:|--------:|--------:|
| serum_creatinine   |   1.394 |    1.100 | 1.035 |   0.500 |   0.900 |   1.400 |   9.400 |
| serum_sodium       | 136.625 |  137.000 | 4.412 | 113.000 | 134.000 | 140.000 | 148.000 |

- `charts/01_lab_distributions.png` shows distributions for both API-enriched laboratory attributes.
- `charts/02_lab_boxplots.png` shows spread and IQR outliers.

### Bivariate analysis

- `charts/03_lab_outcome_relationships.png` compares death-event rates across serum creatinine and serum sodium quartiles.
- The same chart provides two relationship visualizations, one for each API-enriched attribute versus `DEATH_EVENT`.

### Multivariate analysis and fusion-specific insight

- `charts/04_correlation_heatmap.png` evaluates age, ejection fraction, serum creatinine, serum sodium, and death event together.
- `charts/05_api_fusion_coverage.png` demonstrates the fusion result: all 598 patient-lab records received a standard LOINC code from the API metadata.

## Files for submission

| Deliverable | Location |
|---|---|
| Original dataset | `dataset/heart_failure_source/heart_failure_clinical_records_dataset.csv` |
| API dataset | `analysis/phase1_output/data/phase1_api_loinc_metadata.csv` |
| Fused dataset | `analysis/phase1_output/data/phase1_fused_heart_failure_loinc.csv` |
| API request/response evidence | `analysis/phase1_output/data/api_request_response_samples.json` |
| API request/response visual | `analysis/phase1_output/charts/00_api_request_response_evidence.png` |
| EDA/fusion code | `analysis/phase1_fusion_eda.py` |
| Report | `analysis/phase1_output/phase1_report_parts_A_to_E.md` |
| Visualizations | `analysis/phase1_output/charts/` |
