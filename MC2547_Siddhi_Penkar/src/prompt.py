"""
prompt.py
---------
Defines the professional RAG prompt template used to instruct the LLM
to behave as an expert software debugging assistant.
"""

from typing import List, Dict

SYSTEM_ROLE = "You are an expert software debugging assistant."

RESPONSE_FORMAT_INSTRUCTIONS = """
Structure your response using EXACTLY the following sections:

1. Bug Summary
2. Possible Root Cause
3. Technical Explanation
4. Recommended Fix
5. Relevant Source Information

Be precise, technical, and base your answer strictly on the provided context.
If the context does not contain enough information to fully answer, say so
explicitly (e.g. "The provided documents do not contain enough information
to determine X") rather than guessing or inventing details.
"""


def format_context(retrieved_chunks: List[Dict]) -> str:
    """
    Formats retrieved document chunks into a readable context block for the LLM.

    Args:
        retrieved_chunks (List[Dict]): Chunks returned by semantic_search(),
            each containing 'text', 'source', 'chunk_id', and 'score'.

    Returns:
        str: Formatted context string.
    """
    context_blocks = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        source = chunk.get("source", "unknown")
        chunk_id = chunk.get("chunk_id", "?")
        score = chunk.get("score", 0.0)
        text = chunk.get("text", "")
        context_blocks.append(
            f"[Source {i}: {source} | chunk #{chunk_id} | relevance={score:.3f}]\n{text}"
        )
    return "\n\n".join(context_blocks)


def build_rag_prompt(user_query: str, retrieved_chunks: List[Dict]) -> str:
    """
    Builds the complete RAG prompt combining the system role, retrieved
    context, formatting instructions, and the user's query.

    Args:
        user_query (str): The user's bug-related question.
        retrieved_chunks (List[Dict]): Retrieved context chunks from semantic_search().

    Returns:
        str: The complete prompt string to send to the LLM.
    """
    context_text = format_context(retrieved_chunks)

    prompt = f"""{SYSTEM_ROLE}

You will be given a user's question about a software bug, along with relevant
excerpts retrieved from bug reports, logs, and technical documentation.
Use ONLY the provided context to answer. Do not invent information that is
not supported by the context.

--- CONTEXT START ---
{context_text}
--- CONTEXT END ---

USER QUESTION:
{user_query}

{RESPONSE_FORMAT_INSTRUCTIONS}
"""
    return prompt.strip()