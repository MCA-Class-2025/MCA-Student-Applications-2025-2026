from datetime import datetime, timezone

from pydantic import BaseModel, Field


class NotificationModel(BaseModel):

    user_id: str

    title: str

    message: str

    notification_type: str = "general"

    is_read: bool = False

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )