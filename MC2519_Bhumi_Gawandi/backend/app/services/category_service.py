from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId

from app.database.mongodb import database
from app.models.category_model import CategoryModel
from app.schemas.category_schema import (
    CategoryCreate,
    CategoryUpdate,
)


class CategoryService:

    # ============================================================
    # CREATE CATEGORY
    # ============================================================

    @staticmethod
    async def create_category(
        user_id: str,
        category: CategoryCreate
    ):

        name = category.name.strip()

        if not name:
            return {
                "success": False,
                "message": "Category name is required."
            }

        existing = await database.categories.find_one(
            {
                "user_id": user_id,
                "name": {
                    "$regex": f"^{name}$",
                    "$options": "i"
                }
            }
        )

        if existing:
            return {
                "success": False,
                "message": "Category already exists."
            }

        new_category = CategoryModel(
            user_id=user_id,
            name=name,
            description=category.description.strip(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        result = await database.categories.insert_one(
            new_category.model_dump()
        )

        return {
            "success": True,
            "message": "Category created successfully.",
            "category_id": str(result.inserted_id)
        }

    # ============================================================
    # GET ALL CATEGORIES
    # ============================================================

    @staticmethod
    async def get_all_categories(
        user_id: str
    ):

        categories = await database.categories.find(
            {
                "user_id": user_id
            }
        ).sort(
            "name",
            1
        ).to_list(
            length=None
        )

        for category in categories:
            category["_id"] = str(
                category["_id"]
            )

        return categories

    # ============================================================
    # GET SINGLE CATEGORY
    # ============================================================

    @staticmethod
    async def get_category_by_id(
        category_id: str,
        user_id: str
    ):

        try:
            object_id = ObjectId(category_id)

        except (InvalidId, TypeError):
            return {
                "success": False,
                "message": "Invalid category ID."
            }

        category = await database.categories.find_one(
            {
                "_id": object_id,
                "user_id": user_id
            }
        )

        if category is None:
            return {
                "success": False,
                "message": "Category not found."
            }

        category["_id"] = str(
            category["_id"]
        )

        return category

    # ============================================================
    # UPDATE CATEGORY
    # ============================================================

    @staticmethod
    async def update_category(
        category_id: str,
        category: CategoryUpdate,
        user_id: str
    ):

        try:
            object_id = ObjectId(category_id)

        except (InvalidId, TypeError):
            return {
                "success": False,
                "message": "Invalid category ID."
            }

        name = category.name.strip()

        if not name:
            return {
                "success": False,
                "message": "Category name is required."
            }

        existing = await database.categories.find_one(
            {
                "user_id": user_id,
                "name": {
                    "$regex": f"^{name}$",
                    "$options": "i"
                },
                "_id": {
                    "$ne": object_id
                }
            }
        )

        if existing:
            return {
                "success": False,
                "message": "Another category with this name already exists."
            }

        category_exists = await database.categories.find_one(
            {
                "_id": object_id,
                "user_id": user_id
            }
        )

        if category_exists is None:
            return {
                "success": False,
                "message": "Category not found."
            }

        await database.categories.update_one(
            {
                "_id": object_id,
                "user_id": user_id
            },
            {
                "$set": {
                    "name": name,
                    "description": category.description.strip(),
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )

        return {
            "success": True,
            "message": "Category updated successfully.",
            "category_id": category_id
        }

    # ============================================================
    # DELETE CATEGORY
    # ============================================================

    @staticmethod
    async def delete_category(
        category_id: str,
        user_id: str
    ):

        try:
            object_id = ObjectId(category_id)

        except (InvalidId, TypeError):
            return {
                "success": False,
                "message": "Invalid category ID."
            }

        result = await database.categories.delete_one(
            {
                "_id": object_id,
                "user_id": user_id
            }
        )

        if result.deleted_count == 0:
            return {
                "success": False,
                "message": "Category not found."
            }

        return {
            "success": True,
            "message": "Category deleted successfully.",
            "category_id": category_id
        }