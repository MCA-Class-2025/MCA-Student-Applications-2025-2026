
# Compatibility layer:
# Existing RAG code imports generate_answer from this file.
# Actual answer generation is now handled by Groq.

from utils.groq_llm import generate_answer

__all__ = ["generate_answer"]
