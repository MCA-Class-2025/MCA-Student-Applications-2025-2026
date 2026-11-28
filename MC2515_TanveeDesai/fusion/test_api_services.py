"""
tests/test_api_services.py — Basic smoke tests for the five API services.

These tests make real HTTP requests. Run with: pytest tests/ -v
"""

import pytest
from unittest.mock import patch, MagicMock


class TestRxNormService:
    def test_normalize_known_drug(self):
        """Amoxicillin should resolve to a valid RxCUI."""
        from services.rxnorm_service import normalize_drug_name
        result = normalize_drug_name("Amoxicillin")
        assert result["rxcui"] is not None, "Expected RxCUI for Amoxicillin"
        assert result["status"] in ("found", "approximate")

    def test_invalid_drug_returns_gracefully(self):
        """Made-up drug name should not crash."""
        from services.rxnorm_service import normalize_drug_name
        result = normalize_drug_name("xyzXYZnotarealdrugname99999")
        assert result is not None
        assert "status" in result


class TestOpenFDAService:
    def test_get_labels_returns_dict(self):
        """get_drug_labels should return a dict with retrieval_ok key."""
        from services.openfda_service import get_drug_labels
        result = get_drug_labels("Amoxicillin", limit=2)
        assert isinstance(result, dict)
        assert "retrieval_ok" in result
        assert "records" in result

    def test_get_recalls_returns_dict(self):
        from services.openfda_service import get_drug_recalls
        result = get_drug_recalls("Amoxicillin", limit=5)
        assert isinstance(result, dict)
        assert "records" in result

    def test_adverse_events_count(self):
        from services.openfda_service import get_top_adverse_reactions
        result = get_top_adverse_reactions("Amoxicillin", top_n=5)
        assert isinstance(result, list)


class TestDailyMedService:
    def test_search_spls(self):
        from services.dailymed_service import search_spls
        result = search_spls("Amoxicillin", page_size=3)
        assert isinstance(result, dict)
        assert "spls" in result

    def test_full_info(self):
        from services.dailymed_service import get_full_drug_info
        result = get_full_drug_info("Amoxicillin")
        assert isinstance(result, dict)
        assert "source" in result
        assert result["source"] == "DailyMed"


class TestPubMedService:
    def test_search_returns_pmids(self):
        from services.pubmed_service import search_pubmed
        pmids = search_pubmed("Amoxicillin", max_results=5)
        assert isinstance(pmids, list)

    def test_full_info(self):
        from services.pubmed_service import get_full_drug_info
        result = get_full_drug_info("Amoxicillin")
        assert isinstance(result, dict)
        assert "articles" in result


class TestClinicalTrialsService:
    def test_search_trials(self):
        from services.clinicaltrials_service import search_trials
        result = search_trials("Amoxicillin", page_size=5)
        assert isinstance(result, dict)
        assert "trials" in result

    def test_full_info(self):
        from services.clinicaltrials_service import get_full_drug_info
        result = get_full_drug_info("Amoxicillin")
        assert isinstance(result, dict)
        assert "trials" in result


class TestPreprocessing:
    def test_clean_text(self):
        from preprocessing.cleaning import clean_text
        assert clean_text("  hello  world  ") == "hello world"
        assert clean_text(None) == ""

    def test_clean_date(self):
        from preprocessing.cleaning import clean_date
        assert clean_date("20230115") == "2023-01-15"
        assert clean_date("2023-06-01") == "2023-06-01"
        assert clean_date(None) is None


class TestFeatures:
    def test_safety_score_range(self):
        from analysis.features import compute_safety_intelligence_score
        features = {
            "adverse_event_count": 1000,
            "has_recalls": False,
            "class_i_recalls": 0,
            "class_ii_recalls": 0,
            "class_iii_recalls": 0,
            "has_boxed_warning": False,
            "research_count": 10,
            "clinical_trial_count": 5,
        }
        score_data = compute_safety_intelligence_score(features)
        assert 0 <= score_data["score"] <= 100
        assert "category" in score_data
        assert "disclaimer" in score_data
