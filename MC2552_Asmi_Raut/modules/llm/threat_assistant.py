import os

from dotenv import load_dotenv

from modules.llm.ollama_llm import generate as ollama_generate
from modules.llm.groq_llm import generate as groq_generate

load_dotenv()


def generate_answer(prompt):

    provider = os.getenv(
        "LLM_PROVIDER",
        "ollama"
    ).lower()

    if provider == "groq":

        return groq_generate(prompt)

    return ollama_generate(prompt)