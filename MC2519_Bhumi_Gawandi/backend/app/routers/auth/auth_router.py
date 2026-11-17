from fastapi import APIRouter, Depends, HTTPException, status
import traceback

from app.core.auth_dependency import get_current_user
from app.database.mongodb import database
from app.schemas.user_schema import UserLogin, UserRegister
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


@router.post("/register")
async def register(user: UserRegister):

    try:

        result = await AuthService.register_user(user)

        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result["message"]
            )

        return result

    except Exception as e:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/login")
async def login(user: UserLogin):

    try:

        result = await AuthService.login_user(user)

        if not result["success"]:
            raise HTTPException(
                status_code=401,
                detail=result["message"]
            )

        return result

    except Exception as e:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/me")
async def get_logged_in_user(
    current_user=Depends(get_current_user)
):

    user = await database.users.find_one(
        {"email": current_user["email"]},
        {"password": 0},
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    user["_id"] = str(user["_id"])

    return {
        "success": True,
        "user": user,
    }