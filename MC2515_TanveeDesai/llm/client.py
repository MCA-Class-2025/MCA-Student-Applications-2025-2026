"""
llm/client.py — LLM client abstraction.

Supports OpenAI API (and compatible providers) plus Groq's free tier.
API keys read from environment — never hardcoded.
"""

import time
from typing import Any, Dict, List, Optional

from config.settings import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL, GROQ_API_KEY, GROQ_MODEL
from utils.logging import logger

# ── Groq (free-tier provider) ─────────────────────────────────────────────────
GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class LLMClient:
    """
    Abstraction over OpenAI-compatible chat APIs.

    Provider selection (priority order):
      1. GROQ_API_KEY set  → Groq's free API (model: GROQ_MODEL or default)
      2. OPENAI_API_KEY    → OpenAI (or OPENAI_BASE_URL compatible provider)
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or OPENAI_MODEL
        self.base_url = OPENAI_BASE_URL or None

        if GROQ_API_KEY:
            self.api_key = GROQ_API_KEY
            self.model = model or GROQ_MODEL
            self.base_url = GROQ_BASE_URL
            logger.info("LLMClient using Groq API (free tier)")
        elif self.api_key:
            logger.info(f"LLMClient using OpenAI-compatible API ({self.base_url or 'default OpenAI'})")

        self._client = None
        self._available = bool(self.api_key)

        if not self._available:
            logger.warning(
                "No LLM API key configured. LLM features will be unavailable. "
                "Set OPENAI_API_KEY or GROQ_API_KEY (free at https://console.groq.com) "
                "in your .env file."
            )

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            except ImportError:
                raise RuntimeError("openai package not installed. Run: pip install openai")
        return self._client

    @property
    def is_available(self) -> bool:
        return self._available

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1500,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Send a chat request to the LLM.

        Returns:
            dict with keys: content, model, usage, latency_ms, error
        """
        result: Dict[str, Any] = {
            "content": "",
            "model": self.model,
            "usage": {},
            "latency_ms": 0,
            "error": None,
        }

        if not self._available:
            result["error"] = "LLM API key not configured"
            result["content"] = (
                "**LLM unavailable** — no API key is set.\n\n"
                "To enable the AI assistant:\n"
                "1. Get a free key at https://console.groq.com/keys\n"
                "2. Set GROQ_API_KEY in your .env file\n"
                "3. Restart the application\n\n"
                "The retrieved evidence below is still available for your review."
            )
            return result

        t0 = time.time()
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            message = response.choices[0].message
            content = message.content or ""
            if not content.strip() and getattr(message, "reasoning", None):
                # Reasoning models (e.g. Groq's gpt-oss) may burn the whole
                # token budget on reasoning — retry with more headroom.
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max(max_tokens * 3, 1000),
                    temperature=temperature,
                )
                message = response.choices[0].message
                content = message.content or ""
            result["content"] = content
            result["usage"] = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
            result["latency_ms"] = round((time.time() - t0) * 1000)
            logger.info(
                f"LLM response: {result['usage'].get('total_tokens', 0)} tokens, "
                f"{result['latency_ms']}ms"
            )
        except Exception as e:
            result["error"] = str(e)
            result["content"] = _friendly_error_message(str(e))
            logger.error(f"LLM API error: {e}")

        return result

    def simple_completion(
        self,
        system: str,
        user: str,
        max_tokens: int = 1500,
    ) -> str:
        """Convenience method for simple system + user message."""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        result = self.chat(messages, max_tokens=max_tokens)
        return result["content"]


def _friendly_error_message(error_text: str) -> str:
    """Turn raw provider errors into actionable, friendly messages."""
    text = (error_text or "").lower()
    if "429" in error_text and ("quota" in text or "insufficient_quota" in text):
        return (
            "**LLM quota exceeded** — your API account has no remaining "
            "credits/billing quota, so the AI assistant cannot respond.\n\n"
            "To fix this:\n"
            "1. Check billing at https://platform.openai.com/account/billing "
            "(add credits to your account), or\n"
            "2. Use another provider — set `OPENAI_BASE_URL` + `OPENAI_API_KEY` "
            "in your `.env` (e.g., Groq, OpenRouter, or a local Ollama/LM Studio "
            "endpoint).\n\n"
            "The retrieved evidence shown in this app remains available for "
            "your review."
        )
    if "invalid_api_key" in text or "401" in error_text:
        return (
            "**Invalid API key** — the `OPENAI_API_KEY` in your `.env` file "
            "was rejected. Double-check the key at https://platform.openai.com/api-keys "
            "and restart the app."
        )
    if "connection" in text or "timed out" in text:
        return (
            "**Could not reach the LLM provider** — check your internet "
            "connection and that `OPENAI_BASE_URL` (if set) is reachable. "
            "The retrieved evidence below is still available."
        )
    return f"Error calling LLM: {error_text}"
