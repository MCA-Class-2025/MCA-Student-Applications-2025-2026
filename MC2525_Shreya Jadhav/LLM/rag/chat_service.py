"""Single answer path shared by the Streamlit chat and regression tests."""

from __future__ import annotations

from LLM.rag.app_retriever import (
    format_app_context,
    retrieve_app_documents,
    retrieve_medical_documents,
)
from LLM.rag.curated_answers import curated_medical_answer
from LLM.rag.dataset_answers import answer_dataset_question
from LLM.rag.llm import ask_llm
from router import route
from Dashboard.utils.clinical_engine import analyze


def respond_to_question(question: str) -> dict:
    intent = route(question)
    assessment = None
    documents = []
    context = ""

    if intent == "greeting":
        answer = (
            "👋 Hi! Ask me about periods, PCOS, symptoms, or the "
            "FemCare dataset. What would you like to know?"
        )
    elif intent == "conversation":
        answer = (
            "You're welcome! Ask me about menstrual health, PCOS, "
            "symptoms, or the FemCare dataset."
        )
    elif intent == "clinical":
        assessment = analyze(question)
        if assessment["urgent_answer"]:
            # A deterministic response prevents the model from diluting urgent advice.
            answer = assessment["urgent_answer"]
        else:
            documents = retrieve_medical_documents(question)
            context = format_app_context(documents)
            answer = ask_llm(
                question=question,
                clinical_report=assessment["report"],
                context=context,
                mode="clinical",
            )
    else:
        dataset_result = answer_dataset_question(question)
        if dataset_result:
            answer, document = dataset_result
            documents = [document]
            context = format_app_context(documents)
        else:
            documents = retrieve_app_documents(question)
            context = format_app_context(documents)
            answer = curated_medical_answer(question, documents)
            if answer is None:
                answer = ask_llm(question=question, context=context, mode="knowledge")

    return {
        "answer": answer,
        "intent": intent,
        "assessment": assessment,
        "documents": documents,
        "context": context,
    }
