export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'error';
  app_name: string;
  version: string;
  database_connected: boolean;
  ollama_connected: boolean;
  ollama_model: string;
  system_info: {
    environment: string;
    max_upload_size_mb: number;
    allowed_extensions: string[];
  };
}

export type ActiveTab = 
  | 'dashboard'
  | 'chat'
  | 'summarizer'
  | 'flashcards'
  | 'mcqs'
  | 'planner'
  | 'analytics'
  | 'fusion';

export interface UserProfile {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  created_at: string;
}

export interface WideFusedStudentProfile {
  Student_ID: string;
  Age: number;
  Gender: string;
  University_Year: string;
  Major: string;
  Attendance_Percentage: number;
  Study_Hours_Per_Week: number;
  CGPA: number;
  Academic_Performance: string;
  Programming_Skill: number;
  Projects_Completed: number;
  Certifications: number;
  Hackathons: number;
  Internships: number;
  Resume_Score: number;
  Communication_Skills: number;
  Teamwork: number;
  Problem_Solving: number;
  English_Proficiency: string;
  Interview_Score: number;
  Employability_Score: number;
  Placement_Status: string;
  Company_Tier: string;
  Career_Field: string;
  Placement_Mode: string;
  Starting_Salary_USD: number;

  topic_id: string;
  topic_name: string;
  subject_area: string;

  recommended_book_title?: string;
  recommended_book_isbn13?: number;
  recommended_book_author?: string;
  recommended_book_category?: string;
  recommended_book_rating?: number;

  recommended_video_title?: string;
  recommended_video_id?: string;
  recommended_channel?: string;
  recommended_video_views?: number;
  recommended_video_category?: number;

  recommended_paper_title?: string;
  recommended_paper_id?: string;
  recommended_paper_category?: string;
  recommended_paper_category_code?: string;
  recommended_paper_summary?: string;

  city: string;
  latitude: number;
  longitude: number;

  provenance: {
    student_core: string;
    location: string;
    book: string;
    youtube: string;
    arxiv: string;
  };
}
