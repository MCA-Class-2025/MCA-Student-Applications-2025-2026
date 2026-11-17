from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId

from app.database.mongodb import database


class ChatHistoryService:

    # ============================================================
    # CREATE CONVERSATION
    # ============================================================

    @staticmethod
    async def create_conversation(
        user_id: str,
        title: str = "New Conversation"
    ):

        now = datetime.now(
            timezone.utc
        )

        conversation = {

            "user_id": user_id,

            "title": title,

            "messages": [],

            "created_at": now,

            "updated_at": now

        }

        result = await database.chat_conversations.insert_one(
            conversation
        )

        return {

            "success": True,

            "conversation_id":
                str(result.inserted_id),

            "title":
                title

        }


    # ============================================================
    # GET ALL CONVERSATIONS
    # ============================================================

    @staticmethod
    async def get_conversations(
        user_id: str
    ):

        conversations = await database.chat_conversations.find(
            {
                "user_id": user_id
            }
        ).sort(
            "updated_at",
            -1
        ).to_list(
            length=None
        )

        result = []

        for conversation in conversations:

            result.append({

                "conversation_id":
                    str(
                        conversation["_id"]
                    ),

                "title":
                    conversation.get(
                        "title",
                        "New Conversation"
                    ),

                "message_count":
                    len(
                        conversation.get(
                            "messages",
                            []
                        )
                    ),

                "created_at":
                    conversation.get(
                        "created_at"
                    ),

                "updated_at":
                    conversation.get(
                        "updated_at"
                    )

            })

        return result


    # ============================================================
    # GET SINGLE CONVERSATION
    # ============================================================

    @staticmethod
    async def get_conversation(
        user_id: str,
        conversation_id: str
    ):

        try:

            object_id = ObjectId(
                conversation_id
            )

        except (
            InvalidId,
            TypeError
        ):

            return {

                "success": False,

                "message":
                    "Invalid conversation ID."

            }


        conversation = await database.chat_conversations.find_one(
            {
                "_id": object_id,

                "user_id": user_id
            }
        )


        if conversation is None:

            return {

                "success": False,

                "message":
                    "Conversation not found."

            }


        conversation["conversation_id"] = str(
            conversation.pop("_id")
        )


        return conversation


    # ============================================================
    # ADD MESSAGE
    # ============================================================

    @staticmethod
    async def add_message(
        user_id: str,
        conversation_id: str,
        role: str,
        content: str
    ):

        try:

            object_id = ObjectId(
                conversation_id
            )

        except (
            InvalidId,
            TypeError
        ):

            return {

                "success": False,

                "message":
                    "Invalid conversation ID."

            }


        now = datetime.now(
            timezone.utc
        )


        result = await database.chat_conversations.update_one(

            {
                "_id": object_id,

                "user_id": user_id
            },

            {

                "$push": {

                    "messages": {

                        "role": role,

                        "content": content,

                        "created_at": now

                    }

                },

                "$set": {

                    "updated_at": now

                }

            }

        )


        if result.matched_count == 0:

            return {

                "success": False,

                "message":
                    "Conversation not found."

            }


        return {

            "success": True

        }


    # ============================================================
    # UPDATE TITLE
    # ============================================================

    @staticmethod
    async def rename_conversation(
        user_id: str,
        conversation_id: str,
        title: str
    ):

        try:

            object_id = ObjectId(
                conversation_id
            )

        except (
            InvalidId,
            TypeError
        ):

            return {

                "success": False,

                "message":
                    "Invalid conversation ID."

            }


        result = await database.chat_conversations.update_one(

            {
                "_id": object_id,

                "user_id": user_id
            },

            {

                "$set": {

                    "title": title,

                    "updated_at":
                        datetime.now(
                            timezone.utc
                        )

                }

            }

        )


        if result.matched_count == 0:

            return {

                "success": False,

                "message":
                    "Conversation not found."

            }


        return {

            "success": True,

            "message":
                "Conversation renamed successfully."

        }


    # ============================================================
    # DELETE CONVERSATION
    # ============================================================

    @staticmethod
    async def delete_conversation(
        user_id: str,
        conversation_id: str
    ):

        try:

            object_id = ObjectId(
                conversation_id
            )

        except (
            InvalidId,
            TypeError
        ):

            return {

                "success": False,

                "message":
                    "Invalid conversation ID."

            }


        result = await database.chat_conversations.delete_one(

            {
                "_id": object_id,

                "user_id": user_id
            }

        )


        if result.deleted_count == 0:

            return {

                "success": False,

                "message":
                    "Conversation not found."

            }


        return {

            "success": True,

            "message":
                "Conversation deleted successfully."

        }