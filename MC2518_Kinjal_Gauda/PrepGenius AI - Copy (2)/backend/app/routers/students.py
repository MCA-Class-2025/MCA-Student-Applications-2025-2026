from typing import Optional
from fastapi import APIRouter, Query, status
from app.schemas.student import StudentSchema, PaginatedStudentResponse
from app.services.student_service import student_service
from app.utils.exceptions import PrepGeniusException

router = APIRouter(prefix="/students", tags=["Students"])


@router.get(
    "",
    response_model=PaginatedStudentResponse,
    summary="Get paginated student records",
    description="Retrieve a paginated list of student records with optional filters based on dataset attributes."
)
async def get_students(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Number of student records per page (max 100)"),
    major: Optional[str] = Query(None, description="Filter by Major (e.g., Computer Science, Data Science)"),
    university_year: Optional[str] = Query(None, description="Filter by University Year (Freshman, Sophomore, Junior, Senior)"),
    placement_status: Optional[str] = Query(None, description="Filter by Placement Status (Placed, Not Placed)"),
    gender: Optional[str] = Query(None, description="Filter by Gender (Male, Female, Other)"),
    min_cgpa: Optional[float] = Query(None, ge=0.0, le=4.0, description="Minimum CGPA cutoff"),
    max_cgpa: Optional[float] = Query(None, ge=0.0, le=4.0, description="Maximum CGPA cutoff"),
    academic_performance: Optional[str] = Query(None, description="Filter by Academic Performance (Good, Average, Poor, Excellent)"),
    company_tier: Optional[str] = Query(None, description="Filter by Company Tier (Tier 1, Tier 2, Tier 3, No Company)"),
    career_field: Optional[str] = Query(None, description="Filter by Career Field (e.g., Backend Developer, Data Scientist)"),
):
    return student_service.get_students(
        page=page,
        limit=limit,
        major=major,
        university_year=university_year,
        placement_status=placement_status,
        gender=gender,
        min_cgpa=min_cgpa,
        max_cgpa=max_cgpa,
        academic_performance=academic_performance,
        company_tier=company_tier,
        career_field=career_field,
    )


@router.get(
    "/search",
    response_model=PaginatedStudentResponse,
    summary="Search student records",
    description="Perform keyword search across student attributes (ID, Major, Career Field, Year, Placement, etc.)."
)
async def search_students(
    q: str = Query(..., min_length=1, description="Search keyword query string"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Number of student records per page (max 100)"),
    major: Optional[str] = Query(None, description="Filter by Major"),
    university_year: Optional[str] = Query(None, description="Filter by University Year"),
    placement_status: Optional[str] = Query(None, description="Filter by Placement Status"),
    gender: Optional[str] = Query(None, description="Filter by Gender"),
    min_cgpa: Optional[float] = Query(None, ge=0.0, le=4.0, description="Minimum CGPA cutoff"),
    max_cgpa: Optional[float] = Query(None, ge=0.0, le=4.0, description="Maximum CGPA cutoff"),
    academic_performance: Optional[str] = Query(None, description="Filter by Academic Performance"),
    company_tier: Optional[str] = Query(None, description="Filter by Company Tier"),
    career_field: Optional[str] = Query(None, description="Filter by Career Field"),
):
    return student_service.search_students(
        query=q,
        page=page,
        limit=limit,
        major=major,
        university_year=university_year,
        placement_status=placement_status,
        gender=gender,
        min_cgpa=min_cgpa,
        max_cgpa=max_cgpa,
        academic_performance=academic_performance,
        company_tier=company_tier,
        career_field=career_field,
    )


@router.get(
    "/{student_id}",
    response_model=StudentSchema,
    summary="Get single student details by Student_ID",
    description="Retrieve full record of a student using their unique Student_ID primary key (e.g. ST000001)."
)
async def get_student_by_id(student_id: str):
    student = student_service.get_student_by_id(student_id)
    if not student:
        raise PrepGeniusException(
            message=f"Student with Student_ID '{student_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"student_id": student_id}
        )
    return student
