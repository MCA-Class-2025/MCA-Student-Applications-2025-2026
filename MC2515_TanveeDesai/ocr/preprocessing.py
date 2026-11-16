"""
ocr/preprocessing.py — Image preprocessing for OCR.

Applies computer vision techniques to improve OCR accuracy on
medicine package images, labels, and prescription documents.

Fixes over the previous version:
- Adaptive thresholding + heavy denoising DESTROYED small text on many
  medicine packages (low-contrast, colored labels). Thresholding is now
  applied only when the image genuinely has low contrast.
- Added CLAHE contrast enhancement + sharpening, which are safer and
  consistently improve Tesseract results.
- Preprocessing failures fall back to the original image.
"""

from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image

from utils.logging import logger


def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
    """Convert PIL Image to OpenCV BGR array."""
    rgb = np.array(pil_image.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def cv2_to_pil(cv2_image: np.ndarray) -> Image.Image:
    """Convert OpenCV BGR array to PIL Image."""
    rgb = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def _image_contrast(gray: np.ndarray) -> float:
    """Standard deviation of pixel intensities — proxy for contrast."""
    return float(np.std(gray))


def _auto_orient(image: Image.Image) -> Image.Image:
    """Use EXIF orientation data so rotated phone photos OCR correctly."""
    try:
        exif = image.getexif()
        orientation = exif.get(274)  # 274 = Orientation tag
        if orientation == 3:
            return image.rotate(180, expand=True)
        if orientation == 6:
            return image.rotate(270, expand=True)
        if orientation == 8:
            return image.rotate(90, expand=True)
    except Exception:
        pass
    return image


def preprocess_for_ocr(
    image: Image.Image,
    denoise: bool = True,
    deskew: bool = True,
    threshold: Optional[bool] = None,
    scale_factor: float = 2.0,
) -> Image.Image:
    """
    Apply OCR-optimised preprocessing to an image.

    Steps:
    1. EXIF auto-orient (fix rotated phone photos)
    2. Upscale (improves OCR on small text)
    3. Convert to grayscale
    4. CLAHE contrast enhancement + sharpening
    5. Light denoising (optional)
    6. Adaptive thresholding ONLY if contrast is very low
    7. Deskew (straighten rotated text)

    If any step fails, the original image is returned (never a corrupted one).
    """
    try:
        # 0. EXIF orientation
        image = _auto_orient(image)

        # Convert to OpenCV
        img = pil_to_cv2(image)

        # 1. Upscale
        if scale_factor != 1.0:
            h, w = img.shape[:2]
            img = cv2.resize(
                img,
                (int(w * scale_factor), int(h * scale_factor)),
                interpolation=cv2.INTER_CUBIC,
            )

        # 2. Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 3. Contrast enhancement (CLAHE) — safe, big OCR win on washed-out labels
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        # 4. Sharpening (restores edge definition lost in upscaling)
        sharpen_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        gray = cv2.filter2D(gray, -1, sharpen_kernel)

        # 5. Light denoise
        if denoise:
            gray = cv2.fastNlMeansDenoising(gray, h=7, templateWindowSize=7, searchWindowSize=21)

        # 6. Adaptive threshold — ONLY for genuinely low-contrast images.
        #    Default: auto (None). High-contrast text must NOT be binarized.
        if threshold is None:
            threshold = _image_contrast(gray) < 35.0
        if threshold:
            gray = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 15, 8,
            )

        # 7. Deskew
        if deskew:
            gray = _deskew(gray)

        # Convert back to PIL
        result = Image.fromarray(gray)
        logger.debug(
            f"Image preprocessing complete (contrast={_image_contrast(gray):.1f}, "
            f"thresholded={threshold})"
        )
        return result

    except Exception as e:
        logger.warning(f"Image preprocessing error: {e}. Using original image.")
        return image


def _deskew(gray: np.ndarray) -> np.ndarray:
    """Attempt to deskew a grayscale image using Hough line detection."""
    try:
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)

        if lines is None or len(lines) == 0:
            return gray

        angles = []
        for line in lines[:20]:
            _, theta = line[0]
            angle = np.degrees(theta) - 90
            if -45 <= angle <= 45:
                angles.append(angle)

        if not angles:
            return gray

        median_angle = float(np.median(angles))
        if abs(median_angle) < 0.5:
            return gray

        h, w = gray.shape
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        return cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    except Exception:
        return gray


def resize_for_display(image: Image.Image, max_width: int = 600) -> Image.Image:
    """Resize image for display, maintaining aspect ratio."""
    w, h = image.size
    if w <= max_width:
        return image
    scale = max_width / w
    return image.resize((max_width, int(h * scale)), Image.LANCZOS)