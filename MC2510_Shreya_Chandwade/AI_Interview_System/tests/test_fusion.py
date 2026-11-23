import unittest
from contextlib import redirect_stdout
from io import StringIO

from backend.fusion import DataLevelFusion, FeatureLevelFusion, DecisionLevelFusion


class FusionTests(unittest.TestCase):
    def test_data_fusion_normalizes_missing_values_and_duplicates(self):
        fusion = DataLevelFusion()
        records = fusion.fuse(
            database_records=[
                {"question_text": " What is Python? ", "category": "Python", "source": "database"},
            ],
            knowledge_records=[
                {"question": "what is python?", "ideal_answer": "A programming language", "source": "knowledge_base"},
            ],
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["question"], "What is Python?")
        self.assertEqual(records[0]["answer"], "A programming language")
        self.assertEqual(records[0]["difficulty"], "medium")
        self.assertIn("database", records[0]["source"])
        self.assertIn("knowledge_base", records[0]["source"])
        self.assertEqual(fusion.last_status["records_after_deduplication"], 1)

    def test_data_fusion_empty_input(self):
        fusion = DataLevelFusion()
        self.assertEqual(fusion.fuse(), [])
        self.assertEqual(fusion.last_status["records_before_deduplication"], 0)

    def test_feature_fusion_returns_normalized_components(self):
        fusion = FeatureLevelFusion()
        scores = fusion.score(
            "python list",
            {"question": "Explain Python lists", "category": "python", "skill": "python", "difficulty": "medium"},
            0.8,
            {"category": "python", "skill": "python", "difficulty": "medium"},
        )
        self.assertGreater(scores["feature_fusion_score"], 0.0)
        self.assertLessEqual(scores["feature_fusion_score"], 1.0)
        self.assertEqual(set(scores), {"tfidf_score", "lexical_score", "category_score", "skill_score", "difficulty_score", "metadata_score", "feature_fusion_score"})

    def test_decision_fusion_ranks_stronger_signal_higher(self):
        fusion = DecisionLevelFusion()
        strong = fusion.score(0.9, 0.8, "database")
        weak = fusion.score(0.2, 0.3, "csv_source")
        self.assertGreater(strong["final_score"], weak["final_score"])
        self.assertLessEqual(strong["final_score"], 1.0)

    def test_rag_pipeline_returns_decision_ranked_results(self):
        from backend.rag_service import RAGEngine

        engine = RAGEngine()
        with redirect_stdout(StringIO()):
            engine.build_index()
            results = engine.retrieve_relevant_context("python list tuple", top_k=3, query_metadata={"skill": "python", "category": "python"})
        self.assertTrue(results)
        self.assertTrue(all("final_score" in result for result in results))
        self.assertEqual(results, sorted(results, key=lambda item: item["final_score"], reverse=True))

    def test_existing_ai_routes_are_registered(self):
        from backend.main import app

        routes = {route.path for route in app.routes}
        required = {"/generate-questions", "/evaluate-answer", "/interview-feedback", "/analyze-skills", "/generate-study-plan"}
        self.assertTrue(required.issubset(routes))


if __name__ == "__main__":
    unittest.main()