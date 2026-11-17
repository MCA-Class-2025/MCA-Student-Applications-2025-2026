from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId

from app.database.mongodb import database
from app.models.budget_model import BudgetModel
from app.schemas.budget_schema import (
    BudgetCreate,
    BudgetUpdate,
)


class BudgetService:

    # ============================================================
    # CREATE BUDGET
    # ============================================================

    @staticmethod
    async def create_budget(
        user_id: str,
        budget: BudgetCreate
    ):

        # Check if budget already exists
        existing = await database.budgets.find_one(
            {
                "user_id": user_id,
                "category": budget.category,
                "month": budget.month,
                "year": budget.year,
            }
        )

        if existing:

            return {
                "success": False,
                "message": (
                    f"A budget already exists for "
                    f"{budget.category} for "
                    f"{budget.month}/{budget.year}."
                ),
            }

        # Create new budget
        new_budget = BudgetModel(
            user_id=user_id,
            category=budget.category,
            amount=budget.amount,
            month=budget.month,
            year=budget.year,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        result = await database.budgets.insert_one(
            new_budget.model_dump()
        )

        return {
            "success": True,
            "message": "Budget created successfully.",
            "budget_id": str(result.inserted_id),
        }

    # ============================================================
    # CALCULATE SPENT FOR BUDGET
    # ============================================================

    @staticmethod
    async def calculate_spent(
        user_id: str,
        category: str,
        month: int,
        year: int
    ):

        # Start of selected month
        start_date = datetime(
            year,
            month,
            1,
            tzinfo=timezone.utc
        )

        # Start of next month
        if month == 12:

            end_date = datetime(
                year + 1,
                1,
                1,
                tzinfo=timezone.utc
            )

        else:

            end_date = datetime(
                year,
                month + 1,
                1,
                tzinfo=timezone.utc
            )

        # Calculate total expenses
        result = await database.expenses.aggregate(
            [
                {
                    "$match": {
                        "user_id": user_id,
                        "category": category,
                        "date": {
                            "$gte": start_date,
                            "$lt": end_date,
                        },
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total": {
                            "$sum": "$amount"
                        },
                    }
                },
            ]
        ).to_list(
            length=1
        )

        if not result:

            return 0

        return float(
            result[0].get(
                "total",
                0
            )
        )

    # ============================================================
    # GET ALL BUDGETS
    # ============================================================

    @staticmethod
    async def get_all_budgets(
        user_id: str
    ):

        budgets = await database.budgets.find(
            {
                "user_id": user_id
            }
        ).sort(
            [
                ("year", -1),
                ("month", -1),
            ]
        ).to_list(
            length=None
        )

        response = []

        for budget in budgets:

            budget_id = str(
                budget["_id"]
            )

            amount = float(
                budget.get(
                    "amount",
                    0
                )
            )

            month = int(
                budget.get(
                    "month"
                )
            )

            year = int(
                budget.get(
                    "year"
                )
            )

            # Calculate spending
            spent = await BudgetService.calculate_spent(
                user_id=user_id,
                category=budget["category"],
                month=month,
                year=year,
            )

            remaining = amount - spent

            percentage = (
                (spent / amount) * 100
                if amount > 0
                else 0
            )

            response.append(
                {
                    "_id": budget_id,
                    "user_id": budget["user_id"],
                    "category": budget["category"],
                    "amount": amount,
                    "month": month,
                    "year": year,
                    "spent": spent,
                    "remaining": remaining,
                    "percentage": percentage,
                    "is_exceeded": (
                        spent > amount
                    ),
                    "created_at": budget.get(
                        "created_at"
                    ),
                    "updated_at": budget.get(
                        "updated_at"
                    ),
                }
            )

        return response

    # ============================================================
    # GET SINGLE BUDGET
    # ============================================================

    @staticmethod
    async def get_budget_by_id(
        budget_id: str,
        user_id: str
    ):

        try:

            object_id = ObjectId(
                budget_id
            )

        except (
            InvalidId,
            TypeError
        ):

            return {
                "success": False,
                "message": "Invalid budget ID.",
            }

        budget = await database.budgets.find_one(
            {
                "_id": object_id,
                "user_id": user_id,
            }
        )

        if budget is None:

            return {
                "success": False,
                "message": "Budget not found.",
            }

        amount = float(
            budget.get(
                "amount",
                0
            )
        )

        month = int(
            budget.get(
                "month"
            )
        )

        year = int(
            budget.get(
                "year"
            )
        )

        # Calculate spending
        spent = await BudgetService.calculate_spent(
            user_id=user_id,
            category=budget["category"],
            month=month,
            year=year,
        )

        budget["_id"] = str(
            budget["_id"]
        )

        budget["spent"] = spent

        budget["remaining"] = (
            amount - spent
        )

        budget["percentage"] = (
            (spent / amount) * 100
            if amount > 0
            else 0
        )

        budget["is_exceeded"] = (
            spent > amount
        )

        return budget

    # ============================================================
    # REQUEST BUDGET UPGRADE
    #
    # This does NOT change the budget.
    #
    # It only:
    # 1. Checks the budget
    # 2. Checks new amount
    # 3. Returns category information
    #
    # The router will then send the OTP.
    # ============================================================

    @staticmethod
    async def request_budget_upgrade(
        budget_id: str,
        new_amount: float,
        user_id: str
    ):

        try:

            object_id = ObjectId(
                budget_id
            )

        except (
            InvalidId,
            TypeError
        ):

            return {
                "success": False,
                "message": "Invalid budget ID.",
            }

        # Find existing budget
        existing = await database.budgets.find_one(
            {
                "_id": object_id,
                "user_id": user_id,
            }
        )

        if existing is None:

            return {
                "success": False,
                "message": "Budget not found.",
            }

        current_amount = float(
            existing.get(
                "amount",
                0
            )
        )

        # New amount must be greater
        # than current amount
        if new_amount <= current_amount:

            return {
                "success": False,
                "message": (
                    "New budget amount must be "
                    "greater than the current "
                    "budget."
                ),
            }

        return {
            "success": True,
            "category": existing["category"],
            "current_amount": current_amount,
            "new_amount": new_amount,
        }

    # ============================================================
    # COMPLETE BUDGET UPGRADE
    #
    # This is called ONLY after OTP verification.
    # ============================================================

    @staticmethod
    async def complete_budget_upgrade(
        budget_id: str,
        user_id: str,
        new_amount: float
    ):

        try:

            object_id = ObjectId(
                budget_id
            )

        except (
            InvalidId,
            TypeError
        ):

            return {
                "success": False,
                "message": "Invalid budget ID.",
            }

        # Find existing budget
        existing = await database.budgets.find_one(
            {
                "_id": object_id,
                "user_id": user_id,
            }
        )

        if existing is None:

            return {
                "success": False,
                "message": "Budget not found.",
            }

        current_amount = float(
            existing.get(
                "amount",
                0
            )
        )

        # Safety check
        if new_amount <= current_amount:

            return {
                "success": False,
                "message": (
                    "New budget amount must be "
                    "greater than the current budget."
                ),
            }

        # Update budget
        await database.budgets.update_one(
            {
                "_id": object_id,
                "user_id": user_id,
            },
            {
                "$set": {
                    "amount": new_amount,
                    "updated_at": datetime.now(
                        timezone.utc
                    ),
                }
            }
        )

        return {
            "success": True,
            "message": (
                "Budget increased successfully."
            ),
            "budget_id": budget_id,
            "old_amount": current_amount,
            "new_amount": new_amount,
        }

    # ============================================================
    # UPDATE BUDGET
    # ============================================================

    @staticmethod
    async def update_budget(
        budget_id: str,
        budget: BudgetUpdate,
        user_id: str
    ):

        try:

            object_id = ObjectId(
                budget_id
            )

        except (
            InvalidId,
            TypeError
        ):

            return {
                "success": False,
                "message": "Invalid budget ID.",
            }

        # Find existing budget
        existing = await database.budgets.find_one(
            {
                "_id": object_id,
                "user_id": user_id,
            }
        )

        if existing is None:

            return {
                "success": False,
                "message": "Budget not found.",
            }

        current_amount = float(
            existing.get(
                "amount",
                0
            )
        )

        # ========================================================
        # IMPORTANT
        #
        # Increasing an existing budget must go through
        # email OTP verification.
        # ========================================================

        if budget.amount > current_amount:

            return {
                "success": False,
                "requires_verification": True,
                "message": (
                    "Increasing the budget requires "
                    "email verification. Please use "
                    "the budget upgrade option."
                ),
            }

        # ========================================================
        # CHECK DUPLICATE
        # ========================================================

        duplicate = await database.budgets.find_one(
            {
                "_id": {
                    "$ne": object_id
                },
                "user_id": user_id,
                "category": budget.category,
                "month": budget.month,
                "year": budget.year,
            }
        )

        if duplicate:

            return {
                "success": False,
                "message": (
                    "Another budget already exists "
                    "for this category and month."
                ),
            }

        # ========================================================
        # UPDATE
        # ========================================================

        await database.budgets.update_one(
            {
                "_id": object_id,
                "user_id": user_id,
            },
            {
                "$set": {
                    "category": budget.category,
                    "amount": budget.amount,
                    "month": budget.month,
                    "year": budget.year,
                    "updated_at": datetime.now(
                        timezone.utc
                    ),
                }
            }
        )

        return {
            "success": True,
            "message": (
                "Budget updated successfully."
            ),
            "budget_id": budget_id,
        }

    # ============================================================
    # DELETE BUDGET
    # ============================================================

    @staticmethod
    async def delete_budget(
        budget_id: str,
        user_id: str
    ):

        try:

            object_id = ObjectId(
                budget_id
            )

        except (
            InvalidId,
            TypeError
        ):

            return {
                "success": False,
                "message": "Invalid budget ID.",
            }

        result = await database.budgets.delete_one(
            {
                "_id": object_id,
                "user_id": user_id,
            }
        )

        if result.deleted_count == 0:

            return {
                "success": False,
                "message": "Budget not found.",
            }

        return {
            "success": True,
            "message": (
                "Budget deleted successfully."
            ),
            "budget_id": budget_id,
        }