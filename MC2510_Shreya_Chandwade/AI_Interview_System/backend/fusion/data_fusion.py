import csv
import glob
import os
import re
from typing import Any, Dict, Iterable, List


class DataLevelFusion:
    """Normalize heterogeneous interview sources into one deduplicated schema."""

    FIELD_ALIASES = {
        "question": ("question", "question_text", "title", "prompt"),
        "answer": ("answer", "ideal_answer", "solution", "ai_generated_solution", "explanation"),
        "category": ("category", "topic", "domain", "round_type"),
        "skill": ("skill", "skills", "programming_language", "language"),
        "difficulty": ("difficulty", "difficulty_level", "difficulty level"),
    }

    def __init__(self, base_dir: str | None = None):
        self.base_dir = base_dir
        self.last_status: Dict[str, Any] = {}

    @staticmethod
    def _clean(value: Any) -> str:
        if value is None:
            return ""
        return re.sub(r"\s+", " ", str(value)).strip()

    @classmethod
    def normalize_record(cls, record: Dict[str, Any], source: str) -> Dict[str, str]:
        lowered = {str(key).strip().lower(): value for key, value in record.items()}
        normalized: Dict[str, str] = {}
        for field, aliases in cls.FIELD_ALIASES.items():
            value = ""
            for alias in aliases:
                if alias in lowered and cls._clean(lowered[alias]):
                    value = cls._clean(lowered[alias])
                    break
            normalized[field] = value
        normalized["source"] = cls._clean(record.get("source")) or source
        normalized["answer"] = normalized["answer"] or ""
        normalized["category"] = normalized["category"] or "general"
        normalized["skill"] = normalized["skill"] or normalized["category"]
        normalized["difficulty"] = normalized["difficulty"] or "medium"
        return normalized

    @classmethod
    def deduplicate(cls, records: Iterable[Dict[str, Any]]) -> List[Dict[str, str]]:
        merged: Dict[str, Dict[str, str]] = {}
        for record in records:
            item = cls.normalize_record(record, str(record.get("source", "unknown")))
            question_key = re.sub(r"[^a-z0-9]+", " ", item["question"].lower()).strip()
            if not question_key:
                continue
            if question_key not in merged:
                merged[question_key] = item
                continue
            existing = merged[question_key]
            for field in ("answer", "category", "skill", "difficulty"):
                if len(item[field]) > len(existing[field]):
                    existing[field] = item[field]
            sources = [part.strip() for part in existing["source"].split(",")]
            if item["source"] not in sources:
                sources.append(item["source"])
            existing["source"] = ", ".join(sources)
        return list(merged.values())

    def _csv_records(self) -> List[Dict[str, Any]]:
        if not self.base_dir:
            return []
        records: List[Dict[str, Any]] = []
        for path in sorted(glob.glob(os.path.join(self.base_dir, "*.csv"))):
            source = os.path.splitext(os.path.basename(path))[0]
            try:
                with open(path, "r", encoding="utf-8-sig", newline="") as handle:
                    for row in csv.DictReader(handle):
                        row["source"] = source
                        records.append(row)
            except (OSError, UnicodeError, csv.Error) as exc:
                print(f"DATA-LEVEL FUSION: skipped {source}: {exc}")
        return records

    def fuse(self, database_records: Iterable[Dict[str, Any]] = (), knowledge_records: Iterable[Dict[str, Any]] = (), question_bank_records: Iterable[Dict[str, Any]] = ()) -> List[Dict[str, str]]:
        raw: List[Dict[str, Any]] = []
        source_names = []
        for source, records in (("database", database_records), ("knowledge_base", knowledge_records), ("question_bank", question_bank_records)):
            materialized = list(records)
            if materialized:
                source_names.append(source)
            for record in materialized:
                item = dict(record)
                item["source"] = item.get("source") or source
                raw.append(item)
        csv_records = self._csv_records()
        if csv_records:
            source_names.extend(sorted({str(item["source"]) for item in csv_records}))
            raw.extend(csv_records)

        unified = self.deduplicate(raw)
        self.last_status = {
            "sources_loaded": len(set(source_names)),
            "records_before_deduplication": len(raw),
            "records_after_deduplication": len(unified),
            "sources": sorted(set(source_names)),
        }
        print("DATA-LEVEL FUSION")
        print(f"Sources loaded: {self.last_status['sources_loaded']}")
        print(f"Records before deduplication: {len(raw)}")
        print(f"Records after deduplication: {len(unified)}")
        return unified