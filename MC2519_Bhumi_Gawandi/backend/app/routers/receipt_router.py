from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
)

from app.core.auth_dependency import (
    get_current_user,
)

from app.services.receipt_service import (
    ReceiptService,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/receipts",
    tags=["Receipt Scanner"],
)


# ============================================================
# SCAN RECEIPT
# ============================================================

@router.post("/scan")
async def scan_receipt(
    file: UploadFile = File(...),
    current_user=Depends(
        get_current_user
    ),
):

    # --------------------------------------------------------
    # GET LOGGED-IN USER
    # --------------------------------------------------------

    user_id = current_user.get(
        "user_id"
    )


    # --------------------------------------------------------
    # SCAN RECEIPT
    # --------------------------------------------------------

    return await ReceiptService.scan_receipt(
        file=file,
        user_id=user_id,
    )