"""
utils/caching.py — Simple file-based caching for API responses.

Streamlit's @st.cache_data is used at the UI layer.
This module provides a lower-level JSON cache for raw API payloads
so they can survive page reloads.
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Any, Optional

from config.settings import RAW_DIR, CACHE_TTL
from utils.logging import logger

_CACHE_DIR = RAW_DIR / "_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_key(namespace: str, identifier: str) -> str:
    h = hashlib.md5(f"{namespace}:{identifier}".encode()).hexdigest()
    return h


def _cache_path(key: str) -> Path:
    return _CACHE_DIR / f"{key}.json"


def get_cached(namespace: str, identifier: str, ttl: int = CACHE_TTL) -> Optional[Any]:
    """Return cached value if fresh, else None."""
    key = _cache_key(namespace, identifier)
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        with open(path) as f:
            payload = json.load(f)
        age = time.time() - payload.get("timestamp", 0)
        if age < ttl:
            logger.debug(f"Cache HIT  [{namespace}] {identifier[:60]}")
            return payload.get("data")
        else:
            logger.debug(f"Cache STALE [{namespace}] {identifier[:60]}")
            return None
    except Exception as e:
        logger.warning(f"Cache read error: {e}")
        return None


def set_cached(namespace: str, identifier: str, data: Any) -> None:
    """Persist data to cache."""
    key = _cache_key(namespace, identifier)
    path = _cache_path(key)
    try:
        with open(path, "w") as f:
            json.dump({"timestamp": time.time(), "data": data}, f)
        logger.debug(f"Cache WRITE [{namespace}] {identifier[:60]}")
    except Exception as e:
        logger.warning(f"Cache write error: {e}")


def invalidate(namespace: str, identifier: str) -> None:
    """Remove a cached entry."""
    key = _cache_key(namespace, identifier)
    path = _cache_path(key)
    if path.exists():
        path.unlink()
        logger.info(f"Cache INVALIDATED [{namespace}] {identifier[:60]}")


def clear_all_cache() -> int:
    """Remove all cache files. Returns count removed."""
    count = 0
    for f in _CACHE_DIR.glob("*.json"):
        f.unlink()
        count += 1
    logger.info(f"Cache cleared: {count} entries removed")
    return count
