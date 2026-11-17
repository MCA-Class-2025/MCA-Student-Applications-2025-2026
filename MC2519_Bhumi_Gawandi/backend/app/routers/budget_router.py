from fastapi import APIRouter, Depends

from app.core.auth_dependency import get_current_user

from app.schemas.budget_schema import (
    BudgetCreate,
    BudgetUpdate,
    BudgetUpgradeRequest,
    BudgetUpgradeVerify,
)

from app.services.budget_service import BudgetService
from app.services.otp_service import OTPService

from app.services.email_service import (
    send_budget_upgrade_otp_email,
)


router = APIRouter(
    prefix="/api/budgets",
    tags=["Budgets"],
)


# ============================================================
# CREATE BUDGET
# ============================================================

@router.post("/")
async def create_budget(
    budget: BudgetCreate,
    current_user=Depends(
        get_current_user
    ),
):

    user_id = current_user["user_id"]

    return await BudgetService.create_budget(
        user_id,
        budget,
    )


# ============================================================
# GET ALL BUDGETS
# ============================================================

@router.get("/")
async def get_all_budgets(
    current_user=Depends(
        get_current_user
    ),
):

    user_id = current_user["user_id"]

    return await BudgetService.get_all_budgets(
        user_id,
    )


# ============================================================
# REQUEST BUDGET UPGRADE
# ============================================================

@router.post(
    "/{budget_id}/upgrade/request"
)
async def request_budget_upgrade(
    budget_id: str,
    request: BudgetUpgradeRequest,
    current_user=Depends(
        get_current_user
    ),
):

    user_id = current_user["user_id"]

    # IMPORTANT:
    # Email comes from the logged-in user's JWT.
    # User does NOT enter an email.
    email = current_user["email"]

    # Check budget
    result = await BudgetService.request_budget_upgrade(
        budget_id=budget_id,
        new_amount=request.new_amount,
        user_id=user_id,
    )

    if not result["success"]:

        return result

    # Generate OTP
    otp = OTPService.generate_otp()

    # Save OTP
    await OTPService.save_otp(
        user_id=user_id,
        budget_id=budget_id,
        otp=otp,
        new_amount=request.new_amount,
    )

    # Send OTP to logged-in email
    await send_budget_upgrade_otp_email(
        email=email,
        category=result["category"],
        new_amount=request.new_amount,
        otp=otp,
    )

    return {
        "success": True,
        "message": (
            "OTP has been sent to your "
            "registered email address."
        ),
    }


# ============================================================
# VERIFY BUDGET UPGRADE OTP
# ============================================================

@router.post(
    "/{budget_id}/upgrade/verify"
)
async def verify_budget_upgrade(
    budget_id: str,
    request: BudgetUpgradeVerify,
    current_user=Depends(
        get_current_user
    ),
):

    user_id = current_user["user_id"]

    # Verify OTP
    new_amount = await OTPService.verify_otp(
        user_id=user_id,
        budget_id=budget_id,
        otp=request.otp,
    )

    if new_amount is None:

        return {
            "success": False,
            "message": (
                "Invalid or expired OTP."
            ),
        }

    # Update budget only after OTP verification
    result = await BudgetService.complete_budget_upgrade(
        budget_id=budget_id,
        user_id=user_id,
        new_amount=new_amount,
    )

    return result


# ============================================================
# GET SINGLE BUDGET
# ============================================================

@router.get(
    "/{budget_id}"
)
async def get_budget(
    budget_id: str,
    current_user=Depends(
        get_current_user
    ),
):

    user_id = current_user["user_id"]

    return await BudgetService.get_budget_by_id(
        budget_id,
        user_id,
    )


# ============================================================
# UPDATE BUDGET
# ============================================================

@router.put(
    "/{budget_id}"
)
async def update_budget(
    budget_id: str,
    budget: BudgetUpdate,
    current_user=Depends(
        get_current_user
    ),
):

    user_id = current_user["user_id"]

    return await BudgetService.update_budget(
        budget_id,
        budget,
        user_id,
    )


# ============================================================
# DELETE BUDGET
# ============================================================

@router.delete(
    "/{budget_id}"
)
async def delete_budget(
    budget_id: str,
    current_user=Depends(
        get_current_user
    ),
):

    user_id = current_user["user_id"]

    return await BudgetService.delete_budget(
        budget_id,
        user_id,
    )