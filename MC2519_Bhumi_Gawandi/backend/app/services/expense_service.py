from calendar import monthrange
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId

from app.database.mongodb import database
from app.models.expense_model import ExpenseModel
from app.schemas.expense_schema import (
    ExpenseCreate,
    ExpenseUpdate,
)

from app.services.email_service import (
    send_budget_exceeded_email,
)


class ExpenseService:

    # ============================================================
    # CHECK BUDGET AFTER EXPENSE
    # ============================================================

    @staticmethod
    async def check_budget_and_send_email(
        user_id: str,
        category: str,
        expense_date: datetime,
    ):

        try:

            # ====================================================
            # 1. GET MONTH AND YEAR
            # ====================================================

            month = expense_date.month
            year = expense_date.year

            # ====================================================
            # 2. FIND BUDGET
            # ====================================================

            budget = await database.budgets.find_one(
                {
                    "user_id": user_id,
                    "category": category,
                    "month": month,
                    "year": year,
                }
            )

            # No budget set for this category
            if budget is None:

                print(
                    f"No budget found for "
                    f"{category} - {month}/{year}"
                )

                return

            budget_amount = float(
                budget.get("amount", 0)
            )

            # ====================================================
            # 3. MONTH START
            # ====================================================

            start_date = datetime(
                year,
                month,
                1,
                0,
                0,
                0,
                tzinfo=timezone.utc,
            )

            # ====================================================
            # 4. MONTH END
            # ====================================================

            last_day = monthrange(
                year,
                month
            )[1]

            end_date = datetime(
                year,
                month,
                last_day,
                23,
                59,
                59,
                tzinfo=timezone.utc,
            )

            # ====================================================
            # 5. CALCULATE TOTAL CATEGORY SPENDING
            # ====================================================

            spending_result = await database.expenses.aggregate(
                [
                    {
                        "$match": {
                            "user_id": user_id,
                            "category": category,
                            "date": {
                                "$gte": start_date,
                                "$lte": end_date,
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

            spent = 0.0

            if spending_result:

                spent = float(
                    spending_result[0].get(
                        "total",
                        0
                    )
                )

            print(
                f"Budget Check | "
                f"Category: {category} | "
                f"Budget: ₹{budget_amount} | "
                f"Spent: ₹{spent}"
            )

            # ====================================================
            # 6. CHECK BUDGET
            # ====================================================

            if spent <= budget_amount:

                print(
                    "Budget is still within limit."
                )

                return

            # ====================================================
            # 7. GET USER
            # ====================================================

            try:

                user_object_id = ObjectId(
                    user_id
                )

            except (InvalidId, TypeError):

                print(
                    "Invalid user ID while checking budget."
                )

                return

            user = await database.users.find_one(
                {
                    "_id": user_object_id
                }
            )

            if user is None:

                print(
                    "User not found while sending budget email."
                )

                return

            # ====================================================
            # 8. GET LOGGED-IN USER EMAIL
            # ====================================================

            user_email = user.get(
                "email"
            )

            if not user_email:

                print(
                    "User email not found."
                )

                return

            # ====================================================
            # 9. SEND EMAIL
            # ====================================================

            try:

                await send_budget_exceeded_email(
                    email=user_email,
                    category=category,
                    budget=budget_amount,
                    spent=spent,
                )

                print(
                    f"✅ Budget exceeded email sent to "
                    f"{user_email}"
                )

            except Exception as email_error:

                print(
                    "❌ Budget email sending failed:",
                    email_error
                )

        except Exception as error:

            print(
                "❌ Budget checking failed:",
                error
            )

    # ============================================================
    # CREATE EXPENSE
    # ============================================================

    @staticmethod
    async def create_expense(
        user_id: str,
        expense: ExpenseCreate
    ):

        new_expense = ExpenseModel(
            user_id=user_id,
            title=expense.title,
            amount=expense.amount,
            category=expense.category,
            payment_method=expense.payment_method,
            date=expense.date,
            notes=expense.notes,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # ========================================================
        # SAVE EXPENSE
        # ========================================================

        result = await database.expenses.insert_one(
            new_expense.model_dump()
        )

        expense_id = str(
            result.inserted_id
        )

        # ========================================================
        # CHECK BUDGET
        # ========================================================

        try:

            expense_date = expense.date

            # If date is missing
            if expense_date is None:

                expense_date = datetime.now(
                    timezone.utc
                )

            # Convert naive datetime to UTC
            if (
                isinstance(expense_date, datetime)
                and expense_date.tzinfo is None
            ):

                expense_date = expense_date.replace(
                    tzinfo=timezone.utc
                )

            await ExpenseService.check_budget_and_send_email(
                user_id=user_id,
                category=expense.category,
                expense_date=expense_date,
            )

        except Exception as budget_error:

            print(
                "Budget notification error:",
                budget_error
            )

        # ========================================================
        # RESPONSE
        # ========================================================

        return {
            "success": True,
            "message": "Expense added successfully.",
            "expense_id": expense_id,
        }

    # ============================================================
    # GET ALL EXPENSES
    # ============================================================

    @staticmethod
    async def get_all_expenses(
        user_id: str
    ):

        expenses = await database.expenses.find(
            {
                "user_id": user_id
            }
        ).sort(
            "date",
            -1
        ).to_list(
            length=None
        )

        for expense in expenses:

            expense["_id"] = str(
                expense["_id"]
            )

        return expenses

    # ============================================================
    # GET SINGLE EXPENSE
    # ============================================================

    @staticmethod
    async def get_expense_by_id(
        expense_id: str,
        user_id: str
    ):

        try:

            object_id = ObjectId(
                expense_id
            )

        except (InvalidId, TypeError):

            return {
                "success": False,
                "message": "Invalid expense ID.",
            }

        expense = await database.expenses.find_one(
            {
                "_id": object_id,
                "user_id": user_id,
            }
        )

        if expense is None:

            return {
                "success": False,
                "message": "Expense not found.",
            }

        expense["_id"] = str(
            expense["_id"]
        )

        return expense

    # ============================================================
    # UPDATE EXPENSE
    # ============================================================

    @staticmethod
    async def update_expense(
        expense_id: str,
        expense: ExpenseUpdate,
        user_id: str
    ):

        try:

            object_id = ObjectId(
                expense_id
            )

        except (InvalidId, TypeError):

            return {
                "success": False,
                "message": "Invalid expense ID.",
            }

        existing = await database.expenses.find_one(
            {
                "_id": object_id,
                "user_id": user_id,
            }
        )

        if existing is None:

            return {
                "success": False,
                "message": "Expense not found.",
            }

        # ========================================================
        # UPDATE
        # ========================================================

        await database.expenses.update_one(
            {
                "_id": object_id,
                "user_id": user_id,
            },
            {
                "$set": {
                    "title": expense.title,
                    "amount": expense.amount,
                    "category": expense.category,
                    "payment_method": expense.payment_method,
                    "date": expense.date,
                    "notes": expense.notes,
                    "updated_at": datetime.now(
                        timezone.utc
                    ),
                }
            }
        )

        # ========================================================
        # CHECK BUDGET AFTER UPDATE
        # ========================================================

        try:

            expense_date = expense.date

            if expense_date is None:

                expense_date = datetime.now(
                    timezone.utc
                )

            if (
                isinstance(expense_date, datetime)
                and expense_date.tzinfo is None
            ):

                expense_date = expense_date.replace(
                    tzinfo=timezone.utc
                )

            await ExpenseService.check_budget_and_send_email(
                user_id=user_id,
                category=expense.category,
                expense_date=expense_date,
            )

        except Exception as budget_error:

            print(
                "Budget notification error:",
                budget_error
            )

        return {
            "success": True,
            "message": "Expense updated successfully.",
            "expense_id": expense_id,
        }

    # ============================================================
    # DELETE EXPENSE
    # ============================================================

    @staticmethod
    async def delete_expense(
        expense_id: str,
        user_id: str
    ):

        try:

            object_id = ObjectId(
                expense_id
            )

        except (InvalidId, TypeError):

            return {
                "success": False,
                "message": "Invalid expense ID.",
            }

        result = await database.expenses.delete_one(
            {
                "_id": object_id,
                "user_id": user_id,
            }
        )

        if result.deleted_count == 0:

            return {
                "success": False,
                "message": "Expense not found.",
            }

        return {
            "success": True,
            "message": "Expense deleted successfully.",
            "expense_id": expense_id,
        }