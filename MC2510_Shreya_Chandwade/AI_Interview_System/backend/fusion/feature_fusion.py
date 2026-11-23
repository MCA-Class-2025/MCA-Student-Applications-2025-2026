import re
from typing import Any, Dict, Mapping


class FeatureLevelFusion:
    """Combine independent candidate features into one normalized score."""

    DEFAULT_WEIGHTS = {"tfidf": 0.38, "lexical": 0.19, "category": 0.14, "skill": 0.14, "difficulty": 0.10, "metadata": 0.05}

    def __init__(self, weights: Mapping[str, float] | None = None):
        values = dict(weights or self.DEFAULT_WEIGHTS)
        total = sum(max(0.0, value) for value in values.values()) or 1.0
        self.weights = {key: max(0.0, value) / total for key, value in values.items()}

    @staticmethod
    def _tokens(value: Any) -> set[str]:
        return set(re.findall(r"[a-z0-9+#.]+", str(value or "").lower()))

    @classmethod
    def _similarity(cls, left: Any, right: Any) -> float:
        left_tokens = cls._tokens(left)
        right_tokens = cls._tokens(right)
        if not left_tokens or not right_tokens:
            return 0.0
        return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)

    def score(self, query: str, candidate: Dict[str, Any], tfidf_score: float, query_metadata: Mapping[str, Any] | None = None) -> Dict[str, float]:
        metadata = query_metadata or {}
        features = {
            "tfidf_score": max(0.0, min(1.0, float(tfidf_score))),
            "lexical_score": self._similarity(query, candidate.get("question", candidate.get("title", ""))),
            "category_score": self._similarity(metadata.get("category", ""), candidate.get("category", "")),
            "skill_score": self._similarity(metadata.get("skill", ""), candidate.get("skill", "")),
            "difficulty_score": self._similarity(metadata.get("difficulty", ""), candidate.get("difficulty", "")),
        }
        metadata_scores = [
            features["category_score"],
            features["skill_score"],
            features["difficulty_score"],
        ]
        features["metadata_score"] = sum(metadata_scores) / len(metadata_scores)
        features["feature_fusion_score"] = sum(
            self.weights.get(name.removesuffix("_score"), 0.0) * value
            for name, value in features.items()
            if name.endswith("_score")
        )
        return features