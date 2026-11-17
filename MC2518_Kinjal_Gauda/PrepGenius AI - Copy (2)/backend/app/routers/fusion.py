from typing import List
import os
from fastapi import APIRouter, Query, Response, status
from app.schemas.fusion import (
    TopicSchema,
    StudentMappingDetailResponse,
    ResourceRecommendationsSchema,
    FusedStudentProfileResponse,
    WideFusedStudentRecordSchema,
    PaginatedWideFusedStudentResponse,
    RelationshipMetadataSchema,
    ColumnLineageSchema,
    ExportedFileSchema,
    ExportedFileListResponse,
    MasterExportStatusResponse,
)
from app.services.fusion_service import fusion_service
from app.services.student_service import student_service
from app.utils.exceptions import PrepGeniusException

router = APIRouter(prefix="/fusion", tags=["Data Fusion Foundation"])


@router.get(
    "/topics",
    response_model=List[TopicSchema],
    summary="Get normalized topics table",
    description="Retrieve list of all normalized academic/technical topics used for resource domain classification."
)
async def get_topics():
    return fusion_service.get_all_topics()


@router.get(
    "/relationships",
    response_model=List[RelationshipMetadataSchema],
    summary="Get entity relationship metadata catalog",
    description="Retrieve relational catalog detailing table primary keys, foreign keys, join conditions, and dataset sources."
)
async def get_relationships():
    return fusion_service.get_relationship_metadata()


@router.get(
    "/schema",
    response_model=List[ColumnLineageSchema],
    summary="Get column data lineage dictionary",
    description="Retrieve attribute-level data provenance mapping every fused column to its original dataset, source table, and relationship."
)
async def get_schema_lineage():
    return fusion_service.get_column_lineage()


@router.get(
    "/exports",
    response_model=ExportedFileListResponse,
    summary="List persisted fused Excel files",
    description="Retrieve list of generated Excel workbooks stored in data/fused/."
)
async def get_exported_fused_files():
    files = fusion_service.get_exported_files()
    return ExportedFileListResponse(
        total=len(files),
        files=[ExportedFileSchema(**f) for f in files]
    )


@router.get(
    "/export-master-excel",
    summary="Export complete master 16-sheet Data Fusion Excel workbook",
    description="Generates, persists to data/fused/PrepGenius_COMPLETE_DATA_FUSION.xlsx, and downloads the complete 16-sheet relational Data Fusion workbook (1,000 students, PK/FK relationships, bridge tables, EDA metrics, provenance, dictionary)."
)
@router.get("/export-complete-excel", include_in_schema=False)
async def export_master_excel():
    file_path = fusion_service.save_complete_master_excel(target_student_count=1000)
    with open(file_path, "rb") as f:
        excel_bytes = f.read()

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=PrepGenius_COMPLETE_DATA_FUSION.xlsx"
        }
    )


@router.get(
    "/export-status",
    response_model=MasterExportStatusResponse,
    summary="Get master Data Fusion Excel export status",
    description="Reports file size, generation timestamp, and entity record counts for the master 16-sheet Data Fusion workbook."
)
async def get_master_export_status():
    status_data = fusion_service.get_master_export_status()
    return MasterExportStatusResponse(**status_data)



@router.get(
    "/wide",
    response_model=PaginatedWideFusedStudentResponse,
    summary="Get paginated dynamic wide fused student records",
    description="Retrieve paginated dynamically computed wide fused student records combining core profile, topic, books, youtube, arxiv, location, and provenance."
)
async def get_paginated_wide_students(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
):
    return fusion_service.get_paginated_wide_fused_profiles(page=page, limit=limit)


@router.get(
    "/students/{student_id}/mapping",
    response_model=StudentMappingDetailResponse,
    summary="Get topic and location mappings for a student",
    description="Retrieve derived topic classification and deterministic synthetic location mapping for a student."
)
async def get_student_mappings(student_id: str):
    student = student_service.get_student_by_id(student_id)
    if not student:
        raise PrepGeniusException(
            message=f"Student with Student_ID '{student_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"student_id": student_id}
        )
    topic_mapping = fusion_service.derive_topic_for_student(student)
    location_mapping = fusion_service.derive_location_for_student(student.Student_ID)
    return StudentMappingDetailResponse(
        student_id=student.Student_ID,
        topic_mapping=topic_mapping,
        location_mapping=location_mapping,
    )


@router.get(
    "/students/{student_id}/resources",
    response_model=ResourceRecommendationsSchema,
    summary="Get topic-first recommended learning resources",
    description="Retrieve domain-filtered and quality-ranked Books, YouTube videos, and arXiv research papers for a student."
)
async def get_student_resources(student_id: str):
    student = student_service.get_student_by_id(student_id)
    if not student:
        raise PrepGeniusException(
            message=f"Student with Student_ID '{student_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"student_id": student_id}
        )
    topic_mapping = fusion_service.derive_topic_for_student(student)
    books = fusion_service.get_recommended_books(topic_mapping.topic_id, student, limit=3)
    youtube = fusion_service.get_recommended_youtube(topic_mapping.topic_id, student, limit=3)
    arxiv = fusion_service.get_recommended_arxiv(topic_mapping.topic_id, student, limit=3)

    return ResourceRecommendationsSchema(
        books=books,
        youtube=youtube,
        arxiv=arxiv,
    )


@router.get(
    "/students/{student_id}/wide",
    response_model=WideFusedStudentRecordSchema,
    summary="Get single student dynamic wide fused record",
    description="Retrieve dynamically computed flat wide fused record for a single student combining profile, topic, top book, top video, top paper, location, and provenance, and persists it to data/fused/."
)
async def get_student_wide_profile(student_id: str):
    wide_record = fusion_service.get_wide_fused_student_profile(student_id)
    if not wide_record:
        raise PrepGeniusException(
            message=f"Student with Student_ID '{student_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"student_id": student_id}
        )
    # Save/persist fused Excel file to data/fused/
    fusion_service.save_fused_excel(wide_record.Student_ID)
    return wide_record


@router.get(
    "/students/{student_id}/export-excel",
    summary="Export dynamic wide fused student profile to Excel",
    description="Dynamically generates, saves to data/fused/, and downloads an Excel workbook (.xlsx) containing Fused_Data, Provenance, and Relationships sheets for the specified student."
)
async def export_fused_excel(student_id: str):
    file_path = fusion_service.save_fused_excel(student_id)
    if not file_path or not os.path.exists(file_path):
        raise PrepGeniusException(
            message=f"Student with Student_ID '{student_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"student_id": student_id}
        )
    
    with open(file_path, "rb") as f:
        excel_bytes = f.read()

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=PrepGenius_Fused_{student_id.strip().upper()}.xlsx"
        }
    )


@router.get(
    "/students/{student_id}",
    response_model=FusedStudentProfileResponse,
    summary="Get complete wide fused student record",
    description="Retrieve full unified record combining Student profile, Topic mapping, Location mapping, Resource recommendations, and Data Provenance."
)
async def get_fused_student_profile(student_id: str):
    fused_profile = fusion_service.get_fused_student_profile(student_id)
    if not fused_profile:
        raise PrepGeniusException(
            message=f"Student with Student_ID '{student_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"student_id": student_id}
        )
    return fused_profile

