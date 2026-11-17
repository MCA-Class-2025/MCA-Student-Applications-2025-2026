from datetime import datetime, timezone

from app.core.jwt_handler import create_access_token
from app.core.security import (
    hash_password,
    verify_password
)

from app.database.mongodb import database

from app.models.user_model import UserModel

from app.schemas.user_schema import (
    UserLogin,
    UserRegister
)


class AuthService:

    # ========================================================
    # REGISTER
    # ========================================================

    @staticmethod
    async def register_user(
        user: UserRegister
    ):

        existing_user = await database.users.find_one(
            {
                "email": user.email
            }
        )

        if existing_user:

            return {
                "success": False,
                "message": "Email already registered."
            }

        new_user = UserModel(

            full_name=user.full_name,

            email=user.email,

            password=hash_password(
                user.password
            ),

            monthly_income=float(
                user.monthly_income
            ),

            preferred_currency=
                user.preferred_currency,

            created_at=datetime.now(
                timezone.utc
            )

        )

        result = await database.users.insert_one(
            new_user.model_dump()
        )

        return {

            "success": True,

            "message":
                "User registered successfully.",

            "user_id":
                str(result.inserted_id)

        }


    # ========================================================
    # LOGIN
    # ========================================================

    @staticmethod
    async def login_user(
        user: UserLogin
    ):

        db_user = await database.users.find_one(
            {
                "email": user.email
            }
        )

        if db_user is None:

            return {
                "success": False,
                "message":
                    "Invalid email or password."
            }

        if not verify_password(
            user.password,
            db_user["password"]
        ):

            return {
                "success": False,
                "message":
                    "Invalid email or password."
            }

        access_token = create_access_token(
            {
                "user_id":
                    str(db_user["_id"]),

                "email":
                    db_user["email"]
            }
        )

        return {

            "success": True,

            "message":
                "Login successful.",

            "access_token":
                access_token,

            "token_type":
                "Bearer",

            "user": {

                "id":
                    str(db_user["_id"]),

                "full_name":
                    db_user.get(
                        "full_name",
                        ""
                    ),

                "email":
                    db_user.get(
                        "email",
                        ""
                    ),

                "monthly_income":
                    float(
                        db_user.get(
                            "monthly_income",
                            0
                        ) or 0
                    ),

                "preferred_currency":
                    db_user.get(
                        "preferred_currency",
                        "INR"
                    )

            }

        }