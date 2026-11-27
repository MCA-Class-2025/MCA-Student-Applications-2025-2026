import csv
import json
import os
import threading
from datetime import datetime
from typing import Any


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "fused_interview_dataset_all_rows_1939.csv")
CSV_LOCK = threading.RLock()


class FusedDatasetService:
    """Append and query the canonical fused dataset without rewriting old rows."""

    def __init__(self, csv_path: str = CSV_PATH):
        self.csv_path = csv_path

    def _read_rows(self) -> tuple[list[str], list[dict[str, str]]]:
        with open(self.csv_path, "r", newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames:
                raise ValueError("Fused dataset CSV has no header.")
            return list(reader.fieldnames), list(reader)

    @staticmethod
    def _student_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
        return [row for row in rows if row.get("source_dataset") == "student_interview"]

    @staticmethod
    def _metadata(row: dict[str, str]) -> dict[str, Any]:
        if row.get("source_dataset") != "student_interview":
            return {}
        try:
            value = json.loads(row.get("explanation") or "{}")
            return value if isinstance(value, dict) else {}
        except (TypeError, json.JSONDecodeError):
            return {}

    def append_interview(self, result: dict[str, Any]) -> dict[str, Any]:
        answers = result.get("answers") or []
        interview_id = str(result.get("interview_id") or "").strip()
        if not interview_id or not answers:
            raise ValueError("Interview ID and at least one answer are required.")

        with CSV_LOCK:
            fieldnames, rows = self._read_rows()
            prefix = f"interview-{interview_id}-q-"
            existing = next(
                (row for row in self._student_rows(rows)
                 if (row.get("source_id") or "").startswith(prefix)),
                None,
            )
            if existing:
                return self._serialize_student_record(existing)

            numeric_ids = []
            for row in rows:
                try:
                    numeric_ids.append(int(row.get("master_row_id") or 0))
                except (TypeError, ValueError):
                    continue
            next_id = max(numeric_ids, default=0) + 1
            timestamp = result.get("date") or datetime.utcnow().isoformat(timespec="seconds") + "Z"
            total_marks = float(result.get("total_marks") or 0)
            percentage = float(result.get("percentage") or result.get("overall_score") or 0)

            new_rows = []
            for index, answer in enumerate(answers, start=1):
                score = float(answer.get("score") or 0)
                metadata = {
                    "interview_id": interview_id,
                    "accuracy": score,
                    "marks": score,
                    "total_marks": total_marks,
                    "percentage": percentage,
                    "performance": str(result.get("performance") or ""),
                    "feedback": str(result.get("feedback") or ""),
                    "skill_gap": str(result.get("skill_gap") or ""),
                    "evaluation": str(answer.get("evaluation") or ""),
                    "question_type": str(answer.get("question_type") or "text"),
                    "round": answer.get("round") or 1,
                }
                new_rows.append({
                    "master_row_id": str(next_id + index - 1),
                    "source_dataset": "student_interview",
                    "source_id": f"{prefix}{index}",
                    "job_role": str(result.get("job_role") or "General"),
                    "category": "Student Interview",
                    "skill": str(result.get("skills") or ""),
                    "programming_language": "",
                    "difficulty": str(answer.get("difficulty") or result.get("difficulty") or ""),
                    "question": str(answer.get("question") or ""),
                    "answer": str(answer.get("answer") or ""),
                    "expected_topics": str(result.get("skill_gap") or ""),
                    "ai_generated_solution": str(result.get("feedback") or ""),
                    "time_complexity": f"marks={score};total_marks={total_marks}",
                    "explanation": json.dumps(metadata, ensure_ascii=True),
                    "date": timestamp,
                })

            missing = set(fieldnames) - set(new_rows[0])
            if missing:
                raise ValueError(f"Fused dataset is missing required columns: {sorted(missing)}")
            with open(self.csv_path, "a", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
                for row in new_rows:
                    writer.writerow(row)
                file.flush()
                os.fsync(file.fileno())
            return self._serialize_student_record(new_rows[0])

    def list_records(self, search: str = "", source: str = "", job_role: str = "", sort: str = "date_desc") -> list[dict[str, Any]]:
        with CSV_LOCK:
            _, rows = self._read_rows()
        search = search.strip().lower()
        source = source.strip().lower()
        job_role = job_role.strip().lower()

        filtered = []
        for row in rows:
            metadata = self._metadata(row)
            if source and row.get("source_dataset", "").lower() != source:
                continue
            if job_role and row.get("job_role", "").lower() != job_role:
                continue
            searchable = " ".join([
                row.get(key, "") or ""
                for key in ("job_role", "skill", "question", "answer", "source_dataset")
            ] + [str(metadata.get("interview_id", ""))])
            if search and search not in searchable.lower():
                continue
            filtered.append(self._serialize_student_record(row))

        if sort == "score_desc":
            filtered.sort(key=lambda row: float(row.get("score") or 0), reverse=True)
        elif sort == "score_asc":
            filtered.sort(key=lambda row: float(row.get("score") or 0))
        elif sort == "date_asc":
            filtered.sort(key=lambda row: row.get("date") or "")
        else:
            filtered.sort(key=lambda row: row.get("date") or "", reverse=True)
        return filtered

    def stats(self) -> dict[str, int]:
        with CSV_LOCK:
            _, rows = self._read_rows()
        student_count = len(self._student_rows(rows))
        return {
            "total_records": len(rows),
            "original_records": len(rows) - student_count,
            "student_generated_records": student_count,
        }

    def _serialize_student_record(self, row: dict[str, str]) -> dict[str, Any]:
        metadata = self._metadata(row)
        score = metadata.get("marks")
        if score is None:
            try:
                score = float((row.get("time_complexity") or "").split("marks=", 1)[1].split(";", 1)[0])
            except (IndexError, ValueError):
                score = 0
        return {
            "master_row_id": row.get("master_row_id", ""),
            "result_id": metadata.get("interview_id") or row.get("source_id", ""),
            "job_role": row.get("job_role", ""),
            "skills": row.get("skill", ""),
            "question": row.get("question", ""),
            "answer": row.get("answer", ""),
            "accuracy": metadata.get("accuracy", score),
            "score": score,
            "total_marks": metadata.get("total_marks", ""),
            "percentage": metadata.get("percentage", ""),
            "performance": metadata.get("performance", ""),
            "difficulty": row.get("difficulty", ""),
            "feedback": metadata.get("feedback") or row.get("ai_generated_solution", ""),
            "skill_gap": metadata.get("skill_gap") or row.get("expected_topics", ""),
            "date": row.get("date", ""),
            "source": row.get("source_dataset", ""),
        }


fused_dataset_service = FusedDatasetService()