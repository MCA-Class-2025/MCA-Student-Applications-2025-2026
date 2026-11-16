"""
ocr/extractor.py — OCR text extraction and medicine name detection.

Uses Tesseract via pytesseract for OCR, with several reliability fixes:

1. Automatic Tesseract binary discovery (env var, common Windows install
   paths, PATH lookup) — previously OCR silently failed on Windows machines
   where Tesseract is installed in a non-default location.
2. Multi-PSM strategy: runs several page-segmentation modes (6, 11, 3) and
   keeps the highest-quality result instead of trusting a single mode.
3. Confidence filtering: words below a confidence threshold are dropped so
   average confidence is not dragged down by OCR garbage.
4. Robust medicine-name detection: label indicators, case-insensitive drug
   suffixes, font-size analysis (the medicine name is usually the largest
   text on the package), dosage-line context, and a known-drug dictionary.

Falls back gracefully if Tesseract is not installed (LLM vision detection
can be used instead — see ocr/llm_ocr.py).
"""

import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from ocr.preprocessing import preprocess_for_ocr
from utils.logging import logger
from utils.validation import sanitize_drug_name

# ── Tesseract discovery (Windows-friendly) ────────────────────────────────────

_TESSERACT_CANDIDATE_PATHS = [
    "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
    "C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
    "C:\\Users\\{user}\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe",
    "/usr/bin/tesseract",
    "/usr/local/bin/tesseract",
    "/opt/homebrew/bin/tesseract",
]


def _find_tesseract() -> Optional[str]:
    """Locate the Tesseract binary, or None."""
    env_path = os.getenv("TESSERACT_CMD", "").strip()
    if env_path and Path(env_path).exists():
        return env_path

    which = shutil.which("tesseract")
    if which:
        return which

    user = os.getenv("USERNAME", os.getenv("USER", ""))
    for candidate in _TESSERACT_CANDIDATE_PATHS:
        candidate = candidate.format(user=user)
        if Path(candidate).exists():
            return candidate
    return None


_TESSERACT_AVAILABLE = False
_tesseract_bin = _find_tesseract()
try:
    import pytesseract
    if _tesseract_bin:
        pytesseract.pytesseract.tesseract_cmd = _tesseract_bin
        logger.info(f"Using Tesseract binary: {_tesseract_bin}")
    pytesseract.get_tesseract_version()
    _TESSERACT_AVAILABLE = True
    logger.info("Tesseract OCR is available")
except Exception as e:
    _TESSERACT_AVAILABLE = False
    logger.warning(
        f"Tesseract OCR not found ({e}). OCR will return placeholder text. "
        "Install Tesseract from https://github.com/UB-Mannheim/tesseract/wiki "
        "or set TESSERACT_CMD env var. LLM vision detection is available as a fallback."
    )


# ── Text-quality scoring ──────────────────────────────────────────────────────

def _score_ocr_data(ocr_data: Dict[str, Any], min_conf: int = 40) -> Tuple[float, int]:
    """Score an OCR result: (quality, chars). Higher is better."""
    total_conf = 0.0
    chars = 0
    words = 0
    for i, conf in enumerate(ocr_data["conf"]):
        try:
            conf_int = int(conf)
        except (ValueError, TypeError):
            continue
        text = ocr_data["text"][i].strip()
        if conf_int >= min_conf and text:
            total_conf += conf_int
            chars += len(text)
            words += 1
    if words == 0:
        return 0.0, 0
    quality = (total_conf / words) + min(chars / 200.0, 50.0)
    return quality, chars


# ── Common drug-name patterns ─────────────────────────────────────────────────

_LABEL_INDICATORS = [
    r"(?:drug\s+name|product\s+name|medicine\s+name|brand\s+name|generic\s+name)"
    r"\s*[:\-]?\s*([A-Za-z][A-Za-z0-9\-\s]{2,40})",
    r"(?:rx\s+only|prescription)\s+([A-Za-z][A-Za-z0-9\-\s]{2,30})",
    r"(?:contains?|active\s+ingredient[s]?)[:\s]+([A-Za-z][A-Za-z0-9\-\s]{2,40})",
]

# Known drug name suffixes — case-insensitive, hyphen-friendly
_DRUG_SUFFIXES = re.compile(
    r"\b([A-Za-z][A-Za-z\-]{2,}?(?:cillin|mycin|oxacin|zolam|prazole|statin|sartan|"
    r"olol|pril|mab|nib|vir|ine|ide|ate|one|zepam|barbital|cycline|azole|profen|"
    r"afil|pam|amine|taine|lukast|fibrate|glitazone|thiazide|sone|floxacin|"
    r"tidine|dronate|terol|gliptin|glutide|adone))\b",
    re.IGNORECASE,
)

# Common drug names to match directly (case-insensitive, word boundary)
_COMMON_DRUG_NAMES = re.compile(
    r"\b(amoxicillin|metformin|lisinopril|atorvastatin|ibuprofen|acetaminophen|"
    r"paracetamol|aspirin|omeprazole|amlodipine|levothyroxine|losartan|hydrochlorothiazide|"
    r"azithromycin|cephalexin|amoxicillin|ciprofloxacin|doxycycline|prednisone|"
    r"gabapentin|pregabalin|tramadol|sertraline|fluoxetine|alprazolam|diazepam|"
    r"zolpidem|warfarin|clopidogrel|furosemide|metoprolol|carvedilol|simvastatin|"
    r"rosuvastatin|pantoprazole|esomeprazole|ondansetron|clarithromycin|"
    r"penicillin|vancomycin|ceftriaxone|clindamycin|fluconazole|ketoconazole|"
    r"hydroxychloroquine|prednisolone|methotrexate|insulin|glipizide|glimepiride)\b",
    re.IGNORECASE,
)

# Dosage markers that usually follow the drug name on a package
_DOSAGE_MARKER = re.compile(r"\d+\s*(mg|mcg|g|ml|iu|tablet|capsule|caplet)", re.IGNORECASE)

# Common words to strip from detected names
_STOP_WORDS = {
    "tablet", "capsule", "solution", "injection", "suspension", "syrup",
    "for", "and", "the", "oral", "use", "mg", "mcg", "ml", "pack", "packet",
    "tablets", "capsules", "once", "daily", "contains", "net", "contents",
}


def extract_text(image: Image.Image, preprocess: bool = True) -> Dict[str, Any]:
    """
    Extract text from an image using Tesseract OCR.

    Runs multiple page-segmentation modes (6, 11, 3) and keeps the best result.

    Returns:
        dict with keys: text, confidence, words, psm, available
    """
    result: Dict[str, Any] = {
        "text": "",
        "confidence": None,
        "words": [],
        "psm": None,
        "available": _TESSERACT_AVAILABLE,
        "error": None,
    }

    if not _TESSERACT_AVAILABLE:
        result["text"] = (
            "[OCR Unavailable] Tesseract is not installed on this system. "
            "Please install Tesseract and restart the application, or use the "
            "AI Vision detection button below. You can also enter the medicine "
            "name manually."
        )
        result["error"] = "Tesseract not installed"
        return result

    try:
        # Preprocess image for better OCR results
        if preprocess:
            proc_image = preprocess_for_ocr(image)
        else:
            proc_image = image

        import pytesseract

        # Multi-PSM strategy — keep the best-scoring mode
        best: Dict[str, Any] = {"quality": -1.0}
        for psm in ("6", "11", "3"):
            try:
                ocr_data = pytesseract.image_to_data(
                    proc_image,
                    output_type=pytesseract.Output.DICT,
                    config=f"--psm {psm}",
                )
                quality, _chars = _score_ocr_data(ocr_data)
                if quality > best["quality"]:
                    best = {
                        "quality": quality,
                        "data": ocr_data,
                        "psm": int(psm),
                    }
            except Exception as e:
                logger.debug(f"OCR failed with PSM {psm}: {e}")
                continue

        ocr_data = best.get("data")
        if ocr_data is None:
            raise RuntimeError("All Tesseract page-segmentation modes failed")

        # Filter words by confidence
        words = []
        for i, conf in enumerate(ocr_data["conf"]):
            try:
                conf_int = int(conf)
            except (ValueError, TypeError):
                continue
            text = ocr_data["text"][i].strip()
            if conf_int >= 40 and text:
                words.append({
                    "text": text,
                    "confidence": conf_int,
                    "left": ocr_data["left"][i],
                    "top": ocr_data["top"][i],
                    "width": ocr_data["width"][i],
                    "height": ocr_data["height"][i],
                })

        # Full text extraction with the winning PSM
        full_text = pytesseract.image_to_string(
            proc_image, config=f"--psm {best['psm']}"
        )
        avg_conf = (
            sum(w["confidence"] for w in words) / len(words)
            if words else 0
        )

        result["text"] = full_text.strip()
        result["confidence"] = round(avg_conf, 1)
        result["words"] = words
        result["psm"] = best["psm"]
        logger.info(
            f"OCR extracted {len(words)} words (PSM {best['psm']}), "
            f"avg confidence={avg_conf:.1f}%"
        )

    except Exception as e:
        result["error"] = str(e)
        result["text"] = ""
        logger.error(f"OCR extraction error: {e}")

    return result


def detect_medicine_name(ocr_text: str, words: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Attempt to detect the medicine name from OCR-extracted text.

    Strategy (in priority order):
    1. Known-drug dictionary match
    2. Label indicator patterns (e.g., "Drug Name: X")
    3. Largest-font text block (medicine name is the most prominent text)
    4. Drug suffix patterns (-cillin, -mycin, ...)
    5. Line preceding a dosage marker (e.g., "Amoxicillin / 500 mg")

    Returns:
        dict with: detected_name, candidates, method, confidence
    """
    if not ocr_text or len(ocr_text.strip()) < 3:
        return {
            "detected_name": "",
            "candidates": [],
            "method": "none",
            "confidence": 0.0,
        }

    candidates: List[Dict[str, Any]] = []
    text = ocr_text

    # Method 1: known-drug dictionary
    for m in _COMMON_DRUG_NAMES.findall(text):
        name = _clean_detected_name(m)
        if name and len(name) >= 3:
            candidates.append({
                "name": name,
                "method": "drug_dictionary",
                "confidence": 0.95,
            })

    # Method 2: label indicator patterns
    for pattern in _LABEL_INDICATORS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            name = _clean_detected_name(m)
            if name and len(name) >= 4:
                candidates.append({
                    "name": name,
                    "method": "label_indicator",
                    "confidence": 0.90,
                })

    # Method 3: largest-font text (from OCR word boxes)
    if words:
        for name, method_conf in _prominent_text_candidates(words):
            if name and len(name) >= 3:
                candidates.append({
                    "name": name,
                    "method": "largest_font",
                    "confidence": method_conf,
                })

    # Method 4: drug suffix patterns
    suffix_matches = _DRUG_SUFFIXES.findall(text)
    for m in suffix_matches:
        name = _clean_detected_name(m)
        if name and len(name) >= 4:
            candidates.append({
                "name": name,
                "method": "drug_suffix",
                "confidence": 0.75,
            })

    # Method 5: line before a dosage marker (e.g. "500 mg")
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    for idx, line in enumerate(lines):
        if _DOSAGE_MARKER.search(line) and idx > 0:
            prev = _clean_detected_name(lines[idx - 1])
            if prev and 3 <= len(prev) <= 40 and not _DOSAGE_MARKER.search(prev):
                candidates.append({
                    "name": prev,
                    "method": "dosage_context",
                    "confidence": 0.70,
                })

    # Deduplicate by normalized name (highest confidence wins)
    best_by_name: Dict[str, Dict[str, Any]] = {}
    for c in candidates:
        key = c["name"].lower().strip()
        if len(key) < 3:
            continue
        if key not in best_by_name or c["confidence"] > best_by_name[key]["confidence"]:
            best_by_name[key] = c

    unique_candidates = sorted(
        best_by_name.values(), key=lambda x: x["confidence"], reverse=True
    )

    best = unique_candidates[0] if unique_candidates else {"name": "", "method": "none", "confidence": 0.0}

    return {
        "detected_name": best.get("name", ""),
        "candidates": unique_candidates[:5],
        "method": best.get("method", "none"),
        "confidence": best.get("confidence", 0.0),
    }


def _prominent_text_candidates(words: List[Dict], top_n: int = 3) -> List[Tuple[str, float]]:
    """
    Group OCR words into lines and return the text of the LARGEST-FONT lines.
    Medicine names are typically printed larger than surrounding text.
    """
    if not words:
        return []

    # Group words into lines by vertical position
    words_sorted = sorted(words, key=lambda w: w["top"])
    lines: List[List[Dict]] = []
    for word in words_sorted:
        placed = False
        for line in lines:
            line_top = sum(w["top"] for w in line) / len(line)
            if abs(word["top"] - line_top) <= max(12, line_top * 0.15):
                line.append(word)
                placed = True
                break
        if not placed:
            lines.append([word])

    # Rank lines by median font height
    ranked = []
    for line in lines:
        heights = [w.get("height", 0) for w in line]
        if not heights:
            continue
        median_h = sorted(heights)[len(heights) // 2]
        joined = " ".join(w["text"] for w in line).strip()
        if median_h <= 0 or len(joined) < 2 or len(joined) > 45:
            continue
        ranked.append((joined, median_h, sum(w["confidence"] for w in line) / len(line)))

    ranked.sort(key=lambda x: x[1], reverse=True)

    candidates = []
    for joined, _h, _conf in ranked[:top_n]:
        name = _clean_detected_name(joined)
        if name and len(name) >= 3:
            candidates.append((name, 0.80))
    return candidates


def _clean_detected_name(name: str) -> str:
    """Strip dosage info and normalize a detected drug name."""
    name = re.sub(r"\s*\d+\s*(?:mg|mcg|g|ml|IU).*$", "", name, flags=re.IGNORECASE)
    name = sanitize_drug_name(name)
    words = [w for w in name.split() if w.lower() not in _STOP_WORDS]
    return " ".join(words).strip()


def process_uploaded_image(image: Image.Image) -> Dict[str, Any]:
    """
    Full OCR pipeline for a user-uploaded medicine image.

    Returns comprehensive result dict (backwards compatible with the
    previous interface).
    """
    # Extract text
    ocr_result = extract_text(image, preprocess=True)

    # Detect medicine name
    detection_result = {}
    if ocr_result["text"]:
        detection_result = detect_medicine_name(
            ocr_result["text"], words=ocr_result.get("words")
        )

    return {
        "ocr": ocr_result,
        "detection": detection_result,
        "detected_name": detection_result.get("detected_name", ""),
        "ocr_text": ocr_result.get("text", ""),
        "available": ocr_result.get("available", False),
    }