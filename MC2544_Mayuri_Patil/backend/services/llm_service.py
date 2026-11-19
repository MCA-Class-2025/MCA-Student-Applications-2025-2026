import logging
import os
import re
from pathlib import Path

import httpx
from dotenv import load_dotenv

from models.schemas import PatientData, PredictionResponse
from services.fused_rag_service import KnowledgeBaseError, retrieve

logger = logging.getLogger(__name__)

HF_API_URL = "https://router.huggingface.co/v1/chat/completions"
DEFAULT_MODEL = "CohereLabs/tiny-aya-global"
DISCLAIMER = (
    "This is general educational information, not a medical diagnosis or a "
    "substitute for advice from a qualified healthcare professional."
)

load_dotenv(Path(__file__).resolve().parents[2] / ".env", encoding="utf-8-sig")


class LlmServiceError(RuntimeError):
    """Raised when the configured LLM service cannot generate a response."""


def generate_recommendation(patient: PatientData, prediction: PredictionResponse) -> str:
    token = os.getenv("HF_TOKEN")
    if token:
        model = os.getenv("HF_MODEL", DEFAULT_MODEL)
        prompt = (
            "Write three concise, general wellness suggestions for an adult whose "
            f"educational cardiovascular risk model result is {prediction.risk_label} "
            f"({prediction.risk_probability:.0%} estimated probability). "
            f"Relevant measurements: age {patient.age}, blood pressure "
            f"{patient.ap_hi}/{patient.ap_lo}, cholesterol category {patient.cholesterol}, "
            f"glucose category {patient.gluc}, physically active: {bool(patient.active)}."
        )
        try:
            response = httpx.post(
                HF_API_URL,
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Provide educational wellness information only. Do not diagnose, "
                                "prescribe medication, claim certainty, or use alarming language. "
                                "Encourage speaking with a qualified healthcare professional where appropriate."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 180,
                },
                timeout=20.0,
            )
            response.raise_for_status()
            payload = response.json()
            choices = payload.get("choices") if isinstance(payload, dict) else None
            if isinstance(choices, list) and choices and isinstance(choices[0], dict):
                message = choices[0].get("message")
                if isinstance(message, dict):
                    recommendation = message.get("content")
                    if isinstance(recommendation, str) and recommendation.strip():
                        return recommendation.strip()
        except Exception as error:
            logger.warning("External LLM recommendation call failed: %s. Using evidence-based guidance.", error)

    # Seamless fallback to structured, patient-tailored guidance
    return _generate_evidence_recommendation(patient, prediction)


def _generate_evidence_recommendation(patient: PatientData, prediction: PredictionResponse) -> str:
    """Generate 3 personalized, educational cardiovascular wellness suggestions."""
    suggestions: list[str] = []

    # 1. Blood Pressure Management
    if patient.ap_hi >= 140 or patient.ap_lo >= 90:
        suggestions.append(
            f"1. Blood Pressure Management: Your recorded blood pressure ({patient.ap_hi}/{patient.ap_lo} mmHg) is elevated. "
            "Adopt dietary sodium moderation (aim for under 2,000 mg/day), follow DASH diet principles (rich in vegetables, fruits, and lean proteins), "
            "and regularly log your daily readings for physician review."
        )
    elif patient.ap_hi >= 120 or patient.ap_lo >= 80:
        suggestions.append(
            f"1. Blood Pressure Optimization: Your blood pressure is slightly elevated ({patient.ap_hi}/{patient.ap_lo} mmHg). "
            "Maintain heart-healthy hydration, minimize processed and canned foods, and include stress-reduction practices like paced breathing or meditation."
        )
    else:
        suggestions.append(
            f"1. Cardiovascular Baseline: Your blood pressure ({patient.ap_hi}/{patient.ap_lo} mmHg) is in a healthy range. "
            "Continue your current routine with regular hydration and periodic monitoring."
        )

    # 2. Nutrition & Metabolic Balance
    metabolic_notes = []
    if patient.cholesterol > 1:
        metabolic_notes.append("elevated cholesterol")
    if patient.gluc > 1:
        metabolic_notes.append("elevated glucose")

    if metabolic_notes:
        suggestions.append(
            f"2. Metabolic & Nutritional Support: Addressing your {' and '.join(metabolic_notes)}, increase soluble fiber intake "
            "(oats, legumes, flaxseed), reduce saturated and trans fats, and limit added sugars to support lipid and glycemic balance."
        )
    else:
        suggestions.append(
            "2. Heart-Healthy Nutrition: Emphasize a Mediterranean-style dietary pattern rich in leafy greens, nuts, extra-virgin olive oil, "
            "and lean proteins while keeping processed snacks minimal."
        )

    # 3. Physical Activity & Routine Medical Consultation
    if not patient.active:
        suggestions.append(
            "3. Active Lifestyle: Gradually build toward at least 150 minutes of moderate-intensity aerobic activity weekly "
            "(such as brisk walking or cycling), broken into comfortable 20-30 minute sessions."
        )
    elif patient.smoke or patient.alco:
        habits = []
        if patient.smoke:
            habits.append("smoking cessation")
        if patient.alco:
            habits.append("moderating alcohol intake")
        suggestions.append(
            f"3. Lifestyle Risk Reduction: Prioritize {' and '.join(habits)} to decrease arterial stiffness, lower inflammation, "
            "and strengthen overall cardiovascular endurance."
        )
    else:
        suggestions.append(
            f"3. Healthcare Consultation: With an educational estimated {prediction.risk_label.lower()} profile "
            f"({prediction.risk_probability:.0%} risk probability), schedule an annual preventative check-up with your primary physician "
            "for comprehensive lipid and metabolic evaluations."
        )

    return "\n\n".join(suggestions)


def generate_phase2_answer(question: str) -> tuple[str, list[dict[str, object]]]:
    """Answer a Phase 2 question using retrieved fused-dataset context."""
    try:
        sources = retrieve(question)
    except (KnowledgeBaseError, ValueError) as error:
        raise LlmServiceError(str(error)) from error

    token = os.getenv("HF_TOKEN")
    if token:
        try:
            context = "\n\n".join(
                f"[{source['source']}:{source['record_id']}] {source['text']}"
                for source in sources
            )
            answer = _complete_chat(
                token,
                (
                    "Answer only from the supplied retrieved records. If the records do not "
                    "contain the answer, say so. Do not diagnose, prescribe medication, or "
                    "infer facts not present in the records. Cite source IDs in square brackets."
                ),
                f"Question: {question}\n\nRetrieved records:\n{context}",
            )
            if answer and answer.strip():
                return answer.strip(), sources
        except Exception as error:
            logger.warning("External LLM Phase 2 answer call failed: %s. Using grounded synthesis.", error)

    # Fallback to grounded extractive synthesis from retrieved records
    grounded_answer = _generate_grounded_rag_answer(question, sources)
    return grounded_answer, sources


def _generate_grounded_rag_answer(question: str, sources: list[dict[str, object]]) -> str:
    """Synthesize a precise, citation-backed answer from retrieved records."""
    if not sources or max(float(s.get("score", 0)) for s in sources) < 0.005:
        return "The retrieved records do not contain sufficient information to answer this question."

    q_lower = question.lower()

    # 1. LOINC code lookup
    if "loinc" in q_lower or "code" in q_lower:
        for s in sources:
            text = str(s.get("text", ""))
            match = re.search(r"LOINC code ([0-9-]+)", text)
            if match:
                code = match.group(1)
                disp = re.search(r"LOINC display name ([^;]+)", text)
                disp_str = f" (display name: {disp.group(1).strip()})" if disp else ""
                unit = re.search(r"unit ([^;]+)", text)
                unit_str = f" with unit {unit.group(1).strip()}" if unit else ""
                record_id = str(s.get("record_id", "")).replace("_", " ")
                sid = s.get("source")
                rid = s.get("record_id")
                measurement_name = record_id.capitalize()
                return f"{measurement_name} is identified by LOINC code {code}{disp_str}{unit_str} [{sid}:{rid}]."

    # 2. Measurement unit lookup
    if "unit" in q_lower:
        for s in sources:
            text = str(s.get("text", ""))
            unit_match = re.search(r"unit ([^;]+)", text)
            if unit_match:
                record_id = str(s.get("record_id", "")).replace("_", " ")
                sid = s.get("source")
                rid = s.get("record_id")
                return f"The standard measurement unit for {record_id} is {unit_match.group(1).strip()} [{sid}:{rid}]."

    # 3. Dataset size, patient count, attribute counts
    if any(term in q_lower for term in ["how many", "count", "size", "total", "records", "attributes", "fused"]):
        for s in sources:
            text = str(s.get("text", ""))
            if "fusion_summary" in str(s.get("source")) or "original_dataset_summary" in str(s.get("source")):
                sid = s.get("source")
                rid = s.get("record_id")
                return f"According to the dataset records: {text} [{sid}:{rid}]."

    # 4. General query: compile highest-scoring relevant findings
    top = sources[0]
    sid = top.get("source")
    rid = top.get("record_id")
    text = str(top.get("text", ""))
    return f"Based on retrieved record [{sid}:{rid}]: {text}"


def _complete_chat(token: str, system_prompt: str, user_prompt: str) -> str:
    model = os.getenv("HF_MODEL", DEFAULT_MODEL)
    try:
        response = httpx.post(
            HF_API_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 240,
            },
            timeout=25.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise LlmServiceError(
            f"The AI recommendation service returned HTTP {error.response.status_code}."
        ) from error
    except httpx.RequestError as error:
        raise LlmServiceError("The AI recommendation service is unavailable. Please try again later.") from error

    payload = response.json()
    choices = payload.get("choices") if isinstance(payload, dict) else None
    recommendation = None
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        message = choices[0].get("message")
        if isinstance(message, dict):
            recommendation = message.get("content")
    if not isinstance(recommendation, str) or not recommendation.strip():
        raise LlmServiceError("The AI recommendation service returned an invalid response.")
    return recommendation.strip()
