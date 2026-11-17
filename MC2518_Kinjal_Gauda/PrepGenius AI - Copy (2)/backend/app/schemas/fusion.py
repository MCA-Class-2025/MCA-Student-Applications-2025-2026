from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from app.schemas.student import StudentSchema


class TopicSchema(BaseModel):
    topic_id: str = Field(..., description="Unique topic identifier (Primary Key)")
    topic_name: str = Field(..., description="Human-readable topic name")
    subject_area: str = Field(..., description="Broad academic/technical subject area")
    description: str = Field(..., description="Topic description and scope")


class StudentTopicMappingSchema(BaseModel):
    mapping_id: str = Field(..., description="Unique mapping identifier")
    student_id: str = Field(..., description="Student_ID reference")
    topic_id: str = Field(..., description="Mapped topic_id reference")
    topic_name: str = Field(..., description="Name of the mapped topic")
    mapping_source: str = Field("DERIVED_FROM_MAJOR_AND_CAREER", description="Source logic")
    mapping_rule: str = Field(..., description="Specific rule applied")


class StudentLocationMappingSchema(BaseModel):
    mapping_id: str = Field(..., description="Unique mapping identifier")
    student_id: str = Field(..., description="Student_ID reference")
    city: str = Field(..., description="Mapped city name")
    latitude: float = Field(..., description="City latitude")
    longitude: float = Field(..., description="City longitude")
    mapping_source: str = Field("DEMOGRAPHIC_ASSIGNMENT", description="Source logic")
    mapping_rule: str = Field(..., description="Deterministic hash rule applied")
    mapping_type: str = Field("DERIVED / SYNTHETIC (DEMO MAPPING)", description="Mandatory synthetic label")


class BookResourceSchema(BaseModel):
    isbn13: int = Field(..., description="13-digit ISBN primary key")
    isbn10: str = Field(..., description="10-digit ISBN")
    title: str = Field(..., description="Book title")
    authors: Optional[str] = Field(None, description="Author(s)")
    categories: Optional[str] = Field(None, description="Book category")
    average_rating: Optional[float] = Field(None, description="Average rating score")
    ratings_count: Optional[float] = Field(None, description="Total ratings count")
    thumbnail: Optional[str] = Field(None, description="Cover image thumbnail URL")
    description: Optional[str] = Field(None, description="Book synopsis")
    published_year: Optional[float] = Field(None, description="Publication year")
    num_pages: Optional[float] = Field(None, description="Page count")
    match_reason: str = Field(..., description="Domain relevance match explanation")
    provenance: str = Field("data/books.csv", description="Source dataset file")


class YouTubeResourceSchema(BaseModel):
    video_id: str = Field(..., description="YouTube Video ID primary key")
    title: str = Field(..., description="Video title")
    channel_name: str = Field(..., description="Channel name")
    channel_id: str = Field(..., description="Channel ID")
    category_id: int = Field(..., description="YouTube Category ID (27/28)")
    views: int = Field(..., description="View count")
    likes: int = Field(..., description="Like count")
    comments: int = Field(..., description="Comment count")
    duration_sec: Optional[float] = Field(None, description="Duration in seconds")
    publish_date: str = Field(..., description="Publish date")
    subscriber_count: int = Field(..., description="Channel subscriber count")
    popularity_score: float = Field(..., description="Calculated popularity score")
    match_reason: str = Field(..., description="Domain relevance match explanation")
    provenance: str = Field("data/yt data.csv", description="Source dataset file")


class ArXivResourceSchema(BaseModel):
    id: str = Field(..., description="arXiv Paper ID primary key")
    title: str = Field(..., description="Paper title")
    category: str = Field(..., description="Category text")
    category_code: str = Field(..., description="Category code (e.g. cs.AI, cs.SE)")
    published_date: str = Field(..., description="Published date")
    updated_date: str = Field(..., description="Updated date")
    first_author: str = Field(..., description="First author name")
    authors: str = Field(..., description="Authors string")
    summary: str = Field(..., description="Abstract summary")
    summary_word_count: int = Field(..., description="Summary word count")
    match_reason: str = Field(..., description="Domain relevance match explanation")
    provenance: str = Field("data/arXiv_scientific_dataset.csv", description="Source dataset file")


class ResourceRecommendationsSchema(BaseModel):
    books: List[BookResourceSchema] = Field(..., description="Top domain-matched recommended books")
    youtube: List[YouTubeResourceSchema] = Field(..., description="Top domain-matched recommended YouTube videos")
    arxiv: List[ArXivResourceSchema] = Field(..., description="Top domain-matched recommended arXiv research papers")


class DataProvenanceSchema(BaseModel):
    student_core: str = Field("data/student_career_success_dataset.csv", description="Student API core source")
    location: str = Field("data/cities.xlsx via student_location_mapping", description="Location dataset source")
    book: str = Field("data/books.csv via books_topic_mapping", description="Books dataset source")
    youtube: str = Field("data/yt data.csv via youtube_topic_mapping", description="YouTube dataset source")
    arxiv: str = Field("data/arXiv_scientific_dataset.csv via arxiv_topic_mapping", description="arXiv dataset source")


class StudentMappingDetailResponse(BaseModel):
    student_id: str
    topic_mapping: StudentTopicMappingSchema
    location_mapping: StudentLocationMappingSchema


class FusedStudentProfileResponse(BaseModel):
    student_profile: StudentSchema
    topic_mapping: StudentTopicMappingSchema
    location_mapping: StudentLocationMappingSchema
    recommendations: ResourceRecommendationsSchema
    provenance: DataProvenanceSchema


class WideFusedStudentRecordSchema(BaseModel):
    # Student core columns
    Student_ID: str
    Age: int
    Gender: str
    University_Year: str
    Major: str
    Attendance_Percentage: int
    Study_Hours_Per_Week: int
    CGPA: float
    Academic_Performance: str
    Programming_Skill: int
    Projects_Completed: int
    Certifications: int
    Hackathons: int
    Internships: int
    Resume_Score: int
    Communication_Skills: int
    Teamwork: int
    Problem_Solving: int
    English_Proficiency: str
    Interview_Score: int
    Employability_Score: float
    Placement_Status: str
    Company_Tier: str
    Career_Field: str
    Placement_Mode: str
    Starting_Salary_USD: int

    # Topic columns
    topic_id: str
    topic_name: str
    subject_area: str

    # Book columns
    recommended_book_title: Optional[str] = None
    recommended_book_isbn13: Optional[int] = None
    recommended_book_author: Optional[str] = None
    recommended_book_category: Optional[str] = None
    recommended_book_rating: Optional[float] = None

    # YouTube columns
    recommended_video_title: Optional[str] = None
    recommended_video_id: Optional[str] = None
    recommended_channel: Optional[str] = None
    recommended_video_views: Optional[int] = None
    recommended_video_category: Optional[int] = None

    # arXiv columns
    recommended_paper_title: Optional[str] = None
    recommended_paper_id: Optional[str] = None
    recommended_paper_category: Optional[str] = None
    recommended_paper_category_code: Optional[str] = None
    recommended_paper_summary: Optional[str] = None

    # Location columns
    city: str
    latitude: float
    longitude: float

    # Mapping logic & match reasons
    topic_mapping_source: str = "DERIVED_FROM_MAJOR_AND_CAREER"
    topic_mapping_rule: Optional[str] = None
    location_mapping_type: str = "DERIVED / SYNTHETIC (DEMO MAPPING)"
    recommended_book_match_reason: Optional[str] = None
    recommended_video_match_reason: Optional[str] = None
    recommended_paper_match_reason: Optional[str] = None

    # Provenance object
    provenance: DataProvenanceSchema


class PaginatedWideFusedStudentResponse(BaseModel):
    total: int = Field(..., description="Total student records")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total pages available")
    data: List[WideFusedStudentRecordSchema] = Field(..., description="List of wide fused student records")


class RelationshipMetadataSchema(BaseModel):
    table_name: str
    primary_key: str
    foreign_key: Optional[str] = None
    referenced_table: Optional[str] = None
    referenced_column: Optional[str] = None
    relationship_type: str
    source_dataset: str


class ColumnLineageSchema(BaseModel):
    column_name: str
    source_dataset: str
    source_table: str
    source_column: str
    relationship_used: str
    description: str


class ExportedFileSchema(BaseModel):
    filename: str = Field(..., description="Name of the generated Excel file")
    student_id: str = Field(..., description="Student_ID identifier")
    file_path: str = Field(..., description="Relative path where file is persisted")
    file_size_bytes: int = Field(..., description="File size in bytes")
    created_at: str = Field(..., description="File creation/modification timestamp")


class ExportedFileListResponse(BaseModel):
    total: int = Field(..., description="Total persisted Excel files")
    files: List[ExportedFileSchema] = Field(..., description="List of exported Excel files in data/fused/")


class MasterExportStatusResponse(BaseModel):
    filename: str = Field("PrepGenius_COMPLETE_DATA_FUSION.xlsx", description="Name of the master Excel file")
    file_path: str = Field("data/fused/PrepGenius_COMPLETE_DATA_FUSION.xlsx", description="Relative path on disk")
    generated_at: str = Field(..., description="Timestamp when the master workbook was generated")
    student_count: int = Field(1000, description="Total unique students included")
    dynamic_youtube_count: int = Field(..., description="Total YouTube records indexed")
    dynamic_book_count: int = Field(..., description="Total Books records indexed")
    dynamic_arxiv_count: int = Field(..., description="Total arXiv papers indexed")
    file_size_bytes: int = Field(..., description="Workbook file size in bytes")
    status: str = Field("COMPLETED", description="Export generation status")


