import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "event_planner.db")


def create_history_table():
    """Create the event history table if it does not already exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS event_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                event_date TEXT NOT NULL,
                location TEXT NOT NULL,
                guests INTEGER NOT NULL,
                budget REAL NOT NULL,
                event_plan TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.commit()


def save_event_plan(
    user_id,
    event_type,
    event_date,
    location,
    guests,
    budget,
    event_plan
):
    """Save one generated plan for the currently logged-in user."""
    create_history_table()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO event_history
            (
                user_id,
                event_type,
                event_date,
                location,
                guests,
                budget,
                event_plan
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                str(event_type),
                str(event_date),
                str(location).strip(),
                int(guests),
                float(budget),
                str(event_plan)
            )
        )
        conn.commit()
        return cursor.lastrowid


def get_user_event_history(user_id):
    """Return only the current user's history, newest first."""
    create_history_table()

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT
                id,
                event_type,
                event_date,
                location,
                guests,
                budget,
                created_at
            FROM event_history
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC, id DESC
            """,
            (int(user_id),)
        ).fetchall()

    return [dict(row) for row in rows]


def get_event_plan(user_id, history_id):
    """
    Retrieve the complete saved plan only if it belongs to user_id.
    Returns a dictionary or None.
    """
    create_history_table()

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        row = conn.execute(
            """
            SELECT
                id,
                event_type,
                event_date,
                location,
                guests,
                budget,
                event_plan,
                created_at
            FROM event_history
            WHERE id = ? AND user_id = ?
            """,
            (int(history_id), int(user_id))
        ).fetchone()

    return dict(row) if row else None


def delete_event_plan(user_id, history_id):
    """
    Delete only the selected plan belonging to user_id.
    Returns True if one record was deleted.
    """
    create_history_table()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            DELETE FROM event_history
            WHERE id = ? AND user_id = ?
            """,
            (int(history_id), int(user_id))
        )
        conn.commit()

    return cursor.rowcount == 1
