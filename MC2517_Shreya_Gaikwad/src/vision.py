"""
vision.py
---------
Multimodal extension to the RAG pipeline: lets an employee photograph a
printed or scanned policy notice and ask a question about it. The image and
question are sent together to a natively multimodal model (single model,
joint image+text input) — not a separate OCR-then-text pipeline — and the
answer is cross-checked against whatever the text knowledge base already
has indexed on the same topic, so contradictions between a photo and the
official digital policy get surfaced explicitly rather than silently
resolved one way.

This is the real reason a photo mode belongs in an HR policy tool: printed
noticeboards, scanned legacy handbooks, and photographed memos are genuine,
common sources of policy info that are NOT always in sync with the digital
policy documents — the tool should say so when it finds a mismatch, not
pick one silently.
"""

import base64
from typing import List, Dict, Optional

from src.rag_pipeline import build_context
from src.vector_store import PolicyVectorStore
from src.embeddings import embed_query

VISION_MODEL = "qwen/qwen3.6-27b"  # verify current name at console.groq.com/docs/vision before submission

VISION_SYSTEM_PROMPT = """You are PolicyPal, NimbusTech's HR & company-policy assistant. You are shown \
a photo of a printed or scanned policy document, plus the employee's question, plus relevant excerpts \
from the official digital policy database for cross-reference.

Rules:
1. Read the photo carefully — it is the primary source for what it directly shows.
2. Use the official digital excerpts to add context or fill gaps the photo doesn't cover.
3. If the photo and the official digital excerpts disagree on a specific fact (a number, a deadline, \
a rule), say so explicitly and flag it as a discrepancy for HR to resolve — do not silently prefer one.
4. If the photo is unreadable, blurry, or doesn't relate to the question, say so rather than guessing.
5. Be concise and precise on numbers.
"""


def encode_image(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def retrieve_for_image_query(
    query: str, vector_store: PolicyVectorStore, cohere_api_key: str, top_k: int = 4
) -> List[Dict]:
    """Same retrieval path as the text pipeline, reused so photo answers are
    cross-checked against the same indexed knowledge base."""
    if vector_store is None or vector_store.index.ntotal == 0:
        return []
    query_vec = embed_query(query, api_key=cohere_api_key)
    return vector_store.search(query_vec, top_k=top_k)


def answer_image_question(
    groq_api_key: str,
    image_bytes: bytes,
    question: str,
    vector_store: Optional[PolicyVectorStore] = None,
    cohere_api_key: Optional[str] = None,
    mime_type: str = "image/jpeg",
    top_k: int = 4,
) -> Dict:
    """
    Returns {"answer": str, "sources": list, "error": str|None}.
    `sources` are the text-KB chunks used for cross-reference (may be empty
    if no vector store / Cohere key is available — the photo can still be
    answered on its own in that case, just without cross-referencing).
    """
    from groq import Groq

    sources = []
    if vector_store is not None and cohere_api_key:
        try:
            sources = retrieve_for_image_query(question, vector_store, cohere_api_key, top_k=top_k)
        except Exception:
            sources = []  # cross-referencing is best-effort; don't block the photo answer on it

    context = build_context(sources) if sources else "No matching digital policy excerpts were found."
    b64_image = encode_image(image_bytes)

    user_content = [
        {
            "type": "text",
            "text": f"Official digital policy excerpts for cross-reference:\n\n{context}\n\n---\n\nEmployee's question about the photo: {question}",
        },
        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_image}"}},
    ]

    try:
        client = Groq(api_key=groq_api_key)
        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {"role": "system", "content": VISION_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
            max_tokens=700,
        )
        return {"answer": response.choices[0].message.content, "sources": sources, "error": None}
    except Exception as e:
        return {"answer": None, "sources": sources, "error": str(e)}
