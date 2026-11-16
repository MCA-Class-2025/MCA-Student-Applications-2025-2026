"""
base_client.py

Shared HTTP request helper used by every API module in modules/api/.

Provides:
- A configured requests.Session with automatic retries (exponential backoff)
  for transient failures (429, 500, 502, 503, 504).
- Consistent timeout handling.
- Consistent logging (successes, failures, retries) to logs/api_pipeline.log
  and to the console.
- A single place to change retry/timeout behaviour for all 5 APIs.

No API keys are hard-coded here or anywhere else in modules/api/. Keys are
read from environment variables (loaded from .env via python-dotenv) by each
individual API module.
"""

import logging
import os
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("api_pipeline")
if not logger.handlers:
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(os.path.join(LOG_DIR, "api_pipeline.log"))
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


DEFAULT_TIMEOUT = 15  # seconds


def get_session(total_retries: int = 3, backoff_factor: float = 1.5) -> requests.Session:
    """
    Build a requests.Session configured with automatic retry/backoff for
    transient HTTP errors and connection failures.
    """
    session = requests.Session()

    retry_strategy = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


def safe_request(
    method: str,
    url: str,
    api_name: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """
    Perform an HTTP request and always return a normalized result dict:

        {
            "ok": bool,
            "status_code": int | None,
            "data": dict | list | None,
            "error": str | None,
        }

    Never raises. Every failure mode (timeout, connection error, bad status,
    invalid JSON) is caught and reported in the returned dict so callers can
    log and continue instead of crashing the whole pipeline.
    """
    session = get_session()

    try:
        response = session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_body,
            timeout=timeout,
        )
    except requests.exceptions.Timeout:
        msg = f"[{api_name}] Request timed out after {timeout}s: {url}"
        logger.error(msg)
        return {"ok": False, "status_code": None, "data": None, "error": "timeout"}
    except requests.exceptions.ConnectionError as e:
        msg = f"[{api_name}] Connection error: {e}"
        logger.error(msg)
        return {"ok": False, "status_code": None, "data": None, "error": "connection_error"}
    except requests.exceptions.RequestException as e:
        msg = f"[{api_name}] Request exception: {e}"
        logger.error(msg)
        return {"ok": False, "status_code": None, "data": None, "error": str(e)}

    if response.status_code != 200:
        msg = f"[{api_name}] Non-200 response ({response.status_code}) for {url}: {response.text[:300]}"
        logger.warning(msg)
        return {
            "ok": False,
            "status_code": response.status_code,
            "data": None,
            "error": f"http_{response.status_code}",
        }

    try:
        data = response.json()
    except ValueError:
        # Some APIs (e.g. URLhaus form-encoded) may not return JSON in
        # every case; caller can fall back to response.text if needed.
        logger.info(f"[{api_name}] Response was not JSON, returning raw text.")
        return {"ok": True, "status_code": 200, "data": response.text, "error": None}

    logger.info(f"[{api_name}] OK ({response.status_code}) {url}")
    return {"ok": True, "status_code": 200, "data": data, "error": None}
