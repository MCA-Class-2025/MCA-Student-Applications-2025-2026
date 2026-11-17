from fastapi import APIRouter, Depends

from app.core.auth_dependency import get_current_user

from app.schemas.category_schema import (
    CategoryCreate,
    CategoryUpdate,
)

from app.services.category_service import CategoryService


router = APIRouter(
    prefix="/api/categories",
    tags=["Categories"]
)


# ============================================================
# CREATE CATEGORY
# ============================================================

@router.post("/")
async def create_category(
    category: CategoryCreate,
    current_user=Depends(get_current_user)
):

    user_id = current_user["user_id"]

    return await CategoryService.create_category(
        user_id,
        category
    )


# ============================================================
# GET ALL CATEGORIES
# ============================================================

@router.get("/")
async def get_all_categories(
    current_user=Depends(get_current_user)
):

    user_id = current_user["user_id"]

    return await CategoryService.get_all_categories(
        user_id
    )


# ============================================================
# GET SINGLE CATEGORY
# ============================================================

@router.get("/{category_id}")
async def get_category(
    category_id: str,
    current_user=Depends(get_current_user)
):

    user_id = current_user["user_id"]

    return await CategoryService.get_category_by_id(
        category_id,
        user_id
    )


# ============================================================
# UPDATE CATEGORY
# ============================================================

@router.put("/{category_id}")
async def update_category(
    category_id: str,
    category: CategoryUpdate,
    current_user=Depends(get_current_user)
):

    user_id = current_user["user_id"]

    return await CategoryService.update_category(
        category_id,
        category,
        user_id
    )


# ============================================================
# DELETE CATEGORY
# ============================================================

@router.delete("/{category_id}")
async def delete_category(
    category_id: str,
    current_user=Depends(get_current_user)
):

    user_id = current_user["user_id"]

    return await CategoryService.delete_category(
        category_id,
        user_id
    )