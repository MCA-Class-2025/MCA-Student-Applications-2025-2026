from pathlib import Path
import math
from datetime import datetime, timezone, timedelta

import httpx
import pandas as pd

from bson import ObjectId
from bson.errors import InvalidId

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.core.auth_dependency import (
    get_current_user
)

from app.database.mongodb import (
    database
)

from app.core.config import settings


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics"]
)


# ============================================================
# PROJECT PATH
# ============================================================

CURRENT_FILE = Path(
    __file__
).resolve()


# Expected structure:
#
# AI_SMART_EXPENSE/
#
# ├── backend/
# │   └── app/
# │       └── routers/
# │           └── analytics_router.py
# │
# └── ml/
#     ├── dataset/
#     └── data_fusion/
#
# The old code used CURRENT_FILE.parents[3], which can point OUTSIDE
# the project depending on the exact backend folder structure.
# We now search upward for the folder that actually contains "ml".

CURRENT_FILE = Path(__file__).resolve()


def find_project_root():
    candidates = [CURRENT_FILE.parent] + list(CURRENT_FILE.parents)

    for candidate in candidates:
        if (candidate / "ml").is_dir():
            return candidate

        # Also support an ml folder inside backend if that is how
        # the project is currently arranged.
        if (candidate / "backend" / "ml").is_dir():
            return candidate / "backend"

    # Standard structure fallback:
    # .../AI_SMART_EXPENSE/backend/app/routers/analytics_router.py
    if len(CURRENT_FILE.parents) >= 3:
        return CURRENT_FILE.parents[2]

    return CURRENT_FILE.parent


PROJECT_ROOT = find_project_root()

ML_DIRECTORY = PROJECT_ROOT / "ml"

DATASET_DIRECTORY = ML_DIRECTORY / "dataset"

FUSION_DIRECTORY = ML_DIRECTORY / "data_fusion" / "results"


# If ML was placed inside backend, use that location.
if not ML_DIRECTORY.is_dir():
    backend_ml = CURRENT_FILE.parents[1] / "ml"

    if backend_ml.is_dir():
        ML_DIRECTORY = backend_ml
        DATASET_DIRECTORY = ML_DIRECTORY / "dataset"
        FUSION_DIRECTORY = ML_DIRECTORY / "data_fusion" / "results"


print("=" * 70)

print(
    "ANALYTICS PROJECT ROOT:",
    PROJECT_ROOT
)

print(
    "ANALYTICS DATASET DIRECTORY:",
    DATASET_DIRECTORY
)

print(
    "ANALYTICS FUSION DIRECTORY:",
    FUSION_DIRECTORY
)

print("=" * 70)


# ============================================================
# SAFE NUMBER
# ============================================================

def safe_number(
    value,
    default=0.0
):

    try:

        if value is None:

            return default

        if pd.isna(value):

            return default

        number = float(
            value
        )

        if not math.isfinite(
            number
        ):

            return default

        return number

    except Exception:

        return default


# ============================================================
# SAFE TEXT
# ============================================================

def safe_text(
    value,
    default=""
):

    if value is None:

        return default

    try:

        if pd.isna(value):

            return default

    except Exception:

        pass

    text = str(
        value
    ).strip()

    if text.lower() in [
        "nan",
        "none",
        "null",
    ]:

        return default

    return text


# ============================================================
# SAFE DATE
# ============================================================

def safe_date(
    value
):

    if value is None:

        return ""

    try:

        if pd.isna(value):

            return ""

    except Exception:

        pass

    parsed = pd.to_datetime(
        value,
        errors="coerce"
    )

    if pd.isna(
        parsed
    ):

        return safe_text(
            value
        )

    return parsed.strftime(
        "%Y-%m-%d"
    )


# ============================================================
# FIND COLUMN
# ============================================================

def find_column(
    dataframe,
    possible_names
):

    if dataframe.empty:

        return None

    columns = {}

    for column in dataframe.columns:

        normalized = (
            str(column)
            .strip()
            .lower()
            .replace(
                " ",
                "_"
            )
            .replace(
                "-",
                "_"
            )
        )

        columns[
            normalized
        ] = column

    for name in possible_names:

        normalized = (
            str(name)
            .strip()
            .lower()
            .replace(
                " ",
                "_"
            )
            .replace(
                "-",
                "_"
            )
        )

        if normalized in columns:

            return columns[
                normalized
            ]

    return None


# ============================================================
# LOAD CSV
# ============================================================

def load_csv(
    path
):

    print(
        "CHECKING CSV:",
        path
    )

    if not path.exists():

        print(
            "CSV NOT FOUND:",
            path
        )

        return pd.DataFrame()

    try:

        dataframe = pd.read_csv(
            path
        )

        print(
            "CSV LOADED:",
            path
        )

        print(
            "ROWS:",
            len(dataframe)
        )

        print(
            "COLUMNS:",
            list(
                dataframe.columns
            )
        )

        return dataframe

    except Exception as error:

        print(
            "CSV LOAD ERROR:",
            path,
            repr(error)
        )

        return pd.DataFrame()


# ============================================================
# JSON SAFE
# ============================================================

def json_safe(
    value
):

    if isinstance(
        value,
        dict
    ):

        return {
            str(key):
                json_safe(item)

            for key, item
            in value.items()
        }

    if isinstance(
        value,
        list
    ):

        return [
            json_safe(item)
            for item in value
        ]

    if isinstance(
        value,
        tuple
    ):

        return [
            json_safe(item)
            for item in value
        ]

    if isinstance(
        value,
        ObjectId
    ):

        return str(
            value
        )

    if isinstance(
        value,
        pd.Timestamp
    ):

        return value.isoformat()

    try:

        if pd.isna(
            value
        ):

            return None

    except Exception:

        pass

    if isinstance(
        value,
        float
    ):

        if not math.isfinite(
            value
        ):

            return None

    return value


# ============================================================
# USER EXPENSE DATA
# ============================================================

async def load_user_expenses(
    user_id
):

    queries = []

    queries.append(
        {
            "user_id":
                user_id
        }
    )

    try:

        queries.append(
            {
                "user_id":
                    ObjectId(
                        str(
                            user_id
                        )
                    )
            }
        )

    except (
        InvalidId,
        TypeError,
        ValueError
    ):

        pass

    documents = []

    for query in queries:

        try:

            documents = await (
                database.expenses
                .find(query)
                .sort(
                    "date",
                    -1
                )
                .to_list(
                    length=None
                )
            )

        except Exception as error:

            print(
                "MONGODB EXPENSE ERROR:",
                repr(error)
            )

            documents = []

        if documents:

            break

    result = []

    for document in documents:

        result.append(

            {
                "id":
                    str(
                        document.get(
                            "_id",
                            ""
                        )
                    ),

                "date":
                    safe_date(
                        document.get(
                            "date"
                        )
                        or document.get(
                            "created_at"
                        )
                    ),

                "source":
                    "User",

                "source_type":
                    "User",

                "data_source":
                    "User",

                "type":
                    "Expense",

                "category":
                    safe_text(
                        document.get(
                            "category"
                        ),
                        "Other"
                    ),

                "description":
                    safe_text(
                        document.get(
                            "title"
                        )
                        or document.get(
                            "description"
                        ),
                        "Expense"
                    ),

                "amount":
                    round(
                        safe_number(
                            document.get(
                                "amount"
                            )
                        ),
                        2
                    ),

                "payment_method":
                    safe_text(
                        document.get(
                            "payment_method"
                        ),
                        "Other"
                    ),

                "status":
                    "Normal",

                "anomaly_status":
                    "Normal",

                "anomaly_score":
                    None,
            }
        )

    return result


# ============================================================
# HISTORICAL DATASET
# ============================================================

def load_historical_dataset():

    # ========================================================
    # PRIMARY DATASET
    # ========================================================

    possible_files = [

        DATASET_DIRECTORY
        / "personal_finance.csv",

        DATASET_DIRECTORY
        / "monthly_expenses.csv",

        ML_DIRECTORY
        / "eda"
        / "results"
        / "eda_dataset.csv",

        FUSION_DIRECTORY
        / "fused_financial_data.csv",
    ]

    dataframe = pd.DataFrame()

    selected_file = None

    for path in possible_files:

        print(
            "HISTORICAL CHECK:",
            path
        )

        if not path.exists():

            continue

        dataframe = load_csv(
            path
        )

        if not dataframe.empty:

            selected_file = path

            break

    if dataframe.empty:

        print(
            "NO HISTORICAL DATASET FOUND"
        )

        return []

    print(
        "HISTORICAL DATASET SELECTED:",
        selected_file
    )

    # ========================================================
    # COLUMN DETECTION
    # ========================================================

    date_column = find_column(
        dataframe,
        [
            "date",
            "transaction_date",
            "transaction date",
            "timestamp",
            "created_at",
        ]
    )

    amount_column = find_column(
        dataframe,
        [
            "amount",
            "expense",
            "total_amount",
            "transaction_amount",
            "value",
        ]
    )

    category_column = find_column(
        dataframe,
        [
            "category",
            "expense_category",
            "expense category",
        ]
    )

    description_column = find_column(
        dataframe,
        [
            "description",
            "transaction_description",
            "transaction description",
            "title",
            "merchant",
            "name",
        ]
    )

    type_column = find_column(
        dataframe,
        [
            "type",
            "transaction_type",
            "transaction type",
        ]
    )

    source_column = find_column(
        dataframe,
        [
            "source",
            "data_source",
            "data source",
        ]
    )

    anomaly_column = find_column(
        dataframe,
        [
            "anomaly_status",
            "anomaly status",
            "anomaly",
            "status",
        ]
    )

    score_column = find_column(
        dataframe,
        [
            "anomaly_score",
            "anomaly score",
            "score",
        ]
    )

    print(
        "DATE COLUMN:",
        date_column
    )

    print(
        "AMOUNT COLUMN:",
        amount_column
    )

    print(
        "CATEGORY COLUMN:",
        category_column
    )

    # ========================================================
    # RECORDS
    # ========================================================

    records = []

    for index, row in dataframe.iterrows():

        date_value = (
            row.get(
                date_column
            )
            if date_column
            else ""
        )

        amount_value = (
            row.get(
                amount_column
            )
            if amount_column
            else 0
        )

        category_value = (
            row.get(
                category_column
            )
            if category_column
            else "Other"
        )

        description_value = (
            row.get(
                description_column
            )
            if description_column
            else "Historical transaction"
        )

        type_value = (
            row.get(
                type_column
            )
            if type_column
            else "Expense"
        )

        source_value = (
            row.get(
                source_column
            )
            if source_column
            else "Historical Dataset"
        )

        anomaly_value = (
            row.get(
                anomaly_column
            )
            if anomaly_column
            else "Normal"
        )

        score_value = (
            row.get(
                score_column
            )
            if score_column
            else None
        )

        # ====================================================
        # FIX NAN ANOMALY SCORE
        # ====================================================

        if score_value is None:

            safe_score = None

        else:

            try:

                if pd.isna(
                    score_value
                ):

                    safe_score = None

                else:

                    safe_score = round(
                        float(
                            score_value
                        ),
                        6
                    )

            except Exception:

                safe_score = None

        records.append(

            {
                "id":
                    f"historical-{index}",

                "date":
                    safe_date(
                        date_value
                    ),

                "source":
                    safe_text(
                        source_value,
                        "Historical Dataset"
                    ),

                "source_type":
                    "Historical",

                "data_source":
                    "Historical",

                "type":
                    safe_text(
                        type_value,
                        "Expense"
                    ),

                "category":
                    safe_text(
                        category_value,
                        "Other"
                    ),

                "description":
                    safe_text(
                        description_value,
                        "Historical transaction"
                    ),

                "amount":
                    round(
                        safe_number(
                            amount_value
                        ),
                        2
                    ),

                "payment_method":
                    "Historical Dataset",

                "status":
                    safe_text(
                        anomaly_value,
                        "Normal"
                    ),

                "anomaly_status":
                    safe_text(
                        anomaly_value,
                        "Normal"
                    ),

                "anomaly_score":
                    safe_score,
            }
        )

    print(
        "HISTORICAL RECORDS:",
        len(records)
    )

    return json_safe(
        records
    )


# ============================================================
# LIVE API DATA
# ============================================================

# Short in-memory cache prevents the frontend's polling from
# calling external APIs every few seconds.
LIVE_API_CACHE = {
    "timestamp": None,
    "data": [],
}

CACHE_SECONDS = 60


def india_now():
    return datetime.now(
        timezone(
            timedelta(hours=5, minutes=30)
        )
    )


async def fetch_live_news():
    api_key = getattr(
        settings,
        "NEWS_API_KEY",
        ""
    )

    if not api_key:
        return []

    try:
        url = "https://gnews.io/api/v4/search"

        params = {
            "q": "personal finance OR finance OR India economy",
            "lang": "en",
            "max": 10,
            "apikey": api_key,
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                url,
                params=params
            )

        if response.status_code != 200:
            print(
                "LIVE NEWS ERROR:",
                response.status_code,
                response.text[:300]
            )
            return []

        payload = response.json()
        records = []

        for index, article in enumerate(
            payload.get("articles", [])
        ):
            source = article.get(
                "source",
                {}
            )

            if not isinstance(source, dict):
                source = {}

            published = (
                article.get("publishedAt")
                or india_now().isoformat()
            )

            records.append({
                "id": f"live-news-{index}",
                "date": safe_date(published),
                "source": "Financial News API",
                "source_type": "API",
                "data_source": "Live API",
                "type": "News",
                "category": "Financial News",
                "description": safe_text(
                    article.get("title"),
                    "Financial News"
                ),
                "amount": 0,
                "payment_method": "API",
                "status": "Live",
                "anomaly_status": "Normal",
                "anomaly_score": None,
                "additional_data": safe_text(
                    article.get("description"),
                    ""
                ),
                "url": safe_text(
                    article.get("url"),
                    ""
                ),
                "publisher": safe_text(
                    source.get("name"),
                    ""
                ),
            })

        return records

    except Exception as error:
        print(
            "LIVE NEWS EXCEPTION:",
            repr(error)
        )
        return []


async def fetch_live_currency():
    try:
        base = "USD"
        target = "INR"
        amount = 1.0

        url = (
            "https://open.er-api.com/v6/latest/"
            f"{base}"
        )

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url)

        if response.status_code != 200:
            print(
                "LIVE CURRENCY ERROR:",
                response.status_code
            )
            return []

        payload = response.json()
        rate = (
            payload.get("rates", {})
            .get(target)
        )

        if rate is None:
            return []

        today = india_now().strftime(
            "%Y-%m-%d"
        )

        return [{
            "id": f"live-currency-{today}",
            "date": today,
            "source": "Currency API",
            "source_type": "API",
            "data_source": "Live API",
            "type": "Currency",
            "category": "Currency Conversion",
            "description": "USD to INR",
            "amount": amount,
            "payment_method": "API",
            "status": "Live",
            "anomaly_status": "Normal",
            "anomaly_score": None,
            "rate": safe_number(rate),
            "converted_amount": round(
                amount * safe_number(rate),
                4
            ),
        }]

    except Exception as error:
        print(
            "LIVE CURRENCY EXCEPTION:",
            repr(error)
        )
        return []


async def fetch_live_exchange():
    try:
        base = "USD"
        target = "INR"

        url = (
            "https://api.frankfurter.dev/v2/rate/"
            f"{base}/{target}"
        )

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url)

        if response.status_code != 200:
            print(
                "LIVE EXCHANGE ERROR:",
                response.status_code
            )
            return []

        payload = response.json()

        rate = payload.get("rate")

        if rate is None:
            return []

        date_value = (
            payload.get("date")
            or india_now().strftime("%Y-%m-%d")
        )

        return [{
            "id": (
                f"live-exchange-{date_value}-"
                f"{base}-{target}"
            ),
            "date": safe_date(date_value),
            "source": "Exchange Rate API",
            "source_type": "API",
            "data_source": "Live API",
            "type": "Exchange Rate",
            "category": "Exchange Rate",
            "description": "USD to INR",
            "amount": safe_number(rate),
            "payment_method": "API",
            "status": "Live",
            "anomaly_status": "Normal",
            "anomaly_score": None,
            "rate": safe_number(rate),
        }]

    except Exception as error:
        print(
            "LIVE EXCHANGE EXCEPTION:",
            repr(error)
        )
        return []


async def fetch_live_groq():
    try:
        from app.services.ai_service import AIService

        client = AIService.get_groq_client()
        model = await AIService.get_groq_model()

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Give one short practical personal "
                        "finance tip for an expense tracker. "
                        "Return plain text only."
                    )
                }
            ],
            temperature=0.2,
            max_completion_tokens=150,
        )

        message = ""

        if response and response.choices:
            message = (
                response.choices[0]
                .message
                .content
                or ""
            )

        if not message:
            return []

        now = india_now()

        return [{
            "id": (
                "live-groq-"
                + now.strftime("%Y%m%d%H%M%S")
            ),
            "date": now.strftime("%Y-%m-%d"),
            "timestamp": now.isoformat(),
            "source": "Groq AI",
            "source_type": "API",
            "data_source": "Live API",
            "type": "AI",
            "category": "AI Finance",
            "description": "Live AI finance tip",
            "amount": 0,
            "payment_method": "API",
            "status": "Live",
            "anomaly_status": "Normal",
            "anomaly_score": None,
            "additional_data": safe_text(
                message,
                ""
            ),
            "model": model,
        }]

    except Exception as error:
        print(
            "LIVE GROQ EXCEPTION:",
            repr(error)
        )
        return []


async def store_live_api_records(records):
    if not records:
        return

    try:
        operations = []

        from pymongo import UpdateOne

        for record in records:
            source = safe_text(
                record.get("source"),
                "API"
            )

            record_id = safe_text(
                record.get("id"),
                ""
            )

            if not record_id:
                continue

            document = dict(record)

            document["updated_at"] = (
                india_now().isoformat()
            )

            operations.append(
                UpdateOne(
                    {
                        "record_id": record_id,
                        "source": source,
                    },
                    {
                        "$set": document,
                        "$setOnInsert": {
                            "created_at":
                                india_now().isoformat()
                        },
                    },
                    upsert=True,
                )
            )

        if operations:
            result = await database.api_data.bulk_write(
                operations,
                ordered=False
            )

            print(
                "LIVE API DATA STORED:",
                result.upserted_count,
                "new,",
                result.modified_count,
                "updated"
            )

    except Exception as error:
        print(
            "STORE LIVE API ERROR:",
            repr(error)
        )


async def load_live_api_data():
    now = india_now()

    cached_at = LIVE_API_CACHE.get(
        "timestamp"
    )

    if (
        cached_at
        and
        (now - cached_at).total_seconds()
        < CACHE_SECONDS
        and
        LIVE_API_CACHE.get("data")
    ):
        print(
            "USING LIVE API CACHE:",
            len(
                LIVE_API_CACHE["data"]
            )
        )
        return LIVE_API_CACHE["data"]

    print(
        "=" * 70
    )
    print(
        "FETCHING LIVE API DATA"
    )
    print(
        "=" * 70
    )

    live_results = await __import__(
        "asyncio"
    ).gather(
        fetch_live_news(),
        fetch_live_currency(),
        fetch_live_exchange(),
        fetch_live_groq(),
        return_exceptions=True,
    )

    records = []

    for result in live_results:
        if isinstance(result, Exception):
            print(
                "LIVE API RESULT ERROR:",
                repr(result)
            )
            continue

        if isinstance(result, list):
            records.extend(result)

    # Keep OCR from the existing dataset because OCR needs
    # an actual receipt image to create a new live record.
    existing_ocr = load_api_data()

    for record in existing_ocr:
        if record.get("source") == "Receipt OCR API":
            records.append(record)

    # Remove duplicate IDs.
    unique = {}

    for record in records:
        unique[
            safe_text(
                record.get("id"),
                f"record-{len(unique)}"
            )
        ] = record

    records = list(
        unique.values()
    )

    records.sort(
        key=lambda item:
            item.get(
                "date",
                ""
            ),
        reverse=True
    )

    records = json_safe(
        records
    )

    LIVE_API_CACHE["timestamp"] = now
    LIVE_API_CACHE["data"] = records

    await store_live_api_records(
        records
    )

    print(
        "LIVE API RECORDS:",
        len(records)
    )

    return records


# ============================================================
# API DATA
# ============================================================

def load_api_data():

    api_files = [

        (
            "Groq AI",
            "api_groq.csv"
        ),

        (
            "Financial News API",
            "api_news.csv"
        ),

        (
            "Currency API",
            "api_currency.csv"
        ),

        (
            "Exchange Rate API",
            "api_exchange_rate.csv"
        ),

        (
            "Receipt OCR API",
            "api_ocr.csv"
        ),
    ]

    records = []

    for source_name, filename in api_files:

        path = (
            DATASET_DIRECTORY
            / filename
        )

        dataframe = load_csv(
            path
        )

        if dataframe.empty:

            continue

        for index, row in dataframe.iterrows():

            # =================================================
            # DATE
            # =================================================

            date_value = (
                row.get("date")
                or row.get("timestamp")
                or row.get("published_at")
                or row.get("created_at")
                or ""
            )

            # =================================================
            # DESCRIPTION
            # =================================================

            description = (
                row.get(
                    "description"
                )
                or row.get(
                    "title"
                )
                or row.get(
                    "merchant"
                )
                or row.get(
                    "user_message"
                )
                or row.get(
                    "currency_pair"
                )
                or source_name
            )

            # =================================================
            # CATEGORY
            # =================================================

            category = (
                row.get(
                    "category"
                )
                or source_name
            )

            # =================================================
            # AMOUNT
            # =================================================

            amount = (
                row.get(
                    "amount"
                )
                or row.get(
                    "converted_amount"
                )
                or row.get(
                    "exchange_rate"
                )
                or row.get(
                    "value"
                )
                or 0
            )

            # =================================================
            # TYPE
            # =================================================

            record_type = (
                "API"
            )

            if source_name == "Receipt OCR API":

                record_type = (
                    "Expense"
                )

            elif source_name == "Financial News API":

                record_type = (
                    "News"
                )

            elif source_name == "Groq AI":

                record_type = (
                    "AI"
                )

            records.append(

                {
                    "id":
                        f"api-{index}-{filename}",

                    "date":
                        safe_date(
                            date_value
                        ),

                    "source":
                        source_name,

                    "source_type":
                        "API",

                    "data_source":
                        "API",

                    "type":
                        record_type,

                    "category":
                        safe_text(
                            category,
                            "API"
                        ),

                    "description":
                        safe_text(
                            description,
                            source_name
                        ),

                    "amount":
                        round(
                            safe_number(
                                amount
                            ),
                            2
                        ),

                    "payment_method":
                        "API",

                    "status":
                        "Normal",

                    "anomaly_status":
                        "Normal",

                    "anomaly_score":
                        None,
                }
            )

    print(
        "API RECORDS:",
        len(records)
    )

    return json_safe(
        records
    )


# ============================================================
# USER CATEGORIES
# ============================================================

def calculate_categories(
    expenses
):

    categories = {}

    for expense in expenses:

        category = safe_text(
            expense.get(
                "category"
            ),
            "Other"
        )

        amount = safe_number(
            expense.get(
                "amount"
            )
        )

        categories[
            category
        ] = (
            categories.get(
                category,
                0
            )
            + amount
        )

    result = []

    for category, amount in sorted(
        categories.items(),
        key=lambda item:
            item[1],
        reverse=True
    ):

        result.append(

            {
                "category":
                    category,

                "amount":
                    round(
                        amount,
                        2
                    )
            }
        )

    return result


# ============================================================
# USER MONTHLY
# ============================================================

def calculate_monthly(
    expenses
):

    monthly = {}

    for expense in expenses:

        date_value = pd.to_datetime(
            expense.get(
                "date"
            ),
            errors="coerce"
        )

        if pd.isna(
            date_value
        ):

            continue

        month = date_value.strftime(
            "%Y-%m"
        )

        monthly[
            month
        ] = (
            monthly.get(
                month,
                0
            )
            + safe_number(
                expense.get(
                    "amount"
                )
            )
        )

    return [

        {
            "month":
                month,

            "amount":
                round(
                    amount,
                    2
                )
        }

        for month, amount
        in sorted(
            monthly.items()
        )
    ]


# ============================================================
# USER ANOMALIES
# ============================================================

def calculate_anomalies(
    expenses
):

    if len(
        expenses
    ) < 4:

        return []

    amounts = [

        safe_number(
            expense.get(
                "amount"
            )
        )

        for expense in expenses
    ]

    series = pd.Series(
        amounts
    )

    q1 = series.quantile(
        0.25
    )

    q3 = series.quantile(
        0.75
    )

    iqr = q3 - q1

    threshold = (
        q3 + (1.5 * iqr)
    )

    anomalies = []

    for expense in expenses:

        amount = safe_number(
            expense.get(
                "amount"
            )
        )

        if amount > threshold:

            item = dict(
                expense
            )

            item[
                "anomaly_status"
            ] = "Anomaly"

            item[
                "status"
            ] = "Anomaly"

            item[
                "anomaly_score"
            ] = round(
                amount /
                threshold
                if threshold > 0
                else 1,
                6
            )

            anomalies.append(
                item
            )

    return anomalies


# ============================================================
# DEBUG LIVE API
# ============================================================

@router.get(
    "/debug/live-api"
)
async def debug_live_api():

    try:

        data = await load_live_api_data()

        return json_safe({
            "success": True,
            "today": india_now().strftime(
                "%Y-%m-%d"
            ),
            "total_records": len(data),
            "sources": sorted(
                list(
                    set(
                        safe_text(
                            item.get(
                                "source"
                            )
                        )
                        for item in data
                    )
                )
            ),
            "data": data,
        })

    except Exception as error:

        print(
            "DEBUG LIVE API ERROR:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# FUSED DATA
# ============================================================

def create_fused_data(
    user_data,
    historical_data,
    api_data
):

    result = []

    result.extend(
        user_data
    )

    result.extend(
        historical_data
    )

    result.extend(
        api_data
    )

    result.sort(
        key=lambda item:
            item.get(
                "date",
                ""
            ),
        reverse=True
    )

    return json_safe(
        result
    )


# ============================================================
# MAIN DASHBOARD
# ============================================================

@router.get(
    "/dashboard"
)
async def dashboard(
    current_user=Depends(
        get_current_user
    )
):

    try:

        user_id = current_user.get(
            "user_id"
        )

        if not user_id:

            raise HTTPException(
                status_code=401,
                detail="User ID not found."
            )

        # ====================================================
        # USER
        # ====================================================

        user = None

        try:

            user = await database.users.find_one(
                {
                    "_id":
                        ObjectId(
                            str(
                                user_id
                            )
                        )
                }
            )

        except (
            InvalidId,
            TypeError,
            ValueError
        ):

            pass

        # ====================================================
        # USER EXPENSES
        # ====================================================

        user_expenses = (
            await load_user_expenses(
                str(
                    user_id
                )
            )
        )

        # ====================================================
        # HISTORICAL
        # ====================================================

        historical_data = (
            load_historical_dataset()
        )

        # ====================================================
        # API
        # ====================================================

        api_data = await load_live_api_data()

        # ====================================================
        # CATEGORIES
        # ====================================================

        categories = (
            calculate_categories(
                user_expenses
            )
        )

        # ====================================================
        # MONTHLY
        # ====================================================

        monthly = (
            calculate_monthly(
                user_expenses
            )
        )

        # ====================================================
        # ANOMALIES
        # ====================================================

        user_anomalies = (
            calculate_anomalies(
                user_expenses
            )
        )

        # ====================================================
        # INCOME
        # ====================================================

        income = safe_number(

            (
                user or {}
            ).get(
                "monthly_income"
            )
            or (
                user or {}
            ).get(
                "monthlyIncome"
            )
            or (
                user or {}
            ).get(
                "income"
            )
        )

        # ====================================================
        # USER EXPENSE TOTAL
        # ====================================================

        user_expense_total = sum(

            safe_number(
                item.get(
                    "amount"
                )
            )

            for item in user_expenses
        )

        # ====================================================
        # HISTORICAL TOTAL
        # ====================================================

        historical_total = sum(

            safe_number(
                item.get(
                    "amount"
                )
            )

            for item in historical_data
        )

        # ====================================================
        # API TOTAL
        # ====================================================

        api_total = sum(

            safe_number(
                item.get(
                    "amount"
                )
            )

            for item in api_data
        )

        # ====================================================
        # FUSED
        # ====================================================

        fused_data = create_fused_data(

            user_expenses,

            historical_data,

            api_data
        )

        # ====================================================
        # RESPONSE
        # ====================================================

        return json_safe(

            {
                "success":
                    True,

                "overview": {

                    "user_income":
                        round(
                            income,
                            2
                        ),

                    "user_expense":
                        round(
                            user_expense_total,
                            2
                        ),

                    "user_transactions":
                        len(
                            user_expenses
                        ),

                    "user_anomalies":
                        len(
                            user_anomalies
                        ),

                    "historical_transactions":
                        len(
                            historical_data
                        ),

                    "historical_amount":
                        round(
                            historical_total,
                            2
                        ),

                    "historical_anomalies":
                        len(
                            [
                                item
                                for item
                                in historical_data
                                if "anomaly"
                                in safe_text(
                                    item.get(
                                        "anomaly_status"
                                    )
                                ).lower()
                            ]
                        ),

                    "api_transactions":
                        len(
                            api_data
                        ),

                    "api_amount":
                        round(
                            api_total,
                            2
                        ),

                    "fused_records":
                        len(
                            fused_data
                        )
                },

                "user": {

                    "expenses":
                        user_expenses,

                    "categories":
                        categories,

                    "monthly":
                        monthly,

                    "anomalies":
                        user_anomalies
                },

                "historical": {

                    "data":
                        historical_data
                },

                "api": {

                    "data":
                        api_data
                },

                "sources": {

                    "user":
                        len(
                            user_expenses
                        ),

                    "historical":
                        len(
                            historical_data
                        ),

                    "api":
                        len(
                            api_data
                        )
                },

                "fused_data":
                    fused_data
            }
        )

    except HTTPException:

        raise

    except Exception as error:

        print(
            "ANALYTICS DASHBOARD ERROR:",
            repr(error)
        )

        raise HTTPException(

            status_code=500,

            detail=str(
                error
            )
        )


# ============================================================
# HISTORICAL DATA
# ============================================================

@router.get(
    "/historical-data"
)
async def historical_data():

    try:

        data = load_historical_dataset()

        return json_safe({
            "success": True,
            "total_records": len(data),
            "data": data,
            "records": data,
            "dataset_directory": str(DATASET_DIRECTORY),
        })

    except Exception as error:

        print(
            "HISTORICAL DATA ERROR:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# API DATA
# ============================================================

@router.get(
    "/api-data"
)
async def api_data():

    data = await load_live_api_data()

    return {

        "success":
            True,

        "total_records":
            len(
                data
            ),

        "data":
            data,

        "records":
            data
    }


# ============================================================
# FUSED DATA
# ============================================================

@router.get(
    "/data"
)
async def fused_data(
    current_user=Depends(
        get_current_user
    )
):

    result = await dashboard(
        current_user
    )

    return {

        "success":
            True,

        "total_records":
            result[
                "overview"
            ][
                "fused_records"
            ],

        "data":
            result[
                "fused_data"
            ],

        "records":
            result[
                "fused_data"
            ],

        "fused_data":
            result[
                "fused_data"
            ],

        "user_data":
            result[
                "user"
            ][
                "expenses"
            ],

        "historical_data":
            result[
                "historical"
            ][
                "data"
            ],

        "api_data":
            result[
                "api"
            ][
                "data"
            ]
    }


# ============================================================
# SUMMARY
# ============================================================

@router.get(
    "/summary"
)
async def summary(
    current_user=Depends(
        get_current_user
    )
):

    result = await dashboard(
        current_user
    )

    overview = result[
        "overview"
    ]

    return {

        "success":
            True,

        "data": [

            {
                "metric":
                    "Monthly Income",

                "value":
                    overview[
                        "user_income"
                    ]
            },

            {
                "metric":
                    "Total Expenses",

                "value":
                    overview[
                        "user_expense"
                    ]
            },

            {
                "metric":
                    "Historical Records",

                "value":
                    overview[
                        "historical_transactions"
                    ]
            },

            {
                "metric":
                    "API Records",

                "value":
                    overview[
                        "api_transactions"
                    ]
            },

            {
                "metric":
                    "Fused Records",

                "value":
                    overview[
                        "fused_records"
                    ]
            }
        ]
    }


# ============================================================
# CATEGORIES
# ============================================================

@router.get(
    "/categories"
)
async def categories(
    current_user=Depends(
        get_current_user
    )
):

    result = await dashboard(
        current_user
    )

    return {

        "success":
            True,

        "data":
            result[
                "user"
            ][
                "categories"
            ]
    }


# ============================================================
# MONTHLY
# ============================================================

@router.get(
    "/monthly"
)
async def monthly(
    current_user=Depends(
        get_current_user
    )
):

    result = await dashboard(
        current_user
    )

    return {

        "success":
            True,

        "data":
            result[
                "user"
            ][
                "monthly"
            ]
    }


# ============================================================
# SOURCES
# ============================================================

@router.get(
    "/sources"
)
async def sources(
    current_user=Depends(
        get_current_user
    )
):

    result = await dashboard(
        current_user
    )

    return {

        "success":
            True,

        "data": [

            {
                "source":
                    "User",

                "records":
                    result[
                        "sources"
                    ][
                        "user"
                    ]
            },

            {
                "source":
                    "Historical",

                "records":
                    result[
                        "sources"
                    ][
                        "historical"
                    ]
            },

            {
                "source":
                    "API",

                "records":
                    result[
                        "sources"
                    ][
                        "api"
                    ]
            }
        ]
    }


# ============================================================
# ANOMALIES
# ============================================================

@router.get(
    "/anomalies"
)
async def anomalies(
    current_user=Depends(
        get_current_user
    )
):

    result = await dashboard(
        current_user
    )

    return {

        "success":
            True,

        "data":
            result[
                "user"
            ][
                "anomalies"
            ]
    }


# ============================================================
# YEARLY
# ============================================================

@router.get(
    "/yearly"
)
async def yearly():

    historical = (
        load_historical_dataset()
    )

    yearly_data = {}

    for row in historical:

        date_value = pd.to_datetime(
            row.get(
                "date"
            ),
            errors="coerce"
        )

        if pd.isna(
            date_value
        ):

            continue

        year = str(
            date_value.year
        )

        yearly_data[
            year
        ] = (

            yearly_data.get(
                year,
                0
            )

            +

            safe_number(
                row.get(
                    "amount"
                )
            )
        )

    result = [

        {
            "year":
                year,

            "amount":
                round(
                    amount,
                    2
                )
        }

        for year, amount
        in sorted(
            yearly_data.items()
        )
    ]

    return {

        "success":
            True,

        "data":
            result
    }


# ============================================================
# FINANCIAL SUMMARY
# ============================================================

@router.get(
    "/financial-summary"
)
async def financial_summary(
    current_user=Depends(
        get_current_user
    )
):

    result = await dashboard(
        current_user
    )

    overview = result[
        "overview"
    ]

    return {

        "success":
            True,

        "data": [

            {
                "metric":
                    "User Income",

                "value":
                    overview[
                        "user_income"
                    ]
            },

            {
                "metric":
                    "User Expenses",

                "value":
                    overview[
                        "user_expense"
                    ]
            },

            {
                "metric":
                    "Historical Spend",

                "value":
                    overview[
                        "historical_amount"
                    ]
            },

            {
                "metric":
                    "API Amount",

                "value":
                    overview[
                        "api_amount"
                    ]
            }
        ]
    }


# ============================================================
# DEBUG HISTORICAL
# ============================================================

@router.get(
    "/debug/historical"
)
async def debug_historical():

    try:

        data = (
            load_historical_dataset()
        )

        return {

            "success":
                True,

            "project_root":
                str(
                    PROJECT_ROOT
                ),

            "dataset_directory":
                str(
                    DATASET_DIRECTORY
                ),

            "personal_finance_exists":
                (
                    DATASET_DIRECTORY
                    / "personal_finance.csv"
                ).exists(),

            "historical_count":
                len(
                    data
                ),

            "sample":
                data[:5]
        }

    except Exception as error:

        print(
            "DEBUG HISTORICAL ERROR:",
            repr(error)
        )

        raise HTTPException(

            status_code=500,

            detail=str(
                error
            )
        )