import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# ============================================================
# FINANCE AI - DATASET LOADER / PREPROCESSING
# ============================================================
# Flow:
# 1. Check CSV files
# 2. Load datasets
# 3. Display dataset information
# 4. Clean column names
# 5. Normalize missing-value tokens
# 6. Detect/convert numeric columns
# 7. Normalize date columns
# 8. Fill missing values
#    - numeric -> median (or 0 if no median exists)
#    - text/date/category -> "Unknown"
# 9. Remove completely empty rows/columns
# 10. Remove duplicate rows
# 11. Create a quality report
# 12. Convert every row into one searchable document
# 13. Save processed CSVs WITHOUT changing originals
# 14. Return documents + metadata for the existing RAG
#
# Assignment source structure includes:
# Upload Dataset -> Load/Display -> Documents/Dataset ->
# Data Preprocessing -> Remove Missing Values ->
# Convert every row into one document -> Chunking ->
# Embedding Generation -> FAISS Index -> Query Processing ->
# Similarity Search -> Top-3 Results.
# This module implements the dataset/loading/preprocessing and
# row-to-document stages; it does not replace your RAG,
# chunking, embeddings, or API code.
# ============================================================

CSV_FOLDER = Path("csv")
PROCESSED_FOLDER = CSV_FOLDER / "processed"
PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)

DATASET_FILES = {
    "stock_dataset": CSV_FOLDER / "stock_dataset.csv",
    "economic_dataset": CSV_FOLDER / "economic_dataset.csv",
    "crypto_dataset": CSV_FOLDER / "crypto_dataset.csv",
    "economic_indicators": CSV_FOLDER / "Economic Indicators And Inflations.csv",
    "financial_news": CSV_FOLDER / "daily_market_data.csv",
}


def print_section(title: str) -> None:
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [" ".join(str(c).strip().split()) for c in df.columns]
    return df


def normalize_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Turn common textual missing values into pandas NA."""
    df = df.copy()

    missing_tokens = {
        "", " ", "na", "n/a", "nan", "null", "none", "nil",
        "-", "--", "missing", "not available", "not_available",
        "unknown"
    }

    for column in df.columns:
        if pd.api.types.is_object_dtype(df[column]):
            text = df[column].astype(str).str.strip()
            df.loc[text.str.lower().isin(missing_tokens), column] = pd.NA

    return df


def detect_numeric_columns(df: pd.DataFrame) -> List[str]:
    """Detect columns that are predominantly numeric."""
    numeric_columns = []

    for column in df.columns:
        if pd.api.types.is_numeric_dtype(df[column]):
            numeric_columns.append(column)
            continue

        series = df[column].dropna()
        if series.empty:
            continue

        converted = pd.to_numeric(
            series.astype(str).str.replace(",", "", regex=False),
            errors="coerce"
        )

        if converted.notna().mean() >= 0.70:
            numeric_columns.append(column)

    return numeric_columns


def convert_numeric_columns(
    df: pd.DataFrame,
    numeric_columns: Optional[List[str]] = None
) -> pd.DataFrame:
    df = df.copy()

    if numeric_columns is None:
        numeric_columns = detect_numeric_columns(df)

    for column in numeric_columns:
        if column not in df.columns:
            continue
        if pd.api.types.is_numeric_dtype(df[column]):
            continue

        cleaned = (
            df[column].astype(str)
            .str.strip()
            .str.replace(",", "", regex=False)
        )

        converted = pd.to_numeric(cleaned, errors="coerce")
        original_non_empty = df[column].notna().sum()

        if original_non_empty:
            success_ratio = converted.notna().sum() / original_non_empty
            if success_ratio >= 0.70:
                df[column] = converted

    return df


def normalize_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize columns whose names indicate dates.
    Unparseable/missing dates become 'Unknown' when the column
    is actually date-like.
    """
    df = df.copy()

    for column in df.columns:
        name = str(column).lower()

        if not (
            name == "date"
            or "date" in name
            or name.endswith("_date")
        ):
            continue

        if pd.api.types.is_numeric_dtype(df[column]):
            continue

        parsed = pd.to_datetime(df[column], errors="coerce")
        valid_ratio = parsed.notna().mean()

        if valid_ratio >= 0.50:
            df[column] = parsed.dt.strftime("%Y-%m-%d")
            df[column] = df[column].fillna("Unknown")

    return df


def fill_missing_values(
    df: pd.DataFrame,
    unknown_value: str = "Unknown"
) -> pd.DataFrame:
    """
    Fill missing values without putting text into numeric fields.

    Numeric columns:
        median, or 0 when no usable median exists.

    Text/category/date columns:
        'Unknown'.
    """
    df = df.copy()

    for column in df.columns:
        if df[column].isna().sum() == 0:
            continue

        if pd.api.types.is_numeric_dtype(df[column]):
            median = df[column].median()
            df[column] = (
                df[column].fillna(median)
                if pd.notna(median)
                else df[column].fillna(0)
            )
        else:
            df[column] = df[column].fillna(unknown_value)

    return df


def dataset_quality_report(
    df: pd.DataFrame,
    dataset_name: str
) -> Dict[str, Any]:
    return {
        "dataset": dataset_name,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_values_total": int(df.isna().sum().sum()),
        "missing_by_column": df.isna().sum().to_dict(),
    }


def print_quality_report(report: Dict[str, Any]) -> None:
    print(f"Dataset: {report['dataset']}")
    print(f"Rows: {report['rows']}")
    print(f"Columns: {report['columns']}")
    print(f"Duplicate rows: {report['duplicate_rows']}")
    print(f"Missing values: {report['missing_values_total']}")
    print("Columns:")

    for column in report["column_names"]:
        missing = report["missing_by_column"].get(column, 0)
        print(f"  - {column} | missing: {missing}")


def value_to_text(value: Any) -> str:
    if pd.isna(value):
        return "Unknown"
    return str(value).strip()


def row_to_document(
    row: pd.Series,
    dataset_name: str,
    row_number: int
) -> Tuple[str, Dict[str, Any]]:
    """
    Convert ONE CSV row into ONE searchable document.
    """
    lines = [f"Dataset: {dataset_name}", f"Row: {row_number}"]

    metadata: Dict[str, Any] = {
        "dataset": dataset_name,
        "row_number": row_number,
    }

    for column, value in row.items():
        text_value = value_to_text(value)
        lines.append(f"{column}: {text_value}")
        metadata[str(column)] = text_value

    return "\n".join(lines), metadata


def dataframe_to_documents(
    df: pd.DataFrame,
    dataset_name: str
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Convert every row into one document."""
    documents = []
    metadata = []

    for row_number, (_, row) in enumerate(df.iterrows(), start=1):
        document, row_metadata = row_to_document(
            row,
            dataset_name,
            row_number
        )
        documents.append(document)
        metadata.append(row_metadata)

    return documents, metadata


def load_and_process_dataset(
    dataset_name: str,
    file_path: Path,
    save_processed: bool = True
) -> Dict[str, Any]:
    """
    Complete loading and preprocessing pipeline for one CSV.
    """
    print_section(f"DATASET: {dataset_name}")

    # 1. Check file
    if not file_path.exists():
        print(f"✗ File not found: {file_path}")
        return {
            "success": False,
            "dataset_name": dataset_name,
            "file_path": str(file_path),
            "dataframe": pd.DataFrame(),
            "documents": [],
            "metadata": [],
        }

    print(f"✓ File found: {file_path}")

    # 2. Load dataset
    try:
        df = pd.read_csv(file_path, low_memory=False)
    except Exception as error:
        print(f"✗ Could not load CSV: {error}")
        return {
            "success": False,
            "dataset_name": dataset_name,
            "file_path": str(file_path),
            "dataframe": pd.DataFrame(),
            "documents": [],
            "metadata": [],
        }

    print(f"✓ Dataset loaded: {len(df)} rows")
    print("Original columns:", list(df.columns))

    # 3. Clean column names
    df = clean_column_names(df)
    print("✓ Column names cleaned")

    # 4. Remove completely empty rows
    before = len(df)
    df = df.dropna(how="all")
    print(f"✓ Empty rows removed: {before - len(df)}")

    # 5. Remove completely empty columns
    before_columns = len(df.columns)
    df = df.dropna(axis=1, how="all")
    print(f"✓ Empty columns removed: {before_columns - len(df.columns)}")

    # 6. Normalize missing-value tokens
    df = normalize_missing_values(df)
    print("✓ Missing-value tokens normalized")

    # 7. Detect and convert numeric columns
    numeric_columns = detect_numeric_columns(df)
    df = convert_numeric_columns(df, numeric_columns)
    print(f"✓ Numeric columns detected: {len(numeric_columns)}")
    print("Numeric columns:", numeric_columns)

    # 8. Normalize date columns
    df = normalize_date_columns(df)
    print("✓ Date columns checked")

    # 9. Fill missing values
    missing_before = int(df.isna().sum().sum())
    df = fill_missing_values(df, unknown_value="Unknown")
    missing_after = int(df.isna().sum().sum())
    print(
        f"✓ Missing values handled: "
        f"{missing_before} -> {missing_after}"
    )

    # 10. Remove duplicate rows
    before = len(df)
    df = df.drop_duplicates()
    print(f"✓ Duplicate rows removed: {before - len(df)}")

    # 11. Final data-quality report
    report = dataset_quality_report(df, dataset_name)
    print_quality_report(report)

    # 12. Save processed CSV separately.
    processed_path = (
        PROCESSED_FOLDER / f"{dataset_name}_processed.csv"
    )

    if save_processed:
        try:
            df.to_csv(processed_path, index=False)
            print(f"✓ Processed CSV saved: {processed_path}")
        except Exception as error:
            print(f"WARNING: Could not save processed CSV: {error}")

    # 13. Convert every row into one document.
    documents, metadata = dataframe_to_documents(
        df,
        dataset_name
    )
    print(f"✓ Documents created: {len(documents)}")

    return {
        "success": True,
        "dataset_name": dataset_name,
        "file_path": str(file_path),
        "processed_path": str(processed_path),
        "dataframe": df,
        "documents": documents,
        "metadata": metadata,
        "report": report,
    }


def load_all_datasets(
    save_processed: bool = True
) -> Dict[str, Dict[str, Any]]:
    """Load and preprocess all five project datasets."""
    print_section("FINANCE AI - DATASET CHECK")
    print(f"Dataset folder: {CSV_FOLDER.resolve()}")
    print(f"Expected datasets: {len(DATASET_FILES)}")

    results = {}

    for dataset_name, file_path in DATASET_FILES.items():
        results[dataset_name] = load_and_process_dataset(
            dataset_name,
            file_path,
            save_processed=save_processed
        )

    print_section("DATASET CHECK COMPLETE")

    successful = 0
    failed = 0
    total_documents = 0

    for dataset_name, result in results.items():
        if result.get("success"):
            successful += 1
            total_documents += len(result.get("documents", []))
            print(
                f"✓ {dataset_name}"
                f" | rows: {len(result['dataframe'])}"
                f" | documents: {len(result['documents'])}"
            )
        else:
            failed += 1
            print(f"✗ {dataset_name}")

    print()
    print(f"Successful datasets: {successful}/{len(DATASET_FILES)}")
    print(f"Failed datasets: {failed}/{len(DATASET_FILES)}")
    print(f"Total searchable documents: {total_documents}")

    return results


def get_all_documents(
    results: Dict[str, Dict[str, Any]]
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Combine all successful dataset documents and metadata."""
    all_documents = []
    all_metadata = []

    for result in results.values():
        if not result.get("success"):
            continue

        all_documents.extend(result.get("documents", []))
        all_metadata.extend(result.get("metadata", []))

    return all_documents, all_metadata


def prepare_datasets_for_rag():
    """
    Convenience function for later use from rag.py.

    Returns:
        results, documents, metadata

    Chunking, embedding generation, vector indexing and query
    processing remain in the existing RAG pipeline.
    """
    results = load_all_datasets()
    documents, metadata = get_all_documents(results)
    return results, documents, metadata


if __name__ == "__main__":
    results = load_all_datasets()

    documents, metadata = get_all_documents(results)

    print_section("RAG DATA PREPARATION")
    print(f"Total documents: {len(documents)}")
    print(f"Total metadata records: {len(metadata)}")

    if documents:
        print()
        print("First document preview:")
        print("-" * 60)
        print(documents[0][:1500])
        print("-" * 60)

    print()
    print("Dataset loader finished successfully.")
