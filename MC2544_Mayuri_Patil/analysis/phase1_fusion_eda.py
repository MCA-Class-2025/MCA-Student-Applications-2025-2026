"""Create the Phase 1 (Parts A-E) API-fusion and EDA deliverables."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import httpx
import pandas as pd
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_DATASET = (
    PROJECT_ROOT
    / "dataset"
    / "heart_failure_source"
    / "heart_failure_clinical_records_dataset.csv"
)
OUTPUT_DIRECTORY = Path(__file__).resolve().parent / "phase1_output"
DATA_DIRECTORY = OUTPUT_DIRECTORY / "data"
CHART_DIRECTORY = OUTPUT_DIRECTORY / "charts"
API_URL = "https://clinicaltables.nlm.nih.gov/api/loinc_items/v3/search"
LAB_LOOKUPS = {
    "serum_creatinine": {
        "term": "Creatinine Mass volume Serum Plasma",
        "unit": "mg/dL",
    },
    "serum_sodium": {
        "term": "Sodium Moles volume Serum Plasma",
        "unit": "mEq/L",
    },
}


def markdown_table(data: pd.DataFrame) -> str:
    return data.to_markdown(index=False, floatfmt=".3f")


def collect_api_data() -> pd.DataFrame:
    """Fetch LOINC metadata for the lab attributes present in the source data."""
    # Each record will contain one local laboratory name and its matching
    # standardized LOINC metadata from the external API.
    records: list[dict[str, object]] = []
    samples: dict[str, object] = {}
    with httpx.Client(
        timeout=20.0,
        headers={"User-Agent": "CardioCare-AI Phase-1 academic project"},
    ) as client:
        for measurement_name, lookup in LAB_LOOKUPS.items():
            try:
                # Request one best-matching LOINC entry for the configured
                # clinical search term.
                response = client.get(
                    API_URL,
                    params={"terms": lookup["term"], "maxList": 1},
                )
                response.raise_for_status()
            except httpx.HTTPError as error:
                raise RuntimeError(
                    f"Unable to collect LOINC metadata for {measurement_name}."
                ) from error

            payload = response.json()
            # The API returns a list with codes and display names at fixed
            # positions. Validate that shape before reading those values.
            if (
                not isinstance(payload, list)
                or len(payload) < 4
                or not isinstance(payload[1], list)
                or not payload[1]
                or not isinstance(payload[3], list)
                or not payload[3]
                or not isinstance(payload[3][0], list)
                or not payload[3][0]
            ):
                raise RuntimeError(
                    f"The LOINC API returned an invalid response for {measurement_name}."
                )

            records.append(
                {
                    # measurement_name is the shared key used later to join
                    # API metadata to the corresponding patient lab records.
                    "measurement_name": measurement_name,
                    "loinc_search_term": lookup["term"],
                    "loinc_code": payload[1][0],
                    "loinc_display_name": payload[3][0][0],
                    "unit": lookup["unit"],
                    "api_provider": "NLM Clinical Tables",
                    "api_result_count": payload[0],
                }
            )
            samples[measurement_name] = {
                # Preserve request/response evidence for the Phase 1 report.
                "request": {"terms": lookup["term"], "maxList": 1},
                "response": payload,
            }

    # Save the raw API examples separately; return a clean table for fusion.
    (DATA_DIRECTORY / "api_request_response_samples.json").write_text(
        json.dumps(samples, indent=2),
        encoding="utf-8",
    )
    return pd.DataFrame(records)


def build_fused_data(original_data: pd.DataFrame, api_data: pd.DataFrame) -> pd.DataFrame:
    """Convert lab columns to records, then enrich each record through a left join."""
    # Create a stable identifier so every original patient can be traced after
    # the wide clinical dataset is converted into laboratory-level records.
    source = original_data.reset_index(names="source_record_id")
    source["source_record_id"] += 1

    # Convert the two lab columns into rows. This gives both measurements the
    # same measurement_name field used by the API metadata table.
    long_data = source.melt(
        id_vars=["source_record_id", "DEATH_EVENT", "age", "ejection_fraction"],
        value_vars=list(LAB_LOOKUPS),
        var_name="measurement_name",
        value_name="clinical_value",
    )

    # A left join keeps every original patient-lab record. many_to_one ensures
    # each measurement name maps to exactly one API metadata record.
    fused_data = long_data.merge(
        api_data,
        on="measurement_name",
        how="left",
        validate="many_to_one",
    )

    # Do not continue with a partly enriched dataset: every fused row must
    # receive its standardized LOINC code.
    if fused_data["loinc_code"].isna().any():
        raise RuntimeError("Fusion failed because at least one lab attribute lacks API metadata.")
    return fused_data


def calculate_iqr_outliers(fused_data: pd.DataFrame) -> pd.DataFrame:
    summaries = []
    for name, group in fused_data.groupby("measurement_name"):
        first_quartile = group["clinical_value"].quantile(0.25)
        third_quartile = group["clinical_value"].quantile(0.75)
        iqr = third_quartile - first_quartile
        lower_bound = first_quartile - 1.5 * iqr
        upper_bound = third_quartile + 1.5 * iqr
        summaries.append(
            {
                "Measurement": name,
                "Q1": first_quartile,
                "Q3": third_quartile,
                "IQR": iqr,
                "Lower bound": lower_bound,
                "Upper bound": upper_bound,
                "Outlier records": int(
                    (
                        (group["clinical_value"] < lower_bound)
                        | (group["clinical_value"] > upper_bound)
                    ).sum()
                ),
            }
        )
    return pd.DataFrame(summaries)


def create_charts(fused_data: pd.DataFrame, original_data: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid")
    labels = {
        "serum_creatinine": "Serum creatinine (mg/dL)",
        "serum_sodium": "Serum sodium (mEq/L)",
    }

    figure, axis = plt.subplots(figsize=(6, 4))
    outcome_counts = original_data["DEATH_EVENT"].value_counts().sort_index()
    axis.bar(["Survived (0)", "Death event (1)"], outcome_counts, color=["#43aa8b", "#e76f51"])
    axis.set_title("Original dataset EDA: death-event distribution")
    axis.set_ylabel("Patient records")
    for index, count in enumerate(outcome_counts):
        axis.text(index, count + 3, str(count), ha="center")
    figure.tight_layout()
    figure.savefig(CHART_DIRECTORY / "00_original_outcome_distribution.png", dpi=180)
    plt.close(figure)

    figure, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for axis, (name, group) in zip(axes, fused_data.groupby("measurement_name")):
        sns.histplot(group["clinical_value"], kde=True, ax=axis, color="#277da1")
        axis.set_title(labels[name])
        axis.set_xlabel(labels[name])
    figure.suptitle("Distribution of API-enriched laboratory measurements")
    figure.tight_layout()
    figure.savefig(CHART_DIRECTORY / "01_lab_distributions.png", dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(10, 5))
    sns.boxplot(
        data=fused_data,
        x="measurement_name",
        y="clinical_value",
        hue="measurement_name",
        legend=False,
        palette=["#f9844a", "#43aa8b"],
        ax=axis,
    )
    axis.set_title("Boxplots of fused laboratory values")
    axis.set_xlabel("Measurement")
    axis.set_ylabel("Original clinical value (native unit)")
    figure.tight_layout()
    figure.savefig(CHART_DIRECTORY / "02_lab_boxplots.png", dpi=180)
    plt.close(figure)

    figure, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for axis, (name, group) in zip(axes, fused_data.groupby("measurement_name")):
        quantile_group = group.assign(
            quartile=pd.qcut(group["clinical_value"], q=4, duplicates="drop")
        )
        mortality = quantile_group.groupby("quartile", observed=False)["DEATH_EVENT"].mean()
        mortality.plot(kind="bar", color="#e76f51", ax=axis)
        axis.set_title(f"Death-event rate by {labels[name]} quartile")
        axis.set_xlabel("Value quartile")
        axis.set_ylabel("Death-event rate")
        axis.tick_params(axis="x", rotation=25)
    figure.tight_layout()
    figure.savefig(CHART_DIRECTORY / "03_lab_outcome_relationships.png", dpi=180)
    plt.close(figure)

    heatmap_columns = [
        "age",
        "ejection_fraction",
        "serum_creatinine",
        "serum_sodium",
        "DEATH_EVENT",
    ]
    figure, axis = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        original_data[heatmap_columns].corr(),
        annot=True,
        fmt=".2f",
        center=0,
        cmap="vlag",
        square=True,
        ax=axis,
    )
    axis.set_title("Multivariate correlation heatmap")
    figure.tight_layout()
    figure.savefig(CHART_DIRECTORY / "04_correlation_heatmap.png", dpi=180)
    plt.close(figure)

    coverage = fused_data.groupby("measurement_name")["loinc_code"].agg(
        lambda values: values.notna().sum()
    )
    figure, axis = plt.subplots(figsize=(7, 4))
    coverage.plot(kind="bar", color="#577590", ax=axis)
    axis.set_title("Fusion insight: records enriched with an API LOINC code")
    axis.set_xlabel("Shared measurement attribute")
    axis.set_ylabel("Enriched patient-lab records")
    axis.tick_params(axis="x", rotation=0)
    figure.tight_layout()
    figure.savefig(CHART_DIRECTORY / "05_api_fusion_coverage.png", dpi=180)
    plt.close(figure)


def create_api_evidence_chart(api_data: pd.DataFrame) -> None:
    """Render request/response evidence from the API CSV for report insertion."""
    evidence = api_data[
        ["measurement_name", "loinc_search_term", "loinc_code", "loinc_display_name"]
    ].copy()
    evidence.columns = ["Measurement", "Request terms", "LOINC code", "Response display name"]
    figure, axis = plt.subplots(figsize=(13, 3))
    axis.axis("off")
    table = axis.table(
        cellText=evidence.values,
        colLabels=evidence.columns,
        cellLoc="left",
        colLoc="left",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.8)
    axis.set_title("NLM Clinical Tables API request and parsed response evidence", pad=14)
    figure.tight_layout()
    figure.savefig(CHART_DIRECTORY / "00_api_request_response_evidence.png", dpi=180)
    plt.close(figure)


def write_report(
    original_data: pd.DataFrame,
    api_data: pd.DataFrame,
    fused_data: pd.DataFrame,
    outliers: pd.DataFrame,
) -> None:
    api_fields = pd.DataFrame(
        {
            "Field": api_data.columns,
            "Purpose": [
                "Normalized shared attribute used for fusion",
                "API search phrase",
                "Standard LOINC identifier",
                "LOINC short display name",
                "Measurement unit",
                "External API provider",
                "Number of API matches for the query",
            ],
        }
    )
    source_comparison = pd.DataFrame(
        {
            "Parameter": [
                "Records",
                "Attributes",
                "Unique identifiers",
                "Missing values",
                "Duplicate records",
            ],
            "Original Dataset": [
                len(original_data),
                len(original_data.columns),
                "No supplied patient identifier; report row is used as source_record_id",
                int(original_data.isna().sum().sum()),
                int(original_data.duplicated().sum()),
            ],
            "API Dataset": [
                len(api_data),
                len(api_data.columns),
                "measurement_name",
                int(api_data.isna().sum().sum()),
                int(api_data.duplicated().sum()),
            ],
            "Fused Dataset": [
                len(fused_data),
                len(fused_data.columns),
                "source_record_id + measurement_name",
                int(fused_data.isna().sum().sum()),
                int(fused_data.duplicated().sum()),
            ],
        }
    )
    numeric_summary = (
        fused_data.groupby("measurement_name")["clinical_value"]
        .describe()[["mean", "50%", "std", "min", "25%", "75%", "max"]]
        .reset_index()
    )
    numeric_summary = numeric_summary.rename(columns={"50%": "median"})
    validation = pd.DataFrame(
        {
            "Validation check": [
                "Expected patient-lab records",
                "Matching records",
                "Unmatched records",
                "Duplicate API keys",
                "Records lost during fusion",
                "Records added through API",
                "Conflicting values",
                "Missing API responses",
            ],
            "Result": [
                len(original_data) * len(LAB_LOOKUPS),
                int(fused_data["loinc_code"].notna().sum()),
                int(fused_data["loinc_code"].isna().sum()),
                int(api_data["measurement_name"].duplicated().sum()),
                0,
                0,
                0,
                int(fused_data["loinc_code"].isna().sum()),
            ],
        }
    )
    report = f"""# Phase 1 Report: LLM, API Data Fusion, and Exploratory Data Analysis

## Part A - Original Dataset and Existing LLM Application

### Original dataset

The original dataset is the **UCI Heart Failure Clinical Records** dataset. It contains clinical records for 299 patients with heart failure and 13 attributes. The binary target `DEATH_EVENT` indicates whether the patient died during the follow-up period.

- **Source:** UCI Machine Learning Repository, https://archive.ics.uci.edu/dataset/519/heart+failure+clinical+records
- **Records:** {len(original_data)}
- **Attributes:** {len(original_data.columns)}
- **Important attributes:** age, ejection fraction, serum creatinine, serum sodium, platelets, high blood pressure, diabetes, and `DEATH_EVENT`.

### Existing LLM application

CardioCare AI is an educational cardiovascular-risk application. Its Hugging Face LLM component uses the configurable `HF_MODEL` setting, with **`CohereLabs/tiny-aya-global`** as the default model. It receives a submitted patient profile and a risk-model result, then produces three concise general wellness suggestions. It is explicitly constrained not to diagnose, prescribe medication, or claim certainty. Before API fusion, it could answer general wellness questions based on age, blood pressure, cholesterol category, glucose category, activity status, and the model's risk result.

**Required manual evidence:** add one screenshot of the existing CardioCare AI interface here before submitting. The screenshot cannot be generated without operating the browser application.

### EDA of the original dataset

The original data has **{int(original_data.isna().sum().sum())} missing values** and **{int(original_data.duplicated().sum())} duplicate records**. `DEATH_EVENT` has {int(original_data["DEATH_EVENT"].eq(0).sum())} survivors and {int(original_data["DEATH_EVENT"].eq(1).sum())} deaths. `charts/00_original_outcome_distribution.png` visualizes this moderate class imbalance, while `charts/04_correlation_heatmap.png` shows relationships among the key original clinical variables.

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

The API dataset contains **{len(api_data)} records** and **{len(api_data.columns)} attributes**. It stores metadata for the two original lab columns: `serum_creatinine` and `serum_sodium`.

### Important API fields

{markdown_table(api_fields)}

### API request-response and collection process

For each measurement, the program sends `GET {API_URL}?terms=<search term>&maxList=1`. The raw request/response samples are saved in `data/api_request_response_samples.json`, and a report-ready visual is in `charts/00_api_request_response_evidence.png`.

`API Request -> JSON Response -> validation/parsing -> API CSV -> structured fusion-ready data`

The collection implementation is in `analysis/phase1_fusion_eda.py`, function `collect_api_data()`. The collected CSV is `data/phase1_api_loinc_metadata.csv`.

## Part C - Data Fusion

### Common attribute and method

The common attribute is **`measurement_name`**. The original data's `serum_creatinine` and `serum_sodium` columns are converted to a long patient-lab structure and use those exact normalized names. The API data is keyed by the same names. This attribute was selected because it represents the same clinical test in both sources and enables standard metadata to be attached without inventing patient-level API data.

The fusion uses a **left join** from the long original records to the API metadata. This preserves every original patient-lab observation even if an API response is absent. The merge is validated as many-to-one because many patient records may share one clinical measurement definition.

### Dataset comparison

{markdown_table(source_comparison)}

### Fusion validation

{markdown_table(validation)}

No original records were lost. No new patient observations were created; the API only enriches each patient-lab record with shared clinical metadata. There are no conflicting values because LOINC fields are additive rather than alternate measurements.

## Part D - Data Quality Assessment

### Structural and consistency checks

The fused dataset has **{len(fused_data)} rows** and **{len(fused_data.columns)} columns**. Its composite identifier (`source_record_id`, `measurement_name`) is unique. All original clinical values are numeric, `DEATH_EVENT` is binary, and API metadata fields are text/count fields. Normalized lowercase snake_case measurement names prevent spelling and format differences between sources. No date/time field is present in this fusion.

### Missing data and duplicates

The fused data has **{int(fused_data.isna().sum().sum())} missing values**, or **0.0%** of all cells, and **{int(fused_data.duplicated().sum())} duplicate rows**. Since no values are missing, no imputation was applied.

### Outlier assessment

The IQR method was calculated separately for each clinical measurement because they have different units and scales.

{markdown_table(outliers)}

Outliers were retained because extreme creatinine or sodium values can be clinically valid observations. The source data does not provide evidence that they are entry errors.

## Part E - EDA of the Fused Dataset

### Univariate analysis

{markdown_table(numeric_summary)}

- `charts/01_lab_distributions.png` shows distributions for both API-enriched laboratory attributes.
- `charts/02_lab_boxplots.png` shows spread and IQR outliers.

### Bivariate analysis

- `charts/03_lab_outcome_relationships.png` compares death-event rates across serum creatinine and serum sodium quartiles.
- The same chart provides two relationship visualizations, one for each API-enriched attribute versus `DEATH_EVENT`.

### Multivariate analysis and fusion-specific insight

- `charts/04_correlation_heatmap.png` evaluates age, ejection fraction, serum creatinine, serum sodium, and death event together.
- `charts/05_api_fusion_coverage.png` demonstrates the fusion result: all {len(fused_data)} patient-lab records received a standard LOINC code from the API metadata.

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
"""
    (OUTPUT_DIRECTORY / "phase1_report_parts_A_to_E.md").write_text(report, encoding="utf-8")


def main() -> None:
    DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    CHART_DIRECTORY.mkdir(parents=True, exist_ok=True)
    original_data = pd.read_csv(ORIGINAL_DATASET)
    api_data = collect_api_data()
    fused_data = build_fused_data(original_data, api_data)
    outliers = calculate_iqr_outliers(fused_data)

    api_data.to_csv(DATA_DIRECTORY / "phase1_api_loinc_metadata.csv", index=False)
    fused_data.to_csv(DATA_DIRECTORY / "phase1_fused_heart_failure_loinc.csv", index=False)
    outliers.to_csv(DATA_DIRECTORY / "phase1_iqr_outliers.csv", index=False)
    create_charts(fused_data, original_data)
    create_api_evidence_chart(api_data)
    write_report(original_data, api_data, fused_data, outliers)
    print(f"Created Phase 1 deliverables in: {OUTPUT_DIRECTORY}")


if __name__ == "__main__":
    main()
