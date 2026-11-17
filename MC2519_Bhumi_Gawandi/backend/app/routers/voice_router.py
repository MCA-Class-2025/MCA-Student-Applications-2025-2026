from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.core.auth_dependency import (
    get_current_user,
)

from app.schemas.voice_schema import (
    VoiceExpenseRequest,
)

from app.services.voice_service import (
    VoiceService,
)


router = APIRouter(
    prefix="/api/voice",
    tags=["Voice Expense"],
)


# ============================================================
# PARSE VOICE EXPENSE
# ============================================================

@router.post("/parse")
async def parse_voice_expense(

    request: VoiceExpenseRequest,

    current_user=Depends(
        get_current_user
    ),

):

    try:

        result = await VoiceService.parse_expense(

            transcript=request.transcript

        )


        return {

            "success": True,

            "data": result,

        }


    except ValueError as error:

        raise HTTPException(

            status_code=400,

            detail=str(error)

        )


    except Exception as error:

        print(
            "Voice API Error:",
            error
        )

        raise HTTPException(

            status_code=500,

            detail="Unable to process voice expense."

        )