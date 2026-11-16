"""
ocr/llm_ocr.py — LLM-assisted medicine name detection for OCR.

This is the "LLM layer on top" of the OCR pipeline:

1. `detect_medicine_name_with_vision(image)` — sends the medicine package
   image directly to a vision-capable LLM (GPT-4o-mini supports vision) and
   asks it to read the medicine name. Used when Tesseract is unavailable or
   produced a low-confidence detection.

2. `correct_medicine_name_with_llm(ocr_text, candidates)` — asks the LLM to
   pick / correct the medicine name from raw OCR text + heuristic candidates,
   fixing OCR character mistakes (0→O, rn→m, ...).

Both degrade gracefully: if the LLM is unavailable or fails, they return
an empty result and the app falls back to manual entry.
"""

import base64
import io
import json
import re
from typing import Any, Dict, List, Optional

from PIL import Image

from llm.client import LLMClient
from llm.prompts import (
    OCR_CORRECTION_SYSTEM_PROMPT,
    OCR_CORRECTION_USER_PROMPT,
    OCR_VISION_SYSTEM_PROMPT,
)
from utils.logging import logger
from utils.validation import sanitize_drug_name

_MAX_IMAGE_SIZE = 900  # pixels on the longest side


def _encode_image(image: Image.Image) -> str:
    """Resize + JPEG-encode the image into a base64 data URI."""
    img = image.copy()
    img.thumbnail((_MAX_IMAGE_SIZE, _MAX_IMAGE_SIZE), Image.LANCZOS)
    if img.mode != "RGB":
        img = img.convert("RGB")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=88)
    b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def _parse_json(content: str) -> Optional[Dict[str, Any]]:
    if not content:
        return None
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else None
    except (ValueError, TypeError):
        pass
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group())
            return parsed if isinstance(parsed, dict) else None
        except (ValueError, TypeError):
            return None
    return None


def _clean_name(name: str) -> str:
    name = sanitize_drug_name(name or "")
    return name.strip()


def detect_medicine_name_with_vision(
    image: Image.Image,
    llm_client: Optional[LLMClient] = None,
) -> Dict[str, Any]:
    """
    Detect the medicine name printed on an image using a vision LLM.

    Returns:
        dict with: detected_name, confidence, reason, available, error
    """
    result: Dict[str, Any] = {
        "detected_name": "",
        "confidence": 0.0,
        "reason": "",
        "available": False,
        "error": None,
    }

    llm = llm_client or LLMClient()
    if not llm.is_available:
        result["error"] = "LLM API key not configured"
        return result

    try:
        data_uri = _encode_image(image)
        messages = [
            {"role": "system", "content": OCR_VISION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Identify the medicine name in this image."},
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ],
            },
        ]
        response = llm.chat(messages, max_tokens=200, temperature=0.0)
        if response.get("error"):
            raise RuntimeError(response["error"])

        parsed = _parse_json(response.get("content", ""))
        if not parsed:
            raise RuntimeError("LLM returned unparseable content")

        name = _clean_name(parsed.get("medicine_name", ""))
        if not name:
            result["error"] = "LLM could not identify a medicine name"
            return result

        try:
            confidence = float(parsed.get("confidence", 0.7))
        except (TypeError, ValueError):
            confidence = 0.7
        confidence = max(0.0, min(1.0, confidence))

        result.update({
            "detected_name": name,
            "confidence": confidence,
            "reason": str(parsed.get("reason", ""))[:300],
            "available": True,
        })
        logger.info(f"LLM vision detected medicine: '{name}' (conf={confidence:.2f})")

    except Exception as e:
        result["error"] = str(e)
        logger.warning(f"LLM vision detection failed: {e}")

    return result


def correct_medicine_name_with_llm(
    ocr_text: str,
    candidates: List[Dict[str, Any]],
    llm_client: Optional[LLMClient] = None,
) -> Dict[str, Any]:
    """
    Ask the LLM to pick / correct the medicine name from raw OCR text +
    heuristic candidates (fixes OCR character errors).

    Returns:
        dict with: detected_name, confidence, reason, available, error
    """
    result: Dict[str, Any] = {
        "detected_name": "",
        "confidence": 0.0,
        "reason": "",
        "available": False,
        "error": None,
    }

    llm = llm_client or LLMClient()
    if not llm.is_available:
        result["error"] = "LLM API key not configured"
        return result

    candidate_lines = [
        f"- {c.get('name', '')} (method: {c.get('method', '?')}, conf: {c.get('confidence', 0):.0%})"
        for c in candidates[:5]
    ] or ["- (none)"]

    user_content = OCR_CORRECTION_USER_PROMPT.format(
        ocr_text=ocr_text[:4000],
        candidates="\n".join(candidate_lines),
    )
    messages = [
        {"role": "system", "content": OCR_CORRECTION_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    try:
        response = llm.chat(messages, max_tokens=200, temperature=0.0)
        if response.get("error"):
            raise RuntimeError(response["error"])

        parsed = _parse_json(response.get("content", ""))
        if not parsed:
            raise RuntimeError("LLM returned unparseable content")

        name = _clean_name(parsed.get("medicine_name", ""))
        if not name:
            result["error"] = "LLM could not determine a medicine name"
            return result

        try:
            confidence = float(parsed.get("confidence", 0.7))
        except (TypeError, ValueError):
            confidence = 0.7
        confidence = max(0.0, min(1.0, confidence))

        result.update({
            "detected_name": name,
            "confidence": confidence,
            "reason": str(parsed.get("reason", ""))[:300],
            "available": True,
        })
        logger.info(f"LLM corrected medicine name: '{name}' (conf={confidence:.2f})")

    except Exception as e:
        result["error"] = str(e)
        logger.warning(f"LLM OCR correction failed: {e}")

    return result