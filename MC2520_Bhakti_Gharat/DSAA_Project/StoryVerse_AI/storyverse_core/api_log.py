"""
Logs every external API call made anywhere in storyverse_core to a
single growing CSV file: storyverse_data/api_calls.csv

This is separate from dataset.py (which logs one row per STORY).
This one logs one row per individual API CALL - useful for
debugging, cost tracking, and seeing which providers are being hit
and how often / how fast / how reliably.
"""

import csv
import time
from contextlib import contextmanager
from datetime import datetime

from .config import DATA_FOLDER

API_LOG_FILE = DATA_FOLDER / "api_calls.csv"

API_LOG_COLUMNS = [
    "timestamp",
    "api_name",
    "endpoint",
    "request_summary",
    "status",
    "duration_seconds",
    "error",
]


def log_api_call(
    api_name: str,
    endpoint: str,
    request_summary: str,
    status: str,
    duration_seconds: float,
    error: str = "",
):
    """Appends one row. Creates the file with a header on first use."""

    DATA_FOLDER.mkdir(parents=True, exist_ok=True)

    file_exists = API_LOG_FILE.exists()

    with open(API_LOG_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=API_LOG_COLUMNS)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "api_name": api_name,
            "endpoint": endpoint,
            "request_summary": (request_summary or "")[:200],
            "status": status,
            "duration_seconds": round(duration_seconds, 3),
            "error": (error or "")[:300],
        })


@contextmanager
def timed_api_call(api_name: str, endpoint: str, request_summary: str = ""):
    """
    Wrap any external API call with this to auto-log success/failure
    and timing:

        with timed_api_call("Gemini", "generate_content", prompt[:100]):
            response = client.models.generate_content(...)
    """

    start_time = time.time()

    try:
        yield
        log_api_call(
            api_name, endpoint, request_summary,
            "success", time.time() - start_time,
        )

    except Exception as error:
        log_api_call(
            api_name, endpoint, request_summary,
            "failed", time.time() - start_time, error=str(error),
        )
        raise
