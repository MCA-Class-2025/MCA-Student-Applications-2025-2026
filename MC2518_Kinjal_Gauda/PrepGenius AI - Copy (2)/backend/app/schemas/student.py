from typing import List, Optional
from pydantic import BaseModel, Field


class StudentSchema(BaseModel):
    Student_ID: str = Field(..., description="Unique student identifier (Primary Key)")
    Age: int = Field(..., description="Age of the student")
    Gender: str = Field(..., description="Gender (Male, Female, Other)")
    University_Year: str = Field(..., description="Year in university (Freshman, Sophomore, Junior, Senior)")
    Major: str = Field(..., description="Academic major")
    Attendance_Percentage: int = Field(..., description="Class attendance percentage (0-100)")
    Study_Hours_Per_Week: int = Field(..., description="Weekly study hours")
    CGPA: float = Field(..., description="Cumulative Grade Point Average (0.00-4.00)")
    Academic_Performance: str = Field(..., description="Academic performance category (Good, Average, Poor, Excellent)")
    Programming_Skill: int = Field(..., description="Programming skill score (1-10)")
    Projects_Completed: int = Field(..., description="Number of completed projects")
    Certifications: int = Field(..., description="Number of certifications completed")
    Hackathons: int = Field(..., description="Number of hackathons participated in")
    GitHub_Profile: str = Field(..., description="Has GitHub profile (Yes/No)")
    Internships: int = Field(..., description="Number of internships completed")
    Leadership_Experience: str = Field(..., description="Has leadership experience (Yes/No)")
    LinkedIn_Profile: str = Field(..., description="Has LinkedIn profile (Yes/No)")
    Resume_Score: int = Field(..., description="Resume score (0-100)")
    Communication_Skills: int = Field(..., description="Communication skill score (1-10)")
    Teamwork: int = Field(..., description="Teamwork score (1-10)")
    Problem_Solving: int = Field(..., description="Problem solving score (1-10)")
    English_Proficiency: str = Field(..., description="English proficiency level (Basic, Intermediate, Advanced)")
    Interview_Score: int = Field(..., description="Interview score (0-100)")
    Employability_Score: float = Field(..., description="Calculated employability index score")
    Placement_Status: str = Field(..., description="Placement status (Placed, Not Placed)")
    Company_Tier: str = Field(..., description="Company tier if placed (Tier 1, Tier 2, Tier 3, No Company)")
    Career_Field: str = Field(..., description="Career field or domain")
    Placement_Mode: str = Field(..., description="Placement channel/mode")
    Starting_Salary_USD: int = Field(..., description="Starting salary in USD")

    class Config:
        json_schema_extra = {
            "example": {
                "Student_ID": "ST000001",
                "Age": 22,
                "Gender": "Male",
                "University_Year": "Sophomore",
                "Major": "Computer Science",
                "Attendance_Percentage": 86,
                "Study_Hours_Per_Week": 21,
                "CGPA": 3.28,
                "Academic_Performance": "Good",
                "Programming_Skill": 9,
                "Projects_Completed": 10,
                "Certifications": 1,
                "Hackathons": 6,
                "GitHub_Profile": "Yes",
                "Internships": 5,
                "Leadership_Experience": "No",
                "LinkedIn_Profile": "No",
                "Resume_Score": 100,
                "Communication_Skills": 9,
                "Teamwork": 7,
                "Problem_Solving": 8,
                "English_Proficiency": "Advanced",
                "Interview_Score": 72,
                "Employability_Score": 231.7,
                "Placement_Status": "Placed",
                "Company_Tier": "Tier 1",
                "Career_Field": "Backend Developer",
                "Placement_Mode": "Campus Placement",
                "Starting_Salary_USD": 72082
            }
        }


class PaginatedStudentResponse(BaseModel):
    total: int = Field(..., description="Total records matching criteria")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total pages available")
    data: List[StudentSchema] = Field(..., description="List of student records")
