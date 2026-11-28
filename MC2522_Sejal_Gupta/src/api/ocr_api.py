import os
import requests
import mimetypes
from dotenv import load_dotenv

load_dotenv()

OCR_API_KEY = os.getenv("OCR_SPACE_API_KEY")

OCR_URL = "https://api.ocr.space/parse/image"


def extract_text_from_image(uploaded_file):
    """
    Send an uploaded image to OCR.Space and return extracted text.
    Works with both Streamlit UploadedFile and normal Python files.
    """

    if not OCR_API_KEY:
        raise ValueError(
            "OCR_SPACE_API_KEY is missing. "
            "Please add it to your .env file."
        )

    try:
        # Move file pointer to beginning
        uploaded_file.seek(0)

        # Get filename if available
        filename = getattr(
            uploaded_file,
            "name",
            "image.png"
        )

        # Get MIME type if available
        mime_type = getattr(
            uploaded_file,
            "type",
            None
        )

        # If normal Python file, detect MIME type from filename
        if not mime_type:
            mime_type = mimetypes.guess_type(filename)[0]

        # Default to PNG
        if not mime_type:
            mime_type = "image/png"

        files = {
            "file": (
                filename,
                uploaded_file,
                mime_type
            )
        }

        data = {
            "language": "eng",
            "isOverlayRequired": "false",
            "OCREngine": "2"
        }

        headers = {
            "apikey": OCR_API_KEY
        }

        response = requests.post(
            OCR_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=60
        )

        response.raise_for_status()

        result = response.json()

        # Check OCR.Space processing errors
        if result.get("IsErroredOnProcessing"):
            error_message = result.get(
                "ErrorMessage",
                "OCR processing failed."
            )

            if isinstance(error_message, list):
                error_message = " ".join(error_message)

            raise RuntimeError(error_message)

        parsed_results = result.get(
            "ParsedResults",
            []
        )

        if not parsed_results:
            return ""

        extracted_text = "\n".join(
            item.get("ParsedText", "")
            for item in parsed_results
        ).strip()

        return extracted_text

    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"OCR API connection failed: {e}"
        )

    except Exception as e:
        raise RuntimeError(
            f"OCR processing failed: {e}"
        )