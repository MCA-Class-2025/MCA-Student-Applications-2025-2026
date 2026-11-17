from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from app.core.auth_dependency import (
    get_current_user
)

from app.schemas.ai_schema import (
    ConversationCreate,
    ConversationRename,
)

from app.services.chat_history_service import (
    ChatHistoryService,
)


router = APIRouter(
    prefix="/api/chat-history",
    tags=["Chat History"]
)


# ============================================================
# GET ALL CONVERSATIONS
# ============================================================

@router.get("/")
async def get_conversations(
    current_user=Depends(
        get_current_user
    )
):

    try:

        user_id = current_user[
            "user_id"
        ]

        conversations = (
            await ChatHistoryService.get_conversations(
                user_id=user_id
            )
        )

        return {
            "success": True,
            "data": conversations
        }

    except Exception as e:

        print(
            "GET CHAT HISTORY ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# GET ALL CONVERSATIONS
#
# IMPORTANT:
# Frontend is calling:
#
# /api/chat-history/conversations
#
# So this route is required.
# ============================================================

@router.get("/conversations")
async def get_conversations_list(
    current_user=Depends(
        get_current_user
    )
):

    try:

        user_id = current_user[
            "user_id"
        ]

        conversations = (
            await ChatHistoryService.get_conversations(
                user_id=user_id
            )
        )

        return {
            "success": True,
            "data": conversations
        }

    except Exception as e:

        print(
            "GET CONVERSATIONS ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# CREATE CONVERSATION
# ============================================================

@router.post("/")
async def create_conversation(
    request: ConversationCreate,
    current_user=Depends(
        get_current_user
    )
):

    try:

        user_id = current_user[
            "user_id"
        ]

        return await (
            ChatHistoryService.create_conversation(
                user_id=user_id,
                title=request.title
            )
        )

    except Exception as e:

        print(
            "CREATE CHAT ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# CREATE CONVERSATION
#
# Optional compatibility route.
#
# If your frontend uses:
# POST /api/chat-history/conversations
#
# this will also work.
# ============================================================

@router.post("/conversations")
async def create_conversation_from_frontend(
    request: ConversationCreate,
    current_user=Depends(
        get_current_user
    )
):

    try:

        user_id = current_user[
            "user_id"
        ]

        return await (
            ChatHistoryService.create_conversation(
                user_id=user_id,
                title=request.title
            )
        )

    except Exception as e:

        print(
            "CREATE CONVERSATION ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# GET SINGLE CONVERSATION
# ============================================================

@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user=Depends(
        get_current_user
    )
):

    try:

        user_id = current_user[
            "user_id"
        ]

        result = (
            await ChatHistoryService.get_conversation(
                user_id=user_id,
                conversation_id=conversation_id
            )
        )

        if result.get(
            "success"
        ) is False:

            raise HTTPException(
                status_code=404,
                detail=result.get(
                    "message",
                    "Conversation not found."
                )
            )

        return {
            "success": True,
            "data": result
        }

    except HTTPException:

        raise

    except Exception as e:

        print(
            "GET SINGLE CHAT ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# RENAME CONVERSATION
# ============================================================

@router.patch("/{conversation_id}")
async def rename_conversation(
    conversation_id: str,
    request: ConversationRename,
    current_user=Depends(
        get_current_user
    )
):

    try:

        user_id = current_user[
            "user_id"
        ]

        result = (
            await ChatHistoryService.rename_conversation(
                user_id=user_id,
                conversation_id=conversation_id,
                title=request.title
            )
        )

        if result.get(
            "success"
        ) is False:

            raise HTTPException(
                status_code=404,
                detail=result.get(
                    "message",
                    "Conversation not found."
                )
            )

        return result

    except HTTPException:

        raise

    except Exception as e:

        print(
            "RENAME CHAT ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# DELETE CONVERSATION
# ============================================================

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user=Depends(
        get_current_user
    )
):

    try:

        user_id = current_user[
            "user_id"
        ]

        result = (
            await ChatHistoryService.delete_conversation(
                user_id=user_id,
                conversation_id=conversation_id
            )
        )

        if result.get(
            "success"
        ) is False:

            raise HTTPException(
                status_code=404,
                detail=result.get(
                    "message",
                    "Conversation not found."
                )
            )

        return result

    except HTTPException:

        raise

    except Exception as e:

        print(
            "DELETE CHAT ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )