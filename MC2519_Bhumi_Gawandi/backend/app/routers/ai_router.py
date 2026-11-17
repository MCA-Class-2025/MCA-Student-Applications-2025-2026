# ============================================================
# AI ROUTER
# ============================================================

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)


from app.core.auth_dependency import (
    get_current_user
)


from app.schemas.ai_schema import (

    AIChatRequest,

    NewsRequest,

    CurrencyRequest

)


from app.services.ai_service import (
    AIService
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(

    prefix="/api/ai",

    tags=["AI Assistant"]

)


# ============================================================
# 1. AI CHAT
# ============================================================

@router.post("/chat")
async def ai_chat(

    request: AIChatRequest,

    current_user=Depends(
        get_current_user
    )

):

    try:

        # ====================================================
        # GET USER ID
        # ====================================================

        user_id = current_user[
            "user_id"
        ]


        # ====================================================
        # PRINT DEBUG
        # ====================================================

        print(
            "AI CHAT REQUEST:"
        )

        print(
            "User:",
            user_id
        )

        print(
            "Message:",
            request.message
        )

        print(
            "Conversation:",
            request.conversation_id
        )


        # ====================================================
        # CALL AI SERVICE
        # ====================================================

        result = await AIService.chat(

            user_id=user_id,

            user_message=request.message,

            conversation_id=
                request.conversation_id

        )


        # ====================================================
        # RETURN
        # ====================================================

        return result


    except Exception as e:

        # ====================================================
        # PRINT ERROR
        # ====================================================

        print(
            "========================================"
        )

        print(
            "AI CHAT ROUTER ERROR:"
        )

        print(
            repr(e)
        )

        print(
            "========================================"
        )


        # ====================================================
        # HTTP ERROR
        # ====================================================

        raise HTTPException(

            status_code=500,

            detail=str(e)

        )


# ============================================================
# 2. FINANCIAL NEWS
# ============================================================

@router.post("/news")
async def financial_news(

    request: NewsRequest,

    current_user=Depends(
        get_current_user
    )

):

    try:

        result = await AIService.get_news(

            request.query

        )


        return result


    except Exception as e:

        print(
            "NEWS ERROR:",
            repr(e)
        )


        raise HTTPException(

            status_code=500,

            detail=str(e)

        )


# ============================================================
# 3. CURRENCY CONVERSION
# ============================================================

@router.post("/currency")
async def currency_conversion(

    request: CurrencyRequest,

    current_user=Depends(
        get_current_user
    )

):

    try:

        result = (

            await AIService.convert_currency(

                base=request.base,

                target=request.target,

                amount=request.amount

            )

        )


        return result


    except Exception as e:

        print(

            "CURRENCY ERROR:",

            repr(e)

        )


        raise HTTPException(

            status_code=500,

            detail=str(e)

        )


# ============================================================
# 4. FRANKFURTER EXCHANGE RATE
# ============================================================

@router.get("/exchange-rate")
async def exchange_rate(

    base: str,

    target: str,

    current_user=Depends(
        get_current_user
    )

):

    try:

        result = (

            await AIService
            .get_frankfurter_rate(

                base=base,

                target=target

            )

        )


        return result


    except Exception as e:

        print(

            "EXCHANGE RATE ERROR:",

            repr(e)

        )


        raise HTTPException(

            status_code=500,

            detail=str(e)

        )