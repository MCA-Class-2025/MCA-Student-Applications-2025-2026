from fastapi import APIRouter, HTTPException

from app.services.email_service import EmailService
from app.config.settings import settings


router = APIRouter(
    prefix="/api/email",
    tags=["Email"]
)


@router.post("/test")
async def test_email():

    if not settings.MAIL_USERNAME:
        raise HTTPException(
            status_code=500,
            detail="MAIL_USERNAME is not configured."
        )

    try:

        result = await EmailService.send_email(
            recipient=settings.MAIL_USERNAME,
            subject="SpendSmart.ai Email Test",
            body="""
            <html>
                <body style="font-family: Arial;">

                    <h2 style="color:#1F6F5C;">
                        SpendSmart.ai
                    </h2>

                    <p>
                        Email service is working successfully.
                    </p>

                    <p>
                        This is a test email from your
                        AI Smart Expense Tracker.
                    </p>

                </body>
            </html>
            """
        )

        return result

    except Exception as error:

        print("EMAIL ERROR:", error)

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )