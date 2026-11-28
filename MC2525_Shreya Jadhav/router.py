"""Route chat messages without mistaking a question for a symptom report."""

import re


GREETINGS = {
    "hi", "hello", "hey", "hii", "hiya", "yo", "good morning",
    "good afternoon", "good evening",
}
CASUAL = {
    "thanks", "thank you", "bye", "goodbye", "see you",
    "how are you", "who are you", "what can you do",
}

SYMPTOM_WORDS = re.compile(
    r"\b(?:pain|cramps?|bleeding|periods?|cycles?|pcos|spotting|"
    r"fever|fatigue|nausea|vomiting|dizz(?:y|iness)|stress|sleep|flow|"
    r"pads?|tampons?|soak(?:ing|ed|s)?)\b",
    re.IGNORECASE,
)
PERSONAL_REPORT = re.compile(
    r"\b(?:i (?:have|had|feel|felt|experience|experienced|"
    r"am (?:having|bleeding|soaking|in pain)|was diagnosed with)|"
    r"i'm (?:having|bleeding|soaking|in pain)|i've (?:had|been bleeding)|"
    r"my (?:pain|periods?|cycles?|flow|bleeding|stress|sleep|"
    r"pads?|tampons?|diagnosis|doctor))\b",
    re.IGNORECASE,
)
DIAGNOSIS_QUESTION = re.compile(
    r"\b(?:can|could|do|did|might|may|would|should|if)\s+i\s+have\s+pcos\b|"
    r"\bis it possible (?:that )?i have pcos\b",
    re.IGNORECASE,
)


def route(question: str) -> str:
    q = question.strip()
    lower = q.lower()
    if lower in GREETINGS:
        return "greeting"
    if lower in CASUAL:
        return "conversation"
    if DIAGNOSIS_QUESTION.search(q) and not re.search(
        r"\b(?:my pain|my bleeding|i have (?:severe|sudden|heavy))\b", q, re.IGNORECASE
    ):
        return "knowledge"
    if PERSONAL_REPORT.search(q) and SYMPTOM_WORDS.search(q):
        return "clinical"
    return "knowledge"
