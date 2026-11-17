from fastapi_mail import (
    FastMail,
    MessageSchema,
    MessageType,
)

from app.core.email_config import mail_config


# ============================================================
# SEND NORMAL EMAIL
# ============================================================

async def send_email(
    recipient: str,
    subject: str,
    body: str
):

    message = MessageSchema(
        subject=subject,
        recipients=[recipient],
        body=body,
        subtype=MessageType.html,
    )

    fast_mail = FastMail(
        mail_config
    )

    await fast_mail.send_message(
        message
    )

    return {
        "success": True,
        "message": "Email sent successfully."
    }


# ============================================================
# TEST EMAIL
# ============================================================

async def send_test_email(
    recipient: str
):

    body = """
    <html>

        <body style="
            font-family: Arial, sans-serif;
            background-color: #f5f7f6;
            padding: 30px;
        ">

            <div style="
                max-width: 600px;
                margin: auto;
                background: white;
                padding: 30px;
                border-radius: 15px;
            ">

                <h2 style="
                    color: #1F6F5C;
                ">
                    SpendSmart.ai
                </h2>

                <h3>
                    Email Configuration Test
                </h3>

                <p>
                    Hello!
                </p>

                <p>
                    This is a test email from your
                    AI Smart Expense Tracker.
                </p>

                <p>
                    If you received this email,
                    your Gmail SMTP configuration
                    is working correctly.
                </p>

                <hr>

                <p style="
                    color: #777;
                ">
                    SpendSmart.ai
                </p>

            </div>

        </body>

    </html>
    """

    return await send_email(
        recipient=recipient,
        subject="SpendSmart Email Test",
        body=body
    )


# ============================================================
# BUDGET EXCEEDED EMAIL
# ============================================================

async def send_budget_exceeded_email(
    email: str,
    category: str,
    budget: float,
    spent: float
):

    exceeded_amount = (
        spent - budget
    )

    body = f"""
    <html>

        <body style="
            font-family: Arial, sans-serif;
            background-color: #f5f7f6;
            padding: 30px;
        ">

            <div style="
                max-width: 600px;
                margin: auto;
                background: white;
                padding: 30px;
                border-radius: 15px;
            ">

                <h2 style="
                    color: #1F6F5C;
                ">
                    SpendSmart.ai
                </h2>

                <h3 style="
                    color: #dc2626;
                ">
                    Budget Limit Exceeded
                </h3>

                <p>
                    Your
                    <strong>{category}</strong>
                    budget has been exceeded.
                </p>

                <div style="
                    background-color: #fff2f2;
                    padding: 20px;
                    border-radius: 10px;
                    margin: 20px 0;
                ">

                    <p>
                        <strong>Category:</strong>
                        {category}
                    </p>

                    <p>
                        <strong>Budget:</strong>
                        ₹{budget:,.2f}
                    </p>

                    <p>
                        <strong>Total Spent:</strong>
                        ₹{spent:,.2f}
                    </p>

                    <p style="
                        color: #dc2626;
                    ">
                        <strong>
                            Exceeded By:
                        </strong>

                        ₹{exceeded_amount:,.2f}
                    </p>

                </div>

                <p>
                    You have crossed your planned
                    budget for this category.
                </p>

                <p>
                    Try to reduce your spending
                    in <strong>{category}</strong>
                    to stay within your budget.
                </p>

                <hr>

                <p style="
                    color: #777;
                ">
                    This is an automatic notification
                    from SpendSmart.ai.
                </p>

            </div>

        </body>

    </html>
    """

    return await send_email(
        recipient=email,
        subject=f"{category} Budget Exceeded",
        body=body
    )


# ============================================================
# BUDGET UPGRADE OTP EMAIL
# ============================================================

async def send_budget_upgrade_otp_email(
    email: str,
    category: str,
    new_amount: float,
    otp: str
):

    body = f"""
    <html>

        <body style="
            font-family: Arial, sans-serif;
            background-color: #f5f7f6;
            padding: 30px;
        ">

            <div style="
                max-width: 600px;
                margin: auto;
                background: white;
                padding: 35px;
                border-radius: 15px;
            ">

                <h2 style="
                    color: #1F6F5C;
                    margin-bottom: 20px;
                ">
                    SpendSmart.ai
                </h2>

                <h3>
                    Budget Increase Verification
                </h3>

                <p>
                    Someone requested to increase
                    your budget for:
                </p>

                <p>
                    <strong>
                        Category:
                    </strong>

                    {category}
                </p>

                <p>
                    <strong>
                        New Budget:
                    </strong>

                    ₹{new_amount:,.2f}
                </p>

                <div style="
                    background-color: #EAF5F1;
                    padding: 25px;
                    border-radius: 12px;
                    text-align: center;
                    margin: 25px 0;
                ">

                    <p style="
                        margin: 0;
                        color: #64748B;
                    ">
                        Your verification code is
                    </p>

                    <h1 style="
                        letter-spacing: 8px;
                        color: #1F6F5C;
                        margin: 15px 0;
                    ">
                        {otp}
                    </h1>

                    <p style="
                        margin: 0;
                        color: #64748B;
                    ">
                        This OTP is valid for
                        5 minutes.
                    </p>

                </div>

                <p>
                    If you requested this budget
                    increase, enter this OTP in
                    SpendSmart.ai.
                </p>

                <p>
                    If you did not request this
                    change, you can safely ignore
                    this email.
                </p>

                <hr>

                <p style="
                    color: #777;
                ">
                    SpendSmart.ai
                </p>

            </div>

        </body>

    </html>
    """

    return await send_email(
        recipient=email,
        subject="SpendSmart Budget Increase Verification",
        body=body
    )