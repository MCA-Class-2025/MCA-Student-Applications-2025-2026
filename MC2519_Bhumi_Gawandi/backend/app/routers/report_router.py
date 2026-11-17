from fastapi import APIRouter, Depends, Query

from app.core.auth_dependency import get_current_user

from app.services.report_service import ReportService


router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"]
)


# ============================================================
# GET MONTHLY REPORT
# ============================================================

@router.get("/")
async def get_report(

    month: int = Query(
        ...,
        ge=1,
        le=12
    ),

    year: int = Query(
        ...,
        ge=2020,
        le=2100
    ),

    category: str | None = Query(
        default=None
    ),

    current_user=Depends(
        get_current_user
    )
):

    user_id = current_user["user_id"]


    return await ReportService.get_report(

        user_id=user_id,

        month=month,

        year=year,

        category=category

    )