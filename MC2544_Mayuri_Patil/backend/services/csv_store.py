import csv
import json
import os
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any


class ApiDataStoreError(RuntimeError):
    """Raised when an API record cannot be persisted."""


_write_lock = Lock()
_project_root = Path(__file__).resolve().parents[2]
_dataset_path = _project_root / "dataset"
API_CSV_FILES = {
    "fused_assessments": "fused_assessments.csv",
    "huggingface": "huggingface_recommendations.csv",
    "usda": "usda_foods.csv",
    "openfda": "openfda_drug_labels.csv",
    "openfoodfacts": "openfoodfacts_packaged_foods.csv",
    "openstreetmap": "openstreetmap_nearby_care.csv",
}


def _get_csv_path(api_name: str) -> Path:
    configured_path = os.getenv("API_DATA_CSV_PATH")
    if configured_path:
        path = Path(configured_path)
        base_path = path if path.is_absolute() else _project_root / path
    else:
        base_path = _dataset_path

    try:
        filename = API_CSV_FILES[api_name]
    except KeyError as error:
        raise ApiDataStoreError(f"Unsupported API storage name: {api_name}.") from error
    return base_path / filename


def append_api_record(
    api_name: str,
    endpoint: str,
    request_data: dict[str, Any],
    response_data: dict[str, Any],
) -> None:
    """Append one API request and its response as a CSV record."""
    csv_path = _get_csv_path(api_name)
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "endpoint": endpoint,
        "request_json": json.dumps(request_data, separators=(",", ":"), default=str),
        "response_json": json.dumps(response_data, separators=(",", ":"), default=str),
    }

    try:
        with _write_lock:
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            write_header = not csv_path.exists() or csv_path.stat().st_size == 0
            with csv_path.open("a", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=record.keys())
                if write_header:
                    writer.writeheader()
                writer.writerow(record)
    except OSError as error:
        raise ApiDataStoreError("API data could not be saved to the CSV file.") from error


def read_api_records(api_name: str, limit: int = 5) -> dict[str, Any]:
    """Return a small, newest-first preview of saved external API records."""
    csv_path = _get_csv_path(api_name)
    if not csv_path.exists():
        return {"columns": ["timestamp", "endpoint", "request_json", "response_json"], "record_count": 0, "rows": []}

    try:
        with csv_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames is None:
                raise ApiDataStoreError("The API data CSV file is missing its header row.")

            records = deque(reader, maxlen=limit)
            rows = [
                {
                    "timestamp": record["timestamp"],
                    "endpoint": record["endpoint"],
                    "request": json.loads(record["request_json"]),
                    "response": json.loads(record["response_json"]),
                }
                for record in reversed(records)
            ]
            record_count = reader.line_num - 1
    except (OSError, csv.Error, json.JSONDecodeError, KeyError) as error:
        raise ApiDataStoreError("API data could not be read from the CSV file.") from error

    return {
        "columns": ["timestamp", "endpoint", "request_json", "response_json"],
        "record_count": record_count,
        "rows": rows,
    }


def read_csv_preview(csv_path: Path, limit: int = 5) -> dict[str, Any]:
    """Return a small, newest-first preview of a standard CSV dataset."""
    if not csv_path.exists():
        raise ApiDataStoreError("The requested dataset has not been generated yet.")

    try:
        with csv_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames is None:
                raise ApiDataStoreError("The requested dataset is missing its header row.")

            records = deque(reader, maxlen=limit)
            rows = list(reversed(records))
            record_count = reader.line_num - 1
    except (OSError, csv.Error) as error:
        raise ApiDataStoreError("The requested dataset could not be read.") from error

    return {
        "columns": reader.fieldnames,
        "record_count": record_count,
        "rows": rows,
    }
