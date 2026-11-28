"""
rag_pipeline.py
----------------
Phase 7 of the RAG pipeline: ties together the retriever, prompt template,
and the Groq-hosted LLM (Llama 3) to produce grounded, cited answers.

Dataset Collection -> Loader -> Preprocessing -> Chunking -> Embeddings ->
Vector DB -> Retriever -> Prompt Template -> LLM -> Generated Response
"""

import os
from typing import List, Dict, Optional

from src.embeddings import embed_query
from src.vector_store import PolicyVectorStore


SYSTEM_PROMPT = """You are PolicyPal, a helpful and precise HR & company-policy assistant for NimbusTech Solutions.

Rules you must follow strictly:
1. Answer ONLY using the information given in the "Context" section below. Do not use outside knowledge.
2. If the answer is not present in the context, say clearly: "I couldn't find this in the company policy documents. Please check with HR directly." Do not guess or fabricate policy details.
3. Be concise, warm, and professional -- like a knowledgeable HR colleague, not a legal document.
4. When helpful, use short bullet points for multi-part answers (e.g., leave entitlements, approval steps).
5. Always stay consistent with the exact numbers, days, and amounts stated in the context -- never round or alter them, regardless of what language you are answering in.
6. If multiple policies are relevant, briefly mention which policy area(s) the answer draws from.
7. Your VERY FIRST LINE must be exactly one of: "COVERAGE: FULL", "COVERAGE: PARTIAL", or "COVERAGE: NONE" \
-- FULL if the context directly and completely answers the question, PARTIAL if the context is related but \
missing specifics (e.g. the topic is covered but not the exact number asked), NONE if the context does not \
address the question at all. This is a self-assessment used to show the employee how much to trust the \
answer -- do not skip it, and do not let retrieval similarity alone decide it; base it on whether the \
context actually contains the answer.
"""

EMPLOYEE_PROFILE_INSTRUCTION = """
Employee context for this conversation:
- Employment type: {employment_type}
- Tenure: {tenure_months} months

Apply this to eligibility rules found in the context (e.g. probation periods, minimum service \
requirements, "completed 80 working days" type conditions). If the employee does NOT meet an \
eligibility condition stated in the context, say so explicitly rather than giving a generic answer \
that assumes they qualify. If the context doesn't mention any eligibility condition relevant to the \
question, employment type/tenure don't need to be brought up.
"""

LANGUAGE_INSTRUCTION = """
Respond in {language}. Keep all numbers, dates, and amounts exactly as stated in the context \
regardless of language -- translate the surrounding sentence, never the figures themselves.
"""


def build_system_prompt(employee_profile: Optional[Dict] = None, language: str = "English") -> str:
    """
    Builds the final system prompt, optionally appending employee-eligibility
    context and a language instruction. Kept as a separate function (rather
    than always concatenating empty strings) so the base prompt stays
    readable/testable on its own.
    """
    prompt = SYSTEM_PROMPT
    if employee_profile and employee_profile.get("employment_type") and employee_profile.get("tenure_months") is not None:
        prompt += EMPLOYEE_PROFILE_INSTRUCTION.format(
            employment_type=employee_profile["employment_type"],
            tenure_months=employee_profile["tenure_months"],
        )
    if language and language.lower() != "english":
        prompt += LANGUAGE_INSTRUCTION.format(language=language)
    return prompt

USER_PROMPT_TEMPLATE = """Context (retrieved from company policy documents):
---------------------
{context}
---------------------

Conversation so far (most recent last):
{history}

Employee's question: {question}

Answer the employee's question using only the context above."""


def split_coverage_tag(raw_answer: str) -> Dict:
    """
    Parses the model's self-reported "COVERAGE: FULL/PARTIAL/NONE" first line
    out of the raw response. Falls back to "PARTIAL" (a neutral middle
    ground, not a false "FULL") if the model didn't follow the format --
    this happens occasionally with any LLM and should degrade honestly
    rather than crash or silently claim full confidence.
    """
    lines = raw_answer.strip().split("\n", 1)
    first_line = lines[0].strip().upper()
    if first_line.startswith("COVERAGE:"):
        level = first_line.replace("COVERAGE:", "").strip()
        if level not in ("FULL", "PARTIAL", "NONE"):
            level = "PARTIAL"
        answer_text = lines[1].strip() if len(lines) > 1 else ""
        return {"coverage": level, "answer": answer_text}
    return {"coverage": "PARTIAL", "answer": raw_answer.strip()}


def build_context(retrieved_chunks: List[Dict]) -> str:
    """Formats retrieved chunks into a numbered context block with source attribution."""
    if not retrieved_chunks:
        return "No relevant policy content was found."
    parts = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        parts.append(
            f"[Source {i}: {chunk['doc_title']} ({chunk['source_file']})]\n{chunk['text']}"
        )
    return "\n\n".join(parts)


def build_history_text(history: List[Dict], max_turns: int = 4) -> str:
    """Formats the last few turns of conversation for context continuity."""
    if not history:
        return "(no previous conversation)"
    recent = history[-max_turns:]
    lines = []
    for turn in recent:
        lines.append(f"Employee: {turn['question']}")
        lines.append(f"PolicyPal: {turn['answer']}")
    return "\n".join(lines)


def retrieve(query: str, vector_store: PolicyVectorStore, cohere_api_key: str,
             top_k: int = 4) -> List[Dict]:
    """Embeds the query (via Cohere) and retrieves the top_k most relevant chunks."""
    query_vec = embed_query(query, api_key=cohere_api_key)
    return vector_store.search(query_vec, top_k=top_k)


def call_groq_llm(system_prompt: str, user_prompt: str, api_key: str,
                   model: str = "openai/gpt-oss-120b", temperature: float = 0.2,
                   max_tokens: int = 800) -> str:
    """Calls the Groq API (OpenAI-compatible) to generate the final answer (non-streaming)."""
    from groq import Groq

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def stream_groq_llm(system_prompt: str, user_prompt: str, api_key: str,
                     model: str = "openai/gpt-oss-120b", temperature: float = 0.2,
                     max_tokens: int = 800, coverage_result: Optional[Dict] = None):
    """
    Calls the Groq API in streaming mode and yields text chunks as they arrive,
    for a live 'typing' effect via st.write_stream.

    The model's response starts with a "COVERAGE: FULL/PARTIAL/NONE" line
    (see SYSTEM_PROMPT) that should not be shown to the user as part of the
    answer. This buffers only up to that first line, parses it into
    `coverage_result` (a dict passed by the caller, mutated in place since a
    generator can't both yield chunks and return a value), then streams the
    rest of the answer through untouched.
    """
    from groq import Groq

    client = Groq(api_key=api_key)
    stream = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )

    buffer = ""
    header_resolved = False
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if not delta:
            continue
        if header_resolved:
            yield delta
            continue

        buffer += delta
        if "\n" in buffer:
            first_line, rest = buffer.split("\n", 1)
            level = first_line.strip().upper().replace("COVERAGE:", "").strip()
            if level not in ("FULL", "PARTIAL", "NONE"):
                level = "PARTIAL"
                rest = buffer.strip()  # model didn't use the tag format -- treat the whole buffer as the answer
            if coverage_result is not None:
                coverage_result["coverage"] = level
            header_resolved = True
            if rest:
                yield rest
    # if the stream ended before we ever saw a newline, the whole response
    # might STILL be just the coverage tag with nothing after it (or a very
    # short answer with no tag at all) -- try parsing it the same way as the
    # non-streaming path rather than assuming PARTIAL and leaking the raw tag.
    if not header_resolved and buffer:
        parsed = split_coverage_tag(buffer)
        if coverage_result is not None:
            coverage_result["coverage"] = parsed["coverage"]
        if parsed["answer"]:
            yield parsed["answer"]


def prepare_answer(
    question: str,
    vector_store: PolicyVectorStore,
    cohere_api_key: str,
    history: Optional[List[Dict]] = None,
    top_k: int = 4,
    employee_profile: Optional[Dict] = None,
    language: str = "English",
) -> Dict:
    """
    Runs retrieval and builds the final prompt, WITHOUT calling the LLM.
    Split out from answer_question() so the UI can stream the generation step
    separately (retrieval isn't naturally 'streamable', but generation is).
    Returns: {system_prompt, user_prompt, sources, error}
    """
    history = history or []
    try:
        retrieved = retrieve(question, vector_store, cohere_api_key=cohere_api_key, top_k=top_k)
    except Exception as e:
        return {"system_prompt": None, "user_prompt": None, "sources": [], "error": f"Embedding error: {e}"}

    context = build_context(retrieved)
    history_text = build_history_text(history)
    user_prompt = USER_PROMPT_TEMPLATE.format(context=context, history=history_text, question=question)
    system_prompt = build_system_prompt(employee_profile=employee_profile, language=language)

    return {"system_prompt": system_prompt, "user_prompt": user_prompt, "sources": retrieved, "error": None}


def answer_question(
    question: str,
    vector_store: PolicyVectorStore,
    groq_api_key: str,
    cohere_api_key: str,
    history: Optional[List[Dict]] = None,
    top_k: int = 4,
    llm_model: str = "openai/gpt-oss-120b",
    employee_profile: Optional[Dict] = None,
    language: str = "English",
) -> Dict:
    """
    Full RAG call: retrieve relevant chunks -> build prompt -> call LLM -> return
    answer plus the source chunks used, for UI display and citation.
    """
    history = history or []

    try:
        retrieved = retrieve(question, vector_store, cohere_api_key=cohere_api_key, top_k=top_k)
    except Exception as e:
        return {"answer": None, "error": f"Embedding error: {e}", "sources": []}
    context = build_context(retrieved)
    history_text = build_history_text(history)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        context=context, history=history_text, question=question
    )
    system_prompt = build_system_prompt(employee_profile=employee_profile, language=language)

    try:
        raw_answer = call_groq_llm(system_prompt, user_prompt, api_key=groq_api_key, model=llm_model)
    except Exception as e:
        return {
            "answer": None,
            "coverage": None,
            "error": str(e),
            "sources": retrieved,
        }

    parsed = split_coverage_tag(raw_answer)
    return {
        "answer": parsed["answer"],
        "coverage": parsed["coverage"],
        "error": None,
        "sources": retrieved,
    }
