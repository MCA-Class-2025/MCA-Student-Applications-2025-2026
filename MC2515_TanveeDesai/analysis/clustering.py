"""
analysis/clustering.py — ML clustering and anomaly detection for drug data.

Uses lightweight scikit-learn models only. No GPU required.
Results must NOT be interpreted as clinical risk assessments.
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer

from utils.logging import logger


# ── Adverse Event Clustering ──────────────────────────────────────────────────

def cluster_adverse_reactions(top_ae: List[Dict], n_clusters: int = 3) -> Dict[str, Any]:
    """
    Simple K-Means clustering on adverse reaction counts.
    Groups reactions by count magnitude.
    """
    if len(top_ae) < n_clusters:
        return {"available": False, "reason": "Insufficient data"}

    try:
        counts = np.array([[r["count"]] for r in top_ae], dtype=float)
        scaler = StandardScaler()
        X = scaler.fit_transform(counts)

        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = km.fit_predict(X)

        # Assign readable cluster names based on mean count
        cluster_means = {}
        for i in range(n_clusters):
            mask = labels == i
            cluster_means[i] = float(counts[mask].mean())

        sorted_clusters = sorted(cluster_means.items(), key=lambda x: x[1])
        cluster_names = {
            sorted_clusters[0][0]: "Low Frequency",
            sorted_clusters[1][0]: "Medium Frequency",
            sorted_clusters[2][0]: "High Frequency",
        } if n_clusters == 3 else {i: f"Cluster {i}" for i in range(n_clusters)}

        results = []
        for reaction, label in zip(top_ae, labels):
            results.append({
                **reaction,
                "cluster": int(label),
                "cluster_name": cluster_names.get(int(label), f"Cluster {label}"),
            })

        return {
            "available": True,
            "reactions": results,
            "n_clusters": n_clusters,
            "cluster_names": cluster_names,
            "disclaimer": "Clustering groups reactions by reporting count magnitude only.",
        }
    except Exception as e:
        logger.warning(f"Adverse reaction clustering failed: {e}")
        return {"available": False, "reason": str(e)}


# ── Anomaly Detection ─────────────────────────────────────────────────────────

def detect_anomalies_in_ae(top_ae: List[Dict], contamination: float = 0.1) -> Dict[str, Any]:
    """
    Use Isolation Forest to detect unusually high-count adverse reactions.
    Anomalies = reactions with counts significantly different from the distribution.
    """
    if len(top_ae) < 5:
        return {"available": False, "reason": "Insufficient data (need ≥5 reactions)"}

    try:
        counts = np.array([[r["count"]] for r in top_ae], dtype=float)
        scaler = StandardScaler()
        X = scaler.fit_transform(counts)

        iso = IsolationForest(contamination=contamination, random_state=42)
        predictions = iso.fit_predict(X)  # -1 = anomaly, 1 = normal

        results = []
        for reaction, pred in zip(top_ae, predictions):
            results.append({
                **reaction,
                "anomaly": pred == -1,
                "anomaly_label": "Unusual Count" if pred == -1 else "Typical Count",
            })

        anomaly_count = sum(1 for p in predictions if p == -1)

        return {
            "available": True,
            "reactions": results,
            "anomaly_count": anomaly_count,
            "total": len(top_ae),
            "disclaimer": (
                "Anomaly detection identifies statistically unusual reporting counts. "
                "This does NOT indicate clinical significance or causal relationship."
            ),
        }
    except Exception as e:
        logger.warning(f"Anomaly detection failed: {e}")
        return {"available": False, "reason": str(e)}


# ── TF-IDF Text Analysis ──────────────────────────────────────────────────────

def extract_keywords_tfidf(texts: List[str], top_n: int = 20) -> List[Tuple[str, float]]:
    """
    Extract top keywords from a list of text documents using TF-IDF.
    """
    if not texts or len(texts) < 2:
        if texts and len(texts) == 1:
            # Single document: simple word frequency
            words = texts[0].lower().split()
            from collections import Counter
            word_counts = Counter(w for w in words if len(w) > 3)
            total = sum(word_counts.values())
            return [(w, c / total) for w, c in word_counts.most_common(top_n)]
        return []

    try:
        vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()
        # Mean TF-IDF score across documents
        mean_scores = np.asarray(tfidf_matrix.mean(axis=0)).flatten()
        top_indices = mean_scores.argsort()[-top_n:][::-1]
        return [(feature_names[i], float(mean_scores[i])) for i in top_indices]
    except Exception as e:
        logger.warning(f"TF-IDF extraction failed: {e}")
        return []


# ── PCA for visualization ─────────────────────────────────────────────────────

def pca_2d(features_matrix: np.ndarray) -> Optional[np.ndarray]:
    """Reduce feature matrix to 2D for visualization."""
    if features_matrix.shape[0] < 2 or features_matrix.shape[1] < 2:
        return None
    try:
        scaler = StandardScaler()
        X = scaler.fit_transform(features_matrix)
        pca = PCA(n_components=2, random_state=42)
        return pca.fit_transform(X)
    except Exception as e:
        logger.warning(f"PCA failed: {e}")
        return None


# ── Drug Activity Classification ──────────────────────────────────────────────

def classify_reporting_activity(ae_count: int) -> Dict[str, str]:
    """
    Classify a drug's adverse event reporting volume into analytical categories.
    DISCLAIMER: This is based solely on reporting count, not clinical risk.
    """
    if ae_count < 1000:
        return {
            "category": "Low Observed Reporting Activity",
            "description": (
                f"Fewer than 1,000 adverse event reports retrieved "
                f"(retrieved: {ae_count:,}). This may reflect limited availability, "
                f"limited use, or limited reporting — not necessarily low risk."
            ),
            "color": "green",
        }
    elif ae_count < 50_000:
        return {
            "category": "Moderate Observed Reporting Activity",
            "description": (
                f"{ae_count:,} adverse event reports retrieved. "
                f"This is within the moderate range for widely-used medicines."
            ),
            "color": "orange",
        }
    else:
        return {
            "category": "High Observed Reporting Activity",
            "description": (
                f"{ae_count:,} adverse event reports retrieved. "
                f"High reporting may reflect wide use, long market history, "
                f"or heightened surveillance — not necessarily greater inherent risk."
            ),
            "color": "red",
        }
