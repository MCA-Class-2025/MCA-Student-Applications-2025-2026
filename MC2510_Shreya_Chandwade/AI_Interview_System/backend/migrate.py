"""Lightweight SQLite migrations for schema additions."""

from sqlalchemy import inspect, text


def run_migrations(engine):
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if "interviews" in existing_tables:
        _add_columns(
            engine,
            "interviews",
            {
                "interview_mode": "VARCHAR(50) DEFAULT 'text'",
                "current_round": "INTEGER DEFAULT 1",
                "total_rounds": "INTEGER DEFAULT 3",
                "difficulty": "VARCHAR(50) DEFAULT ''",
            },
        )

    if "interview_answers" in existing_tables:
        _add_columns(
            engine,
            "interview_answers",
            {
                "question_type": "VARCHAR(50) DEFAULT 'text'",
                "round_number": "INTEGER DEFAULT 1",
                "sentiment_score": "FLOAT",
                "confidence_score": "FLOAT",
                "sentiment_label": "VARCHAR(50)",
            },
        )

    if "question_items" in existing_tables:
        _add_columns(
            engine,
            "question_items",
            {
                "question_type": "VARCHAR(50) DEFAULT 'text'",
                "difficulty": "VARCHAR(50) DEFAULT 'medium'",
                "round_type": "VARCHAR(50) DEFAULT 'technical'",
                "starter_code": "TEXT",
                "test_cases_json": "TEXT",
                "language": "VARCHAR(50) DEFAULT 'python'",
            },
        )


def _add_columns(engine, table_name, columns):
    inspector = inspect(engine)
    existing = {col["name"] for col in inspector.get_columns(table_name)}

    with engine.begin() as conn:
        for col_name, col_def in columns.items():
            if col_name not in existing:
                conn.execute(
                    text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}")
                )
