"""
llm/chatbot.py — RAG-powered chatbot for drug safety Q&A.

Implements:
- Conversation history
- Medicine context awareness
- RAG retrieval before LLM generation
- Source attribution
- Medical safety guardrails
"""

import time
from typing import Any, Dict, List, Optional, Tuple

from llm.client import LLMClient
from llm.prompts import SYSTEM_PROMPT, RAG_PROMPT_TEMPLATE, EVALUATION_PROMPT
from rag.rag_pipeline import RAGPipeline
from utils.logging import logger


class DrugSafetyChatbot:
    """
    RAG-powered drug safety Q&A chatbot.

    The chatbot always retrieves relevant evidence before generating an answer.
    It NEVER answers solely from LLM training data for drug safety questions.
    """

    def __init__(
        self,
        rag_pipeline: Optional[RAGPipeline] = None,
        llm_client: Optional[LLMClient] = None,
    ):
        self.rag = rag_pipeline
        self.llm = llm_client or LLMClient()
        self.history: List[Dict[str, str]] = []
        self.current_drug: Optional[str] = None

    def set_drug_context(self, drug_name: str, rag_pipeline: RAGPipeline) -> None:
        """Set the current medicine context and RAG pipeline."""
        self.current_drug = drug_name
        self.rag = rag_pipeline
        # Don't clear history so follow-up questions work
        logger.info(f"Chatbot context set to: {drug_name}")

    def ask(
        self,
        question: str,
        top_k: int = 6,
    ) -> Dict[str, Any]:
        """
        Process a user question through the RAG pipeline.

        1. Retrieve relevant chunks from FAISS
        2. Format context
        3. Build prompt with history
        4. Call LLM
        5. Return answer with sources

        Returns:
            dict with: answer, retrieved_chunks, sources, context, latency_ms, error
        """
        t0 = time.time()

        result: Dict[str, Any] = {
            "question": question,
            "answer": "",
            "retrieved_chunks": [],
            "sources": [],
            "context": "",
            "latency_ms": 0,
            "drug_name": self.current_drug,
            "rag_used": False,
            "error": None,
        }

        # ── Step 1: Retrieve relevant evidence ────────────────────────────
        if self.rag and self.rag.is_ready:
            try:
                retrieved = self.rag.query(question, top_k=top_k)
                result["retrieved_chunks"] = retrieved
                result["sources"] = self.rag.retriever.get_source_summary(retrieved)
                result["context"] = self.rag.retriever.format_context(retrieved)
                result["rag_used"] = True
            except Exception as e:
                logger.error(f"RAG retrieval failed: {e}")
                result["error"] = f"RAG retrieval error: {e}"
        else:
            result["context"] = "No drug knowledge base available. Please analyze a drug first."

        # ── Step 2: Build LLM prompt ───────────────────────────────────────
        user_content = RAG_PROMPT_TEMPLATE.format(
            context=result["context"],
            question=question,
        )

        # Build messages with history (last 4 exchanges = 8 messages)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        for h in self.history[-8:]:
            messages.append({"role": h["role"], "content": h["content"]})

        messages.append({"role": "user", "content": user_content})

        # ── Step 3: Call LLM ───────────────────────────────────────────────
        llm_result = self.llm.chat(messages, max_tokens=1500, temperature=0.1)
        result["answer"] = llm_result["content"]
        result["latency_ms"] = round((time.time() - t0) * 1000)

        if llm_result.get("error"):
            result["error"] = llm_result["error"]

        # ── Step 4: Update history ─────────────────────────────────────────
        self.history.append({"role": "user", "content": question})
        self.history.append({"role": "assistant", "content": result["answer"]})

        logger.info(
            f"Chatbot response: drug='{self.current_drug}', "
            f"retrieved={len(result['retrieved_chunks'])} chunks, "
            f"latency={result['latency_ms']}ms"
        )
        return result

    def clear_history(self) -> None:
        """Reset conversation history."""
        self.history = []
        logger.info("Chatbot history cleared")

    def evaluate_response(
        self,
        question: str,
        context: str,
        answer: str,
    ) -> Dict[str, Any]:
        """
        Basic RAG evaluation: check if answer is grounded.
        Returns evaluation metrics.
        """
        eval_prompt = EVALUATION_PROMPT.format(
            question=question,
            context=context[:2000],
            answer=answer[:1000],
        )
        messages = [
            {"role": "system", "content": "You are a RAG system evaluator. Return only valid JSON."},
            {"role": "user", "content": eval_prompt},
        ]
        try:
            response = self.llm.chat(messages, max_tokens=300, temperature=0.0)
            import json
            # Try to parse JSON from response
            content = response["content"]
            # Find JSON object in response
            import re
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"RAG evaluation failed: {e}")
        return {"grounded": None, "sources_cited": None, "score": None}
