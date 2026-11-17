"""
BookMuse 2.0 - OCR & Vision Cover Processor
Improved OCR for book-cover title/author recognition.
"""

import os
import io
import base64
import re

from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import pytesseract
from pytesseract import Output

from typing import Dict, Optional


class OCRProcessor:

    def __init__(self):
        """Initialize OCR processor with safe Tesseract detection."""

        self.tesseract_available = False

        try:
            pytesseract.pytesseract.get_tesseract_version()
            self.tesseract_available = True
            print("✅ Tesseract OCR detected")
        except Exception:
            print(
                "INFO: Tesseract OCR binary not detected on host system. "
                "Advanced image feature extraction mode active."
            )

    # ============================================================
    # BASIC UTILITIES
    # ============================================================

    def is_ocr_available(self) -> bool:
        """Check whether Tesseract OCR is available."""
        return self.tesseract_available

    def encode_image_base64(
        self,
        image_path: str
    ) -> Optional[str]:
        """Encode image file to Base64 for Vision APIs."""

        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(
                    image_file.read()
                ).decode("utf-8")

        except Exception as e:
            print(f"Error encoding image to base64: {e}")
            return None

    # ============================================================
    # IMAGE PREPROCESSING
    # ============================================================

    def _prepare_image(self, image: Image.Image) -> Image.Image:
        """
        Prepare a book-cover image for better OCR.

        Steps:
        - Convert to RGB
        - Upscale smaller images
        - Convert to grayscale
        - Increase contrast
        - Sharpen
        """

        image = image.convert("RGB")

        width, height = image.size

        # Upscale smaller images.
        # OCR performs much better when text has enough pixels.
        if width < 1600:
            scale = 1600 / width
            image = image.resize(
                (
                    int(width * scale),
                    int(height * scale)
                ),
                Image.Resampling.LANCZOS
            )

        # Grayscale
        gray = ImageOps.grayscale(image)

        # Increase contrast
        gray = ImageEnhance.Contrast(gray).enhance(1.8)

        # Slight sharpening
        gray = ImageEnhance.Sharpness(gray).enhance(2.0)

        # Remove tiny noise
        gray = gray.filter(ImageFilter.MedianFilter(size=3))

        return gray

    def _create_ocr_variants(
        self,
        image: Image.Image
    ):
        """
        Create multiple image variants.

        Different book covers work better with different
        thresholding/contrast levels.
        """

        prepared = self._prepare_image(image)

        variants = []

        # Variant 1: Enhanced grayscale
        variants.append(prepared)

        # Variant 2: Normal binary threshold
        threshold_1 = prepared.point(
            lambda p: 255 if p > 150 else 0
        )
        variants.append(threshold_1)

        # Variant 3: Darker threshold
        threshold_2 = prepared.point(
            lambda p: 255 if p > 110 else 0
        )
        variants.append(threshold_2)

        # Variant 4: Lighter threshold
        threshold_3 = prepared.point(
            lambda p: 255 if p > 190 else 0
        )
        variants.append(threshold_3)

        return variants

    # ============================================================
    # OCR ENGINE
    # ============================================================

    def _run_ocr(self, image: Image.Image) -> str:
        """Run OCR using several Tesseract page segmentation modes."""

        if not self.tesseract_available:
            return ""

        results = []

        configs = [
            "--psm 6",
            "--psm 11",
            "--psm 12",
        ]

        for config in configs:

            try:
                text = pytesseract.image_to_string(
                    image,
                    config=config
                )

                if text and text.strip():
                    results.append(text)

            except Exception:
                continue

        return "\n".join(results)

    # ============================================================
    # OCR WITH LINE INFORMATION
    # ============================================================

    def _extract_lines(self, image: Image.Image):
        """
        Extract OCR lines while preserving their structure.

        This is important because the previous implementation
        destroyed newline information before identifying title/author.
        """

        if not self.tesseract_available:
            return []

        lines = []

        try:

            data = pytesseract.image_to_data(
                image,
                config="--psm 11",
                output_type=Output.DICT
            )

            current_lines = {}

            n = len(data["text"])

            for i in range(n):

                text = data["text"][i].strip()

                if not text:
                    continue

                try:
                    confidence = float(data["conf"][i])
                except Exception:
                    confidence = 0

                if confidence < 15:
                    continue

                block = data["block_num"][i]
                par = data["par_num"][i]
                line = data["line_num"][i]

                key = (block, par, line)

                if key not in current_lines:
                    current_lines[key] = {
                        "text": [],
                        "confidence": [],
                        "top": data["top"][i],
                        "height": data["height"][i]
                    }

                current_lines[key]["text"].append(text)
                current_lines[key]["confidence"].append(confidence)

            for item in current_lines.values():

                line_text = " ".join(item["text"]).strip()

                if len(line_text) < 2:
                    continue

                avg_confidence = (
                    sum(item["confidence"])
                    / len(item["confidence"])
                )

                lines.append({
                    "text": line_text,
                    "confidence": round(avg_confidence, 2),
                    "top": item["top"],
                    "height": item["height"]
                })

        except Exception as e:
            print(f"INFO: Structured OCR failed: {e}")

        # Reading order
        lines.sort(key=lambda x: x["top"])

        return lines

    # ============================================================
    # TITLE / AUTHOR DETECTION
    # ============================================================

    def _identify_title_and_author(
        self,
        lines,
        full_text: str
    ):
        """
        Heuristic title/author detection.

        Uses OCR line size, position and common author patterns.
        """

        if not lines:
            return "", ""

        # Remove obvious OCR junk
        cleaned_lines = []

        for item in lines:

            text = item["text"].strip()

            if len(text) < 2:
                continue

            # Ignore lines that are almost entirely symbols/numbers
            alpha_count = sum(
                char.isalpha()
                for char in text
            )

            if alpha_count < 2:
                continue

            cleaned_lines.append(item)

        if not cleaned_lines:
            return "", ""

        # --------------------------------------------------------
        # AUTHOR DETECTION
        # --------------------------------------------------------

        author_keywords = [
            "written by",
            "by ",
            "author",
            "novel by"
        ]

        author_candidate = ""

        for item in cleaned_lines:

            text = item["text"].strip()
            lower = text.lower()

            if any(
                keyword in lower
                for keyword in author_keywords
            ):
                author_candidate = re.sub(
                    r"^(written\s+by|novel\s+by|by|author)\s*:?\s*",
                    "",
                    text,
                    flags=re.IGNORECASE
                ).strip()

                break

        # If no explicit "by", look at likely author line.
        if not author_candidate:

            # Author names are usually short-ish text lines
            # and frequently appear toward the bottom.
            bottom_candidates = [
                item
                for item in cleaned_lines
                if len(item["text"].split()) <= 6
            ]

            if bottom_candidates:

                author_candidate = bottom_candidates[-1]["text"]

        # --------------------------------------------------------
        # TITLE DETECTION
        # --------------------------------------------------------

        # Prefer lines with larger OCR bounding boxes.
        # Book titles are often visually larger than other text.

        title_candidates = sorted(
            cleaned_lines,
            key=lambda item: (
                item["height"],
                item["confidence"]
            ),
            reverse=True
        )

        title_lines = []

        for item in title_candidates[:5]:

            text = item["text"]

            # Don't select obvious author line
            if (
                author_candidate
                and text.lower() == author_candidate.lower()
            ):
                continue

            # Ignore very long description lines
            if len(text) > 80:
                continue

            title_lines.append(item)

        if title_lines:

            # Take the strongest title candidate.
            best = title_lines[0]

            title_candidate = best["text"].strip()

        else:
            title_candidate = cleaned_lines[0]["text"].strip()

        # --------------------------------------------------------
        # CLEAN TITLE
        # --------------------------------------------------------

        title_candidate = re.sub(
            r"\s+",
            " ",
            title_candidate
        ).strip()

        author_candidate = re.sub(
            r"\s+",
            " ",
            author_candidate
        ).strip()

        # Avoid accidentally returning the same thing
        if (
            title_candidate.lower()
            == author_candidate.lower()
        ):
            author_candidate = ""

        return title_candidate, author_candidate

    # ============================================================
    # TEXT EXTRACTION
    # ============================================================

    def extract_text_from_image(
        self,
        image_path: str,
        max_chars: int = 800
    ) -> Dict:
        """Extract text from book cover or page image."""

        if not self.tesseract_available:

            return {
                "success": False,
                "extracted_text": "",
                "full_text": "",
                "source": "Fallback (No OCR Binary)",
                "message": (
                    "Tesseract OCR binary not detected "
                    "on host environment."
                )
            }

        try:

            image = Image.open(image_path)

            variants = self._create_ocr_variants(image)

            all_text = []

            for variant in variants:

                text = self._run_ocr(variant)

                if text:
                    all_text.append(text)

            combined = "\n".join(all_text)

            # Preserve lines first
            raw_lines = [
                line.strip()
                for line in combined.splitlines()
                if line.strip()
            ]

            # Remove duplicates while preserving order
            unique_lines = []

            seen = set()

            for line in raw_lines:

                normalized = re.sub(
                    r"\s+",
                    " ",
                    line
                ).strip()

                key = normalized.lower()

                if key not in seen:
                    seen.add(key)
                    unique_lines.append(normalized)

            full_text = "\n".join(unique_lines)

            cleaned_text = " ".join(unique_lines)

            return {
                "success": True,
                "extracted_text": cleaned_text[:max_chars],
                "full_text": full_text,
                "text_length": len(cleaned_text),
                "source": "Enhanced OCR",
                "ocr_variants": len(variants)
            }

        except Exception as e:

            return {
                "success": False,
                "extracted_text": "",
                "full_text": "",
                "message": f"OCR extraction error: {str(e)}"
            }

    # ============================================================
    # BOOK COVER ANALYSIS
    # ============================================================

    def analyze_book_cover(
        self,
        image_path: str
    ) -> Dict:
        """
        Extract:
        - OCR text
        - title
        - author
        - visual palette
        - aspect ratio
        - orientation
        """

        try:

            image = Image.open(image_path)

            width, height = image.size

            # ----------------------------------------------------
            # OCR
            # ----------------------------------------------------

            cleaned_text = ""
            title_candidate = ""
            author_candidate = ""

            ocr_lines = []

            if self.tesseract_available:

                try:

                    variants = self._create_ocr_variants(image)

                    # Use enhanced grayscale for structured OCR
                    structured_image = variants[0]

                    ocr_lines = self._extract_lines(
                        structured_image
                    )

                    # If structured OCR found nothing,
                    # use regular OCR fallback.
                    if ocr_lines:

                        title_candidate, author_candidate = (
                            self._identify_title_and_author(
                                ocr_lines,
                                ""
                            )
                        )

                    else:

                        raw_text = self._run_ocr(
                            structured_image
                        )

                        cleaned_text = " ".join(
                            raw_text.split()
                        )

                except Exception as e:

                    print(
                        f"INFO: Enhanced OCR failed: {e}"
                    )

            # Build readable OCR text
            if ocr_lines:

                cleaned_lines = [
                    item["text"]
                    for item in ocr_lines
                ]

                cleaned_text = "\n".join(
                    cleaned_lines
                )

            # ----------------------------------------------------
            # VISUAL COLOR ANALYSIS
            # ----------------------------------------------------

            image_rgb = image.convert("RGB")

            # Resize before pixel processing.
            # This makes color extraction much faster.
            sample_image = image_rgb.copy()
            sample_image.thumbnail((200, 200))

            pixels = list(
                sample_image.getdata()
            )

            if pixels:

                r_avg = sum(
                    p[0] for p in pixels
                ) / len(pixels)

                g_avg = sum(
                    p[1] for p in pixels
                ) / len(pixels)

                b_avg = sum(
                    p[2] for p in pixels
                ) / len(pixels)

                if (
                    r_avg > 130
                    and g_avg < 100
                    and b_avg < 100
                ):
                    dominant_color = "Warm Crimson Red"

                elif (
                    b_avg > 130
                    and r_avg < 110
                ):
                    dominant_color = "Deep Sapphire Blue"

                elif (
                    g_avg > 120
                    and r_avg < 110
                ):
                    dominant_color = "Emerald Forest Green"

                elif (
                    r_avg > 180
                    and g_avg > 180
                    and b_avg > 180
                ):
                    dominant_color = (
                        "Bright Light / Minimalist White"
                    )

                elif (
                    r_avg < 70
                    and g_avg < 70
                    and b_avg < 70
                ):
                    dominant_color = (
                        "Dark Gothic / Noir Shadow"
                    )

                elif (
                    r_avg > 140
                    and g_avg > 100
                    and b_avg < 90
                ):
                    dominant_color = (
                        "Golden Amber Vintage"
                    )

                else:
                    dominant_color = (
                        "Balanced Multi-tone"
                    )

            else:
                dominant_color = "Unknown"

            # ----------------------------------------------------
            # GEOMETRY
            # ----------------------------------------------------

            aspect_ratio = (
                round(width / height, 2)
                if height > 0
                else 0.7
            )

            orientation = (
                "Portrait (Standard Book Cover)"
                if height > width
                else "Landscape / Wide Layout"
            )

            # ----------------------------------------------------
            # FINAL RESULT
            # ----------------------------------------------------

            return {
                "success": True,
                "image_size": f"{width}x{height} px",
                "orientation": orientation,
                "aspect_ratio": aspect_ratio,

                "extracted_text": (
                    cleaned_text[:400]
                    if cleaned_text
                    else ""
                ),

                "title_candidate": title_candidate,
                "author_candidate": author_candidate,

                "dominant_color": dominant_color,

                "has_text": len(cleaned_text) > 5,

                "ocr_available": (
                    self.tesseract_available
                ),

                "ocr_method": (
                    "Enhanced Multi-Pass OCR"
                    if self.tesseract_available
                    else "Unavailable"
                )
            }

        except Exception as e:

            return {
                "success": False,
                "message": (
                    f"Cover analysis error: {str(e)}"
                )
            }

    # ============================================================
    # PUBLIC API
    # ============================================================

    def get_book_info_from_image(
        self,
        image_path: str
    ) -> Dict:
        """Get complete book information from image."""

        return self.analyze_book_cover(
            image_path
        )