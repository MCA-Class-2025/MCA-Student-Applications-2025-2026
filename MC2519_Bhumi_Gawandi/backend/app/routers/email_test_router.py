from fastapi import APIRouter, Depends

from app.core.auth_dependency import get_current_user

from app.services.email_service import (
    send_test_email,
    send_budget_exceeded_email,
)


router = APIRouter(
    prefix="/api/email-test",
    tags=["Email Test"],
)


# ============================================================
# TEST NORMAL EMAIL
# ============================================================

@router.post("/")
async def test_email(
    current_user=Depends(get_current_user)
):

    email = current_user["email"]

    result = await send_test_email(
        recipient=email
    )

    return {
        "success": True,
        "message": f"Test email sent to {email}",
        "email_result": result,
    }


# ============================================================
# TEST BUDGET EXCEEDED EMAIL
# ============================================================

@router.post("/budget-exceeded")
async def test_budget_exceeded_email(
    current_user=Depends(get_current_user)
):

    email = current_user["email"]

    result = await send_budget_exceeded_email(
        email=email,
        category="Food",
        budget=500,
        spent=650,
    )

    return {
        "success": True,
        "message": f"Budget exceeded email sent to {email}",
        "email_result": result,
    }