import json
import re
import asyncio
from typing import Any, Dict

from groq import Groq

from app.config.settings import settings


class VoiceService:

    # ============================================================
    # GROQ CLIENT
    # ============================================================

    @classmethod
    def _get_client(cls) -> Groq:
        api_key = getattr(
            settings,
            "GROQ_API_KEY",
            None
        )

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is missing. "
                "Add a valid Groq API key to your .env file."
            )

        return Groq(
            api_key=api_key
        )

    # ============================================================
    # MODEL
    # ============================================================

    @classmethod
    def _get_model(cls) -> str:
        model = getattr(
            settings,
            "GROQ_MODEL",
            None
        )

        # Current Groq documentation continues to list this
        # model for Chat Completions.
        return (
            str(model).strip()
            if model
            else "llama-3.3-70b-versatile"
        )

    # ============================================================
    # EXTRACT JSON OBJECT
    # ============================================================

    @staticmethod
    def _extract_json(content: str) -> Dict[str, Any]:

        if not content:
            raise ValueError(
                "Groq returned an empty response."
            )

        content = content.strip()

        # Remove markdown code fences.
        content = re.sub(
            r"^```(?:json)?\s*",
            "",
            content,
            flags=re.IGNORECASE
        )

        content = re.sub(
            r"\s*```$",
            "",
            content
        ).strip()

        # First attempt: complete response is JSON.
        try:
            parsed = json.loads(content)

            if isinstance(parsed, dict):
                return parsed

        except json.JSONDecodeError:
            pass

        # Second attempt: find the first JSON object.
        match = re.search(
            r"\{[\s\S]*\}",
            content
        )

        if match:
            try:
                parsed = json.loads(
                    match.group(0)
                )

                if isinstance(parsed, dict):
                    return parsed

            except json.JSONDecodeError:
                pass

        raise ValueError(
            "AI returned invalid JSON."
        )

    # ============================================================
    # NORMALIZE CATEGORY
    # ============================================================

    @staticmethod
    def _normalize_category(
        value: Any
    ) -> str:

        allowed = {
            "food": "Food",
            "groceries": "Groceries",
            "grocery": "Groceries",
            "shopping": "Shopping",
            "travel": "Travel",
            "transport": "Transport",
            "transportation": "Transport",
            "fuel": "Fuel",
            "healthcare": "Healthcare",
            "health": "Healthcare",
            "medical": "Healthcare",
            "entertainment": "Entertainment",
            "bills": "Bills",
            "bill": "Bills",
            "education": "Education",
            "other": "Other",
        }

        value = str(
            value or "Other"
        ).strip()

        return allowed.get(
            value.lower(),
            "Other"
        )

    # ============================================================
    # NORMALIZE PAYMENT METHOD
    # ============================================================

    @staticmethod
    def _normalize_payment_method(
        value: Any
    ) -> str:

        allowed = {
            "upi": "UPI",
            "cash": "Cash",
            "credit card": "Credit Card",
            "creditcard": "Credit Card",
            "debit card": "Debit Card",
            "debitcard": "Debit Card",
            "net banking": "Net Banking",
            "netbanking": "Net Banking",
            "online banking": "Net Banking",
            "other": "Other",
        }

        value = str(
            value or "Other"
        ).strip()

        return allowed.get(
            value.lower(),
            "Other"
        )

    # ============================================================
    # PARSE AMOUNT
    # ============================================================

    @staticmethod
    def _normalize_amount(
        value: Any
    ) -> float:

        if value is None:
            return 0.0

        if isinstance(
            value,
            (int, float)
        ):
            amount = float(value)

        else:
            cleaned = re.sub(
                r"[^\d.]",
                "",
                str(value)
            )

            if not cleaned:
                return 0.0

            try:
                amount = float(cleaned)
            except ValueError:
                return 0.0

        if amount < 0:
            return 0.0

        return round(
            amount,
            2
        )

    # ============================================================
    # PARSE VOICE EXPENSE
    # ============================================================

    @classmethod
    async def parse_expense(
        cls,
        transcript: str
    ):

        transcript = str(
            transcript or ""
        ).strip()

        if not transcript:
            raise ValueError(
                "Voice transcript cannot be empty."
            )

        prompt = f"""
You are an expense extraction assistant.

Convert the user's voice sentence into ONE structured
expense object.

User sentence:
{transcript}

Return ONLY a JSON object.

Use exactly these fields:

{{
  "title": "short expense title",
  "amount": 0,
  "category": "Food",
  "payment_method": "UPI",
  "notes": ""
}}

Rules:

1. amount must be a positive number.
2. If the user says rupees, INR or ₹, convert it to a number.
3. Understand natural phrases such as:
   - five hundred rupees -> 500
   - 1,200 rupees -> 1200
   - one thousand five hundred -> 1500
4. Use one of these categories:
   Food
   Groceries
   Shopping
   Travel
   Transport
   Fuel
   Healthcare
   Entertainment
   Bills
   Education
   Other
5. Use one of these payment methods:
   UPI
   Cash
   Credit Card
   Debit Card
   Net Banking
   Other
6. Keep title short and natural.
7. notes should contain useful extra information only.
8. Do not add markdown.
9. Do not add explanations.
10. Return exactly one JSON object.
"""

        client = cls._get_client()
        model = cls._get_model()

        try:

            # Groq's Chat Completions API is synchronous, so run it
            # outside the FastAPI event loop.
            response = await asyncio.to_thread(
                client.chat.completions.create,

                model=model,

                messages=[
                    {
                        "role": "system",
                        "content":
                            "You extract expense information from natural language. "
                            "Return valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                temperature=0,

                max_tokens=300,

            )

        except Exception as exc:

            # Print the real backend error in the terminal.
            # Do not expose secrets.
            status_code = getattr(
                exc,
                "status_code",
                None
            )

            error_body = getattr(
                exc,
                "body",
                None
            )

            print(
                "\n========== GROQ VOICE ERROR =========="
            )

            print(
                "Model:",
                model
            )

            print(
                "Status:",
                status_code
            )

            print(
                "Body:",
                error_body
            )

            print(
                "Error:",
                str(exc)
            )

            print(
                "=======================================\n"
            )

            raise RuntimeError(
                f"Groq voice parsing failed "
                f"(status={status_code or 'unknown'}). "
                f"Check GROQ_MODEL and GROQ_API_KEY."
            ) from exc

        try:

            content = (
                response
                .choices[0]
                .message
                .content
            )

        except (
            AttributeError,
            IndexError,
            TypeError
        ) as exc:

            raise RuntimeError(
                "Groq returned an unexpected response."
            ) from exc

        data = cls._extract_json(
            content
        )

        title = str(
            data.get(
                "title",
                "Voice Expense"
            )
            or "Voice Expense"
        ).strip()

        amount = cls._normalize_amount(
            data.get(
                "amount",
                0
            )
        )

        category = (
            cls
            ._normalize_category(
                data.get(
                    "category",
                    "Other"
                )
            )
        )

        payment_method = (
            cls
            ._normalize_payment_method(
                data.get(
                    "payment_method",
                    "Other"
                )
            )
        )

        notes = str(
            data.get(
                "notes",
                ""
            )
            or ""
        ).strip()

        if amount <= 0:

            raise ValueError(
                "The voice input did not contain a valid expense amount."
            )

        return {

            "title":
                title,

            "amount":
                amount,

            "category":
                category,

            "payment_method":
                payment_method,

            "notes":
                notes,

        }