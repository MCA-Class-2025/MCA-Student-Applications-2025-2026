from datetime import datetime, timezone

from app.database.mongodb import database


class ReportService:

    # ============================================================
    # GET COMPLETE REPORT
    # ============================================================

    @staticmethod
    async def get_report(
        user_id: str,
        month: int,
        year: int,
        category: str | None = None
    ):

        # ========================================================
        # DATE RANGE
        # ========================================================

        start_date = datetime(
            year,
            month,
            1,
            tzinfo=timezone.utc
        )

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


        # ========================================================
        # EXPENSE FILTER
        # ========================================================

        expense_filter = {
            "user_id": user_id,
            "date": {
                "$gte": start_date,
                "$lt": end_date
            }
        }


        if category:

            expense_filter["category"] = category


        # ========================================================
        # GET EXPENSES
        # ========================================================

        expenses = await database.expenses.find(
            expense_filter
        ).to_list(
            length=None
        )


        # ========================================================
        # TOTAL EXPENSE
        # ========================================================

        total_expense = 0.0

        for expense in expenses:

            total_expense += float(
                expense.get("amount", 0)
            )


        # ========================================================
        # CATEGORY ANALYSIS
        # ========================================================

        category_totals = {}


        for expense in expenses:

            expense_category = (
                expense.get("category")
                or "Other"
            )

            amount = float(
                expense.get("amount", 0)
            )

            if expense_category not in category_totals:

                category_totals[
                    expense_category
                ] = 0.0

            category_totals[
                expense_category
            ] += amount


        category_analysis = []


        for name, amount in category_totals.items():

            percentage = 0.0

            if total_expense > 0:

                percentage = (
                    amount / total_expense
                ) * 100


            category_analysis.append({

                "category": name,

                "amount": round(
                    amount,
                    2
                ),

                "percentage": round(
                    percentage,
                    2
                )

            })


        category_analysis.sort(
            key=lambda x: x["amount"],
            reverse=True
        )


        # ========================================================
        # GET BUDGETS
        # ========================================================

        budget_filter = {
            "user_id": user_id,
            "month": month,
            "year": year
        }


        if category:

            budget_filter[
                "category"
            ] = category


        budgets = await database.budgets.find(
            budget_filter
        ).to_list(
            length=None
        )


        # ========================================================
        # TOTAL BUDGET
        # ========================================================

        total_budget = 0.0


        for budget in budgets:

            total_budget += float(
                budget.get("amount", 0)
            )


        # ========================================================
        # BUDGET VS ACTUAL
        # ========================================================

        budget_analysis = []


        for budget in budgets:

            budget_category = (
                budget.get("category")
                or "Other"
            )

            budget_amount = float(
                budget.get("amount", 0)
            )

            spent = category_totals.get(
                budget_category,
                0.0
            )

            remaining = (
                budget_amount - spent
            )

            percentage_used = 0.0

            if budget_amount > 0:

                percentage_used = (
                    spent / budget_amount
                ) * 100


            if spent > budget_amount:

                status = "Exceeded"

            elif spent >= budget_amount * 0.8:

                status = "Near Limit"

            else:

                status = "Within Budget"


            budget_analysis.append({

                "category": budget_category,

                "budget": round(
                    budget_amount,
                    2
                ),

                "spent": round(
                    spent,
                    2
                ),

                "remaining": round(
                    remaining,
                    2
                ),

                "percentage_used": round(
                    percentage_used,
                    2
                ),

                "status": status

            })


        # ========================================================
        # REMAINING BUDGET
        # ========================================================

        remaining_budget = (
            total_budget - total_expense
        )


        # ========================================================
        # HIGHEST SPENDING CATEGORY
        # ========================================================

        highest_category = None


        if category_analysis:

            highest_category = (
                category_analysis[0]
            )


        # ========================================================
        # DAILY SPENDING
        # ========================================================

        daily_totals = {}


        for expense in expenses:

            expense_date = expense.get(
                "date"
            )

            if not expense_date:

                continue


            if isinstance(
                expense_date,
                datetime
            ):

                day = expense_date.day

            else:

                try:

                    parsed_date = datetime.fromisoformat(
                        str(expense_date).replace(
                            "Z",
                            "+00:00"
                        )
                    )

                    day = parsed_date.day

                except ValueError:

                    continue


            if day not in daily_totals:

                daily_totals[day] = 0.0


            daily_totals[day] += float(
                expense.get("amount", 0)
            )


        daily_analysis = []


        for day, amount in sorted(
            daily_totals.items()
        ):

            daily_analysis.append({

                "day": day,

                "amount": round(
                    amount,
                    2
                )

            })


        # ========================================================
        # PAYMENT METHOD ANALYSIS
        # ========================================================

        payment_totals = {}


        for expense in expenses:

            payment_method = (
                expense.get(
                    "payment_method"
                )
                or "Other"
            )

            amount = float(
                expense.get("amount", 0)
            )


            if payment_method not in payment_totals:

                payment_totals[
                    payment_method
                ] = 0.0


            payment_totals[
                payment_method
            ] += amount


        payment_analysis = []


        for method, amount in payment_totals.items():

            payment_analysis.append({

                "payment_method": method,

                "amount": round(
                    amount,
                    2
                )

            })


        payment_analysis.sort(
            key=lambda x: x["amount"],
            reverse=True
        )


        # ========================================================
        # RESULT
        # ========================================================

        return {

            "success": True,

            "period": {

                "month": month,

                "year": year

            },

            "summary": {

                "total_expense": round(
                    total_expense,
                    2
                ),

                "total_budget": round(
                    total_budget,
                    2
                ),

                "remaining_budget": round(
                    remaining_budget,
                    2
                ),

                "expense_count": len(
                    expenses
                ),

                "budget_count": len(
                    budgets
                )

            },

            "highest_spending_category":
                highest_category,

            "category_analysis":
                category_analysis,

            "budget_analysis":
                budget_analysis,

            "daily_analysis":
                daily_analysis,

            "payment_analysis":
                payment_analysis

        }