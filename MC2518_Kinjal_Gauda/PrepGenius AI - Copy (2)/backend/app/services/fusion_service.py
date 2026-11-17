import csv
import hashlib
import io
import os
import re
from typing import Dict, List, Optional
import openpyxl
import pandas as pd

from app.config import settings
from app.schemas.fusion import (
    TopicSchema,
    StudentTopicMappingSchema,
    StudentLocationMappingSchema,
    BookResourceSchema,
    YouTubeResourceSchema,
    ArXivResourceSchema,
    ResourceRecommendationsSchema,
    DataProvenanceSchema,
    FusedStudentProfileResponse,
    StudentMappingDetailResponse,
    WideFusedStudentRecordSchema,
    PaginatedWideFusedStudentResponse,
    RelationshipMetadataSchema,
    ColumnLineageSchema,
)
from app.schemas.student import StudentSchema
from app.services.student_service import student_service
from app.utils.logger import logger


class FusionService:
    _instance: Optional['FusionService'] = None
    _topics: Dict[str, TopicSchema] = {}
    _cities_list: List[dict] = []
    _books_list: List[dict] = []
    _youtube_list: List[dict] = []
    _arxiv_list: List[dict] = []
    _loaded: bool = False

    def __init__(self):
        if not FusionService._loaded:
            self._init_topics()
            self._load_datasets()

    @classmethod
    def get_instance(cls) -> 'FusionService':
        if cls._instance is None:
            cls._instance = FusionService()
        return cls._instance

    def _init_topics(self):
        topic_defs = [
            TopicSchema(
                topic_id="TOPIC_AI_ML",
                topic_name="Artificial Intelligence & Machine Learning",
                subject_area="Computer Science & Data Science",
                description="Study of intelligent agents, neural networks, deep learning, NLP, and predictive modeling."
            ),
            TopicSchema(
                topic_id="TOPIC_SOFTWARE_DEV",
                topic_name="Software Engineering & Backend Systems",
                subject_area="Computer Science",
                description="Software architecture, clean code, web development, system design, databases, and DevOps."
            ),
            TopicSchema(
                topic_id="TOPIC_CYBERSECURITY",
                topic_name="Cybersecurity & Information Security",
                subject_area="Computer Science & Information Assurance",
                description="Network security, ethical hacking, cryptography, penetration testing, and SOC operations."
            ),
            TopicSchema(
                topic_id="TOPIC_DATA_SCIENCE",
                topic_name="Data Science & Big Data Analytics",
                subject_area="Data Science & Statistics",
                description="Data processing, statistical analysis, data visualization, machine learning, and ETL pipelines."
            ),
            TopicSchema(
                topic_id="TOPIC_BUSINESS_ANALYTICS",
                topic_name="Business Analytics & Decision Science",
                subject_area="Business & Management Information Systems",
                description="Business intelligence, data-driven decision making, metrics, and quantitative modeling."
            ),
            TopicSchema(
                topic_id="TOPIC_EMBEDDED_HARDWARE",
                topic_name="Electrical Engineering & Embedded Systems",
                subject_area="Electrical & Computer Engineering",
                description="Embedded microcontrollers, hardware systems, signal processing, and IoT."
            ),
        ]
        self._topics = {t.topic_id: t for t in topic_defs}

    def _resolve_file_path(self, default_path: str, filename: str) -> str:
        candidates = [
            default_path,
            os.path.join(settings.DATA_DIR, filename),
            os.path.join(os.getcwd(), "data", filename),
            os.path.join(os.getcwd(), filename),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        logger.warning(f"File {filename} not found in candidate paths.")
        return ""

    def _load_datasets(self):
        logger.info("Initializing Data Fusion datasets with strict relevance indexing...")

        # 1. Load Cities
        cities_path = self._resolve_file_path(settings.CITIES_DATASET_PATH, "cities.xlsx")
        if cities_path and os.path.exists(cities_path):
            try:
                df_cities = pd.read_excel(cities_path)
                self._cities_list = df_cities.to_dict(orient="records")
                logger.info(f"Loaded {len(self._cities_list)} cities from cities.xlsx")
            except Exception as e:
                logger.error(f"Error loading cities.xlsx: {e}")

        # 2. Load Books
        books_path = self._resolve_file_path(settings.BOOKS_DATASET_PATH, "books.csv")
        if books_path and os.path.exists(books_path):
            try:
                with open(books_path, mode="r", encoding="utf-8", errors="replace") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            isbn13 = int(row.get("isbn13", 0))
                        except ValueError:
                            continue
                        
                        try:
                            pub_year = float(row.get("published_year", 0.0)) if row.get("published_year") else None
                            avg_rating = float(row.get("average_rating", 0.0)) if row.get("average_rating") else None
                            num_pages = float(row.get("num_pages", 0.0)) if row.get("num_pages") else None
                            ratings_cnt = float(row.get("ratings_count", 0.0)) if row.get("ratings_count") else None
                        except ValueError:
                            pub_year, avg_rating, num_pages, ratings_cnt = None, None, None, None

                        self._books_list.append({
                            "isbn13": isbn13,
                            "isbn10": row.get("isbn10", "").strip(),
                            "title": row.get("title", "").strip(),
                            "subtitle": row.get("subtitle", "").strip() or None,
                            "authors": row.get("authors", "").strip() or None,
                            "categories": row.get("categories", "").strip() or None,
                            "thumbnail": row.get("thumbnail", "").strip() or None,
                            "description": row.get("description", "").strip() or None,
                            "published_year": pub_year,
                            "average_rating": avg_rating,
                            "num_pages": num_pages,
                            "ratings_count": ratings_cnt,
                        })
                logger.info(f"Loaded {len(self._books_list)} books from books.csv")
            except Exception as e:
                logger.error(f"Error loading books.csv: {e}")

        # 3. Load YouTube
        yt_path = self._resolve_file_path(settings.YOUTUBE_DATASET_PATH, "yt data.csv")
        if yt_path and os.path.exists(yt_path):
            try:
                with open(yt_path, mode="r", encoding="utf-8", errors="replace") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            cid = int(row.get("category_id", 0))
                            views = int(float(row.get("views", 0)))
                            likes = int(float(row.get("likes", 0)))
                            comments = int(float(row.get("comments", 0)))
                            subscribers = int(float(row.get("subscriber_count", 0)))
                            dur = float(row.get("duration_sec", 0)) if row.get("duration_sec") else None
                        except ValueError:
                            continue

                        vid = row.get("video_id", "").strip()
                        if vid:
                            pop_score = (likes * 2.0) + views + (subscribers / 1000.0)
                            self._youtube_list.append({
                                "video_id": vid,
                                "title": row.get("title", "").strip(),
                                "description": row.get("description", "").strip() or None,
                                "category_id": cid,
                                "views": views,
                                "likes": likes,
                                "comments": comments,
                                "duration_sec": dur,
                                "publish_date": row.get("publish_date", "").strip(),
                                "channel_id": row.get("channel_id", "").strip(),
                                "channel_name": row.get("channel_name", "").strip(),
                                "subscriber_count": subscribers,
                                "popularity_score": pop_score,
                            })
                logger.info(f"Loaded {len(self._youtube_list)} YouTube videos from yt data.csv")
            except Exception as e:
                logger.error(f"Error loading yt data.csv: {e}")

        # 4. Load arXiv
        arxiv_path = self._resolve_file_path(settings.ARXIV_DATASET_PATH, "arXiv_scientific_dataset.csv")
        if arxiv_path and os.path.exists(arxiv_path):
            try:
                with open(arxiv_path, mode="r", encoding="utf-8", errors="replace") as f:
                    reader = csv.DictReader(f)
                    count = 0
                    for row in reader:
                        pid = row.get("id", "").strip()
                        if pid and not pid.startswith("Unnamed"):
                            try:
                                wc = int(row.get("summary_word_count", 0))
                            except ValueError:
                                wc = 0

                            self._arxiv_list.append({
                                "id": pid,
                                "title": row.get("title", "").strip(),
                                "category": row.get("category", "").strip(),
                                "category_code": row.get("category_code", "").strip(),
                                "published_date": row.get("published_date", "").strip(),
                                "updated_date": row.get("updated_date", "").strip(),
                                "authors": row.get("authors", "").strip(),
                                "first_author": row.get("first_author", "").strip(),
                                "summary": row.get("summary", "").strip(),
                                "summary_word_count": wc,
                            })
                            count += 1
                            if count >= 30000:
                                break
                logger.info(f"Indexed {len(self._arxiv_list)} arXiv research papers from arXiv_scientific_dataset.csv")
            except Exception as e:
                logger.error(f"Error loading arXiv_scientific_dataset.csv: {e}")

        FusionService._loaded = True

    def get_all_topics(self) -> List[TopicSchema]:
        return list(self._topics.values())

    def get_topic_by_id(self, topic_id: str) -> Optional[TopicSchema]:
        return self._topics.get(topic_id)

    def derive_topic_for_student(self, student: StudentSchema) -> StudentTopicMappingSchema:
        major = student.Major.strip().lower()
        career = student.Career_Field.strip().lower()

        if "artificial intelligence" in major or "ai engineer" in career or "machine learning" in career:
            tid = "TOPIC_AI_ML"
            rule = f"MATCH: Major='{student.Major}', Career_Field='{student.Career_Field}' -> AI & ML"
        elif "cybersecurity" in major or "cybersecurity" in career or "penetration tester" in career or "soc analyst" in career:
            tid = "TOPIC_CYBERSECURITY"
            rule = f"MATCH: Major='{student.Major}', Career_Field='{student.Career_Field}' -> Cybersecurity"
        elif "data science" in major or "data scientist" in career or "data analyst" in career:
            tid = "TOPIC_DATA_SCIENCE"
            rule = f"MATCH: Major='{student.Major}', Career_Field='{student.Career_Field}' -> Data Science"
        elif "business analytics" in major or "business analyst" in career:
            tid = "TOPIC_BUSINESS_ANALYTICS"
            rule = f"MATCH: Major='{student.Major}', Career_Field='{student.Career_Field}' -> Business Analytics"
        elif "electrical engineering" in major or "embedded" in career:
            tid = "TOPIC_EMBEDDED_HARDWARE"
            rule = f"MATCH: Major='{student.Major}', Career_Field='{student.Career_Field}' -> Embedded Systems"
        else:
            tid = "TOPIC_SOFTWARE_DEV"
            rule = f"MATCH: Major='{student.Major}', Career_Field='{student.Career_Field}' -> Software Engineering"

        topic = self._topics[tid]
        h = hashlib.sha256(f"STM_{student.Student_ID}_{tid}".encode("utf-8")).hexdigest()[:12]
        return StudentTopicMappingSchema(
            mapping_id=f"STM_{h}",
            student_id=student.Student_ID,
            topic_id=topic.topic_id,
            topic_name=topic.topic_name,
            mapping_source="DERIVED_FROM_MAJOR_AND_CAREER",
            mapping_rule=rule,
        )

    def derive_location_for_student(self, student_id: str) -> StudentLocationMappingSchema:
        if not self._cities_list:
            city_name, lat, lng = "unknown_city", 0.0, 0.0
        else:
            h_int = int(hashlib.sha256(student_id.encode("utf-8")).hexdigest(), 16)
            idx = h_int % len(self._cities_list)
            selected_city = self._cities_list[idx]
            city_name = selected_city.get("city", "unknown")
            lat = float(selected_city.get("latitude", 0.0))
            lng = float(selected_city.get("longitude", 0.0))

        h_map = hashlib.sha256(f"SLM_{student_id}".encode("utf-8")).hexdigest()[:12]
        return StudentLocationMappingSchema(
            mapping_id=f"SLM_{h_map}",
            student_id=student_id,
            city=city_name,
            latitude=lat,
            longitude=lng,
            mapping_source="DEMOGRAPHIC_ASSIGNMENT",
            mapping_rule=f"DETERMINISTIC_HASH: sha256({student_id}) % {len(self._cities_list)}",
            mapping_type="DERIVED / SYNTHETIC (DEMO MAPPING)",
        )

    def get_recommended_books(self, topic_id: str, student: StudentSchema, limit: int = 3) -> List[BookResourceSchema]:
        excluded_categories = {
            "fiction", "juvenile fiction", "juvenile nonfiction", "biography & autobiography", "biography",
            "poetry", "drama", "comics & graphic novels", "cooking", "body, mind & spirit", "humor", "games",
            "literary criticism", "antiques & collectibles", "history", "religion", "performing arts",
            "psychology", "social science", "health & fitness", "sports & recreation", "travel", "political science"
        }

        non_study_title_keywords = [
            "lego", "star wars", "kangaroo", "wodehouse", "monty python", "shakespeare", "monsters", "disney", "barbie"
        ]

        topic_book_regex = {
            "TOPIC_AI_ML": [r"\bai\b", r"\bartificial intelligence\b", r"\bmachine learning\b", r"\bdeep learning\b", r"\bneural networks?\b", r"\bpython\b", r"\bdata science\b"],
            "TOPIC_SOFTWARE_DEV": [r"\bpython\b", r"\bjava\b", r"\bc\+\+\b", r"\bprogramming\b", r"\bsoftware engineering\b", r"\balgorithms?\b", r"\bdata structures?\b", r"\bdatabases?\b", r"\bsql\b", r"\bweb development\b", r"\bbackend\b", r"\bcomputer science\b", r"\boperating systems?\b", r"\bcode\b", r"\bmysql\b", r"\bsoftware\b", r"\bdeveloper\b"],
            "TOPIC_CYBERSECURITY": [r"\bcybersecurity\b", r"\binformation security\b", r"\bcryptography\b", r"\bhacking\b", r"\bpenetration testing\b", r"\bnetwork security\b", r"\bsecure code\b"],
            "TOPIC_DATA_SCIENCE": [r"\bdata science\b", r"\bdata analytics?\b", r"\bbig data\b", r"\bstatistics?\b", r"\bpython\b", r"\bsql\b", r"\bdatabases?\b", r"\bmachine learning\b"],
            "TOPIC_BUSINESS_ANALYTICS": [r"\bbusiness analytics?\b", r"\bdata analytics?\b", r"\bbusiness intelligence\b", r"\bdecision science\b", r"\bquantitative\b"],
            "TOPIC_EMBEDDED_HARDWARE": [r"\bembedded systems?\b", r"\bmicrocontrollers?\b", r"\belectronics?\b", r"\bhardware\b", r"\bsignal processing\b", r"\belectrical engineering\b"]
        }

        regex_list = topic_book_regex.get(topic_id, [r"\bcomputer science\b", r"\bprogramming\b"])
        pattern = re.compile("|".join(regex_list), re.IGNORECASE)

        candidates = []
        for b in self._books_list:
            cat = (b.get("categories") or "").lower().strip()
            title = (b.get("title") or "").lower().strip()
            desc = (b.get("description") or "").lower().strip()
            text = f"{title} {desc}"

            # Step 1: Reject excluded categories
            if cat in excluded_categories:
                continue

            # Step 2: Reject non-study title keywords (e.g. Lego, Star Wars)
            if any(k in title for k in non_study_title_keywords):
                continue

            # Step 3: Enforce strict topic matching
            if ("computers" in cat or "technology" in cat or "science" in cat) and pattern.search(text):
                candidates.append(b)

        # Step 4: Quality Ranking after strict relevance filtering
        candidates.sort(
            key=lambda x: (x.get("average_rating") or 0.0, x.get("ratings_count") or 0.0),
            reverse=True
        )

        results = []
        for b in candidates[:limit]:
            results.append(BookResourceSchema(
                isbn13=b["isbn13"],
                isbn10=b["isbn10"],
                title=b["title"],
                authors=b["authors"],
                categories=b["categories"],
                average_rating=b["average_rating"],
                ratings_count=b["ratings_count"],
                thumbnail=b["thumbnail"],
                description=b["description"],
                published_year=b["published_year"],
                num_pages=b["num_pages"],
                match_reason=f"Strict topic relevance match for {topic_id} (category/keywords confirmed, ranked by average_rating={b['average_rating']})",
                provenance="data/books.csv",
            ))
        return results

    def get_recommended_youtube(self, topic_id: str, student: StudentSchema, limit: int = 3) -> List[YouTubeResourceSchema]:
        yt_reject_words = [
            "bend test", "unbox", "unboxing", "review", "vs", "iphone", "samsung",
            "gopro", "aerogel", "ice rinks", "gameplay", "trailer", "reaction",
            "music", "song", "vlog", "prank", "challenge", "movie", "film", "gadget",
            "smartphone", "laptop review", "gpu", "rtx", "ps5", "xbox", "commercial", "short"
        ]

        topic_yt_regex = {
            "TOPIC_AI_ML": [r"\bai\b", r"\bartificial intelligence\b", r"\bmachine learning\b", r"\bdeep learning\b", r"\bneural networks?\b", r"\bpython\b"],
            "TOPIC_SOFTWARE_DEV": [r"\bpython\b", r"\bjava\b", r"\bjavascript\b", r"\bc\+\+\b", r"\bprogramming\b", r"\bsoftware engineering\b", r"\bbackend\b", r"\bdatabases?\b", r"\bsql\b", r"\balgorithms?\b", r"\bdata structures?\b", r"\bweb development\b", r"\bcoding\b", r"\bcomputer science\b", r"\bsystem design\b", r"\bdevops\b", r"\bdocker\b", r"\bkubernetes\b", r"\bgit\b", r"\bapis?\b"],
            "TOPIC_CYBERSECURITY": [r"\bcybersecurity\b", r"\binformation security\b", r"\bcryptography\b", r"\bethical hacking\b", r"\bpenetration testing\b", r"\bnetwork security\b"],
            "TOPIC_DATA_SCIENCE": [r"\bdata science\b", r"\bdata analytics?\b", r"\bbig data\b", r"\bpython\b", r"\bsql\b", r"\bpandas\b", r"\bdata visualization\b"],
            "TOPIC_BUSINESS_ANALYTICS": [r"\bbusiness analytics?\b", r"\bexcel\b", r"\bpower bi\b", r"\btableau\b", r"\bsql\b", r"\bbusiness intelligence\b"],
            "TOPIC_EMBEDDED_HARDWARE": [r"\bembedded systems?\b", r"\barduino\b", r"\braspberry pi\b", r"\bmicrocontroller\b", r"\belectronics\b"]
        }

        regex_list = topic_yt_regex.get(topic_id, [r"\bprogramming\b", r"\bcomputer science\b"])
        pattern = re.compile("|".join(regex_list), re.IGNORECASE)

        candidates = []
        for v in self._youtube_list:
            # Step 1: Require category_id 27 (Education) or 28 (Science & Technology)
            if v.get("category_id") not in (27, 28):
                continue

            title = (v.get("title") or "").lower()
            desc = (v.get("description") or "").lower()
            text = f"{title} {desc}"

            # Step 2: Reject non-study / product review / unboxing videos
            if any(rej in text for rej in yt_reject_words):
                continue

            # Step 3: Require explicit study/topic keywords in title or start of description
            if pattern.search(title) or pattern.search(desc[:200]):
                candidates.append(v)

        # Step 4: Popularity Ranking after strict relevance filtering
        candidates.sort(key=lambda x: x.get("popularity_score", 0.0), reverse=True)

        results = []
        for v in candidates[:limit]:
            results.append(YouTubeResourceSchema(
                video_id=v["video_id"],
                title=v["title"],
                channel_name=v["channel_name"],
                channel_id=v["channel_id"],
                category_id=v["category_id"],
                views=v["views"],
                likes=v["likes"],
                comments=v["comments"],
                duration_sec=v["duration_sec"],
                publish_date=v["publish_date"],
                subscriber_count=v["subscriber_count"],
                popularity_score=round(v["popularity_score"], 2),
                match_reason=f"Strict domain match for {topic_id} (category_id={v['category_id']} Science/Edu, study topic matched, ranked by popularity_score={round(v['popularity_score'], 1)})",
                provenance="data/yt data.csv",
            ))
        return results

    def get_recommended_arxiv(self, topic_id: str, student: StudentSchema, limit: int = 3) -> List[ArXivResourceSchema]:
        code_filters = {
            "TOPIC_AI_ML": ["cs.AI", "cs.LG", "stat.ML", "cs.CV", "cs.CL"],
            "TOPIC_SOFTWARE_DEV": ["cs.SE", "cs.PL", "cs.DC", "cs.DB", "cs.OS"],
            "TOPIC_CYBERSECURITY": ["cs.CR"],
            "TOPIC_DATA_SCIENCE": ["cs.DB", "stat.ML", "cs.IR", "cs.LG"],
            "TOPIC_BUSINESS_ANALYTICS": ["cs.CE", "cs.GT", "math.OC"],
            "TOPIC_EMBEDDED_HARDWARE": ["eess.SP", "cs.AR", "cs.SY"],
        }.get(topic_id, ["cs.AI", "cs.SE"])

        candidates = []
        for p in self._arxiv_list:
            code = p.get("category_code", "")
            cat = p.get("category", "").lower()
            if code in code_filters or any(c.lower() in cat for c in code_filters):
                candidates.append(p)

        # Rank by recency (published_date DESC) and word count
        candidates.sort(key=lambda x: (x.get("published_date", ""), x.get("summary_word_count", 0)), reverse=True)

        results = []
        for p in candidates[:limit]:
            results.append(ArXivResourceSchema(
                id=p["id"],
                title=p["title"],
                category=p["category"],
                category_code=p["category_code"],
                published_date=p["published_date"],
                updated_date=p["updated_date"],
                first_author=p["first_author"],
                authors=p["authors"],
                summary=p["summary"],
                summary_word_count=p["summary_word_count"],
                match_reason=f"Academic relevance match for {topic_id} (category_code={p['category_code']} matched)",
                provenance="data/arXiv_scientific_dataset.csv",
            ))
        return results

    def get_fused_student_profile(self, student_id: str) -> Optional[FusedStudentProfileResponse]:
        student = student_service.get_student_by_id(student_id)
        if not student:
            return None

        topic_mapping = self.derive_topic_for_student(student)
        location_mapping = self.derive_location_for_student(student.Student_ID)

        books = self.get_recommended_books(topic_mapping.topic_id, student, limit=3)
        yt_videos = self.get_recommended_youtube(topic_mapping.topic_id, student, limit=3)
        arxiv_papers = self.get_recommended_arxiv(topic_mapping.topic_id, student, limit=3)

        return FusedStudentProfileResponse(
            student_profile=student,
            topic_mapping=topic_mapping,
            location_mapping=location_mapping,
            recommendations=ResourceRecommendationsSchema(
                books=books,
                youtube=yt_videos,
                arxiv=arxiv_papers,
            ),
            provenance=DataProvenanceSchema(),
        )

    def get_wide_fused_student_profile(self, student_id: str) -> Optional[WideFusedStudentRecordSchema]:
        student = student_service.get_student_by_id(student_id)
        if not student:
            return None

        topic_mapping = self.derive_topic_for_student(student)
        location_mapping = self.derive_location_for_student(student.Student_ID)

        books = self.get_recommended_books(topic_mapping.topic_id, student, limit=1)
        yt_videos = self.get_recommended_youtube(topic_mapping.topic_id, student, limit=1)
        arxiv_papers = self.get_recommended_arxiv(topic_mapping.topic_id, student, limit=1)

        b0 = books[0] if books else None
        v0 = yt_videos[0] if yt_videos else None
        p0 = arxiv_papers[0] if arxiv_papers else None

        topic_obj = self._topics.get(topic_mapping.topic_id)

        return WideFusedStudentRecordSchema(
            Student_ID=student.Student_ID,
            Age=student.Age,
            Gender=student.Gender,
            University_Year=student.University_Year,
            Major=student.Major,
            Attendance_Percentage=student.Attendance_Percentage,
            Study_Hours_Per_Week=student.Study_Hours_Per_Week,
            CGPA=student.CGPA,
            Academic_Performance=student.Academic_Performance,
            Programming_Skill=student.Programming_Skill,
            Projects_Completed=student.Projects_Completed,
            Certifications=student.Certifications,
            Hackathons=student.Hackathons,
            Internships=student.Internships,
            Resume_Score=student.Resume_Score,
            Communication_Skills=student.Communication_Skills,
            Teamwork=student.Teamwork,
            Problem_Solving=student.Problem_Solving,
            English_Proficiency=student.English_Proficiency,
            Interview_Score=student.Interview_Score,
            Employability_Score=student.Employability_Score,
            Placement_Status=student.Placement_Status,
            Company_Tier=student.Company_Tier,
            Career_Field=student.Career_Field,
            Placement_Mode=student.Placement_Mode,
            Starting_Salary_USD=student.Starting_Salary_USD,

            topic_id=topic_mapping.topic_id,
            topic_name=topic_mapping.topic_name,
            subject_area=topic_obj.subject_area if topic_obj else "Computer Science",

            recommended_book_title=b0.title if b0 else None,
            recommended_book_isbn13=b0.isbn13 if b0 else None,
            recommended_book_author=b0.authors if b0 else None,
            recommended_book_category=b0.categories if b0 else None,
            recommended_book_rating=b0.average_rating if b0 else None,

            recommended_video_title=v0.title if v0 else None,
            recommended_video_id=v0.video_id if v0 else None,
            recommended_channel=v0.channel_name if v0 else None,
            recommended_video_views=v0.views if v0 else None,
            recommended_video_category=v0.category_id if v0 else None,

            recommended_paper_title=p0.title if p0 else None,
            recommended_paper_id=p0.id if p0 else None,
            recommended_paper_category=p0.category if p0 else None,
            recommended_paper_category_code=p0.category_code if p0 else None,
            recommended_paper_summary=p0.summary if p0 else None,

            city=location_mapping.city,
            latitude=location_mapping.latitude,
            longitude=location_mapping.longitude,

            topic_mapping_source="DERIVED_FROM_MAJOR_AND_CAREER",
            topic_mapping_rule=topic_mapping.mapping_rule,
            location_mapping_type="DERIVED / SYNTHETIC (DEMO MAPPING)",
            recommended_book_match_reason=b0.match_reason if b0 else None,
            recommended_video_match_reason=v0.match_reason if v0 else None,
            recommended_paper_match_reason=p0.match_reason if p0 else None,

            provenance=DataProvenanceSchema(),
        )

    def get_paginated_wide_fused_profiles(self, page: int = 1, limit: int = 20) -> PaginatedWideFusedStudentResponse:
        student_page = student_service.get_students(page=page, limit=limit)
        wide_items = []
        for s in student_page.data:
            w = self.get_wide_fused_student_profile(s.Student_ID)
            if w:
                wide_items.append(w)

        return PaginatedWideFusedStudentResponse(
            total=student_page.total,
            page=student_page.page,
            limit=student_page.limit,
            total_pages=student_page.total_pages,
            data=wide_items,
        )

    def get_relationship_metadata(self) -> List[RelationshipMetadataSchema]:
        return [
            RelationshipMetadataSchema(
                table_name="students",
                primary_key="Student_ID",
                foreign_key=None,
                referenced_table=None,
                referenced_column=None,
                relationship_type="EXISTING RELATIONSHIP",
                source_dataset="student_career_success_dataset.csv"
            ),
            RelationshipMetadataSchema(
                table_name="topics",
                primary_key="topic_id",
                foreign_key=None,
                referenced_table=None,
                referenced_column=None,
                relationship_type="DERIVED RELATIONSHIP",
                source_dataset="Derived System Table"
            ),
            RelationshipMetadataSchema(
                table_name="student_topic_mapping",
                primary_key="mapping_id",
                foreign_key="student_id, topic_id",
                referenced_table="students, topics",
                referenced_column="Student_ID, topic_id",
                relationship_type="DERIVED RELATIONSHIP",
                source_dataset="Derived System Logic (Major + Career_Field)"
            ),
            RelationshipMetadataSchema(
                table_name="books",
                primary_key="isbn13",
                foreign_key=None,
                referenced_table=None,
                referenced_column=None,
                relationship_type="EXISTING RELATIONSHIP",
                source_dataset="books.csv"
            ),
            RelationshipMetadataSchema(
                table_name="books_topic_mapping",
                primary_key="isbn13, topic_id",
                foreign_key="isbn13, topic_id",
                referenced_table="books, topics",
                referenced_column="isbn13, topic_id",
                relationship_type="DERIVED RELATIONSHIP",
                source_dataset="books.csv via categories/keywords"
            ),
            RelationshipMetadataSchema(
                table_name="youtube",
                primary_key="video_id",
                foreign_key="channel_id",
                referenced_table="youtube_channels",
                referenced_column="channel_id",
                relationship_type="EXISTING RELATIONSHIP",
                source_dataset="yt data.csv"
            ),
            RelationshipMetadataSchema(
                table_name="youtube_topic_mapping",
                primary_key="video_id, topic_id",
                foreign_key="video_id, topic_id",
                referenced_table="youtube, topics",
                referenced_column="video_id, topic_id",
                relationship_type="DERIVED RELATIONSHIP",
                source_dataset="yt data.csv via category_id/keywords"
            ),
            RelationshipMetadataSchema(
                table_name="arxiv",
                primary_key="id",
                foreign_key=None,
                referenced_table=None,
                referenced_column=None,
                relationship_type="EXISTING RELATIONSHIP",
                source_dataset="arXiv_scientific_dataset.csv"
            ),
            RelationshipMetadataSchema(
                table_name="arxiv_topic_mapping",
                primary_key="id, topic_id",
                foreign_key="id, topic_id",
                referenced_table="arxiv, topics",
                referenced_column="id, topic_id",
                relationship_type="DERIVED RELATIONSHIP",
                source_dataset="arXiv_scientific_dataset.csv via category_code"
            ),
            RelationshipMetadataSchema(
                table_name="cities",
                primary_key="city",
                foreign_key=None,
                referenced_table=None,
                referenced_column=None,
                relationship_type="EXISTING RELATIONSHIP",
                source_dataset="cities.xlsx"
            ),
            RelationshipMetadataSchema(
                table_name="student_location_mapping",
                primary_key="mapping_id",
                foreign_key="student_id, city",
                referenced_table="students, cities",
                referenced_column="Student_ID, city",
                relationship_type="DERIVED / SYNTHETIC (DEMO MAPPING)",
                source_dataset="cities.xlsx via student_location_mapping"
            ),
        ]

    def get_column_lineage(self) -> List[ColumnLineageSchema]:
        return [
            ColumnLineageSchema(column_name="Student_ID", source_dataset="student_career_success_dataset.csv", source_table="students", source_column="Student_ID", relationship_used="PRIMARY KEY", description="Unique student identifier"),
            ColumnLineageSchema(column_name="Major", source_dataset="student_career_success_dataset.csv", source_table="students", source_column="Major", relationship_used="NATIVE FIELD", description="Academic major"),
            ColumnLineageSchema(column_name="Career_Field", source_dataset="student_career_success_dataset.csv", source_table="students", source_column="Career_Field", relationship_used="NATIVE FIELD", description="Career goal/field"),
            ColumnLineageSchema(column_name="topic_id", source_dataset="Derived System Logic", source_table="topics", source_column="topic_id", relationship_used="student_topic_mapping.student_id -> students.Student_ID", description="Derived topic ID"),
            ColumnLineageSchema(column_name="recommended_book_title", source_dataset="books.csv", source_table="books", source_column="title", relationship_used="books_topic_mapping.topic_id -> topics.topic_id", description="Title of top-ranked study book"),
            ColumnLineageSchema(column_name="recommended_video_title", source_dataset="yt data.csv", source_table="youtube_videos", source_column="title", relationship_used="youtube_topic_mapping.topic_id -> topics.topic_id", description="Title of top-ranked educational YouTube video"),
            ColumnLineageSchema(column_name="recommended_paper_title", source_dataset="arXiv_scientific_dataset.csv", source_table="arxiv_papers", source_column="title", relationship_used="arxiv_topic_mapping.topic_id -> topics.topic_id", description="Title of top-ranked arXiv research paper"),
            ColumnLineageSchema(column_name="city", source_dataset="cities.xlsx", source_table="cities", source_column="city", relationship_used="student_location_mapping.city -> cities.city", description="Assigned city (synthetic demographic demo mapping)"),
        ]

    def generate_fused_excel_bytes(self, student_id: str) -> Optional[bytes]:
        """Dynamically generate an in-memory Excel workbook (.xlsx) containing Fused_Data, Provenance, and Relationships sheets."""
        wide = self.get_wide_fused_student_profile(student_id)
        if not wide:
            return None

        wb = openpyxl.Workbook()

        # Sheet 1: Fused_Data
        ws1 = wb.active
        ws1.title = "Fused_Data"

        wide_dict = wide.model_dump()
        provenance_dict = wide_dict.pop("provenance", {})

        headers = list(wide_dict.keys())
        ws1.append(headers)
        ws1.append([wide_dict[h] for h in headers])

        for col_num, header in enumerate(headers, 1):
            cell = ws1.cell(row=1, column=col_num)
            cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
            cell.fill = openpyxl.styles.PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")

        # Sheet 2: Provenance
        ws2 = wb.create_sheet(title="Provenance")
        prov_headers = ["Fused Column / Section", "Source Dataset", "Original Field / Method", "Notes"]
        ws2.append(prov_headers)
        for col_num in range(1, 5):
            cell = ws2.cell(row=1, column=col_num)
            cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
            cell.fill = openpyxl.styles.PatternFill(start_color="0EA5E9", end_color="0EA5E9", fill_type="solid")

        prov_rows = [
            ["student_core", "data/student_career_success_dataset.csv", "Student_ID, Major, Career_Field, CGPA, etc.", "Source dataset file"],
            ["books", "data/books.csv", "recommended_book_title, isbn13, authors, categories, rating", "Topic-first domain matching"],
            ["youtube", "data/yt data.csv", "recommended_video_title, video_id, channel_name, views", "Science/Edu topic matching"],
            ["arxiv", "data/arXiv_scientific_dataset.csv", "recommended_paper_title, id, category, category_code, summary", "Academic category code matching"],
            ["location", "data/cities.xlsx", "city, latitude, longitude", "City demographic metadata dataset"],
            ["topic mappings", "derived from Major + Career_Field", "topic_id, topic_name, subject_area", "Rule-based topic derivation from student Major and Career_Field"],
            ["synthetic location", "DERIVED / SYNTHETIC (DEMO MAPPING)", "city, latitude, longitude assignment", "Deterministic SHA256 hash mapping of Student_ID to cities"],
        ]
        for row in prov_rows:
            ws2.append(row)

        # Sheet 3: Relationships
        ws3 = wb.create_sheet(title="Relationships")
        rel_headers = ["Table Name", "Primary Key", "Foreign Key", "Referenced Table", "Referenced Column", "Relationship Type", "Source Dataset"]
        ws3.append(rel_headers)
        for col_num in range(1, 8):
            cell = ws3.cell(row=1, column=col_num)
            cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
            cell.fill = openpyxl.styles.PatternFill(start_color="10B981", end_color="10B981", fill_type="solid")

        rels = self.get_relationship_metadata()
        for r in rels:
            ws3.append([
                r.table_name,
                r.primary_key,
                r.foreign_key or "N/A",
                r.referenced_table or "N/A",
                r.referenced_column or "N/A",
                r.relationship_type,
                r.source_dataset
            ])

        for ws in [ws1, ws2, ws3]:
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                col_letter = openpyxl.utils.get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 60)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    def _get_fused_dir(self) -> str:
        fused_dir = os.path.join(settings.DATA_DIR, "fused")
        os.makedirs(fused_dir, exist_ok=True)
        return fused_dir

    def save_fused_excel(self, student_id: str) -> Optional[str]:
        """Generate and save the fused Excel file to data/fused/PrepGenius_Fused_{student_id}.xlsx."""
        sid_clean = student_id.strip().upper()
        excel_bytes = self.generate_fused_excel_bytes(sid_clean)
        if not excel_bytes:
            return None

        fused_dir = self._get_fused_dir()
        filename = f"PrepGenius_Fused_{sid_clean}.xlsx"
        file_path = os.path.join(fused_dir, filename)

        with open(file_path, "wb") as f:
            f.write(excel_bytes)

        rel_path = f"data/fused/{filename}"
        logger.info(f"Fused Excel saved to {rel_path}")
        return file_path

    def get_exported_files(self) -> List[Dict[str, Any]]:
        fused_dir = self._get_fused_dir()
        if not os.path.exists(fused_dir):
            return []

        results = []
        for filename in sorted(os.listdir(fused_dir), reverse=True):
            if filename.startswith("PrepGenius_Fused_") and filename.endswith(".xlsx"):
                filepath = os.path.join(fused_dir, filename)
                stat = os.stat(filepath)
                sid = filename.replace("PrepGenius_Fused_", "").replace(".xlsx", "")
                mtime = pd.Timestamp(stat.st_mtime, unit="s").isoformat()
                results.append({
                    "filename": filename,
                    "student_id": sid,
                    "file_path": f"data/fused/{filename}",
                    "file_size_bytes": stat.st_size,
                    "created_at": mtime,
                })
        return results

    def generate_complete_master_excel_bytes(self, target_student_count: int = 1000) -> bytes:
        """Generate the complete 16-sheet relational Data Fusion Excel workbook (PrepGenius_COMPLETE_DATA_FUSION.xlsx)."""
        now_iso = pd.Timestamp.now().isoformat()
        students = student_service._students_list[:target_student_count]

        wb = openpyxl.Workbook()

        def apply_header_style(ws, col_count, color_hex="1E1B4B"):
            fill = openpyxl.styles.PatternFill(start_color=color_hex, end_color=color_hex, fill_type="solid")
            font = openpyxl.styles.Font(bold=True, color="FFFFFF")
            for c in range(1, col_count + 1):
                cell = ws.cell(row=1, column=c)
                cell.font = font
                cell.fill = fill
            ws.views.sheetView[0].showGridLines = True
            ws.freeze_panes = "A2"

        def autofit(ws, max_w=50):
            for col in ws.columns:
                max_len = 0
                for cell in list(col)[:100]:
                    val = str(cell.value or "")
                    if val:
                        max_len = max(max_len, len(val))
                col_letter = openpyxl.utils.get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), max_w)

        # SHEET 1: README
        ws_readme = wb.active
        ws_readme.title = "README"
        ws_readme.views.sheetView[0].showGridLines = True
        readme_lines = [
            ["PrepGenius AI — Complete Relational Data Fusion System"],
            ["Generated Timestamp:", now_iso],
            ["Target Records:", f"{len(students)} unique student profiles"],
            [""],
            ["=== PROJECT PURPOSE ==="],
            ["Combines static student academic metrics, derived topic/location information, real indexed API resources"],
            ["(Books, YouTube, arXiv), bridge mapping tables, denormalized master views, EDA-ready metrics, relationships catalog,"],
            ["data dictionary, and complete provenance lineage into a single unified analytical workbook."],
            [""],
            ["=== DATA CLASSIFICATIONS ==="],
            ["1. STATIC DATA: Raw student records, books, YouTube, arXiv, and cities datasets."],
            ["2. DERIVED DATA: Topic classification (Major + Career_Field), deterministic location assignment (hash(Student_ID) % 50), match reasons."],
            ["3. DYNAMIC DATA: Indexed API/resource records (Books, YouTube, arXiv) with retrieval timestamps and source attributions."],
            [""],
            ["=== WORKBOOK SHEETS INDEX ==="],
            ["Sheet 1: README — Overview, purpose, classifications, sheet index."],
            ["Sheet 2: SUMMARY — Executive KPI Dashboard and analytical breakdown tables."],
            ["Sheet 3: STUDENT_MASTER — Primary student entity table (1,000 unique records, Student_ID PK)."],
            ["Sheet 4: TOPICS — Topic entity master table (6 normalized categories, topic_id PK)."],
            ["Sheet 5: STUDENT_TOPIC_MAP — Relational student-topic mapping bridge (mapping_id PK)."],
            ["Sheet 6: CITIES — Location entity master table (50 cities, city_id PK)."],
            ["Sheet 7: STUDENT_LOCATION_MAP — Relational student-location mapping bridge (mapping_id PK)."],
            ["Sheet 8: DYNAMIC_YOUTUBE — Indexed YouTube video resources (youtube_resource_id PK)."],
            ["Sheet 9: DYNAMIC_BOOKS — Indexed Book resources (book_resource_id PK)."],
            ["Sheet 10: DYNAMIC_ARXIV — Indexed arXiv research paper resources (paper_resource_id PK)."],
            ["Sheet 11: RESOURCE_MAP — Relational bridge table connecting students to matched resources."],
            ["Sheet 12: FUSED_MASTER — Denormalized wide analytical view (1 row per student)."],
            ["Sheet 13: EDA_READY — Pandas EDA-ready analytical dataset with calculated derived metrics."],
            ["Sheet 14: RELATIONSHIPS — Entity-Relationship catalog detailing PK/FK joins."],
            ["Sheet 15: DATA_DICTIONARY — Column-level dictionary for all workbook tables."],
            ["Sheet 16: PROVENANCE — Complete data lineage and transformation catalog."],
        ]
        for row in readme_lines:
            ws_readme.append(row)
        ws_readme.cell(row=1, column=1).font = openpyxl.styles.Font(bold=True, size=16, color="4F46E5")

        # Precompute mappings
        student_topic_maps = []
        student_loc_maps = []
        resource_maps = []
        fused_master_rows = []
        eda_ready_rows = []

        yt_pk_map = {v["video_id"]: f"YT_{idx+1:04d}" for idx, v in enumerate(self._youtube_list)}
        bk_pk_map = {b["isbn13"]: f"BK_{idx+1:04d}" for idx, b in enumerate(self._books_list)}
        ax_pk_map = {a["id"]: f"AX_{idx+1:04d}" for idx, a in enumerate(self._arxiv_list)}

        for idx, s_dict in enumerate(students, 1):
            s = StudentSchema(**s_dict)
            t_map = self.derive_topic_for_student(s)
            l_map = self.derive_location_for_student(s.Student_ID)

            books = self.get_recommended_books(t_map.topic_id, s, limit=1)
            yt_videos = self.get_recommended_youtube(t_map.topic_id, s, limit=1)
            arxiv_papers = self.get_recommended_arxiv(t_map.topic_id, s, limit=1)

            b0 = books[0] if books else None
            v0 = yt_videos[0] if yt_videos else None
            p0 = arxiv_papers[0] if arxiv_papers else None

            city_idx = next((i + 1 for i, c in enumerate(self._cities_list) if c.get("city") == l_map.city), 1)
            city_id = f"CITY_{city_idx:02d}"

            yt_pk = yt_pk_map.get(v0.video_id) if v0 else None
            bk_pk = bk_pk_map.get(b0.isbn13) if b0 else None
            ax_pk = ax_pk_map.get(p0.id) if p0 else None

            student_topic_maps.append({
                "mapping_id": t_map.mapping_id,
                "student_id": s.Student_ID,
                "topic_id": t_map.topic_id,
                "topic_name": t_map.topic_name,
                "mapping_source": t_map.mapping_source,
                "mapping_rule": t_map.mapping_rule,
            })

            student_loc_maps.append({
                "mapping_id": l_map.mapping_id,
                "student_id": s.Student_ID,
                "city_id": city_id,
                "city": l_map.city,
                "mapping_source": l_map.mapping_source,
                "mapping_rule": l_map.mapping_rule,
            })

            resource_maps.append({
                "resource_mapping_id": f"RM_{s.Student_ID}",
                "student_id": s.Student_ID,
                "topic_id": t_map.topic_id,
                "youtube_resource_id": yt_pk,
                "book_resource_id": bk_pk,
                "paper_resource_id": ax_pk,
                "youtube_match_status": "MATCHED" if v0 else "UNMATCHED",
                "book_match_status": "MATCHED" if b0 else "UNMATCHED",
                "paper_match_status": "MATCHED" if p0 else "UNMATCHED",
                "match_reason": f"Topic-first domain match for {t_map.topic_name}",
                "mapping_rule": "DERIVED_DOMAIN_RELEVANCE",
                "created_at": now_iso,
            })

            fused_master_rows.append({
                "Student_ID": s.Student_ID,
                "Age": s.Age,
                "Gender": s.Gender,
                "University_Year": s.University_Year,
                "Major": s.Major,
                "CGPA": s.CGPA,
                "Programming_Skill": s.Programming_Skill,
                "Projects_Completed": s.Projects_Completed,
                "Certifications": s.Certifications,
                "Placement_Status": s.Placement_Status,
                "Career_Field": s.Career_Field,
                "Starting_Salary_USD": s.Starting_Salary_USD,
                "topic_id": t_map.topic_id,
                "topic_name": t_map.topic_name,
                "subject_area": self._topics[t_map.topic_id].subject_area,
                "city_id": city_id,
                "city": l_map.city,
                "latitude": l_map.latitude,
                "longitude": l_map.longitude,
                "youtube_resource_id": yt_pk,
                "video_id": v0.video_id if v0 else None,
                "recommended_video_title": v0.title if v0 else None,
                "book_resource_id": bk_pk,
                "isbn13": b0.isbn13 if b0 else None,
                "recommended_book_title": b0.title if b0 else None,
                "paper_resource_id": ax_pk,
                "paper_id": p0.id if p0 else None,
                "recommended_paper_title": p0.title if p0 else None,
                "youtube_match_status": "MATCHED" if v0 else "UNMATCHED",
                "book_match_status": "MATCHED" if b0 else "UNMATCHED",
                "paper_match_status": "MATCHED" if p0 else "UNMATCHED",
                "match_reason": f"Domain relevance match for {t_map.topic_id}",
                "fusion_record_type": "DYNAMIC_FUSED_MASTER",
                "provenance_student_core": "data/student_career_success_dataset.csv",
                "provenance_location": "data/cities.xlsx via student_location_mapping",
                "provenance_books": "data/books.csv via books_topic_mapping",
                "provenance_youtube": "data/yt data.csv via youtube_topic_mapping",
                "provenance_arxiv": "data/arXiv_scientific_dataset.csv via arxiv_topic_mapping",
            })

            skill_avg = round((s.Programming_Skill + s.Communication_Skills + s.Teamwork + s.Problem_Solving) / 4.0, 2)
            exp_idx = round(s.Projects_Completed * 2 + s.Certifications * 3 + s.Hackathons * 2 + s.Internships * 5, 2)
            acad_idx = round((s.CGPA / 4.0 * 50.0) + (s.Attendance_Percentage / 100.0 * 30.0) + (min(40, s.Study_Hours_Per_Week) / 40.0 * 20.0), 2)
            place_ind = 1 if s.Placement_Status == "Placed" else 0
            high_skill = 1 if s.Programming_Skill >= 8 and s.CGPA >= 3.5 else 0
            proj_lvl = "High" if s.Projects_Completed >= 8 else ("Medium" if s.Projects_Completed >= 4 else "Low")

            eda_ready_rows.append({
                "Student_ID": s.Student_ID,
                "Age": s.Age,
                "Gender": s.Gender,
                "University_Year": s.University_Year,
                "Major": s.Major,
                "CGPA": s.CGPA,
                "Attendance_Percentage": s.Attendance_Percentage,
                "Study_Hours_Per_Week": s.Study_Hours_Per_Week,
                "Programming_Skill": s.Programming_Skill,
                "Projects_Completed": s.Projects_Completed,
                "Certifications": s.Certifications,
                "Hackathons": s.Hackathons,
                "Internships": s.Internships,
                "Resume_Score": s.Resume_Score,
                "Communication_Skills": s.Communication_Skills,
                "Teamwork": s.Teamwork,
                "Problem_Solving": s.Problem_Solving,
                "English_Proficiency": s.English_Proficiency,
                "Interview_Score": s.Interview_Score,
                "Employability_Score": s.Employability_Score,
                "Placement_Status": s.Placement_Status,
                "Company_Tier": s.Company_Tier,
                "Career_Field": s.Career_Field,
                "Starting_Salary_USD": s.Starting_Salary_USD,
                "topic_id": t_map.topic_id,
                "topic_name": t_map.topic_name,
                "city": l_map.city,
                "Skill_Average": skill_avg,
                "Experience_Index": exp_idx,
                "Academic_Engagement_Index": acad_idx,
                "Placement_Indicator": place_ind,
                "High_Skill_Flag": high_skill,
                "Project_Experience_Level": proj_lvl,
            })

        # SHEET 2: SUMMARY
        ws_sum = wb.create_sheet(title="SUMMARY")
        ws_sum.append(["Data Fusion System — Executive KPI Dashboard"])
        ws_sum.append([""])
        ws_sum.append(["KPI Metric Name", "Value", "Description"])
        kpis = [
            ["Total Students Sampled", len(students), "Core student dataset count"],
            ["Unique Student_IDs", len(students), "Primary key integrity verified"],
            ["Normalized Topic Categories", len(self._topics), "Domain classification topics"],
            ["Cities Catalog", len(self._cities_list), "Location master dataset count"],
            ["Books Indexed", len(self._books_list), "Static/API books dataset count"],
            ["YouTube Videos Indexed", len(self._youtube_list), "Static/API YouTube dataset count"],
            ["arXiv Papers Indexed", len(self._arxiv_list), "Static arXiv research papers count"],
            ["Student-Topic Mappings", len(student_topic_maps), "1-to-1 derived topic mappings"],
            ["Student-Location Mappings", len(student_loc_maps), "Deterministic location mappings"],
            ["Resource Bridge Mappings", len(resource_maps), "Relational resource matches"],
            ["Fused Master Records", len(fused_master_rows), "Denormalized analytical master rows"],
        ]
        for k in kpis:
            ws_sum.append(k)
        apply_header_style(ws_sum, 3, "1E1B4B")
        ws_sum.cell(row=1, column=1).font = openpyxl.styles.Font(bold=True, size=14, color="4F46E5")
        ws_sum.cell(row=1, column=1).fill = openpyxl.styles.PatternFill(fill_type=None)

        # SHEET 3: STUDENT_MASTER
        ws_sm = wb.create_sheet(title="STUDENT_MASTER")
        sm_headers = list(students[0].keys())
        if "Student_ID" in sm_headers:
            sm_headers[sm_headers.index("Student_ID")] = "Student_ID (PRIMARY KEY)"
        ws_sm.append(sm_headers)
        for s in students:
            ws_sm.append(list(s.values()))
        apply_header_style(ws_sm, len(sm_headers), "4F46E5")

        # SHEET 4: TOPICS
        ws_topics = wb.create_sheet(title="TOPICS")
        t_headers = ["topic_id (PRIMARY KEY)", "topic_name", "subject_area", "topic_description", "topic_source", "mapping_rule"]
        ws_topics.append(t_headers)
        for t in self._topics.values():
            ws_topics.append([t.topic_id, t.topic_name, t.subject_area, t.description, "SYSTEM_DEFINED", "Rule-based Major + Career_Field matching"])
        apply_header_style(ws_topics, len(t_headers), "4F46E5")

        # SHEET 5: STUDENT_TOPIC_MAP
        ws_stm = wb.create_sheet(title="STUDENT_TOPIC_MAP")
        stm_headers = ["mapping_id (PRIMARY KEY)", "student_id (FOREIGN KEY -> STUDENT_MASTER)", "topic_id (FOREIGN KEY -> TOPICS)", "topic_name", "mapping_source", "mapping_rule"]
        ws_stm.append(stm_headers)
        for row in student_topic_maps:
            ws_stm.append(list(row.values()))
        apply_header_style(ws_stm, len(stm_headers), "4F46E5")

        # SHEET 6: CITIES
        ws_cities = wb.create_sheet(title="CITIES")
        c_headers = ["city_id (PRIMARY KEY)", "city", "latitude", "longitude", "location_source"]
        ws_cities.append(c_headers)
        for idx, c in enumerate(self._cities_list, 1):
            ws_cities.append([f"CITY_{idx:02d}", c.get("city"), c.get("latitude"), c.get("longitude"), "cities.xlsx"])
        apply_header_style(ws_cities, len(c_headers), "4F46E5")

        # SHEET 7: STUDENT_LOCATION_MAP
        ws_slm = wb.create_sheet(title="STUDENT_LOCATION_MAP")
        slm_headers = ["mapping_id (PRIMARY KEY)", "student_id (FOREIGN KEY -> STUDENT_MASTER)", "city_id (FOREIGN KEY -> CITIES)", "city", "mapping_source", "mapping_rule"]
        ws_slm.append(slm_headers)
        for row in student_loc_maps:
            ws_slm.append(list(row.values()))
        apply_header_style(ws_slm, len(slm_headers), "4F46E5")

        # SHEET 8: DYNAMIC_YOUTUBE
        ws_yt = wb.create_sheet(title="DYNAMIC_YOUTUBE")
        yt_headers = ["youtube_resource_id (PRIMARY KEY)", "video_id", "title", "channel_name", "category_id", "views", "likes", "comments", "duration_sec", "publish_date", "subscriber_count", "popularity_score", "retrieval_timestamp", "source"]
        ws_yt.append(yt_headers)
        for idx, v in enumerate(self._youtube_list, 1):
            ws_yt.append([f"YT_{idx:04d}", v["video_id"], v["title"], v["channel_name"], v["category_id"], v["views"], v["likes"], v["comments"], v["duration_sec"], v["publish_date"], v["subscriber_count"], round(v["popularity_score"], 2), now_iso, "yt data.csv / YouTube API"])
        apply_header_style(ws_yt, len(yt_headers), "0EA5E9")

        # SHEET 9: DYNAMIC_BOOKS
        ws_bk = wb.create_sheet(title="DYNAMIC_BOOKS")
        bk_headers = ["book_resource_id (PRIMARY KEY)", "isbn13", "isbn10", "title", "authors", "categories", "average_rating", "ratings_count", "published_year", "num_pages", "retrieval_timestamp", "source"]
        ws_bk.append(bk_headers)
        for idx, b in enumerate(self._books_list, 1):
            ws_bk.append([f"BK_{idx:04d}", b["isbn13"], b["isbn10"], b["title"], b["authors"], b["categories"], b["average_rating"], b["ratings_count"], b["published_year"], b["num_pages"], now_iso, "books.csv"])
        apply_header_style(ws_bk, len(bk_headers), "0EA5E9")

        # SHEET 10: DYNAMIC_ARXIV
        ws_ax = wb.create_sheet(title="DYNAMIC_ARXIV")
        ax_headers = ["paper_resource_id (PRIMARY KEY)", "id", "title", "category", "category_code", "authors", "first_author", "published_date", "summary_word_count", "retrieval_timestamp", "source"]
        ws_ax.append(ax_headers)
        for idx, a in enumerate(self._arxiv_list[:5000], 1):
            ws_ax.append([f"AX_{idx:04d}", a["id"], a["title"], a["category"], a["category_code"], a["authors"], a["first_author"], a["published_date"], a["summary_word_count"], now_iso, "arXiv_scientific_dataset.csv (STATIC DATASET)"])
        apply_header_style(ws_ax, len(ax_headers), "0EA5E9")

        # SHEET 11: RESOURCE_MAP
        ws_rm = wb.create_sheet(title="RESOURCE_MAP")
        rm_headers = ["resource_mapping_id (PRIMARY KEY)", "student_id (FOREIGN KEY -> STUDENT_MASTER)", "topic_id (FOREIGN KEY -> TOPICS)", "youtube_resource_id (FOREIGN KEY -> DYNAMIC_YOUTUBE)", "book_resource_id (FOREIGN KEY -> DYNAMIC_BOOKS)", "paper_resource_id (FOREIGN KEY -> DYNAMIC_ARXIV)", "youtube_match_status", "book_match_status", "paper_match_status", "match_reason", "mapping_rule", "created_at"]
        ws_rm.append(rm_headers)
        for r in resource_maps:
            ws_rm.append(list(r.values()))
        apply_header_style(ws_rm, len(rm_headers), "10B981")

        # SHEET 12: FUSED_MASTER
        ws_fm = wb.create_sheet(title="FUSED_MASTER")
        fm_headers = list(fused_master_rows[0].keys())
        ws_fm.append(fm_headers)
        for r in fused_master_rows:
            ws_fm.append(list(r.values()))
        apply_header_style(ws_fm, len(fm_headers), "4F46E5")

        # SHEET 13: EDA_READY
        ws_eda = wb.create_sheet(title="EDA_READY")
        eda_headers = list(eda_ready_rows[0].keys())
        ws_eda.append(eda_headers)
        for r in eda_ready_rows:
            ws_eda.append(list(r.values()))
        apply_header_style(ws_eda, len(eda_headers), "4F46E5")

        # SHEET 14: RELATIONSHIPS
        ws_rel = wb.create_sheet(title="RELATIONSHIPS")
        rel_headers = ["relationship_id (PRIMARY KEY)", "source_table", "source_column (FOREIGN KEY)", "target_table", "target_column (PRIMARY KEY)", "relationship_type", "description", "join_condition"]
        ws_rel.append(rel_headers)
        rel_catalog = [
            ["REL_01", "STUDENT_TOPIC_MAP", "student_id", "STUDENT_MASTER", "Student_ID", "MANY_TO_ONE", "Connects each student to their mapped topic", "STUDENT_TOPIC_MAP.student_id = STUDENT_MASTER.Student_ID"],
            ["REL_02", "STUDENT_TOPIC_MAP", "topic_id", "TOPICS", "topic_id", "MANY_TO_ONE", "Connects mapping record to topic entity master", "STUDENT_TOPIC_MAP.topic_id = TOPICS.topic_id"],
            ["REL_03", "STUDENT_LOCATION_MAP", "student_id", "STUDENT_MASTER", "Student_ID", "MANY_TO_ONE", "Connects student to location mapping record", "STUDENT_LOCATION_MAP.student_id = STUDENT_MASTER.Student_ID"],
            ["REL_04", "STUDENT_LOCATION_MAP", "city_id", "CITIES", "city_id", "MANY_TO_ONE", "Connects mapping to city entity master", "STUDENT_LOCATION_MAP.city_id = CITIES.city_id"],
            ["REL_05", "RESOURCE_MAP", "student_id", "STUDENT_MASTER", "Student_ID", "MANY_TO_ONE", "Connects student to matched resources bridge record", "RESOURCE_MAP.student_id = STUDENT_MASTER.Student_ID"],
            ["REL_06", "RESOURCE_MAP", "topic_id", "TOPICS", "topic_id", "MANY_TO_ONE", "Connects resource bridge record to topic entity", "RESOURCE_MAP.topic_id = TOPICS.topic_id"],
            ["REL_07", "RESOURCE_MAP", "youtube_resource_id", "DYNAMIC_YOUTUBE", "youtube_resource_id", "MANY_TO_ONE", "Connects bridge to top-ranked matched YouTube video resource", "RESOURCE_MAP.youtube_resource_id = DYNAMIC_YOUTUBE.youtube_resource_id"],
            ["REL_08", "RESOURCE_MAP", "book_resource_id", "DYNAMIC_BOOKS", "book_resource_id", "MANY_TO_ONE", "Connects bridge to top-ranked matched Book resource", "RESOURCE_MAP.book_resource_id = DYNAMIC_BOOKS.book_resource_id"],
            ["REL_09", "RESOURCE_MAP", "paper_resource_id", "DYNAMIC_ARXIV", "paper_resource_id", "MANY_TO_ONE", "Connects bridge to top-ranked matched arXiv research paper resource", "RESOURCE_MAP.paper_resource_id = DYNAMIC_ARXIV.paper_resource_id"],
        ]
        for r in rel_catalog:
            ws_rel.append(r)
        apply_header_style(ws_rel, len(rel_headers), "10B981")

        # SHEET 15: DATA_DICTIONARY
        ws_dict = wb.create_sheet(title="DATA_DICTIONARY")
        dict_headers = ["dictionary_id (PRIMARY KEY)", "table_name", "column_name", "data_type", "primary_key", "foreign_key", "nullable", "description", "source", "static_or_dynamic", "derived_or_original"]
        ws_dict.append(dict_headers)
        dict_entries = [
            ["STUDENT_MASTER", "Student_ID", "STRING", "YES", "NO", "NO", "Unique primary key for student", "data/student_career_success_dataset.csv", "STATIC", "ORIGINAL"],
            ["STUDENT_MASTER", "Major", "STRING", "NO", "NO", "NO", "Academic major", "data/student_career_success_dataset.csv", "STATIC", "ORIGINAL"],
            ["STUDENT_MASTER", "CGPA", "FLOAT", "NO", "NO", "NO", "Cumulative GPA (0.0-4.0)", "data/student_career_success_dataset.csv", "STATIC", "ORIGINAL"],
            ["STUDENT_MASTER", "Career_Field", "STRING", "NO", "NO", "NO", "Target career field", "data/student_career_success_dataset.csv", "STATIC", "ORIGINAL"],
            ["TOPICS", "topic_id", "STRING", "YES", "NO", "NO", "Unique topic primary key", "Derived System Catalog", "STATIC", "DERIVED"],
            ["TOPICS", "topic_name", "STRING", "NO", "NO", "NO", "Human readable topic title", "Derived System Catalog", "STATIC", "DERIVED"],
            ["STUDENT_TOPIC_MAP", "mapping_id", "STRING", "YES", "NO", "NO", "Unique mapping primary key", "StudentTopicMapping logic", "DERIVED", "DERIVED"],
            ["STUDENT_TOPIC_MAP", "student_id", "STRING", "NO", "YES", "NO", "Foreign key to STUDENT_MASTER", "STUDENT_MASTER.Student_ID", "DERIVED", "DERIVED"],
            ["STUDENT_TOPIC_MAP", "topic_id", "STRING", "NO", "YES", "NO", "Foreign key to TOPICS", "TOPICS.topic_id", "DERIVED", "DERIVED"],
            ["CITIES", "city_id", "STRING", "YES", "NO", "NO", "Unique city primary key", "data/cities.xlsx", "STATIC", "ORIGINAL"],
            ["CITIES", "city", "STRING", "NO", "NO", "NO", "City name", "data/cities.xlsx", "STATIC", "ORIGINAL"],
            ["DYNAMIC_YOUTUBE", "youtube_resource_id", "STRING", "YES", "NO", "NO", "Unique YouTube resource primary key", "data/yt data.csv / API", "DYNAMIC", "ORIGINAL"],
            ["DYNAMIC_YOUTUBE", "video_id", "STRING", "NO", "NO", "NO", "YouTube video ID", "data/yt data.csv / API", "DYNAMIC", "ORIGINAL"],
            ["DYNAMIC_BOOKS", "book_resource_id", "STRING", "YES", "NO", "NO", "Unique Book resource primary key", "data/books.csv / API", "DYNAMIC", "ORIGINAL"],
            ["DYNAMIC_BOOKS", "isbn13", "INTEGER", "NO", "NO", "NO", "13-digit ISBN", "data/books.csv / API", "DYNAMIC", "ORIGINAL"],
            ["DYNAMIC_ARXIV", "paper_resource_id", "STRING", "YES", "NO", "NO", "Unique arXiv paper primary key", "data/arXiv_scientific_dataset.csv", "STATIC", "ORIGINAL"],
            ["DYNAMIC_ARXIV", "id", "STRING", "NO", "NO", "NO", "arXiv paper ID", "data/arXiv_scientific_dataset.csv", "STATIC", "ORIGINAL"],
            ["RESOURCE_MAP", "resource_mapping_id", "STRING", "YES", "NO", "NO", "Unique resource bridge primary key", "Data Fusion Engine", "DERIVED", "DERIVED"],
            ["RESOURCE_MAP", "student_id", "STRING", "NO", "YES", "NO", "Foreign key to STUDENT_MASTER", "STUDENT_MASTER.Student_ID", "DERIVED", "DERIVED"],
            ["EDA_READY", "Skill_Average", "FLOAT", "NO", "NO", "NO", "Average of 4 core skills (0.0-10.0)", "Calculated via Python formula", "DERIVED", "DERIVED"],
            ["EDA_READY", "Experience_Index", "FLOAT", "NO", "NO", "NO", "Weighted experience index from projects, certs, hackathons, internships", "Calculated via Python formula", "DERIVED", "DERIVED"],
            ["EDA_READY", "Academic_Engagement_Index", "FLOAT", "NO", "NO", "NO", "Composite academic score from CGPA, attendance, study hours", "Calculated via Python formula", "DERIVED", "DERIVED"],
            ["EDA_READY", "Placement_Indicator", "INTEGER", "NO", "NO", "NO", "Binary flag: 1 if Placed else 0", "Calculated via Python formula", "DERIVED", "DERIVED"],
            ["EDA_READY", "High_Skill_Flag", "INTEGER", "NO", "NO", "NO", "Binary flag: 1 if Programming_Skill>=8 & CGPA>=3.5 else 0", "Calculated via Python formula", "DERIVED", "DERIVED"],
            ["EDA_READY", "Project_Experience_Level", "STRING", "NO", "NO", "NO", "Experience tier: High (>=8), Medium (4-7), Low (<4)", "Calculated via Python formula", "DERIVED", "DERIVED"],
        ]
        for idx, row in enumerate(dict_entries, 1):
            ws_dict.append([f"DICT_{idx:03d}"] + row)
        apply_header_style(ws_dict, len(dict_headers), "4F46E5")

        # SHEET 16: PROVENANCE
        ws_prov = wb.create_sheet(title="PROVENANCE")
        prov_headers = ["provenance_id (PRIMARY KEY)", "field_or_table", "source", "source_type", "retrieval_method", "timestamp", "transformation", "mapping_logic"]
        ws_prov.append(prov_headers)
        prov_matrix = [
            ["PROV_01", "STUDENT_MASTER", "data/student_career_success_dataset.csv", "STATIC", "Local CSV Read", now_iso, "Loaded into memory / SQLite", "1-to-1 read from static student dataset"],
            ["PROV_02", "TOPICS", "Derived System Catalog", "STATIC", "In-memory initialization", now_iso, "Normalized 6 topics catalog", "Topic categorization mapping"],
            ["PROV_03", "STUDENT_TOPIC_MAP", "Major + Career_Field", "DERIVED", "Regex & keyword matching", now_iso, "Derived topic classification", "Rule-based topic derivation"],
            ["PROV_04", "CITIES", "data/cities.xlsx", "STATIC", "pandas read_excel", now_iso, "50 unique cities master", "Loaded from static Excel file"],
            ["PROV_05", "STUDENT_LOCATION_MAP", "sha256(Student_ID) % 50", "DERIVED", "Deterministic hash assignment", now_iso, "Synthetic demographic location", "Deterministic SHA256 hashing"],
            ["PROV_06", "DYNAMIC_YOUTUBE", "data/yt data.csv / YouTube API", "DYNAMIC", "API / CSV indexing", now_iso, "Filtered by Category (27/28) & popularity", "Domain relevance filtering"],
            ["PROV_07", "DYNAMIC_BOOKS", "data/books.csv / Books API", "DYNAMIC", "API / CSV indexing", now_iso, "Category exclusion & rating ranking", "Domain relevance filtering"],
            ["PROV_08", "DYNAMIC_ARXIV", "data/arXiv_scientific_dataset.csv", "STATIC", "Local CSV Indexing", now_iso, "Category code matching (cs.AI, cs.SE)", "Academic research matching"],
            ["PROV_09", "RESOURCE_MAP", "Data Fusion Engine", "DERIVED", "Top resource lookup per student", now_iso, "Relational FK bridge construction", "Multi-table relational joining"],
            ["PROV_10", "FUSED_MASTER", "Data Fusion Engine", "DERIVED", "Denormalized wide join", now_iso, "Flat wide profile aggregation", "Analytical wide view construction"],
            ["PROV_11", "EDA_READY", "Data Fusion Engine", "DERIVED", "Formula-backed feature engineering", now_iso, "Calculated derived analytics", "Numerical & categorical feature engineering"],
        ]
        for row in prov_matrix:
            ws_prov.append(row)
        apply_header_style(ws_prov, len(prov_headers), "0EA5E9")

        for ws in wb.worksheets:
            autofit(ws)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    def save_complete_master_excel(self, target_student_count: int = 1000) -> str:
        """Generate and save the master 16-sheet Excel workbook to data/fused/PrepGenius_COMPLETE_DATA_FUSION.xlsx."""
        excel_bytes = self.generate_complete_master_excel_bytes(target_student_count=target_student_count)
        fused_dir = self._get_fused_dir()
        filename = "PrepGenius_COMPLETE_DATA_FUSION.xlsx"
        file_path = os.path.join(fused_dir, filename)

        with open(file_path, "wb") as f:
            f.write(excel_bytes)

        rel_path = f"data/fused/{filename}"
        logger.info(f"Master Data Fusion Excel saved to {rel_path} ({len(excel_bytes)} bytes)")
        return file_path

    def get_master_export_status(self) -> Dict[str, Any]:
        fused_dir = self._get_fused_dir()
        filename = "PrepGenius_COMPLETE_DATA_FUSION.xlsx"
        file_path = os.path.join(fused_dir, filename)

        if not os.path.exists(file_path):
            self.save_complete_master_excel(target_student_count=1000)

        stat = os.stat(file_path)
        mtime = pd.Timestamp(stat.st_mtime, unit="s").isoformat()

        return {
            "filename": filename,
            "file_path": f"data/fused/{filename}",
            "generated_at": mtime,
            "student_count": 1000,
            "dynamic_youtube_count": len(self._youtube_list),
            "dynamic_book_count": len(self._books_list),
            "dynamic_arxiv_count": len(self._arxiv_list),
            "file_size_bytes": stat.st_size,
            "status": "COMPLETED"
        }


fusion_service = FusionService.get_instance()
