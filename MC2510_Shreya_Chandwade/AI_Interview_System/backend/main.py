import os
from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from pydantic import BaseModel
from sqlalchemy.orm import Session

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

try:
    from backend.database import engine, get_db
    from backend.models import Base, User, Interview, InterviewAnswer
    from backend.migrate import run_migrations
    from backend.auth import (
        hash_password,
        verify_password,
        create_access_token,
        decode_access_token
    )
    from backend.ai_service import (
        generate_interview_questions,
        generate_multi_round_interview,
        evaluate_answer,
        evaluate_coding_answer,
        analyze_sentiment_and_confidence,
        generate_study_plan,
        analyze_skill_gaps,
        generate_interview_feedback_summary,
        generate_interview_report,
        get_ideal_answer,
    )
    from backend.resume_service import (
        extract_text_from_pdf,
        extract_skills_from_resume,
        generate_resume_questions,
    )
    from backend.fused_dataset_service import fused_dataset_service
except ModuleNotFoundError:
    from database import engine, get_db
    from models import Base, User, Interview, InterviewAnswer
    from migrate import run_migrations
    from auth import (
        hash_password,
        verify_password,
        create_access_token,
        decode_access_token
    )
    from ai_service import (
        generate_interview_questions,
        generate_multi_round_interview,
        evaluate_answer,
        evaluate_coding_answer,
        analyze_sentiment_and_confidence,
        generate_study_plan,
        analyze_skill_gaps,
        generate_interview_feedback_summary,
        generate_interview_report,
        get_ideal_answer,
    )
    from resume_service import (
        extract_text_from_pdf,
        extract_skills_from_resume,
        generate_resume_questions,
    )
    from fused_dataset_service import fused_dataset_service


# =========================================================
# DATABASE
# =========================================================

Base.metadata.create_all(bind=engine)
run_migrations(engine)


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="AI Interview Preparation & Mock Interview System",
    description="AI-powered interview preparation system using LLM",
    version="1.0.0"
)


# =========================================================
# FRONTEND STATIC FILES
# =========================================================

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static"
)


@app.on_event("startup")
def startup_event():
    try:
        try:
            from backend.database import SessionLocal
        except ModuleNotFoundError:
            from database import SessionLocal

        try:
            from backend.seed import seed_dataset
        except ModuleNotFoundError:
            from seed import seed_dataset

        db = SessionLocal()
        try:
            seed_dataset(db)
        finally:
            db.close()
    except Exception as exc:
        print("Error during startup database seeding:", exc)



# =========================================================
# PYDANTIC MODELS
# =========================================================


class RegisterRequest(BaseModel):

    name: str

    email: str

    password: str


class LoginRequest(BaseModel):

    email: str

    password: str


class InterviewRequest(BaseModel):

    job_role: str

    skills: str

    experience: str = ""

    interview_mode: str = "text"

    multi_round: bool = True

    difficulty: str = ""

    question_count: int = 0


class AnswerRequest(BaseModel):

    job_role: str = ""

    question: str

    answer: str

    question_type: str = "text"

    ideal_answer_hint: str = ""


class ResumeQuestionsRequest(BaseModel):

    resume_text: str

    skills: list = []

    job_role: str = "Software Developer"


class CodingAnswerRequest(BaseModel):

    job_role: str = ""

    question: str

    code: str

    test_cases: list = []


class SentimentRequest(BaseModel):

    answer: str


class SkillAnalysisRequest(BaseModel):

    job_role: str

    skills: str

    experience: str = ""


class InterviewFeedbackRequest(BaseModel):

    job_role: str = ""

    skills: str = ""

    overall_score: float = 0

    answers: list = []


class StudyPlanRequest(BaseModel):

    job_role: str = "Software Developer"

    weak_topics: str = ""

    score: float = 0.0


# =========================================================
# HELPER FUNCTIONS
# =========================================================


def get_current_user(
    authorization: str | None,
    db: Session
):

    if not authorization:

        raise HTTPException(
            status_code=401,
            detail="Authentication required."
        )

    auth_str = authorization.strip()

    if auth_str.lower().startswith("bearer "):
        token = auth_str[7:].strip()
    else:
        token = auth_str

    if not token:

        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header."
        )


    try:

        payload = decode_access_token(token)

        user_id = payload.get("user_id")

        if not user_id:

            raise HTTPException(
                status_code=401,
                detail="Invalid token."
            )

    except HTTPException:

        raise

    except Exception:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token."
        )


    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )


    if not user:

        raise HTTPException(
            status_code=401,
            detail="User not found."
        )


    return user


def extract_score(evaluation: str) -> float:

    """
    Extract a score such as Score: 8/10 from the AI evaluation.
    Returns a value on a 0-100 scale.
    """

    import re

    if not evaluation:
        return 0.0

    match = re.search(
        r"Score\s*:\s*(\d+(?:\.\d+)?)\s*/\s*10",
        evaluation,
        re.IGNORECASE
    )

    if not match:
        return 0.0

    score = float(match.group(1))
    return round(score * 10, 2)


def normalize_score(raw_score) -> float:

    """Convert interview scores to a consistent 0-100 scale."""

    try:
        score = float(raw_score) if raw_score is not None else 0.0
    except (ValueError, TypeError):
        return 0.0

    if score <= 10:
        score *= 10

    return round(max(0.0, min(score, 100.0)), 2)


# =========================================================
# HOME PAGE
# =========================================================


@app.get("/")
def home():

    return FileResponse(
        os.path.join(FRONTEND_DIR, "index.html")
    )


# =========================================================
# LOGIN PAGE
# =========================================================


@app.get("/login")
def login_page():

    return FileResponse(
        os.path.join(FRONTEND_DIR, "login.html")
    )


# =========================================================
# REGISTER PAGE
# =========================================================


@app.get("/register")
def register_page():

    return FileResponse(
        os.path.join(FRONTEND_DIR, "register.html")
    )


# =========================================================
# DASHBOARD PAGE
# =========================================================


@app.get("/dashboard")
def dashboard_page():

    return FileResponse(
        os.path.join(FRONTEND_DIR, "dashboard.html")
    )


@app.get("/fused-dataset")
def fused_dataset_page():
    return FileResponse(
        os.path.join(FRONTEND_DIR, "fused_dataset.html")
    )


@app.get("/interview")
def interview_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "interview.html"))


@app.get("/feedback")
def feedback_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "feedback.html"))


@app.get("/analytics")
def analytics_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "analytics.html"))


@app.get("/plan")
def study_plan_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "plan.html"))


@app.get("/fusion")
def fusion_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "fusion.html"))


# =========================================================
# HEALTH CHECK
# =========================================================


@app.get("/health")
def health_check():

    return {
        "status": "ok",
        "message": "AI Interview System is running."
    }


@app.get("/fusion-status")
def fusion_status(db: Session = Depends(get_db)):
    try:
        try:
            from backend.rag_service import get_rag_engine
        except ModuleNotFoundError:
            from rag_service import get_rag_engine
        return get_rag_engine(db).fusion_status
    except Exception as exc:
        print("Fusion status error:", exc)
        raise HTTPException(status_code=500, detail="Fusion status unavailable.")


# =========================================================
# REGISTER
# =========================================================


@app.post("/register")
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):

    # Check empty values

    if not data.name.strip():

        raise HTTPException(
            status_code=400,
            detail="Name is required."
        )


    if not data.email.strip():

        raise HTTPException(
            status_code=400,
            detail="Email is required."
        )


    if len(data.password) < 6:

        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 6 characters."
        )


    # Check existing user

    existing_user = (
        db.query(User)
        .filter(
            User.email == data.email.lower().strip()
        )
        .first()
    )


    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Email already registered."
        )


    # Create user

    user = User(

        name=data.name.strip(),

        email=data.email.lower().strip(),

        password=hash_password(
            data.password
        )

    )


    db.add(user)

    db.commit()

    db.refresh(user)


    return {

        "message":
            "Registration successful.",

        "user_id":
            user.id

    }


# =========================================================
# LOGIN
# =========================================================


@app.post("/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(
            User.email ==
            data.email.lower().strip()
        )
        .first()
    )


    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )


    if not verify_password(
        data.password,
        user.password
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )


    token = create_access_token(
        user.id
    )


    return {

        "message":
            "Login successful.",

        "token":
            token,

        "user": {

            "id":
                user.id,

            "name":
                user.name,

            "email":
                user.email

        }

    }


# =========================================================
# RESUME UPLOAD & PROCESSING
# =========================================================


@app.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF resume file.",
        )

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be under 5 MB.")

    resume_text = extract_text_from_pdf(file_bytes)
    if not resume_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from PDF. Ensure the PDF contains selectable text.",
        )

    profile = extract_skills_from_resume(resume_text, db)

    return {
        "message": "Resume processed successfully.",
        "filename": file.filename,
        "text_length": len(resume_text),
        "text_preview": profile["text_preview"],
        "skills": profile["skills"],
        "inferred_role": profile["inferred_role"],
        "experience_years": profile["experience_years"],
        "detected_keywords": profile["detected_keywords"],
        "resume_text": resume_text[:3000],
    }


@app.post("/generate-resume-questions")
def generate_questions_from_resume(
    data: ResumeQuestionsRequest,
    db: Session = Depends(get_db),
):
    if not data.resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume text is required.")

    skills = data.skills if data.skills else []
    job_role = data.job_role.strip() or "Software Developer"

    try:
        question_list = generate_resume_questions(
            resume_text=data.resume_text,
            skills=skills,
            job_role=job_role,
            db=db,
        )

        rounds = [{
            "round": 1,
            "name": "Resume-Based Interview",
            "type": "resume",
            "description": "Personalized questions from your uploaded resume",
            "questions": [
                {
                    "text": q.get("text", ""),
                    "type": q.get("type", "text"),
                    "round": 1,
                    "round_name": "Resume-Based",
                    "category": q.get("category", "technical"),
                    "ideal_answer": q.get("ideal_answer", ""),
                }
                for q in question_list
            ],
        }]

        all_questions = rounds[0]["questions"]

        return {
            "total_rounds": 1,
            "interview_mode": "text",
            "source": "resume",
            "rounds": rounds,
            "questions": all_questions,
            "total_questions": len(all_questions),
        }

    except Exception as e:
        print("Resume question generation error:", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate resume questions: {str(e)}",
        )


@app.post("/ideal-answer")
def fetch_ideal_answer(
    data: AnswerRequest,
    db: Session = Depends(get_db),
):
    if not data.question.strip():
        raise HTTPException(status_code=400, detail="Question is required.")

    ideal = get_ideal_answer(
        db=db,
        question=data.question,
        job_role=data.job_role,
        stored_ideal=data.ideal_answer_hint,
    )

    return {"ideal_answer": ideal}


# =========================================================
# GENERATE INTERVIEW QUESTIONS
# =========================================================


@app.post("/generate-questions")
def generate_questions(
    data: InterviewRequest,
    db: Session = Depends(get_db)
):

    if not data.job_role.strip():

        raise HTTPException(
            status_code=400,
            detail="Job role is required."
        )


    if not data.skills.strip():

        raise HTTPException(
            status_code=400,
            detail="Skills are required."
        )


    try:

        if data.multi_round:
            result = generate_multi_round_interview(
                db=db,
                job_role=data.job_role,
                skills=data.skills,
                experience=data.experience,
                interview_mode=data.interview_mode,
                difficulty=data.difficulty,
                max_questions=data.question_count,
            )
            return result

        questions = generate_interview_questions(

            db=db,

            job_role=data.job_role,

            skills=data.skills,

            experience=data.experience

        )


        return {

            "questions":
                questions

        }


    except Exception as e:

        print(
            "Question generation error:",
            str(e)
        )


        raise HTTPException(

            status_code=500,

            detail=
                f"Failed to generate questions: {str(e)}"

        )


# =========================================================
# EVALUATE ANSWER
# =========================================================


@app.post("/evaluate-answer")
def evaluate_candidate_answer(
    data: AnswerRequest,
    db: Session = Depends(get_db)
):

    if not data.question.strip():

        raise HTTPException(
            status_code=400,
            detail="Question is required."
        )


    if not data.answer.strip():

        raise HTTPException(
            status_code=400,
            detail="Answer is required."
        )


    try:

        evaluation = evaluate_answer(

            db=db,

            job_role=data.job_role,

            question=data.question,

            answer=data.answer

        )

        sentiment = analyze_sentiment_and_confidence(data.answer)

        score = extract_score(
            evaluation
        )

        if data.question_type in ("text", "voice") and sentiment:
            evaluation += (
                f"\n\nCommunication Analysis:\n"
                f"Sentiment: {sentiment['sentiment_label']} ({sentiment['sentiment_score']}%)\n"
                f"Confidence: {sentiment['confidence_score']}%"
            )

        ideal_answer = get_ideal_answer(
            db=db,
            question=data.question,
            job_role=data.job_role,
            stored_ideal=data.ideal_answer_hint,
            evaluation=evaluation,
        )

        return {

            "evaluation":
                evaluation,

            "score":
                score,

            "sentiment": sentiment,

            "ideal_answer": ideal_answer,

        }


    except Exception as e:

        print(
            "Evaluation error:",
            str(e)
        )


        raise HTTPException(

            status_code=500,

            detail=
                f"Failed to evaluate answer: {str(e)}"

        )


# =========================================================
# EVALUATE CODING ANSWER
# =========================================================


@app.post("/evaluate-coding")
def evaluate_coding_submission(
    data: CodingAnswerRequest,
    db: Session = Depends(get_db)
):

    if not data.question.strip():
        raise HTTPException(status_code=400, detail="Question is required.")

    if not data.code.strip():
        raise HTTPException(status_code=400, detail="Code is required.")

    try:
        result = evaluate_coding_answer(
            question=data.question,
            code=data.code,
            test_cases=data.test_cases,
            job_role=data.job_role,
        )

        sentiment = analyze_sentiment_and_confidence(
            f"Code submission for: {data.question}"
        )

        ideal_answer = get_ideal_answer(
            db=db,
            question=data.question,
            job_role=data.job_role,
            evaluation=result["evaluation"],
        )

        return {
            "evaluation": result["evaluation"],
            "score": result["score"],
            "tests_passed": result["tests_passed"],
            "tests_total": result["tests_total"],
            "sentiment": sentiment,
            "ideal_answer": ideal_answer,
        }

    except Exception as e:
        print("Coding evaluation error:", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to evaluate code: {str(e)}"
        )


# =========================================================
# SENTIMENT ANALYSIS
# =========================================================


@app.post("/analyze-sentiment")
def analyze_sentiment(data: SentimentRequest):

    if not data.answer.strip():
        raise HTTPException(status_code=400, detail="Answer text is required.")

    try:
        result = analyze_sentiment_and_confidence(data.answer)
        return result

    except Exception as e:
        print("Sentiment analysis error:", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze sentiment: {str(e)}"
        )


# =========================================================
# SKILL GAP ANALYSIS (API 5)
# =========================================================


@app.post("/analyze-skills")
def analyze_skills(data: SkillAnalysisRequest):

    if not data.job_role.strip():
        raise HTTPException(status_code=400, detail="Job role is required.")

    if not data.skills.strip():
        raise HTTPException(status_code=400, detail="Skills are required.")

    try:
        analysis = analyze_skill_gaps(
            job_role=data.job_role,
            skills=data.skills,
            experience=data.experience
        )

        return {"analysis": analysis}

    except Exception as e:
        print("Skill analysis error:", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze skills: {str(e)}"
        )


# =========================================================
# INTERVIEW FEEDBACK SUMMARY (API 4)
# =========================================================


@app.post("/interview-feedback")
def interview_feedback(data: InterviewFeedbackRequest):

    try:
        feedback = generate_interview_feedback_summary(
            job_role=data.job_role,
            skills=data.skills,
            overall_score=data.overall_score,
            answers=data.answers
        )

        return {"feedback": feedback}

    except Exception as e:
        print("Interview feedback error:", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate feedback: {str(e)}"
        )


# =========================================================
# GENERATE RAG INTERVIEW REPORT
# =========================================================

class ReportRequest(BaseModel):
    job_role: str = ""
    skills: str = ""
    experience: str = ""
    answers: list = []


@app.post("/generate-interview-report")
def generate_report_endpoint(
    data: ReportRequest,
    db: Session = Depends(get_db)
):
    try:
        report = generate_interview_report(
            interview_data={
                "job_role": data.job_role,
                "skills": data.skills,
                "experience": data.experience,
                "answers": data.answers,
            },
            db=db
        )
        return report
    except Exception as e:
        print("Report generation error:", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate report: {str(e)}"
        )



# =========================================================
# SAVE COMPLETED INTERVIEW
# =========================================================


class SaveInterviewRequest(BaseModel):

    result_id: str = ""

    job_role: str

    skills: str

    experience: str = ""

    interview_mode: str = "text"

    total_rounds: int = 3

    answers: list

    feedback: str = ""

    skill_gap: str = ""

    performance: str = ""

    difficulty: str = ""


@app.post("/save-interview")
def save_interview(
    data: SaveInterviewRequest,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db)
):

    user = get_current_user(
        authorization,
        db
    )


    if not data.answers:

        raise HTTPException(
            status_code=400,
            detail="No interview answers found."
        )


    # Calculate overall score

    scores = []


    for item in data.answers:
        scores.append(normalize_score(item.get("score", 0)))


    if scores:

        overall_score = round(
            sum(scores) / len(scores),
            2
        )

    else:

        overall_score = 0.0


    # Create interview

    interview = Interview(

        user_id=user.id,

        job_role=data.job_role,

        skills=data.skills,

        experience=data.experience,

        overall_score=overall_score,

        interview_mode=data.interview_mode,

        difficulty=(data.difficulty or "").strip().lower(),

        total_rounds=data.total_rounds,

        current_round=data.total_rounds

    )


    db.add(interview)

    db.commit()

    db.refresh(interview)


    # Save answers

    for item in data.answers:

        score = normalize_score(item.get("score", 0))

        answer_record = InterviewAnswer(

            interview_id=interview.id,

            question=item.get(
                "question",
                ""
            ),

            answer=item.get(
                "answer",
                ""
            ),

            evaluation=item.get(
                "evaluation",
                ""
            ),

            score=score,

            question_type=item.get("question_type", "text"),

            round_number=item.get("round", 1),

            sentiment_score=item.get("sentiment_score"),

            confidence_score=item.get("confidence_score"),

            sentiment_label=item.get("sentiment_label"),

        )


        db.add(
            answer_record
        )


    db.commit()

    try:
        fused_record = fused_dataset_service.append_interview({
            "interview_id": data.result_id.strip() or interview.id,
            "job_role": data.job_role,
            "skills": data.skills,
            "answers": data.answers,
            "feedback": data.feedback,
            "skill_gap": data.skill_gap,
            "performance": data.performance,
            "difficulty": data.difficulty,
            "total_marks": len(data.answers) * 100,
            "percentage": overall_score,
        })
    except (OSError, ValueError) as exc:
        print("Fused dataset append error:", str(exc))
        raise HTTPException(
            status_code=500,
            detail="Interview saved, but the fused dataset could not be updated."
        )

    return {

        "message":
            "Interview saved successfully.",

        "interview_id":
            interview.id,

        "overall_score":
            overall_score,

        "fused_dataset_record": fused_record

    }


@app.get("/api/fused-dataset")
def get_fused_dataset(
    search: str = "",
    source: str = "",
    job_role: str = "",
    sort: str = "date_desc",
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    get_current_user(authorization, db)
    try:
        records = fused_dataset_service.list_records(search, source, job_role, sort)
        return {"records": records, "count": len(records)}
    except (OSError, ValueError) as exc:
        print("Fused dataset read error:", str(exc))
        raise HTTPException(status_code=500, detail="Fused dataset unavailable.")


@app.get("/api/fused-dataset/stats")
def get_fused_dataset_stats(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
):
    get_current_user(authorization, db)
    try:
        return fused_dataset_service.stats()
    except (OSError, ValueError) as exc:
        print("Fused dataset stats error:", str(exc))
        raise HTTPException(status_code=500, detail="Fused dataset statistics unavailable.")


# =========================================================
# PERFORMANCE DASHBOARD
# =========================================================


@app.get("/dashboard-data")
def dashboard_data(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db)
):

    user = get_current_user(
        authorization,
        db
    )


    interviews = (
        db.query(Interview)
        .filter(
            Interview.user_id ==
            user.id
        )
        .order_by(
            Interview.created_at.desc()
        )
        .all()
    )


    total_interviews = len(
        interviews
    )


    interview_history = []


    for interview in interviews:

        interview_history.append({

            "id":
                interview.id,

            "job_role":
                interview.job_role,

            "skills":
                interview.skills,

            "experience":
                interview.experience,

            "score":
                normalize_score(interview.overall_score),

            "interview_mode":
                interview.interview_mode or "text",

            "difficulty":
                interview.difficulty or "",

            "questions_answered":
                len(interview.answers),

            "total_rounds":
                interview.total_rounds or 3,

            "date":
                interview.created_at.strftime(
                    "%Y-%m-%d %H:%M"
                ) if interview.created_at else ""

        })


    normalized_scores = [
        normalize_score(interview.overall_score)
        for interview in interviews
    ]


    if normalized_scores:

        average_score = round(
            sum(normalized_scores) / len(normalized_scores),
            2
        )

        best_score = max(normalized_scores)

    else:

        average_score = 0
        best_score = 0


    questions_completed = sum(len(interview.answers) for interview in interviews)

    skill_totals = {}
    difficulty_totals = {}

    for interview in interviews:
        score = normalize_score(interview.overall_score)
        for skill in [part.strip() for part in (interview.skills or "").split(",") if part.strip()]:
            bucket = skill_totals.setdefault(skill, {"total": 0.0, "count": 0})
            bucket["total"] += score
            bucket["count"] += 1

        level = (interview.difficulty or "").strip() or "Not recorded"
        bucket = difficulty_totals.setdefault(level, {"total": 0.0, "count": 0})
        bucket["total"] += score
        bucket["count"] += 1

    skill_scores = [
        {
            "skill": skill,
            "average": round(values["total"] / values["count"], 2),
            "count": values["count"],
        }
        for skill, values in skill_totals.items()
    ]
    skill_scores.sort(key=lambda item: item["average"])

    difficulty_scores = [
        {
            "difficulty": level,
            "average": round(values["total"] / values["count"], 2),
            "count": values["count"],
        }
        for level, values in difficulty_totals.items()
    ]


    return {

        "user": {

            "id":
                user.id,

            "name":
                user.name,

            "email":
                user.email

        },

        "total_interviews":
            total_interviews,

        "average_score":
            average_score,

        "best_score":
            best_score,

        "questions_completed":
            questions_completed,

        "skill_scores":
            skill_scores,

        "difficulty_scores":
            difficulty_scores,

        "interviews":
            interview_history

    }


# =========================================================
# INTERVIEW DETAILS
# =========================================================


@app.get("/interview/{interview_id}")
def interview_details(
    interview_id: int,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db)
):

    user = get_current_user(
        authorization,
        db
    )


    interview = (
        db.query(Interview)
        .filter(
            Interview.id ==
            interview_id,

            Interview.user_id ==
            user.id
        )
        .first()
    )


    if not interview:

        raise HTTPException(
            status_code=404,
            detail="Interview not found."
        )


    answers_list = [
        {
            "question": answer.question,
            "answer": answer.answer,
            "evaluation": answer.evaluation,
            "score": answer.score,
            "question_type": answer.question_type or "text",
            "round": answer.round_number or 1,
            "sentiment_score": answer.sentiment_score,
            "confidence_score": answer.confidence_score,
            "sentiment_label": answer.sentiment_label,
        }
        for answer in interview.answers
    ]

    report = generate_interview_report(
        interview_data={
            "job_role": interview.job_role,
            "skills": interview.skills,
            "experience": interview.experience or "",
            "answers": answers_list
        },
        db=db
    )

    return {
        "id": interview.id,
        "job_role": interview.job_role,
        "skills": interview.skills,
        "experience": interview.experience,
        "overall_score": interview.overall_score,
        "interview_mode": interview.interview_mode or "text",
        "total_rounds": interview.total_rounds or 3,
        "date": interview.created_at.strftime("%Y-%m-%d %H:%M") if interview.created_at else "",
        "answers": answers_list,
        "report": report
    }


# =========================================================
# PERSONALIZED STUDY PLAN
# =========================================================


@app.get("/study-plan")
def study_plan(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db)
):

    user = get_current_user(
        authorization,
        db
    )


    interviews = (
        db.query(Interview)
        .filter(
            Interview.user_id ==
            user.id
        )
        .order_by(
            Interview.created_at.desc()
        )
        .limit(5)
        .all()
    )


    if not interviews:

        return {

            "study_plan":
                "Complete at least one mock interview first. Your AI study plan will be generated from your performance."
        }


    # Collect answers from recent interviews

    topic_scores = {}


    for interview in interviews:

        for answer in interview.answers:

            topic = interview.job_role

            if topic not in topic_scores:

                topic_scores[topic] = []


            topic_scores[topic].append(
                normalize_score(answer.score)
            )


    # Overall score

    all_scores = []


    for interview in interviews:

        for answer in interview.answers:

            all_scores.append(
                normalize_score(answer.score)
            )


    if all_scores:

        current_score = round(

            sum(all_scores)
            / len(all_scores),

            2

        )

    else:

        current_score = 0


    weak_topics = []


    # Use job roles as a basic topic grouping

    for topic, scores in topic_scores.items():

        average = sum(scores) / len(scores)

        if average < 70:

            weak_topics.append(
                f"{topic} ({average:.1f}%)"
            )


    if not weak_topics:

        weak_topics.append(
            "Continue practicing technical and behavioral interview questions"
        )


    latest_job_role = interviews[0].job_role


    try:

        plan = generate_study_plan(

            job_role=latest_job_role,

            weak_topics=", ".join(
                weak_topics
            ),

            score=current_score

        )


        return {

            "job_role":
                latest_job_role,

            "current_score":
                current_score,

            "weak_topics":
                weak_topics,

            "study_plan":
                plan

        }


    except Exception as e:

        print(
            "Study plan error:",
            str(e)
        )


        raise HTTPException(

            status_code=500,

            detail=
                f"Failed to generate study plan: {str(e)}"

        )


@app.post("/study-plan")
@app.post("/generate-study-plan")
def generate_custom_study_plan(data: StudyPlanRequest):
    try:
        plan = generate_study_plan(
            job_role=data.job_role,
            weak_topics=data.weak_topics,
            score=data.score
        )
        return {
            "job_role": data.job_role,
            "current_score": data.score,
            "weak_topics": data.weak_topics.split(", ") if data.weak_topics else [],
            "study_plan": plan
        }
    except Exception as e:
        print("Study plan generation error:", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate study plan: {str(e)}"
        )