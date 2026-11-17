from fastapi import APIRouter, Depends

from app.core.auth_dependency import get_current_user

from app.services.notification_service import (
    NotificationService,
)


router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"],
)


# ============================================================
# GET NOTIFICATIONS
# ============================================================

@router.get("/")
async def get_notifications(
    current_user=Depends(
        get_current_user
    )
):

    user_id = current_user["user_id"]

    return await NotificationService.get_notifications(
        user_id
    )