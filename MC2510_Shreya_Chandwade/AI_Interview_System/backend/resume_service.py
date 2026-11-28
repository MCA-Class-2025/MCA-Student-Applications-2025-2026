import io
import re
from typing import Dict, List, Any

# Common technical skill taxonomy
SKILL_TAXONOMY = [
    # Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang",
    "rust", "ruby", "php", "swift", "kotlin", "sql", "html", "css", "r", "scala",
    # Frameworks & Libraries
    "react", "angular", "vue", "next.js", "node.js", "express", "django", "flask",
    "fastapi", "spring", "spring boot", "pandas", "numpy", "scikit-learn",
    "tensorflow", "pytorch", "keras", "bootstrap", "tailwind",
    # Databases & Tools
    "postgresql", "mysql", "mongodb", "sqlite", "redis", "elasticsearch",
    "git", "docker", "kubernetes", "aws", "azure", "gcp", "linux", "jira",
    "jenkins", "ci/cd", "rest api", "graphql", "microservices", "agile",
    # Domains
    "machine learning", "deep learning", "artificial intelligence", "data science",
    "web development", "full stack", "frontend", "backend", "devops", "cybersecurity",
    "cloud computing", "system design", "data structures", "algorithms"
]

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract plain text from uploaded PDF file bytes using PyPDF."""
    text = ""
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    except Exception as exc:
        print("PyPDF extraction notice:", exc)

    # Fallback text cleanup if pypdf extracts raw streams
    if not text.strip():
        try:
            # Simple string extraction heuristic for plain text embedded in streams
            decoded = file_bytes.decode("utf-8", errors="ignore")
            clean_lines = re.findall(r"[\x20-\x7E]{4,}", decoded)
            text = "\n".join(clean_lines)
        except Exception:
            text = ""

    return text.strip()

def extract_skills_from_resume(text: str, db_session=None) -> Dict[str, Any]:
    """Extract technical skills, inferred job role, and experience metrics from resume text."""
    if not text:
        return {
            "text_preview": "",
            "skills": [],
            "inferred_role": "Software Developer",
            "experience_years": "1-2 years",
            "detected_keywords": []
        }

    text_lower = text.lower()

    # Match skills against taxonomy
    found_skills = []
    for skill in SKILL_TAXONOMY:
        # Match whole word or exact skill phrase
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found_skills.append(skill.title() if len(skill) <= 4 else skill.capitalize())

    found_skills = list(dict.fromkeys(found_skills))

    # Infer candidate target role
    inferred_role = "Software Engineer"
    if any(k in text_lower for k in ["data scientist", "machine learning", "deep learning", "nlp", "pandas"]):
        inferred_role = "Data Scientist / ML Engineer"
    elif any(k in text_lower for k in ["full stack", "react", "node", "django"]):
        inferred_role = "Full Stack Developer"
    elif any(k in text_lower for k in ["frontend", "react", "vue", "angular", "css", "html"]):
        inferred_role = "Frontend Developer"
    elif any(k in text_lower for k in ["backend", "python", "java", "fastapi", "spring"]):
        inferred_role = "Backend Developer"
    elif any(k in text_lower for k in ["devops", "aws", "docker", "kubernetes", "ci/cd"]):
        inferred_role = "DevOps / Cloud Engineer"
    elif any(k in text_lower for k in ["android", "ios", "react native", "flutter", "swift", "kotlin"]):
        inferred_role = "Mobile App Developer"

    # Infer experience years
    years_match = re.search(r"(\d+)\+?\s*years?\s*(?:of)?\s*experience", text_lower)
    if years_match:
        exp_years = f"{years_match.group(1)}+ years"
    else:
        exp_years = "1-3 years"

    # Preview snippet
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    preview = "\n".join(lines[:6]) if lines else ""

    return {
        "text_preview": preview,
        "skills": found_skills if found_skills else ["Python", "Problem Solving", "Software Architecture"],
        "inferred_role": inferred_role,
        "experience_years": exp_years,
        "detected_keywords": found_skills[:10]
    }

def generate_resume_questions(resume_text: str, skills: List[str], job_role: str, db=None) -> List[Dict[str, Any]]:
    """Generate personalized interview questions based on candidate's uploaded resume."""
    try:
        try:
            from backend.ai_service import _call_openai
            from backend.rag_service import get_rag_engine
        except ModuleNotFoundError:
            from ai_service import _call_openai
            from rag_service import get_rag_engine

        skills_str = ", ".join(skills) if isinstance(skills, list) else str(skills)

        rag_context = ""
        try:
            rag = get_rag_engine(db)
            rag_context = rag.get_job_role_context(job_role, skills_str)
        except Exception as exc:
            print("Notice: RAG context for resume questions:", exc)

        prompt = f"""
You are an expert technical recruiter and hiring manager.
Generate 5 personalized interview questions based on the candidate's resume content and skills.

Target Job Role: {job_role}
Extracted Skills: {skills_str}

Resume Content Snippet:
{resume_text[:1200]}

Relevant Knowledge Base Context (RAG):
{rag_context[:800] if rag_context else "N/A"}

Generate 5 specific questions:
- 2 Technical questions directly testing the candidate's listed skills and tools
- 2 Project/Experience questions based on their resume background
- 1 HR/Behavioral question tailored to their career trajectory

Respond in JSON format:
[
  {{"text": "Question 1", "type": "text", "category": "technical", "ideal_answer": "Expected ideal answer explanation"}},
  ...
]
"""
        result = _call_openai(
            "question_generation",
            "You generate tailored interview questions from candidate resumes.",
            prompt,
            temperature=0.7
        )

        if result:
            import json
            json_match = re.search(r"\[.*\]", result, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                if isinstance(parsed, list) and len(parsed) >= 3:
                    return parsed
    except Exception as exc:
        print("Notice: AI resume question generation notice:", exc)

    # Fallback personalized resume question generator
    skills_list = skills if isinstance(skills, list) else [s.strip() for s in str(skills).split(",") if s.strip()]
    primary_skill = skills_list[0] if skills_list else "software development"
    secondary_skill = skills_list[1] if len(skills_list) > 1 else "problem solving"

    return [
        {
            "text": f"Walk me through a project on your resume where you used {primary_skill}. What challenges did you face?",
            "type": "text",
            "category": "project",
            "ideal_answer": f"A strong answer outlines project goals, the role of {primary_skill}, technical trade-offs made, and specific measurable outcomes achieved."
        },
        {
            "text": f"How do you implement best practices and optimize performance when working with {primary_skill}?",
            "type": "text",
            "category": "technical",
            "ideal_answer": f"Should discuss profiling, caching, clean architecture, automated testing, and language/tool specific optimizations for {primary_skill}."
        },
        {
            "text": f"Explain how you integrated {secondary_skill} into your software workflow as mentioned in your experience.",
            "type": "text",
            "category": "technical",
            "ideal_answer": f"Detailed explanation of integration patterns, API boundaries, error handling, and reliability when leveraging {secondary_skill}."
        },
        {
            "text": f"Describe a situation in your previous experience where you had to debug a complex production issue under tight deadlines.",
            "type": "text",
            "category": "experience",
            "ideal_answer": "Uses the STAR method to describe systematic log analysis, isolating the root cause, deploying a hotfix, and adding regression tests."
        },
        {
            "text": f"Why are you seeking a {job_role} position at this stage of your career, and how does your background prepare you for it?",
            "type": "text",
            "category": "hr",
            "ideal_answer": f"Demonstrates clear alignment between their past hands-on experience in {primary_skill} and the responsibilities of a {job_role}."
        }
    ]
