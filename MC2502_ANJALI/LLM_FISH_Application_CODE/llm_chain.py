"""
llm_chain.py
------------
Uses LangChain + Google Gemini (free tier) to:
  1. Generate a structured explanation for a fish species predicted by the CNN.
  2. Answer free-form follow-up questions about fish, with conversation memory,
     so the app can support a voice/text Q&A mode.

Requires GOOGLE_API_KEY to be set (see .env.example).
Get a free key at: https://aistudio.google.com/apikey
"""

import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from rag_utils import get_relevant_context

load_dotenv()

#MODEL_NAME = "gemini-3.6-flash"  # confirmed working — current stable Gemini model
MODEL_NAME = "gemini-3.5-flash-lite"
#MODEL_NAME = "gemini-3.6-flash"  # current stable, 
# Maps the language code used across the app (also gTTS codes) to a
# human-readable name the LLM prompt can refer to.
# Maps the language code used across the app (also gTTS codes) to a
# human-readable name the LLM prompt can refer to.
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
}


def _get_llm(temperature: float = 0.4):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GOOGLE_API_KEY not set. Copy .env.example to .env and add your key "
            "from https://aistudio.google.com/apikey"
        )
    return ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=temperature,
        google_api_key=api_key,
        timeout=30,       # fail fast instead of hanging indefinitely
        max_retries=2,    # avoid long silent retry loops on rate limits
    )


# ---------------------------------------------------------------------------
# 1) Structured "fish info card" generator — this is the CNN -> LLM handoff
# ---------------------------------------------------------------------------

FISH_INFO_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a marine biologist and culinary expert who writes clear, "
     "accurate, well-structured fact sheets about seafood fish sold in "
     "Indian fish markets. You are given REFERENCE FACTS retrieved from a "
     "curated knowledge base below — prefer these over your own assumptions "
     "whenever they cover the fish in question, since they are the verified "
     "source for this app. If the reference facts don't fully cover something "
     "(or don't mention this fish at all), fill the gap with your own "
     "reasonable knowledge, but never invent false precision on numbers. "
     "Write your ENTIRE response in {language}, including all section labels, "
     "translated naturally (do not leave any part in English unless "
     "{language} is English).\n\n"
     "REFERENCE FACTS:\n{context}"),
    ("human",
     "The fish in this photo was identified by an image classifier as: "
     "'{fish_name}' (a common Indian fish-market name). Confidence: {confidence:.1%}.\n\n"
     "Write a fact sheet with exactly these seven sections, translated into "
     "{language}, using short lines (not long paragraphs):\n\n"
     "Fish Name:\nScientific Name:\nHabitat:\nNutrition:\nAverage Weight:\n"
     "Cooking Uses:\nHealth Benefits:\n\n"
     "Keep the section labels themselves in {language} too. Keep it factual "
     "and concise, suitable for reading aloud via text-to-speech."),
])


def generate_fish_info(fish_name: str, confidence: float, language: str = "en") -> str:
    """Given the CNN's predicted label, retrieve grounding facts from the FAISS
    knowledge-base index (RAG), then ask the LLM to write the fact sheet in
    the requested language ('en', 'hi', or 'mr')."""
    llm = _get_llm(temperature=0.3)
    chain = FISH_INFO_PROMPT | llm | StrOutputParser()
    language_name = LANGUAGE_NAMES.get(language, "English")
    context = get_relevant_context(fish_name, k=3)
    return chain.invoke({
        "fish_name": fish_name,
        "confidence": confidence,
        "language": language_name,
        "context": context if context else "(no matching reference facts found)",
    })


# ---------------------------------------------------------------------------
# 2) Conversational Q&A chain with memory — for voice/text follow-up questions
# ---------------------------------------------------------------------------

QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a friendly assistant embedded in a fish-identification app. "
     "The user has just had a fish photo classified by a CNN model. You are "
     "given REFERENCE FACTS retrieved from a curated knowledge base below — "
     "use these when they're relevant to ground your answer, but you can also "
     "use your own general knowledge for anything the reference facts don't "
     "cover. Answer follow-up questions about fish species, cooking, "
     "nutrition, or sustainability concisely (2-4 sentences), in a tone "
     "suitable for text-to-speech playback.\n\n"
     "REFERENCE FACTS:\n{context}\n\n"
     "IMPORTANT: You must write your entire answer in {language} — every "
     "word, not just part of it — even though the reference facts above and "
     "the user's question may be in English. Do not mix languages."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}\n\n(Please answer entirely in {language}.)"),
])

_session_histories: dict[str, InMemoryChatMessageHistory] = {}


def _get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in _session_histories:
        _session_histories[session_id] = InMemoryChatMessageHistory()
    return _session_histories[session_id]


def get_qa_chain():
    llm = _get_llm(temperature=0.5)
    base_chain = QA_PROMPT | llm | StrOutputParser()
    return RunnableWithMessageHistory(
        base_chain,
        _get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )


def ask_followup(question: str, session_id: str = "default", language: str = "en") -> str:
    chain = get_qa_chain()
    language_name = LANGUAGE_NAMES.get(language, "English")
    context = get_relevant_context(question, k=3)
    return chain.invoke(
        {
            "input": question,
            "language": language_name,
            "context": context if context else "(no matching reference facts found)",
        },
        config={"configurable": {"session_id": session_id}},
    )


if __name__ == "__main__":
    # quick manual test
    print(generate_fish_info("Rohu", 0.94))
    print("\n---\n")
    print(ask_followup("Is this fish good for someone with high cholesterol?"))
