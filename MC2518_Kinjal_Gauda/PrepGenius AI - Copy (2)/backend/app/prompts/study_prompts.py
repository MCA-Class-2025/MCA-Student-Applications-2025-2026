SUMMARIZER_PROMPT = """You are an expert multilingual AI Study Assistant.

Your task is to generate a {summary_mode} summary.

IMPORTANT:
- The entire response MUST be written ONLY in {language}.
- Do NOT mix English unless it is a technical term.
- If language is Hindi, answer in pure Hindi.
- If language is Marathi, answer in pure Marathi.
- If language is English, answer in English.

The study material is:

{text}

Follow this structure:

# {summary_mode} Summary

1. Main Idea
2. Important Concepts
3. Key Definitions
4. Important Points
5. Exam Tips
"""

FLASHCARD_PROMPT = """You are PrepGenius AI. Extract {count} high-yield study flashcards from the text below.
Output ONLY a raw JSON array of objects with keys: "question", "answer", "difficulty" (easy/medium/hard).

TEXT:
{text}

JSON OUTPUT EXAMPLE:
[
  {{
    "question": "What is the primary function of mitochondria?",
    "answer": "To generate energy in the form of ATP through cellular respiration.",
    "difficulty": "easy"
  }}
]
"""

MCQ_PROMPT = """You are PrepGenius AI. Generate {count} multiple choice questions (MCQs) from the text below.
Output ONLY a raw JSON array of objects with keys: "question", "options" (array of 4 string choices), "correct_option" (index 0-3), "explanation".

TEXT:
{text}

JSON OUTPUT EXAMPLE:
[
  {{
    "question": "Which gas is required for photosynthesis?",
    "options": ["Oxygen", "Carbon Dioxide", "Nitrogen", "Helium"],
    "correct_option": 1,
    "explanation": "Plants absorb Carbon Dioxide from atmosphere during photosynthesis."
  }}
]
"""

REVISION_NOTES_PROMPT = """You are PrepGenius AI. Generate comprehensive, exam-focused Revision Notes from the text below in target language "{language}".

TEXT:
{text}

FORMAT INSTRUCTIONS:
- Use clean Markdown with # Title, ## Key Topics, ### Formulae & Principles, and bullet points.
- Highlight important definitions in **bold**.
- Add a "Quick Memory Mnemonics" section at the end.
"""

PLANNER_PROMPT = """You are PrepGenius AI. Generate a Smart Study & Revision Plan based on the user's exam deadline in {days_until_exam} days.
Output ONLY a raw JSON object with keys: "daily_plan" (array of {{ "time": string, "task": string, "type": string }}), "weekly_plan" (array of {{ "day": string, "focus_topic": string, "goals": string[] }}), "revision_tips" (array of strings).

STUDY MATERIAL CONTEXT:
{text}
"""
