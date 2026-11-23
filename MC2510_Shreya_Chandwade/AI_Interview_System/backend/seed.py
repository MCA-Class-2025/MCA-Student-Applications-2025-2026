import json
from sqlalchemy.orm import Session

try:
    from backend.models import QuestionItem, AnswerKnowledge
    from backend.ai_service import (
        QUESTION_BANK,
        GENERAL_TECHNICAL,
        PROBLEM_SOLVING,
        HR_QUESTIONS,
        ANSWER_KNOWLEDGE,
        WRONG_CONCEPTS,
    )
    from backend.dataset import CODING_QUESTIONS, EXTRA_TECHNICAL, VOICE_PROMPT_QUESTIONS
except ModuleNotFoundError:
    from models import QuestionItem, AnswerKnowledge
    from ai_service import (
        QUESTION_BANK,
        GENERAL_TECHNICAL,
        PROBLEM_SOLVING,
        HR_QUESTIONS,
        ANSWER_KNOWLEDGE,
        WRONG_CONCEPTS,
    )
    from dataset import CODING_QUESTIONS, EXTRA_TECHNICAL, VOICE_PROMPT_QUESTIONS


def _add_question(db, category, q_text, question_type="text", round_type="technical",
                  starter_code=None, test_cases=None, language="python", difficulty="medium"):
    q_text = q_text.strip()
    if not q_text:
        return False

    existing = db.query(QuestionItem).filter(QuestionItem.question_text == q_text).first()
    if existing:
        return False

    db.add(QuestionItem(
        category=category.strip().lower(),
        question_text=q_text,
        question_type=question_type,
        round_type=round_type,
        starter_code=starter_code,
        test_cases_json=json.dumps(test_cases) if test_cases else None,
        language=language,
        difficulty=difficulty,
    ))
    return True


def seed_dataset(db: Session):
    added = 0

    # Always try to add new questions (skip duplicates)
    print("Database Seeder: Seeding QuestionItem table...")

    for category, questions in QUESTION_BANK.items():
        for question in questions:
            if _add_question(db, category, question, round_type="technical"):
                added += 1

    for question in GENERAL_TECHNICAL:
        if _add_question(db, "general", question, round_type="technical"):
            added += 1

    for question in PROBLEM_SOLVING:
        if _add_question(db, "problem_solving", question, round_type="technical"):
            added += 1

    for question in HR_QUESTIONS:
        if _add_question(db, "hr", question, round_type="hr"):
            added += 1

    for category, questions in EXTRA_TECHNICAL.items():
        for question in questions:
            if _add_question(db, category, question, round_type="technical"):
                added += 1

    for question in VOICE_PROMPT_QUESTIONS:
        if _add_question(db, "voice", question, question_type="voice", round_type="technical"):
            added += 1

    for item in CODING_QUESTIONS:
        if _add_question(
            db,
            "coding",
            item["question"],
            question_type="coding",
            round_type="coding",
            starter_code=item.get("starter_code"),
            test_cases=item.get("test_cases"),
            language=item.get("language", "python"),
            difficulty="medium",
        ):
            added += 1

    db.commit()
    print(f"Database Seeder: Added {added} new QuestionItem records.")

    # Seed AnswerKnowledge (only if empty)
    if db.query(AnswerKnowledge).count() == 0:
        print("Database Seeder: Seeding AnswerKnowledge table...")
        for question, knowledge in ANSWER_KNOWLEDGE.items():
            keywords = knowledge.get("keywords", [])
            ideal_answer = knowledge.get("answer", "")
            wrong_concepts = WRONG_CONCEPTS.get(question, [])

            existing = db.query(AnswerKnowledge).filter(
                AnswerKnowledge.question_text == question.strip()
            ).first()
            if not existing:
                db.add(AnswerKnowledge(
                    question_text=question.strip(),
                    keywords_json=json.dumps(keywords),
                    wrong_concepts_json=json.dumps(wrong_concepts),
                    ideal_answer=ideal_answer,
                ))
        db.commit()
        print("Database Seeder: AnswerKnowledge seeding complete.")
    else:
        print("Database Seeder: AnswerKnowledge table is already populated.")
