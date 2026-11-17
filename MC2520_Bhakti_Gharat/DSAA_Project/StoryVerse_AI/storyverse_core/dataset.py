"""
Excel dataset logging: one growing .xlsx with one row per story.
"""

from datetime import datetime
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

from .config import DATA_FOLDER

EXCEL_DATASET_FILE = DATA_FOLDER / "storyverse_dataset.xlsx"

EXCEL_COLUMNS = [
    "Story ID", "Timestamp", "Mode", "Title", "Language",
    "Source / Prompt", "City", "Weather Condition", "Temperature (C)",
    "Story Text", "Detected Emotion", "Emotion Confidence",
    "Audio File Path", "Background Music Added", "Video Created",
    "Video File Path",
]


def log_story_to_excel(record: dict) -> bool:

    story_id = record.get("Story ID")

    if not story_id:
        return False

    DATA_FOLDER.mkdir(parents=True, exist_ok=True)

    if EXCEL_DATASET_FILE.exists():
        workbook = load_workbook(EXCEL_DATASET_FILE)
        sheet = workbook.active
    else:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "StoryVerse Dataset"
        sheet.append(EXCEL_COLUMNS)
        for header_cell in sheet[1]:
            header_cell.font = Font(bold=True)

    target_row = None
    for row_index in range(2, sheet.max_row + 1):
        if sheet.cell(row=row_index, column=1).value == story_id:
            target_row = row_index
            break

    if target_row is None:
        record.setdefault("Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        sheet.append([record.get(column, "") for column in EXCEL_COLUMNS])
    else:
        for col_index, column in enumerate(EXCEL_COLUMNS, start=1):
            if column in record:
                sheet.cell(row=target_row, column=col_index, value=record[column])

    workbook.save(EXCEL_DATASET_FILE)
    return True
