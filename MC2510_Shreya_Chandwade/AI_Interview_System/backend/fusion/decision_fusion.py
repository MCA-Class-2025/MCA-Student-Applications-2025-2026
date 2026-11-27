from typing import Dict, Mapping


class DecisionLevelFusion:
    """Fuse independent ranking decisions into the final retrieval score."""

    DEFAULT_WEIGHTS = {"tfidf": 0.30, "feature_fusion": 0.50, "source_reliability": 0.20}
    SOURCE_RELIABILITY = {
        "database": 1.0,
        "database_answer_knowledge": 1.0,
        "database_question_item": 0.95,
        "knowledge_base": 0.90,
        "question_bank": 0.85,
    }

    def __init__(self, weights: Mapping[str, float] | None = None):
        values = dict(weights or self.DEFAULT_WEIGHTS)
        total = sum(max(0.0, value) for value in values.values()) or 1.0
        self.weights = {key: max(0.0, value) / total for key, value in values.items()}

    def source_reliability(self, source: str) -> float:
        sources = [part.strip() for part in str(source or "").split(",")]
        return max((self.SOURCE_RELIABILITY.get(item, 0.70) for item in sources), default=0.70)

    def score(self, tfidf_score: float, feature_fusion_score: float, source: str) -> Dict[str, float]:
        decisions = {
            "tfidf_decision": max(0.0, min(1.0, float(tfidf_score))),
            "feature_fusion_decision": max(0.0, min(1.0, float(feature_fusion_score))),
            "source_reliability": self.source_reliability(source),
        }
        decisions["final_score"] = (
            self.weights.get("tfidf", 0.0) * decisions["tfidf_decision"]
            + self.weights.get("feature_fusion", 0.0) * decisions["feature_fusion_decision"]
            + self.weights.get("source_reliability", 0.0) * decisions["source_reliability"]
        )
        return decisions