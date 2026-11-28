"""
analytics.py
------------
Persists employee questions and feedback to a local JSONL log, and
aggregates them for an HR-facing "Insights" panel.

This replaces feedback buttons that only update session state (gone on
refresh, visible to no one) with something that actually does what it
claims: HR can see which questions get asked most and which answers were
marked unhelpful -- a real gap in most commercial policy-chatbot UIs, which
collect employee feedback but rarely expose it back to the people who could
act on it (fixing unclear policy docs, adding missing coverage).

Note: writes to a local file, which is fine for a single-instance demo /
class project deployment. On Streamlit Community Cloud specifically, the
filesystem is ephemeral across redeploys -- documented in the README as a
real limitation, not hidden.
"""

import os
import json
import time
import uuid
from typing import Dict, List, Optional

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LOG_PATH = os.path.join(BASE_DIR, "Dataset", "analytics", "interaction_log.jsonl")


def _ensure_log_dir():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)


def log_interaction(question: str, coverage: Optional[str], mode: str = "text") -> str:
    """
    Logs a question at the time it's answered. Returns an interaction_id so
    a later feedback event (👍/👎) can be linked back to this record.
    """
    _ensure_log_dir()
    # uuid4, not a millisecond timestamp -- timestamps collide under back-to-back
    # calls (confirmed by testing: a tight loop produced duplicate IDs and silently
    # dropped interactions in the aggregation step below).
    interaction_id = uuid.uuid4().hex
    record = {
        "interaction_id": interaction_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "question": question,
        "coverage": coverage,
        "mode": mode,       # "text" or "photo"
        "feedback": None,   # filled in later if the employee rates it
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return interaction_id


def log_feedback(interaction_id: str, feedback: str) -> None:
    """
    Appends a feedback event as its own log line (append-only log, simpler
    and safer than rewriting the file to update a prior record -- avoids
    concurrent-write corruption if two sessions write at once).
    """
    _ensure_log_dir()
    record = {
        "interaction_id": interaction_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "feedback_event": feedback,  # "up" or "down"
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def load_insights() -> Dict:
    """
    Reads the full log and aggregates it into HR-facing numbers:
    - most-asked questions
    - questions marked unhelpful (👎), which surface real documentation gaps
    - how often the assistant reported low/no coverage (surfaces missing policy content)
    """
    if not os.path.exists(LOG_PATH):
        return {"total_questions": 0, "top_questions": [], "flagged_questions": [], "low_coverage_count": 0}

    questions_seen: Dict[str, int] = {}
    coverage_by_id: Dict[str, str] = {}
    question_by_id: Dict[str, str] = {}
    feedback_by_id: Dict[str, str] = {}

    with open(LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "question" in rec:
                q = rec["question"].strip().lower()
                questions_seen[q] = questions_seen.get(q, 0) + 1
                coverage_by_id[rec["interaction_id"]] = rec.get("coverage")
                question_by_id[rec["interaction_id"]] = rec["question"]
            elif "feedback_event" in rec:
                feedback_by_id[rec["interaction_id"]] = rec["feedback_event"]

    top_questions = sorted(questions_seen.items(), key=lambda x: -x[1])[:8]

    flagged_questions = [
        question_by_id[iid] for iid, fb in feedback_by_id.items()
        if fb == "down" and iid in question_by_id
    ]

    low_coverage_count = sum(1 for c in coverage_by_id.values() if c == "NONE")

    return {
        "total_questions": len(coverage_by_id),
        "top_questions": top_questions,
        "flagged_questions": flagged_questions,
        "low_coverage_count": low_coverage_count,
    }
