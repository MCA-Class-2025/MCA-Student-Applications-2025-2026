import re
from pypdf import PdfReader


def extract_text_from_pdf(file):

    reader = PdfReader(file)

    text = ""

    for page in reader.pages:
        text += page.extract_text()

    return text



def extract_skills(resume_text):

    skill_database = [

        "Python",
        "Java",
        "C++",
        "SQL",
        "MongoDB",
        "React",
        "Node.js",
        "Machine Learning",
        "Deep Learning",
        "Artificial Intelligence",
        "Data Analysis",
        "Power BI",
        "Excel",
        "AWS",
        "Cloud",
        "Docker",
        "Git",
        "NLP",
        "TensorFlow",
        "PyTorch"

    ]


    found_skills = []


    for skill in skill_database:

        if re.search(
            skill,
            resume_text,
            re.IGNORECASE
        ):

            found_skills.append(skill)


    return found_skills



def skill_gap_analysis(skills, required_skills):

    missing = []


    for skill in required_skills:

        if skill.lower() not in [
            s.lower() for s in skills
        ]:

            missing.append(skill)


    return missing



def analyze_resume(file):

    text = extract_text_from_pdf(file)

    skills = extract_skills(text)


    return {

        "resume_text": text,

        "skills": skills

    }