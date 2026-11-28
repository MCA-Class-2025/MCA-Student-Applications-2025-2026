"""
llm.py
------
Integrates the Qwen2.5-1.5B-Instruct model (via HuggingFace Transformers)
to generate bug analysis responses using retrieved context (RAG).

The model and tokenizer are loaded once and cached as module-level
singletons to avoid reloading on every query.
"""

from typing import List, Dict

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from src.prompt import build_rag_prompt
from src.utils import MODELS_DIR, get_logger

logger = get_logger(__name__)

LLM_MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

_tokenizer_instance = None
_model_instance = None


class LLMError(Exception):
    """Raised when the LLM fails to load or generate a response."""
    pass


def _get_device() -> str:
    """Returns 'cuda' if a GPU is available, otherwise 'cpu'."""
    return "cuda" if torch.cuda.is_available() else "cpu"


def load_llm():
    """
    Loads (or returns cached instances of) the Qwen tokenizer and model.

    Returns:
        Tuple[AutoTokenizer, AutoModelForCausalLM]: Loaded tokenizer and model.

    Raises:
        LLMError: If the model or tokenizer fails to load.
    """
    global _tokenizer_instance, _model_instance

    if _tokenizer_instance is not None and _model_instance is not None:
        return _tokenizer_instance, _model_instance

    try:
        device = _get_device()
        logger.info(f"Loading LLM '{LLM_MODEL_NAME}' on device '{device}'...")

        _tokenizer_instance = AutoTokenizer.from_pretrained(
            LLM_MODEL_NAME, cache_dir=MODELS_DIR
        )
        _model_instance = AutoModelForCausalLM.from_pretrained(
            LLM_MODEL_NAME,
            cache_dir=MODELS_DIR,
            torch_dtype=torch.float32,
            device_map=None,
        ).to(device)

        logger.info("LLM loaded successfully.")

    except Exception as exc:
        logger.error(f"Failed to load LLM '{LLM_MODEL_NAME}': {exc}")
        raise LLMError(
            f"Could not load the language model '{LLM_MODEL_NAME}'. "
            f"Ensure you have sufficient memory/disk space and an internet "
            f"connection for the first download. Details: {exc}"
        )

    return _tokenizer_instance, _model_instance


def generate_response(
    user_query: str,
    retrieved_chunks: List[Dict],
    max_new_tokens: int = 120,
) -> str:

    if not user_query.strip():
        raise LLMError("Cannot generate a response for an empty query.")

    if not retrieved_chunks:
        raise LLMError("No retrieved context was provided.")

    try:
        tokenizer, model = load_llm()
        device = _get_device()

        # Reduce context size for faster generation
        for chunk in retrieved_chunks:
            chunk["text"] = chunk["text"][:500]

        prompt = build_rag_prompt(user_query, retrieved_chunks)

        messages = [
            {
                "role": "system",
                "content": "You are an expert software debugging assistant.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        text_input = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        model_inputs = tokenizer(
            [text_input],
            return_tensors="pt",
        ).to(device)

        with torch.no_grad():
            generated_ids = model.generate(
                **model_inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )

        generated_ids = [
            output_ids[len(input_ids):]
            for input_ids, output_ids in zip(
                model_inputs.input_ids,
                generated_ids,
            )
        ]

        response = tokenizer.batch_decode(
            generated_ids,
            skip_special_tokens=True,
        )[0].strip()

        if not response:
            raise LLMError("The model returned an empty response.")

        return response

    except LLMError:
        raise

    except Exception as exc:
        logger.error(f"LLM generation failed: {exc}")
        raise LLMError(f"Failed to generate a response: {exc}")
