"""
Local conversation history for PlatePal.

Saves conversations to a plain JSON file (chat_history.json) in the
project folder, so past conversations persist across app restarts.
No account or cloud storage needed - it's just a file on your machine.
"""

import json
import os
import uuid
from datetime import datetime

HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chat_history.json")

MAX_SAVED_CONVERSATIONS = 50


def load_history() -> list:
    """Returns saved conversations, newest first. Empty list if none/corrupt."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_all(history: list) -> None:
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def save_conversation(messages: list, food_context: str = "", dish_name: str = "") -> dict:
    """
    Saves the given conversation as a new history entry (newest first).
    No-op (returns {}) if there are no messages to save.
    """
    if not messages:
        return {}

    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "dish": dish_name or "Conversation",
        "messages": messages,
        "food_context": food_context,
    }

    history = load_history()
    history.insert(0, entry)
    history = history[:MAX_SAVED_CONVERSATIONS]
    _save_all(history)
    return entry


def delete_conversation(entry_id: str) -> None:
    history = load_history()
    history = [h for h in history if h.get("id") != entry_id]
    _save_all(history)


def clear_all_history() -> None:
    _save_all([])