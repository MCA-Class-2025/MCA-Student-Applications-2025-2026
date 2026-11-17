import random
from datetime import datetime, timedelta, timezone

from app.database.mongodb import database


class OTPService:

    # ============================================================
    # GENERATE OTP
    # ============================================================

    @staticmethod
    def generate_otp():

        return str(
            random.randint(
                100000,
                999999
            )
        )

    # ============================================================
    # SAVE OTP
    # ============================================================

    @staticmethod
    async def save_otp(
        user_id: str,
        budget_id: str,
        otp: str,
        new_amount: float
    ):

        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(minutes=5)
        )

        # Remove previous OTP for this budget
        await database.budget_otps.delete_many(
            {
                "user_id": user_id,
                "budget_id": budget_id,
            }
        )

        # Save new OTP
        await database.budget_otps.insert_one(
            {
                "user_id": user_id,
                "budget_id": budget_id,
                "otp": otp,
                "new_amount": new_amount,
                "expires_at": expires_at,
                "created_at": datetime.now(
                    timezone.utc
                ),
            }
        )

    # ============================================================
    # VERIFY OTP
    # ============================================================

    @staticmethod
    async def verify_otp(
        user_id: str,
        budget_id: str,
        otp: str
    ):

        record = await database.budget_otps.find_one(
            {
                "user_id": user_id,
                "budget_id": budget_id,
                "otp": otp,
            }
        )

        if record is None:
            return None

        expires_at = record.get(
            "expires_at"
        )

        if expires_at is None:
            return None

        # Make sure datetime is timezone-aware
        if expires_at.tzinfo is None:

            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

        # Check expiration
        if (
            datetime.now(timezone.utc)
            > expires_at
        ):

            await database.budget_otps.delete_one(
                {
                    "_id": record["_id"]
                }
            )

            return None

        new_amount = float(
            record["new_amount"]
        )

        # OTP can only be used once
        await database.budget_otps.delete_one(
            {
                "_id": record["_id"]
            }
        )

        return new_amount