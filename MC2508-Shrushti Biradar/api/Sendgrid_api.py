import os
import base64
from pathlib import Path
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

last_error = ""


def get_last_error():
    return last_error


def send_email(to_email, subject, content):
    global last_error
    last_error = ""

    try:
        creds = None

        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(
                str(TOKEN_FILE), SCOPES
            )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CREDENTIALS_FILE), SCOPES
                )
                creds = flow.run_local_server(port=0)

            TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

        service = build("gmail", "v1", credentials=creds)

        message = MIMEText(content)
        message["to"] = to_email.strip()
        message["subject"] = subject

        encoded_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode("utf-8")

        body = {"raw": encoded_message}

        service.users().messages().send(
            userId="me",
            body=body
        ).execute()

        print("[Email] Successfully sent to:", to_email)
        return True

    except Exception as e:
        last_error = f"{type(e).__name__}: {e}"
        print("[Email] ERROR:", last_error)
        return False