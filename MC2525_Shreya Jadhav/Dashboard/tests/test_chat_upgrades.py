"""Regression checks for questions that previously exposed chat failures."""

import unittest
from unittest.mock import patch

from LLM.rag.chat_service import respond_to_question
from LLM.rag.curated_answers import curated_medical_answer
from LLM.rag.dataset_answers import answer_dataset_question
from router import route
from Dashboard.utils.clinical_engine import analyze, extract_pcos


class ChatUpgradeTests(unittest.TestCase):
    def test_diagnosis_question_is_not_a_personal_report(self):
        question = "Can I have PCOS even if my ultrasound is normal?"
        self.assertEqual(route(question), "knowledge")
        self.assertFalse(extract_pcos(question))
        self.assertEqual(route("Do I have PCOS?"), "knowledge")

    def test_severe_pelvic_pain_bypasses_normal_chat(self):
        question = "I have sudden severe pelvic pain, fever, and a missed period."
        self.assertEqual(route(question), "clinical")
        assessment = analyze(question)
        self.assertEqual(assessment["urgency"], "emergency")
        self.assertIn("seek emergency medical care now", assessment["urgent_answer"])
        self.assertNotIn("Low", assessment["risk"])
        with patch("LLM.rag.chat_service.ask_llm") as model:
            reply = respond_to_question(question)
            model.assert_not_called()
            self.assertIn("seek emergency medical care now", reply["answer"])

    def test_severe_pain_and_rapid_bleeding(self):
        assessment = analyze("My pain is 9/10 and I am soaking a pad every hour.")
        self.assertEqual(assessment["urgency"], "emergency")
        self.assertIn("rapid bleeding", assessment["urgent_answer"])

    def test_alternative_bleeding_wording_reaches_safety_gate(self):
        question = "I'm bleeding through a pad every hour."
        self.assertEqual(route(question), "clinical")
        self.assertEqual(analyze(question)["urgency"], "prompt")

    def test_unknown_details_are_not_called_low_risk(self):
        assessment = analyze("I have pain, but I cannot rate it.")
        self.assertNotIn("Low", assessment["risk"])
        self.assertNotIn("No significant clinical concerns", assessment["report"])

    def test_explicitly_negated_pain_does_not_raise_pain_flag(self):
        assessment = analyze("I have no severe pelvic pain and no fever.")
        self.assertEqual(assessment["urgency"], "none")

    def test_pcos_percentage_uses_distinct_users(self):
        result = answer_dataset_question("What percentage of FemCare users have PCOS?")
        self.assertIsNotNone(result)
        answer, source = result
        self.assertIn("164 of 2,000 distinct users (8.2%)", answer)
        self.assertIn("femcare_final_cleaned.csv", source["source"])
        self.assertIsNone(answer_dataset_question("What percentage of people worldwide have PCOS?"))
        with patch("LLM.rag.chat_service.ask_llm") as model:
            reply = respond_to_question("What percentage of FemCare users have PCOS?")
            model.assert_not_called()
            self.assertIn("8.2%", reply["answer"])

    def test_compound_comparison_answers_fertility_part(self):
        question = "Is PCOD milder than PCOS, and can it never affect fertility?"
        answer = curated_medical_answer(
            question, [{"source": "pcos_pcod_terms.txt"}]
        )
        self.assertIn("not two separate diagnoses", answer)
        self.assertIn("can affect fertility", answer)

    def test_general_questions_are_not_clinical_reports(self):
        self.assertEqual(route("How is PCOS different from PCOD?"), "knowledge")
        self.assertEqual(route("What is PCOS?"), "knowledge")
        self.assertEqual(route("hi"), "greeting")

    def test_lightheaded_does_not_mean_light_flow(self):
        assessment = analyze("I feel lightheaded and have pelvic pain.")
        self.assertIsNone(assessment["flow"])
        self.assertEqual(assessment["urgency"], "emergency")

    def test_reported_pcos_with_stopped_periods_is_a_symptom_report(self):
        question = "I have PCOS and my periods stopped for three months."
        self.assertEqual(route(question), "clinical")
        self.assertTrue(analyze(question)["pcos"])


if __name__ == "__main__":
    unittest.main()
