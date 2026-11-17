import csv
import math
import os
from typing import Dict, List, Optional
from app.config import settings
from app.schemas.student import StudentSchema, PaginatedStudentResponse
from app.utils.logger import logger


class StudentService:
    _instance: Optional['StudentService'] = None
    _students_list: List[dict] = []
    _students_map: Dict[str, dict] = {}
    _loaded: bool = False

    def __init__(self):
        if not StudentService._loaded:
            self._load_dataset()

    @classmethod
    def get_instance(cls) -> 'StudentService':
        if cls._instance is None:
            cls._instance = StudentService()
        return cls._instance

    def _resolve_csv_path(self) -> str:
        candidates = [
            settings.STUDENT_DATASET_PATH,
            os.path.join(os.getcwd(), "data", "student_career_success_dataset.csv"),
            os.path.join(os.getcwd(), "student_career_success_dataset.csv"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "student_career_success_dataset.csv"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "student_career_success_dataset.csv"),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        raise FileNotFoundError(
            f"student_career_success_dataset.csv not found in candidate paths: {candidates}"
        )

    def _load_dataset(self):
        csv_path = self._resolve_csv_path()
        logger.info(f"Loading student dataset from: {csv_path}")

        students_list = []
        students_map = {}

        int_fields = {
            "Age", "Attendance_Percentage", "Study_Hours_Per_Week",
            "Programming_Skill", "Projects_Completed", "Certifications",
            "Hackathons", "Internships", "Resume_Score",
            "Communication_Skills", "Teamwork", "Problem_Solving",
            "Interview_Score", "Starting_Salary_USD"
        }
        float_fields = {"CGPA", "Employability_Score"}

        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                formatted_row = {}
                for k, v in row.items():
                    key = k.strip()
                    val = v.strip() if isinstance(v, str) else v
                    if key in int_fields:
                        formatted_row[key] = int(float(val)) if val != "" else 0
                    elif key in float_fields:
                        formatted_row[key] = float(val) if val != "" else 0.0
                    else:
                        formatted_row[key] = val
                
                sid = formatted_row.get("Student_ID")
                if sid:
                    students_list.append(formatted_row)
                    students_map[sid.upper()] = formatted_row

        StudentService._students_list = students_list
        StudentService._students_map = students_map
        StudentService._loaded = True
        logger.info(f"Successfully loaded {len(students_list)} student records.")

    def is_loaded(self) -> bool:
        return StudentService._loaded and len(StudentService._students_list) > 0

    def get_total_count(self) -> int:
        return len(StudentService._students_list)

    def get_student_by_id(self, student_id: str) -> Optional[StudentSchema]:
        row = self._students_map.get(student_id.strip().upper())
        if not row:
            return None
        return StudentSchema(**row)

    def get_students(
        self,
        page: int = 1,
        limit: int = 20,
        major: Optional[str] = None,
        university_year: Optional[str] = None,
        placement_status: Optional[str] = None,
        gender: Optional[str] = None,
        min_cgpa: Optional[float] = None,
        max_cgpa: Optional[float] = None,
        academic_performance: Optional[str] = None,
        company_tier: Optional[str] = None,
        career_field: Optional[str] = None,
    ) -> PaginatedStudentResponse:
        filtered = self._apply_filters(
            self._students_list,
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
        return self._paginate(filtered, page=page, limit=limit)

    def search_students(
        self,
        query: str,
        page: int = 1,
        limit: int = 20,
        major: Optional[str] = None,
        university_year: Optional[str] = None,
        placement_status: Optional[str] = None,
        gender: Optional[str] = None,
        min_cgpa: Optional[float] = None,
        max_cgpa: Optional[float] = None,
        academic_performance: Optional[str] = None,
        company_tier: Optional[str] = None,
        career_field: Optional[str] = None,
    ) -> PaginatedStudentResponse:
        q_lower = query.strip().lower()
        search_results = []
        for student in self._students_list:
            searchable_text = f"{student.get('Student_ID', '')} {student.get('Major', '')} {student.get('Career_Field', '')} {student.get('University_Year', '')} {student.get('Academic_Performance', '')} {student.get('Placement_Status', '')} {student.get('Company_Tier', '')} {student.get('Placement_Mode', '')}".lower()
            if q_lower in searchable_text:
                search_results.append(student)

        filtered = self._apply_filters(
            search_results,
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
        return self._paginate(filtered, page=page, limit=limit)

    def _apply_filters(
        self,
        dataset: List[dict],
        major: Optional[str] = None,
        university_year: Optional[str] = None,
        placement_status: Optional[str] = None,
        gender: Optional[str] = None,
        min_cgpa: Optional[float] = None,
        max_cgpa: Optional[float] = None,
        academic_performance: Optional[str] = None,
        company_tier: Optional[str] = None,
        career_field: Optional[str] = None,
    ) -> List[dict]:
        res = dataset
        if major:
            m_lower = major.strip().lower()
            res = [s for s in res if s.get("Major", "").lower() == m_lower]
        if university_year:
            uy_lower = university_year.strip().lower()
            res = [s for s in res if s.get("University_Year", "").lower() == uy_lower]
        if placement_status:
            ps_lower = placement_status.strip().lower()
            res = [s for s in res if s.get("Placement_Status", "").lower() == ps_lower]
        if gender:
            g_lower = gender.strip().lower()
            res = [s for s in res if s.get("Gender", "").lower() == g_lower]
        if min_cgpa is not None:
            res = [s for s in res if s.get("CGPA", 0.0) >= min_cgpa]
        if max_cgpa is not None:
            res = [s for s in res if s.get("CGPA", 0.0) <= max_cgpa]
        if academic_performance:
            ap_lower = academic_performance.strip().lower()
            res = [s for s in res if s.get("Academic_Performance", "").lower() == ap_lower]
        if company_tier:
            ct_lower = company_tier.strip().lower()
            res = [s for s in res if s.get("Company_Tier", "").lower() == ct_lower]
        if career_field:
            cf_lower = career_field.strip().lower()
            res = [s for s in res if s.get("Career_Field", "").lower() == cf_lower]
        return res

    def _paginate(self, dataset: List[dict], page: int, limit: int) -> PaginatedStudentResponse:
        total = len(dataset)
        page = max(1, page)
        limit = max(1, min(100, limit))
        total_pages = math.ceil(total / limit) if total > 0 else 1

        start = (page - 1) * limit
        end = start + limit
        items = dataset[start:end]

        schemas = [StudentSchema(**item) for item in items]
        return PaginatedStudentResponse(
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            data=schemas,
        )


student_service = StudentService.get_instance()
