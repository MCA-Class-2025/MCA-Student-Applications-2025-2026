"""Loading the Excel dataset and validating that the required columns exist."""

from pathlib import Path
from typing import Tuple, Union

import pandas as pd

DEFAULT_SHEET = "StoryVerse Dataset"

REQUIRED_COLUMNS = [
    "Story ID", "Timestamp", "Mode", "Title", "Language", "Source / Prompt",
    "City", "Weather Condition", "Temperature (C)", "Story Text",
    "Detected Emotion", "Emotion Confidence", "Audio File Path",
    "Background Music Added", "Video Created", "Video File Path",
]


class DatasetError(Exception):
    """Raised with a friendly message when the dataset cannot be used."""


def validate_columns(df: pd.DataFrame) -> list:
    """Return the list of required columns that are missing from df."""
    return [c for c in REQUIRED_COLUMNS if c not in df.columns]


def load_excel(source: Union[str, Path, object]) -> Tuple[pd.DataFrame, str]:
    """Load the dataset from a file path or an uploaded file object.

    Returns (dataframe, sheet_name_used). Raises DatasetError with a
    beginner-friendly message if anything is wrong.
    """
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise DatasetError(
                f"Dataset file not found: '{path}'. Place storyverse_dataset.xlsx "
                "inside the 'data' folder or upload it from the sidebar."
            )
    try:
        workbook = pd.ExcelFile(source, engine="openpyxl")
    except Exception as exc:  # corrupt file, wrong format, etc.
        raise DatasetError(f"The file could not be read as an Excel workbook: {exc}") from exc

    # Prefer the documented sheet name; otherwise fall back to the first sheet.
    sheet = DEFAULT_SHEET if DEFAULT_SHEET in workbook.sheet_names else workbook.sheet_names[0]
    df = workbook.parse(sheet_name=sheet)

    if df.empty:
        raise DatasetError(f"Sheet '{sheet}' contains no rows.")

    missing = validate_columns(df)
    if missing:
        raise DatasetError(
            "The dataset is missing required column(s): " + ", ".join(missing)
        )
    return df, sheet
