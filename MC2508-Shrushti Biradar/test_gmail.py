import os
import ssl
import smtplib
from pathlib import Path
from dotenv import load_dotenv

from email.message import EmailMessage

load_dotenv(Path(__file__).resolve().parent / ".env")

gmail = os.getenv("GMAIL_ADDRESS", "").strip()
password = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "").strip()
print("Gmail loaded:", bool(gmail))
print("App Password length:", len(password))
try:
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465,
        context=context,
        timeout=30
    ) as server:

        print("SSL connection successful!")
        print("Trying Gmail login...")

        server.login(gmail, password)
        print("Gmail login successful!")
        

        msg = EmailMessage()
        msg["From"] = gmail
        msg["To"] = gmail
        msg["Subject"] = "AI Event Planner Test"
        msg.set_content("Gmail email test successful!")

        server.send_message(msg)
        print("Test email sent successfully!")

except Exception as e:
    print("ERROR:", type(e).__name__, str(e))