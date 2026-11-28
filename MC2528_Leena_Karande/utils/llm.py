"""Gemini generation helpers; embeddings and FAISS retrieval stay local."""

from __future__ import annotations

import os
import time

import streamlit as st

try:
    from google import genai
    from google.genai import types
    GEMINI_SDK_AVAILABLE = True
except ImportError:
    GEMINI_SDK_AVAILABLE = False


GEMINI_MODELS = ("gemini-3.6-flash", "gemini-3.5-flash-lite")


def get_gemini_api_key() -> str:
    return st.session_state.get("gemini_api_key") or os.getenv("GEMINI_API_KEY", "")


def gemini_available() -> bool:
    return GEMINI_SDK_AVAILABLE and bool(get_gemini_api_key())


@st.cache_resource(show_spinner=False)
def _client(api_key: str):
    return genai.Client(api_key=api_key)


def ask_llm(system_prompt: str, user_prompt, *, max_tokens: int = 2048,
            image_bytes: bytes | None = None, image_mime_type: str = "image/jpeg",
            minimum_words: int = 0) -> str:
    """Generate through Gemini after the app has retrieved local evidence."""
    if not gemini_available():
        raise RuntimeError("Add a Gemini API key in the sidebar to use AI generation.")
    contents = user_prompt
    if image_bytes:
        contents = [user_prompt, types.Part.from_bytes(data=image_bytes, mime_type=image_mime_type)]

    # NOTE: an earlier attempt to cap gemini-3.6-flash's internal
    # "thinking" tokens via ThinkingConfig(thinking_budget=0) turned out
    # to be rejected outright by the API (400 INVALID_ARGUMENT) rather
    # than silently ignored, breaking every single call. We don't have a
    # way to verify the exact accepted parameter shape for this SDK
    # version from here, so instead of guessing again, we just give the
    # call a generous max_output_tokens ceiling -- enough headroom for
    # thinking *and* a full visible answer -- which needs no
    # model-specific parameter and can't itself be rejected as invalid.
    config = types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.2, max_output_tokens=max_tokens)

    last_error = None
    for model in GEMINI_MODELS:
        for attempt in range(2):
            try:
                response = _client(get_gemini_api_key()).models.generate_content(
                    model=model, contents=contents, config=config,
                )
                answer = (response.text or "").strip()
                if answer and len(answer.split()) >= minimum_words:
                    return answer
                last_error = RuntimeError("Gemini returned an incomplete response.")
            except Exception as exc:
                last_error = exc
                if "503" not in str(exc):
                    break
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Gemini is temporarily busy. Please try again in a minute. Details: {last_error}")


def generate_rag_answer(query: str, context_chunks: list[dict], *, domain_instructions: str | None = None,
                         conversation_history: str = "", max_tokens: int = 2048) -> str:
    blocks = []
    for chunk in context_chunks:
        name = chunk.get("name")
        header = f"[Source: {name}]" if name else None
        source_tag = "" if chunk.get("has_enrichment") else " (curated dataset only, no open-data enrichment on file)"
        block = f"{header}{source_tag}\n{chunk['text']}" if header else chunk["text"]
        blocks.append(block)
    context = "\n\n---\n\n".join(blocks)
    system = domain_instructions or "Answer only from provided context. State when it is insufficient."
    history_block = f"Recent conversation (for context on follow-up questions like 'it' or 'that one'):\n{conversation_history}\n\n" if conversation_history else ""
    prompt = f"{history_block}Context (each block is one dance form's full profile):\n\n{context}\n\nQuestion: {query}"
    return ask_llm(system, prompt, max_tokens=max_tokens)


def translate_local(text: str, target_language: str) -> str:
    return ask_llm(
        "Translate the COMPLETE text faithfully. Preserve every paragraph, bullet, fact, number, and Markdown emphasis. "
        "Return only the complete translation; never summarize, shorten, or omit content.",
        f"Translate into {target_language}:\n\n{text}",
        max_tokens=1600,
        minimum_words=max(10, len(text.split()) // 3),
    )
