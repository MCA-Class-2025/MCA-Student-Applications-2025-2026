import os
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv()

api_key = os.getenv("SENDGRID_API_KEY")
sender = os.getenv("SENDER_EMAIL")

print("API key found?", bool(api_key))
print("Sender email found?", bool(sender))

if api_key and sender:
    to_email = input("Type the email to send a test to: ").strip()

    message = Mail(
        from_email=sender,
        to_emails=to_email,
        subject="Test from AI Event Planner",
        plain_text_content="Hello! This is a test."
    )

    try:
        response = SendGridAPIClient(api_key).send(message)
        print("STATUS CODE:", response.status_code)
    except Exception as e:
        print("ERROR:", e)
        print("DETAILS:", getattr(e, "body", ""))
else:
    print("Cannot test, the key or the sender is missing.")