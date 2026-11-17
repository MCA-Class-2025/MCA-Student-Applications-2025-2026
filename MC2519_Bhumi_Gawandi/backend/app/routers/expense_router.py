from fastapi import (
    APIRouter,
    Depends
)

from app.core.auth_dependency import (
    get_current_user
)

from app.schemas.expense_schema import (
    ExpenseCreate,
    ExpenseUpdate
)

from app.services.expense_service import (
    ExpenseService
)


router = APIRouter(
    prefix="/api/expenses",
    tags=["Expenses"]
)


@router.post("/")
async def create_expense(
    expense: ExpenseCreate,
    current_user=Depends(
        get_current_user
    )
):

    user_id = current_user[
        "user_id"
    ]

    return await ExpenseService.create_expense(
        user_id,
        expense
    )


@router.get("/")
async def get_all_expenses(
    current_user=Depends(
        get_current_user
    )
):

    user_id = current_user[
        "user_id"
    ]

    return await ExpenseService.get_all_expenses(
        user_id
    )


@router.get("/{expense_id}")
async def get_expense(
    expense_id: str,
    current_user=Depends(
        get_current_user
    )
):

    user_id = current_user[
        "user_id"
    ]

    return await ExpenseService.get_expense_by_id(
        expense_id,
        user_id
    )


@router.put("/{expense_id}")
async def update_expense(
    expense_id: str,
    expense: ExpenseUpdate,
    current_user=Depends(
        get_current_user
    )
):

    user_id = current_user[
        "user_id"
    ]

    return await ExpenseService.update_expense(
        expense_id,
        expense,
        user_id
    )


@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: str,
    current_user=Depends(
        get_current_user
    )
):

    user_id = current_user[
        "user_id"
    ]

    return await ExpenseService.delete_expense(
        expense_id,
        user_id
    )