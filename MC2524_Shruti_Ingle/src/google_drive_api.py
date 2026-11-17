
import os
import io
import shutil
from datetime import datetime

import pandas as pd

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from langchain.schema import Document


# ============================================================
# CONFIGURATION
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly"
]

DATASET_DIR = "datasets"
DATASET_PATH = os.path.join(
    DATASET_DIR,
    "google_drive_dataset.csv"
)

# Keep the original CSV column names and order.
DATASET_COLUMNS = [
    "mimeType",
    "id",
    "name",
    "modifiedTime"
]


# ============================================================
# GOOGLE DRIVE AUTHENTICATION
# ============================================================

def authenticate_drive():
    """Authenticate with Google Drive using OAuth."""

    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )

    if not creds or not creds.valid:

        if (
            creds
            and creds.expired
            and creds.refresh_token
        ):
            creds.refresh(Request())

        else:
            if not os.path.exists("credentials.json"):
                raise FileNotFoundError(
                    "credentials.json was not found. "
                    "Run this script from the project root."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )

            creds = flow.run_local_server(
                host="127.0.0.1",
                port=54701,
                open_browser=True,
                authorization_prompt_message=(
                    "Opening browser for Google login..."
                ),
                success_message=(
                    "Authentication complete. "
                    "You may close this window."
                )
            )

        with open("token.json", "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    service = build(
        "drive",
        "v3",
        credentials=creds
    )

    return service


# ============================================================
# BACKUP EXISTING DATASET
# ============================================================

def backup_existing_dataset():
    """Back up the existing CSV before replacing it."""

    if not os.path.exists(DATASET_PATH):
        print("No previous Google Drive CSV found.")
        return None

    backup_dir = os.path.join(
        DATASET_DIR,
        "backups"
    )

    os.makedirs(
        backup_dir,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = os.path.join(
        backup_dir,
        f"google_drive_dataset_{timestamp}.csv"
    )

    shutil.copy2(
        DATASET_PATH,
        backup_path
    )

    print(f"Backup created: {backup_path}")

    return backup_path


# ============================================================
# EXPORT ALL GOOGLE DRIVE FILE METADATA
# ============================================================

def export_google_drive_dataset():
    """
    Fetch Google Drive metadata using pagination.

    The API can return multiple pages of files.
    This function continues until nextPageToken is absent.
    """

    service = authenticate_drive()

    all_files = []
    page_token = None
    page_number = 0

    print("\nFetching Google Drive file metadata...")

    while True:

        request_args = {
            "pageSize": 1000,
            "q": "trashed = false",
            "orderBy": "name",
            "fields": (
                "nextPageToken,"
                "files(id,name,mimeType,modifiedTime)"
            )
        }

        if page_token:
            request_args["pageToken"] = page_token

        results = service.files().list(
            **request_args
        ).execute()

        page_files = results.get(
            "files",
            []
        )

        page_number += 1

        all_files.extend(page_files)

        print(
            f"Page {page_number}: "
            f"{len(page_files)} files fetched; "
            f"total so far: {len(all_files)}"
        )

        page_token = results.get(
            "nextPageToken"
        )

        if not page_token:
            break

    # Remove duplicate file IDs, if any.
    unique_files = []
    seen_ids = set()

    for file_info in all_files:

        file_id = file_info.get("id")

        if not file_id or file_id in seen_ids:
            continue

        seen_ids.add(file_id)
        unique_files.append(file_info)

    os.makedirs(
        DATASET_DIR,
        exist_ok=True
    )

    # Preserve the previous dataset before replacing it.
    backup_existing_dataset()

    df = pd.DataFrame(
        unique_files,
        columns=DATASET_COLUMNS
    )

    df.to_csv(
        DATASET_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    print("\nGoogle Drive metadata export completed.")
    print(f"Total unique files: {len(df)}")
    print(f"CSV saved to: {DATASET_PATH}")

    return unique_files


# ============================================================
# DOWNLOAD OR EXPORT A DRIVE FILE
# ============================================================

def download_drive_file(service, file_id, mime_type):
    """Download a file or export a Google Workspace file."""

    if mime_type == "application/vnd.google-apps.document":

        request = service.files().export_media(
            fileId=file_id,
            mimeType="text/plain"
        )

    elif mime_type == "application/vnd.google-apps.spreadsheet":

        request = service.files().export_media(
            fileId=file_id,
            mimeType="text/csv"
        )

    elif mime_type == "application/vnd.google-apps.presentation":

        request = service.files().export_media(
            fileId=file_id,
            mimeType="text/plain"
        )

    elif mime_type.startswith(
        "application/vnd.google-apps."
    ):
        # Skip unsupported Google Workspace file types.
        return None

    else:
        request = service.files().get_media(
            fileId=file_id
        )

    file_buffer = io.BytesIO()

    downloader = MediaIoBaseDownload(
        file_buffer,
        request
    )

    done = False

    while not done:
        _, done = downloader.next_chunk()

    file_buffer.seek(0)

    return file_buffer.read()


# ============================================================
# CREATE A DOCUMENT FROM A SPREADSHEET ROW
# ============================================================

def create_row_document(
    row,
    columns,
    file_name,
    file_id,
    mime_type,
    row_number
):
    """Convert one spreadsheet row into a LangChain Document."""

    parts = []

    for column in columns:

        value = row.get(
            column,
            ""
        )

        if pd.isna(value):
            continue

        value = str(value).strip()

        if value:
            parts.append(
                f"{column}: {value}"
            )

    text = "\n".join(parts)

    text = (
        f"Spreadsheet: {file_name}\n"
        f"Row: {row_number}\n"
        f"{text}"
    )

    return Document(
        page_content=text,
        metadata={
            "source": "Google Drive",
            "source_file": file_name,
            "drive_file_id": file_id,
            "mime_type": mime_type,
            "row_number": row_number,
            "document_type": "spreadsheet_row"
        }
    )


# ============================================================
# LOAD AND EXTRACT GOOGLE DRIVE DOCUMENTS
# ============================================================

def load_google_drive_documents(limit=None):
    """
    Extract actual text from supported Google Drive files.

    limit=None processes all files listed in the metadata CSV.
    A numeric limit processes only the first N files.
    """

    if not os.path.exists(DATASET_PATH):
        print(
            "Google Drive metadata CSV not found. "
            "Export the dataset first."
        )
        return []

    df = pd.read_csv(DATASET_PATH)

    if df.empty:
        print("Google Drive metadata CSV is empty.")
        return []

    if limit is not None:
        if limit < 0:
            raise ValueError("limit cannot be negative.")

        df = df.head(limit)

    service = authenticate_drive()
    documents = []

    print(f"\nFiles selected for extraction: {len(df)}")

    for _, row in df.iterrows():

        file_id = str(
            row.get("id", "")
        ).strip()

        file_name = str(
            row.get("name", "Unknown")
        ).strip()

        mime_type = str(
            row.get("mimeType", "")
        ).strip()

        if not file_id or file_id.lower() == "nan":
            print(f"Skipping file without an ID: {file_name}")
            continue

        if not mime_type or mime_type.lower() == "nan":
            print(f"Skipping file without a MIME type: {file_name}")
            continue

        print(f"\nProcessing: {file_name}")
        print(f"Type: {mime_type}")

        try:
            content = download_drive_file(
                service,
                file_id,
                mime_type
            )

            if content is None:
                print(f"Unsupported file type: {file_name}")
                continue

            # ------------------------------------------------
            # GOOGLE SHEETS
            # ------------------------------------------------

            if mime_type == (
                "application/vnd.google-apps.spreadsheet"
            ):

                csv_text = content.decode(
                    "utf-8-sig",
                    errors="replace"
                )

                sheet_df = pd.read_csv(
                    io.StringIO(csv_text)
                )

                sheet_df = sheet_df.dropna(
                    how="all"
                )

                columns = list(sheet_df.columns)

                for index, data_row in sheet_df.iterrows():

                    document = create_row_document(
                        data_row,
                        columns,
                        file_name,
                        file_id,
                        mime_type,
                        index + 1
                    )

                    documents.append(document)

                summary_document = Document(
                    page_content=(
                        f"Google Drive spreadsheet: {file_name}\n"
                        f"Total data rows: {len(sheet_df)}\n"
                        f"Columns: {', '.join(columns)}"
                    ),
                    metadata={
                        "source": "Google Drive",
                        "source_file": file_name,
                        "drive_file_id": file_id,
                        "mime_type": mime_type,
                        "document_type": "spreadsheet_summary",
                        "total_rows": len(sheet_df)
                    }
                )

                documents.append(summary_document)

                print(
                    f"Extracted {len(sheet_df)} spreadsheet rows."
                )

            # ------------------------------------------------
            # TEXT, MARKDOWN, CSV AND JSON
            # ------------------------------------------------

            elif (
                mime_type.startswith("text/")
                or file_name.lower().endswith(
                    (".txt", ".md", ".csv", ".json")
                )
            ):

                text = content.decode(
                    "utf-8-sig",
                    errors="replace"
                )

                if text.strip():
                    documents.append(
                        Document(
                            page_content=text,
                            metadata={
                                "source": "Google Drive",
                                "source_file": file_name,
                                "drive_file_id": file_id,
                                "mime_type": mime_type,
                                "document_type": "text"
                            }
                        )
                    )

                    print("Text extracted successfully.")

            # ------------------------------------------------
            # PDF
            # ------------------------------------------------

            elif (
                mime_type == "application/pdf"
                or file_name.lower().endswith(".pdf")
            ):

                from pypdf import PdfReader

                reader = PdfReader(
                    io.BytesIO(content)
                )

                extracted_pages = 0

                for page_number, page in enumerate(
                    reader.pages,
                    start=1
                ):

                    text = page.extract_text() or ""

                    if text.strip():
                        documents.append(
                            Document(
                                page_content=text,
                                metadata={
                                    "source": "Google Drive",
                                    "source_file": file_name,
                                    "drive_file_id": file_id,
                                    "mime_type": mime_type,
                                    "page": page_number,
                                    "document_type": "pdf"
                                }
                            )
                        )

                        extracted_pages += 1

                print(
                    f"Extracted text from "
                    f"{extracted_pages} PDF pages."
                )

            # ------------------------------------------------
            # WORD DOCX
            # ------------------------------------------------

            elif (
                mime_type == (
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                )
                or file_name.lower().endswith(".docx")
            ):

                from docx import Document as DocxDocument

                word_doc = DocxDocument(
                    io.BytesIO(content)
                )

                paragraphs = [
                    paragraph.text
                    for paragraph in word_doc.paragraphs
                    if paragraph.text.strip()
                ]

                text = "\n".join(paragraphs)

                if text.strip():
                    documents.append(
                        Document(
                            page_content=text,
                            metadata={
                                "source": "Google Drive",
                                "source_file": file_name,
                                "drive_file_id": file_id,
                                "mime_type": mime_type,
                                "document_type": "docx"
                            }
                        )
                    )

                    print("DOCX text extracted successfully.")

            # ------------------------------------------------
            # UNSUPPORTED FILE
            # ------------------------------------------------

            else:
                print(
                    f"Skipped unsupported file: {file_name}"
                )

        except Exception as exc:
            # Continue with the next file if one file fails.
            print(
                f"Could not process {file_name}: {exc}"
            )

    print(
        f"\nTotal extracted document chunks: {len(documents)}"
    )

    return documents


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    print("\n=== GOOGLE DRIVE DATASET EXPORT ===")

    try:
        files = export_google_drive_dataset()

        print(f"\nUnique Drive files: {len(files)}")

        print("\n=== TESTING ONE FILE ===")

        documents = load_google_drive_documents(
            limit=1
        )

        print(
            f"\nDocuments extracted from test: "
            f"{len(documents)}"
        )

        if documents:
            print("\n=== SAMPLE EXTRACTED CONTENT ===\n")

            for document in documents[:5]:
                print(document.page_content)
                print("\n" + "-" * 50 + "\n")

    except Exception as exc:
        print(f"\nGoogle Drive operation failed: {exc}")
        print(
            "Check authentication, API permissions, "
            "and the error message above."
        )
