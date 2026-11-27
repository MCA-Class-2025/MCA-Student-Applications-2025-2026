from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey
)

from sqlalchemy.orm import relationship

from datetime import datetime

try:
    from backend.database import Base
except ModuleNotFoundError:
    from database import Base


class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(150),
        unique=True,
        index=True,
        nullable=False
    )

    password = Column(
        String(255),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


    interviews = relationship(
        "Interview",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Interview(Base):

    __tablename__ = "interviews"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    job_role = Column(
        String(150),
        nullable=False
    )

    skills = Column(
        Text,
        nullable=False
    )

    experience = Column(
        String(100)
    )

    overall_score = Column(
        Float,
        default=0
    )

    interview_mode = Column(
        String(50),
        default="text"
    )

    difficulty = Column(
        String(50),
        default=""
    )

    current_round = Column(
        Integer,
        default=1
    )

    total_rounds = Column(
        Integer,
        default=3
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


    user = relationship(
        "User",
        back_populates="interviews"
    )


    answers = relationship(
        "InterviewAnswer",
        back_populates="interview",
        cascade="all, delete-orphan"
    )


class InterviewAnswer(Base):

    __tablename__ = "interview_answers"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    interview_id = Column(
        Integer,
        ForeignKey("interviews.id"),
        nullable=False
    )

    question = Column(
        Text,
        nullable=False
    )

    answer = Column(
        Text,
        nullable=False
    )

    evaluation = Column(
        Text
    )

    score = Column(
        Float,
        default=0
    )

    question_type = Column(
        String(50),
        default="text"
    )

    round_number = Column(
        Integer,
        default=1
    )

    sentiment_score = Column(
        Float,
        nullable=True
    )

    confidence_score = Column(
        Float,
        nullable=True
    )

    sentiment_label = Column(
        String(50),
        nullable=True
    )


    interview = relationship(
        "Interview",
        back_populates="answers"
    )


class QuestionItem(Base):

    __tablename__ = "question_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    category = Column(
        String(100),
        nullable=False,
        index=True
    )

    question_text = Column(
        Text,
        nullable=False,
        unique=True
    )

    question_type = Column(
        String(50),
        default="text"
    )

    difficulty = Column(
        String(50),
        default="medium"
    )

    round_type = Column(
        String(50),
        default="technical"
    )

    starter_code = Column(
        Text,
        nullable=True
    )

    test_cases_json = Column(
        Text,
        nullable=True
    )

    language = Column(
        String(50),
        default="python"
    )


class AnswerKnowledge(Base):

    __tablename__ = "answer_knowledge"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    question_text = Column(
        Text,
        nullable=False,
        unique=True
    )

    keywords_json = Column(
        Text,
        nullable=False
    )

    wrong_concepts_json = Column(
        Text,
        nullable=True
    )

    ideal_answer = Column(
        Text,
        nullable=False
    )
