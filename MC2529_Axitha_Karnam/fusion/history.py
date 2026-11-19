"""Append-only audit history for API questions and generated answers."""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

HISTORY_PATH = Path("csv/fused/api_conversation_history.csv")


def append_api_history(api_name: str, question: str, api_result, answer: str,
                       fusion_mode: str = "api_dataset_fusion") -> str:
    """Append one interaction. Never deduplicates or overwrites prior rows."""
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "Timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "API_Type": str(api_name),
        "Question": str(question),
        "API_Response": json.dumps(api_result, ensure_ascii=False, default=str),
        "Gemma_Answer": str(answer),
        "Fusion_Mode": str(fusion_mode),
    }
    pd.DataFrame([row]).to_csv(
        HISTORY_PATH, mode="a", header=not HISTORY_PATH.exists(),
        index=False, encoding="utf-8"
    )
    return str(HISTORY_PATH)
