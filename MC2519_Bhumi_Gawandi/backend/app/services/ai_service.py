# ============================================================
# app/services/ai_service.py
# ============================================================

import re

import httpx

from groq import AsyncGroq

from app.core.config import settings

from app.database.mongodb import database

from app.services.chat_history_service import (
    ChatHistoryService
)


# ============================================================
# AI SERVICE
# ============================================================

class AIService:

    # ========================================================
    # GROQ CLIENT
    # ========================================================

    @staticmethod
    def get_groq_client():

        api_key = getattr(
            settings,
            "GROQ_API_KEY",
            ""
        )

        if not api_key:

            raise ValueError(
                "GROQ_API_KEY is missing from .env"
            )

        return AsyncGroq(
            api_key=api_key
        )


    # ========================================================
    # GET AVAILABLE GROQ MODEL
    # ========================================================

    @staticmethod
    async def get_groq_model():

        client = (
            AIService
            .get_groq_client()
        )

        configured_model = getattr(
            settings,
            "GROQ_MODEL",
            "llama-3.1-8b-instant"
        )

        print(
            "========================================"
        )

        print(
            "GROQ CONFIGURED MODEL:",
            configured_model
        )

        print(
            "========================================"
        )


        try:

            models = (
                await client.models.list()
            )


            available_models = [

                model.id

                for model in models.data

                if getattr(
                    model,
                    "active",
                    True
                )

            ]


            print(
                "AVAILABLE GROQ MODELS:"
            )

            print(
                available_models
            )


            # ==================================================
            # USE CONFIGURED MODEL IF AVAILABLE
            # ==================================================

            if (
                configured_model
                in available_models
            ):

                print(
                    "USING CONFIGURED MODEL:",
                    configured_model
                )

                return configured_model


            # ==================================================
            # SAFE FALLBACK
            # ==================================================

            fallback_models = [

                "llama-3.1-8b-instant",

                "openai/gpt-oss-20b",

                "llama-3.3-70b-versatile",

            ]


            for fallback in fallback_models:

                if (
                    fallback
                    in available_models
                ):

                    print(
                        "USING FALLBACK MODEL:",
                        fallback
                    )

                    return fallback


            raise ValueError(

                "No supported Groq chat model "
                "is available for this API key."

            )


        except Exception as e:

            print(
                "GROQ MODEL LIST ERROR:",
                repr(e)
            )

            # ==================================================
            # FALLBACK WITHOUT MODEL LIST
            # ==================================================

            return (
                "llama-3.1-8b-instant"
            )


    # ========================================================
    # CLEAN RESPONSE
    # ========================================================

    @staticmethod
    def clean_ai_response(
        text
    ):

        if not text:

            return (
                "Sorry, I could not generate "
                "a response right now."
            )


        cleaned = str(
            text
        )


        cleaned = re.sub(

            r"^\s*#{1,6}\s*",

            "",

            cleaned,

            flags=re.MULTILINE

        )


        cleaned = re.sub(

            r"\*\*(.*?)\*\*",

            r"\1",

            cleaned,

            flags=re.DOTALL

        )


        cleaned = re.sub(

            r"^\s*[-*_]{3,}\s*$",

            "",

            cleaned,

            flags=re.MULTILINE

        )


        cleaned = cleaned.replace(
            "`",
            ""
        )


        cleaned = re.sub(

            r"^\s*\*\s+",

            "",

            cleaned,

            flags=re.MULTILINE

        )


        cleaned = re.sub(

            r"\n{3,}",

            "\n\n",

            cleaned

        )


        return cleaned.strip()


    # ========================================================
    # USER FINANCIAL CONTEXT
    # ========================================================

    @staticmethod
    async def get_user_context(
        user_id
    ):

        expenses = await database.expenses.find(

            {
                "user_id": user_id
            }

        ).sort(

            "date",
            -1

        ).limit(

            100

        ).to_list(

            length=100

        )


        budgets = await database.budgets.find(

            {
                "user_id": user_id
            }

        ).to_list(

            length=None

        )


        categories = await database.categories.find(

            {
                "user_id": user_id
            }

        ).to_list(

            length=None

        )


        expense_data = []


        for expense in expenses:

            expense_data.append({

                "title":
                    expense.get(
                        "title",
                        ""
                    ),

                "amount":
                    float(
                        expense.get(
                            "amount",
                            0
                        )
                    ),

                "category":
                    expense.get(
                        "category",
                        "Other"
                    ),

                "payment_method":
                    expense.get(
                        "payment_method",
                        ""
                    ),

                "date":
                    str(
                        expense.get(
                            "date",
                            ""
                        )
                    )

            })


        budget_data = []


        for budget in budgets:

            budget_data.append({

                "category":
                    budget.get(
                        "category",
                        "Other"
                    ),

                "amount":
                    float(
                        budget.get(
                            "amount",
                            0
                        )
                    ),

                "month":
                    budget.get(
                        "month"
                    ),

                "year":
                    budget.get(
                        "year"
                    )

            })


        category_data = []


        for category in categories:

            name = category.get(
                "name",
                ""
            )

            if name:

                category_data.append(
                    name
                )


        return {

            "expenses":
                expense_data,

            "budgets":
                budget_data,

            "categories":
                category_data

        }


    # ========================================================
    # AI CHAT
    # ========================================================

    @staticmethod
    async def chat(

        user_id,

        user_message,

        conversation_id=None

    ):

        try:

            # ==================================================
            # CREATE NEW CONVERSATION
            # ==================================================

            if not conversation_id:

                title = (
                    user_message.strip()
                )


                if len(title) > 45:

                    title = (
                        title[:45]
                        + "..."
                    )


                conversation = (

                    await ChatHistoryService
                    .create_conversation(

                        user_id=user_id,

                        title=title

                    )

                )


                conversation_id = (

                    conversation[
                        "conversation_id"
                    ]

                )


            # ==================================================
            # GET FINANCIAL DATA
            # ==================================================

            context = (

                await AIService
                .get_user_context(
                    user_id
                )

            )


            # ==================================================
            # GET PREVIOUS CONVERSATION
            # ==================================================

            conversation = (

                await ChatHistoryService
                .get_conversation(

                    user_id=user_id,

                    conversation_id=
                        conversation_id

                )

            )


            previous_messages = []


            if conversation.get(
                "success",
                True
            ):

                previous_messages = (

                    conversation.get(
                        "messages",
                        []
                    )

                )


            # ==================================================
            # SAVE USER MESSAGE
            # ==================================================

            await ChatHistoryService.add_message(

                user_id=user_id,

                conversation_id=
                    conversation_id,

                role="user",

                content=user_message

            )


            # ==================================================
            # SYSTEM PROMPT
            # ==================================================

            system_prompt = """

You are SpendSmart AI.

You are a friendly personal finance
assistant.

You help users with:

Expenses
Budgets
Savings
Travel planning
Shopping planning
Event planning
Financial planning
Currency conversion
Financial news
General financial questions

When the user asks about their own
expenses or budgets, use the supplied
financial data.

Never invent personal financial data.

If data is unavailable, clearly say so.

Use simple English.

Be practical and concise.

Do not use Markdown.

Do not use ###.

Do not use **.

Do not use ---.

Do not expose API keys.

Do not expose database IDs.

Do not expose user IDs.

"""


            # ==================================================
            # USER PROMPT
            # ==================================================

            prompt = f"""

USER FINANCIAL DATA:

{context}


PREVIOUS CONVERSATION:

{previous_messages}


USER QUESTION:

{user_message}


Answer the user using the financial
data when relevant.

If this is a personal finance question,
analyze the user's actual expenses and
budgets.

Do not invent numbers.

Return plain text.

"""


            # ==================================================
            # GET MODEL
            # ==================================================

            model = (

                await AIService
                .get_groq_model()

            )


            # ==================================================
            # CREATE GROQ CLIENT
            # ==================================================

            client = (

                AIService
                .get_groq_client()

            )


            print(
                "========================================"
            )

            print(
                "GROQ REQUEST"
            )

            print(
                "MODEL:",
                model
            )

            print(
                "API KEY EXISTS:",
                bool(
                    getattr(
                        settings,
                        "GROQ_API_KEY",
                        ""
                    )
                )
            )

            print(
                "========================================"
            )


            # ==================================================
            # GROQ REQUEST
            # ==================================================

            response = (

                await client
                .chat
                .completions
                .create(

                    model=model,

                    messages=[

                        {
                            "role":
                                "system",

                            "content":
                                system_prompt

                        },

                        {
                            "role":
                                "user",

                            "content":
                                prompt

                        }

                    ],

                    temperature=0.3,

                    max_completion_tokens=1200

                )

            )


            # ==================================================
            # CHECK RESPONSE
            # ==================================================

            if not response:

                raise ValueError(
                    "Empty response from Groq."
                )


            if not response.choices:

                raise ValueError(
                    "Groq returned no choices."
                )


            # ==================================================
            # GET RESPONSE TEXT
            # ==================================================

            ai_message = (

                response
                .choices[0]
                .message
                .content

            )


            ai_message = (

                AIService
                .clean_ai_response(
                    ai_message
                )

            )


            # ==================================================
            # SAVE AI MESSAGE
            # ==================================================

            await ChatHistoryService.add_message(

                user_id=user_id,

                conversation_id=
                    conversation_id,

                role="assistant",

                content=ai_message

            )


            # ==================================================
            # RETURN
            # ==================================================

            return {

                "success":
                    True,

                "message":
                    ai_message,

                "conversation_id":
                    conversation_id,

                "source":
                    "Groq",

                "model":
                    model

            }


        except Exception as e:

            print(
                "========================================"
            )

            print(
                "AI CHAT ERROR"
            )

            print(
                "TYPE:",
                type(e).__name__
            )

            print(
                "ERROR:",
                repr(e)
            )

            print(
                "========================================"
            )

            raise


    # ========================================================
    # FINANCIAL NEWS
    # ========================================================

    @staticmethod
    async def get_news(

        query="personal finance India"

    ):

        if not settings.NEWS_API_KEY:

            raise ValueError(
                "NEWS_API_KEY is not configured."
            )


        url = (
            "https://gnews.io/api/v4/search"
        )


        params = {

            "q":
                query,

            "lang":
                "en",

            "max":
                10,

            "apikey":
                settings.NEWS_API_KEY

        }


        async with httpx.AsyncClient(
            timeout=15
        ) as client:

            response = await client.get(

                url,

                params=params

            )


        if response.status_code != 200:

            raise ValueError(
                f"News API error: "
                f"{response.text}"
            )


        data = response.json()


        articles = []


        for article in data.get(
            "articles",
            []
        ):

            source = article.get(
                "source",
                {}
            )


            if not isinstance(
                source,
                dict
            ):

                source = {}


            articles.append({

                "title":
                    article.get(
                        "title",
                        ""
                    ),

                "description":
                    article.get(
                        "description",
                        ""
                    ),

                "url":
                    article.get(
                        "url",
                        ""
                    ),

                "published_at":
                    article.get(
                        "publishedAt",
                        ""
                    ),

                "source":
                    source.get(
                        "name",
                        ""
                    )

            })


        return {

            "success":
                True,

            "query":
                query,

            "articles":
                articles

        }


    # ========================================================
    # CURRENCY
    # ========================================================

    @staticmethod
    async def convert_currency(

        base,

        target,

        amount

    ):

        base = base.upper()

        target = target.upper()

        amount = float(
            amount
        )


        url = (

            "https://open.er-api.com/v6/latest/"

            f"{base}"

        )


        async with httpx.AsyncClient(
            timeout=15
        ) as client:

            response = await client.get(
                url
            )


        if response.status_code != 200:

            raise ValueError(
                "Currency API request failed."
            )


        data = response.json()


        rates = data.get(
            "rates",
            {}
        )


        rate = rates.get(
            target
        )


        if rate is None:

            raise ValueError(
                f"Currency {target} not found."
            )


        converted_amount = (

            amount *
            float(rate)

        )


        return {

            "success":
                True,

            "base":
                base,

            "target":
                target,

            "amount":
                amount,

            "rate":
                float(rate),

            "converted_amount":
                round(
                    converted_amount,
                    2
                )

        }


    # ========================================================
    # WEATHER
    # ========================================================

    @staticmethod
    async def get_weather(

        latitude,

        longitude

    ):

        url = (
            "https://api.open-meteo.com/v1/forecast"
        )


        params = {

            "latitude":
                latitude,

            "longitude":
                longitude,

            "current":
                (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "precipitation,"
                    "weather_code,"
                    "wind_speed_10m"
                )

        }


        async with httpx.AsyncClient(
            timeout=15
        ) as client:

            response = await client.get(

                url,

                params=params

            )


        if response.status_code != 200:

            raise ValueError(
                "Weather API request failed."
            )


        data = response.json()


        return {

            "success":
                True,

            "latitude":
                latitude,

            "longitude":
                longitude,

            "current":
                data.get(
                    "current",
                    {}
                )

        }


    # ========================================================
    # FRANKFURTER
    # ========================================================

    @staticmethod
    async def get_frankfurter_rate(

        base,

        target

    ):

        base = base.upper()

        target = target.upper()


        url = (

            "https://api.frankfurter.dev/v2/rate/"

            f"{base}/{target}"

        )


        async with httpx.AsyncClient(
            timeout=15
        ) as client:

            response = await client.get(
                url
            )


        if response.status_code != 200:

            raise ValueError(
                "Unable to fetch exchange rate."
            )


        data = response.json()


        return {

            "success":
                True,

            "date":
                data.get(
                    "date"
                ),

            "base":
                data.get(
                    "base"
                ),

            "target":
                data.get(
                    "quote"
                ),

            "rate":
                data.get(
                    "rate"
                )

        }