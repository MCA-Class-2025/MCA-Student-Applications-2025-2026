from fastapi import FastAPI
from pydantic import BaseModel
from typing import List


app = FastAPI(
    title="AI Career Guidance API",
    description="Internal APIs for Career Guidance Assistant",
    version="1.0"
)


# ====================================================
# API 1 — CAREER RECOMMENDATION
# ====================================================

class CareerRequest(BaseModel):

    education: str
    skills: List[str]
    interests: List[str]


@app.post("/api/career-recommendation")
def career_recommendation(data: CareerRequest):

    recommendations = []

    skills = [
        skill.lower()
        for skill in data.skills
    ]

    interests = [
        interest.lower()
        for interest in data.interests
    ]

    if (
        "python" in skills
        and (
            "data science" in interests
            or "artificial intelligence" in interests
        )
    ):

        recommendations.append(
            "Data Scientist"
        )

    if "react" in skills:

        recommendations.append(
            "Frontend Developer"
        )

    if "javascript" in skills:

        recommendations.append(
            "Web Developer"
        )

    if "sql" in skills:

        recommendations.append(
            "Data Analyst"
        )

    if "cloud computing" in interests:

        recommendations.append(
            "Cloud Engineer"
        )

    if "cyber security" in interests:

        recommendations.append(
            "Cyber Security Analyst"
        )

    if not recommendations:

        recommendations.append(
            "Software Developer"
        )

    return {
        "success": True,
        "recommendations": recommendations
    }


# ====================================================
# API 2 — SKILL GAP ANALYSIS
# ====================================================

class SkillGapRequest(BaseModel):

    current_skills: List[str]
    target_role: str


@app.post("/api/skill-gap")
def skill_gap(data: SkillGapRequest):

    role_skills = {

        "data scientist": [
            "Python",
            "SQL",
            "Machine Learning",
            "Statistics",
            "Pandas",
            "NumPy"
        ],

        "frontend developer": [
            "HTML",
            "CSS",
            "JavaScript",
            "React",
            "Git"
        ],

        "backend developer": [
            "Python",
            "Java",
            "SQL",
            "REST API",
            "Git"
        ],

        "data analyst": [
            "SQL",
            "Excel",
            "Python",
            "Power BI",
            "Statistics"
        ],

        "cloud engineer": [
            "Linux",
            "AWS",
            "Docker",
            "Networking",
            "Git"
        ]
    }

    required = role_skills.get(
        data.target_role.lower(),
        []
    )

    current = [
        skill.lower()
        for skill in data.current_skills
    ]

    missing = [
        skill
        for skill in required
        if skill.lower() not in current
    ]

    return {

        "success": True,

        "target_role": data.target_role,

        "required_skills": required,

        "current_skills": data.current_skills,

        "missing_skills": missing,

        "skill_gap_count": len(missing)

    }



# ====================================================
# API 3 — RESUME ANALYSIS
# ====================================================

class ResumeRequest(BaseModel):
    resume_text: str


@app.post("/api/resume-analysis")
def resume_analysis(data: ResumeRequest):

    skill_list = [
        "Python",
        "Java",
        "JavaScript",
        "TypeScript",
        "React",
        "Next.js",
        "SQL",
        "HTML",
        "CSS",
        "Machine Learning",
        "Deep Learning",
        "AWS",
        "Docker",
        "Git",
        "GitHub",
        "Power BI",
        "Excel",
        "Node.js",
        "MongoDB",
        "PostgreSQL",
        "FastAPI",
        "LangChain"
    ]

    text = data.resume_text.lower()

    detected_skills = []

    for skill in skill_list:

        if skill.lower() in text:
            detected_skills.append(skill)

    return {
        "success": True,
        "skills_detected": detected_skills,
        "skill_count": len(detected_skills),
        "message": "Resume analyzed successfully."
    }

# ====================================================
# API 4 — INTERVIEW QUESTIONS
# ====================================================

class InterviewRequest(BaseModel):

    role: str
    difficulty: str = "Beginner"


@app.post("/api/interview-questions")
def interview_questions(
    data: InterviewRequest
):

    questions = {

        "python developer": [

            "What is Python?",

            "What are Python lists and tuples?",

            "What is a dictionary in Python?",

            "What are Python functions?",

            "What is exception handling?"
        ],

        "frontend developer": [

            "What is HTML?",

            "What is CSS?",

            "What is JavaScript?",

            "What is React?",

            "What are React components?"
        ],

        "data analyst": [

            "What is SQL?",

            "What is data cleaning?",

            "What is data visualization?",

            "What is a JOIN in SQL?",

            "What is Power BI?"
        ],

        "data scientist": [

            "What is Machine Learning?",

            "What is supervised learning?",

            "What is overfitting?",

            "What is regression?",

            "What is classification?"
        ]
    }

    result = questions.get(
        data.role.lower(),
        [
            "Tell me about yourself.",

            "What are your technical skills?",

            "Explain one of your projects.",

            "What are your strengths?",

            "Why should we hire you?"
        ]
    )

    return {

        "success": True,

        "role": data.role,

        "difficulty": data.difficulty,

        "questions": result

    }


# ====================================================
# API 5 — CAREER ROADMAP
# ====================================================

class RoadmapRequest(BaseModel):

    role: str


@app.post("/api/career-roadmap")
def career_roadmap(data: RoadmapRequest):

    roadmaps = {

        "frontend developer": [

            "HTML & CSS",

            "JavaScript",

            "React",

            "Git & GitHub",

            "Build Projects",

            "Practice DSA",

            "Prepare for Interviews"
        ],

        "data scientist": [

            "Python",

            "Statistics",

            "Pandas & NumPy",

            "Machine Learning",

            "Data Visualization",

            "Build ML Projects",

            "Practice Interviews"
        ],

        "data analyst": [

            "Excel",

            "SQL",

            "Python",

            "Power BI",

            "Statistics",

            "Data Visualization",

            "Build Portfolio"
        ],

        "cloud engineer": [

            "Linux",

            "Networking",

            "AWS",

            "Docker",

            "Kubernetes",

            "Cloud Projects",

            "Cloud Certification"
        ]
    }

    roadmap = roadmaps.get(
        data.role.lower(),
        [

            "Learn Programming",

            "Learn Data Structures",

            "Learn Git & GitHub",

            "Build Projects",

            "Practice Coding",

            "Prepare Resume",

            "Practice Interviews"
        ]
    )

    return {

        "success": True,

        "role": data.role,

        "roadmap": roadmap

    }