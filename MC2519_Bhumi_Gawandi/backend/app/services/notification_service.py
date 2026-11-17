from datetime import datetime, timezone

from app.database.mongodb import database
from app.models.notification_model import NotificationModel


class NotificationService:

    # ============================================================
    # CREATE NOTIFICATION
    # ============================================================

    @staticmethod
    async def create_notification(
        user_id: str,
        title: str,
        message: str,
        notification_type: str = "general",
    ):

        notification = NotificationModel(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )

        result = await database.notifications.insert_one(
            notification.model_dump()
        )

        return {
            "success": True,
            "notification_id": str(
                result.inserted_id
            ),
        }

    # ============================================================
    # GET USER NOTIFICATIONS
    # ============================================================

    @staticmethod
    async def get_notifications(
        user_id: str
    ):

        notifications = await database.notifications.find(
            {
                "user_id": user_id
            }
        ).sort(
            "created_at",
            -1
        ).to_list(
            length=None
        )

        for notification in notifications:

            notification["_id"] = str(
                notification["_id"]
            )

        return notifications

    # ============================================================
    # MARK AS READ
    # ============================================================

    @staticmethod
    async def mark_as_read(
        notification_id: str,
        user_id: str
    ):

        from bson import ObjectId
        from bson.errors import InvalidId

        try:

            object_id = ObjectId(
                notification_id
            )

        except (InvalidId, TypeError):

            return {
                "success": False,
                "message": "Invalid notification ID.",
            }

        result = await database.notifications.update_one(
            {
                "_id": object_id,
                "user_id": user_id,
            },
            {
                "$set": {
                    "is_read": True
                }
            }
        )

        if result.modified_count == 0:

            return {
                "success": False,
                "message": "Notification not found.",
            }

        return {
            "success": True,
            "message": "Notification marked as read.",
        }