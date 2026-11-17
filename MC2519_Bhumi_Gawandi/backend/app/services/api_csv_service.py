from pathlib import Path
import json

import pandas as pd

from bson import ObjectId
from bson.errors import InvalidId

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from app.core.auth_dependency import (
    get_current_user
)

from app.database.mongodb import database


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics"]
)


# ============================================================
# PROJECT ROOT
# ============================================================

ROUTER_PATH = Path(__file__).resolve()

PROJECT_ROOT_CANDIDATES = [
    ROUTER_PATH.parents[2],
    ROUTER_PATH.parents[3],
    Path.cwd(),
]

PROJECT_ROOT = next(
    (
        path
        for path in PROJECT_ROOT_CANDIDATES
        if (
            (path / "app").exists()
            or (path / "ml").exists()
            or (path / "dataset").exists()
        )
    ),
    ROUTER_PATH.parents[2],
)


# ============================================================
# EDA RESULTS
# ============================================================

# Historical files can be stored in different folders depending
# on the project structure. Search all common locations.

EDA_RESULT_CANDIDATES = [

    ROUTER_PATH.parents[2] / "eda" / "results",

    ROUTER_PATH.parents[3] / "eda" / "results",

    ROUTER_PATH.parents[2] / "ml" / "eda" / "results",

    ROUTER_PATH.parents[3] / "ml" / "eda" / "results",

    PROJECT_ROOT / "eda" / "results",

    PROJECT_ROOT / "ml" / "eda" / "results",

    Path.cwd() / "eda" / "results",

    Path.cwd() / "ml" / "eda" / "results",

]


def get_eda_results_directory():

    for directory in EDA_RESULT_CANDIDATES:

        try:

            if directory.exists():

                return directory.resolve()

        except Exception:

            continue

    return None


EDA_RESULTS = (
    get_eda_results_directory()
)


# ============================================================
# API DATA DIRECTORY
# ============================================================

API_DATA_DIRECTORY = (
    PROJECT_ROOT
    / "ml"
    / "dataset"
)


# ============================================================
# SECOND API DATA DIRECTORY
# ============================================================

# This makes the API work even if your dataset folder
# is directly inside the project root.

API_DATA_DIRECTORY_ALTERNATIVE = (
    PROJECT_ROOT
    / "dataset"
)


# ============================================================
# FIND API DATA DIRECTORY
# ============================================================

def get_api_data_directory():

    candidates = [
        API_DATA_DIRECTORY,
        API_DATA_DIRECTORY_ALTERNATIVE,
        PROJECT_ROOT / "ml" / "dataset",
        PROJECT_ROOT / "dataset",
        ROUTER_PATH.parents[2] / "ml" / "dataset",
        ROUTER_PATH.parents[2] / "dataset",
        ROUTER_PATH.parents[3] / "ml" / "dataset",
        ROUTER_PATH.parents[3] / "dataset",
    ]

    checked = set()

    for directory in candidates:

        directory = directory.resolve()

        if directory in checked:
            continue

        checked.add(directory)

        if directory.exists():
            return directory

    return API_DATA_DIRECTORY


# ============================================================
# JSON SAFE DATAFRAME
# ============================================================

def dataframe_to_records(df):

    if df.empty:

        return []

    json_data = df.to_json(
        orient="records",
        date_format="iso"
    )

    return json.loads(
        json_data
    )


# ============================================================
# LOAD CSV
# ============================================================

def load_csv(filename):

    directories = [

        EDA_RESULTS,

        ROUTER_PATH.parents[2] / "eda" / "results",

        ROUTER_PATH.parents[3] / "eda" / "results",

        ROUTER_PATH.parents[2] / "ml" / "eda" / "results",

        ROUTER_PATH.parents[3] / "ml" / "eda" / "results",

        PROJECT_ROOT / "eda" / "results",

        PROJECT_ROOT / "ml" / "eda" / "results",

        Path.cwd() / "eda" / "results",

        Path.cwd() / "ml" / "eda" / "results",

    ]

    checked = set()

    for directory in directories:

        if directory is None:
            continue

        try:
            directory = directory.resolve()
        except Exception:
            continue

        if directory in checked:
            continue

        checked.add(directory)

        file_path = directory / filename

        if not file_path.exists():
            continue

        try:

            df = pd.read_csv(
                file_path
            )

            print(
                f"Loaded historical CSV: "
                f"{file_path} ({len(df)} rows)"
            )

            return df

        except Exception as error:

            print(
                f"CSV error {file_path}:",
                repr(error)
            )

    # Final fallback. Search for the exact file name.
    roots = [
        ROUTER_PATH.parents[2],
        ROUTER_PATH.parents[3],
        PROJECT_ROOT,
        Path.cwd(),
    ]

    searched = set()

    for root in roots:

        try:
            root = root.resolve()
        except Exception:
            continue

        if root in searched or not root.exists():
            continue

        searched.add(root)

        try:
            matches = root.rglob(filename)
        except Exception:
            matches = []

        for file_path in matches:

            if not file_path.is_file():
                continue

            try:

                df = pd.read_csv(
                    file_path
                )

                print(
                    f"Loaded historical CSV by fallback: "
                    f"{file_path} ({len(df)} rows)"
                )

                return df

            except Exception:
                continue

    print(
        f"Historical CSV not found: {filename}"
    )

    return pd.DataFrame()


# ============================================================
# LOAD API CSV
# ============================================================

def load_api_csv(filename):

    api_directory = (
        get_api_data_directory()
    )

    file_path = (
        api_directory
        / filename
    )

    print(
        f"Checking API CSV: {file_path}"
    )

    if not file_path.exists():

        print(
            f"API CSV not found: {file_path}"
        )

        return pd.DataFrame()

    try:

        df = pd.read_csv(
            file_path
        )

        print(
            f"Loaded {filename}: {len(df)} rows"
        )

        return df

    except Exception as error:

        print(
            f"API CSV error {filename}:",
            repr(error)
        )

        return pd.DataFrame()


# ============================================================
# SAFE NUMBER
# ============================================================

def safe_number(value):

    try:

        if value is None:

            return 0.0

        number = float(
            value
        )

        if pd.isna(number):

            return 0.0

        return number

    except Exception:

        return 0.0


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
        "null"
    ]:

        return default

    return text


# ============================================================
# SAFE DATE
# ============================================================

def safe_date(value):

    if value is None:

        return ""

    try:

        if pd.isna(value):

            return ""

    except Exception:

        pass

    if isinstance(
        value,
        pd.Timestamp
    ):

        return value.isoformat()

    return str(
        value
    )


# ============================================================
# FIND COLUMN
# ============================================================

def find_column(
    df,
    possible_names
):

    columns = {
        str(column).lower().strip():
            column

        for column in df.columns
    }

    for name in possible_names:

        if name.lower() in columns:

            return columns[
                name.lower()
            ]

    return None


# ============================================================
# GET USER EXPENSES
# ============================================================

async def get_user_expenses(
    user_id
):

    expenses = await database.expenses.find(
        {
            "user_id": user_id
        }
    ).sort(
        "date",
        -1
    ).to_list(
        length=None
    )

    result = []

    for expense in expenses:

        result.append({

            "id":
                str(
                    expense.get(
                        "_id"
                    )
                ),

            "date":
                safe_date(
                    expense.get(
                        "date"
                    )
                ),

            "source":
                "User Expense",

            "source_type":
                "user",

            "data_source":
                "User",

            "type":
                "Expense",

            "category":
                safe_text(
                    expense.get(
                        "category"
                    ),
                    "Other"
                ),

            "description":
                safe_text(
                    expense.get(
                        "title"
                    ),
                    "Expense"
                ),

            "amount":
                safe_number(
                    expense.get(
                        "amount",
                        0
                    )
                ),

            "payment_method":
                safe_text(
                    expense.get(
                        "payment_method"
                    )
                ),

            "notes":
                safe_text(
                    expense.get(
                        "notes"
                    )
                ),

            "anomaly_status":
                "Normal",

            "status":
                "Normal"

        })

    return result


# ============================================================
# HISTORICAL DATA
# ============================================================

def get_historical_data():

    possible_files = [

        "eda_dataset.csv",

        "fused_financial_data.csv"

    ]

    for filename in possible_files:

        df = load_csv(
            filename
        )

        if df.empty:

            continue

        records = []

        date_column = find_column(
            df,
            [
                "date",
                "timestamp",
                "transaction_date"
            ]
        )

        source_column = find_column(
            df,
            [
                "source"
            ]
        )

        type_column = find_column(
            df,
            [
                "type",
                "transaction_type"
            ]
        )

        category_column = find_column(
            df,
            [
                "category",
                "expense_category"
            ]
        )

        description_column = find_column(
            df,
            [
                "description",
                "title",
                "merchant",
                "name"
            ]
        )

        amount_column = find_column(
            df,
            [
                "amount",
                "expense",
                "total_amount"
            ]
        )

        anomaly_column = find_column(
            df,
            [
                "anomaly_status",
                "anomaly"
            ]
        )

        for index, row in df.iterrows():

            date_value = (
                row.get(
                    date_column
                )
                if date_column
                else ""
            )

            source_value = (
                row.get(
                    source_column
                )
                if source_column
                else "Historical Finance Dataset"
            )

            type_value = (
                row.get(
                    type_column
                )
                if type_column
                else "Expense"
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
                else ""
            )

            amount_value = (
                row.get(
                    amount_column
                )
                if amount_column
                else 0
            )

            anomaly_value = (
                row.get(
                    anomaly_column
                )
                if anomaly_column
                else "Normal"
            )

            records.append({

                "id":
                    f"historical-{index}",

                "date":
                    safe_date(
                        date_value
                    ),

                "source":
                    safe_text(
                        source_value,
                        "Historical Finance Dataset"
                    ),

                "source_type":
                    "historical",

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
                        description_value
                    ),

                "amount":
                    safe_number(
                        amount_value
                    ),

                "payment_method":
                    "",

                "notes":
                    "",

                "anomaly_status":
                    safe_text(
                        anomaly_value,
                        "Normal"
                    ),

                "status":
                    safe_text(
                        anomaly_value,
                        "Normal"
                    )

            })

        return records

    return []


# ============================================================
# HISTORICAL DATA
# ============================================================

@router.get("/historical-data")
async def historical_data():

    print()
    print(
        "================================================"
    )
    print(
        "HISTORICAL DATA ENDPOINT"
    )
    print(
        "================================================"
    )

    print(
        "EDA results directory:",
        EDA_RESULTS
    )

    data = get_historical_data()

    print(
        "Historical records:",
        len(data)
    )

    return {

        "success":
            True,

        "total_records":
            len(data),

        "data":
            data

    }


# ============================================================
# API DATA
# ============================================================

def get_api_data():

    records = []


    # ========================================================
    # GROQ AI
    # ========================================================

    df = load_api_csv(
        "api_groq.csv"
    )

    if not df.empty:

        for index, row in df.iterrows():

            timestamp = safe_date(
                row.get(
                    "timestamp"
                )
            )

            user_message = safe_text(
                row.get(
                    "user_message"
                ),
                "AI Query"
            )

            response = safe_text(
                row.get(
                    "response"
                )
            )

            status = safe_text(
                row.get(
                    "status"
                ),
                "Success"
            )

            records.append({

                "id":
                    f"groq-{index}",

                "date":
                    timestamp,

                "source":
                    "Groq AI",

                "source_type":
                    "api",

                "data_source":
                    "API",

                "type":
                    "AI",

                "category":
                    "AI Query",

                "description":
                    user_message,

                "amount":
                    0.0,

                "payment_method":
                    "AI",

                "notes":
                    response,

                "anomaly_status":
                    "Normal",

                "status":
                    status

            })


    # ========================================================
    # FINANCIAL NEWS API
    # ========================================================

    df = load_api_csv(
        "api_news.csv"
    )

    if not df.empty:

        for index, row in df.iterrows():

            published_at = safe_date(
                row.get(
                    "published_at"
                )
            )

            timestamp = safe_date(
                row.get(
                    "timestamp"
                )
            )

            date_value = (
                published_at
                or timestamp
            )

            title = safe_text(
                row.get(
                    "title"
                ),
                "Financial News"
            )

            description = safe_text(
                row.get(
                    "description"
                )
            )

            source_name = safe_text(
                row.get(
                    "source"
                )
            )

            records.append({

                "id":
                    f"news-{index}",

                "date":
                    date_value,

                "source":
                    "Financial News API",

                "source_type":
                    "api",

                "data_source":
                    "API",

                "type":
                    "News",

                "category":
                    "Financial News",

                "description":
                    title,

                "amount":
                    0.0,

                "payment_method":
                    "API",

                "notes":
                    description,

                "api_source":
                    source_name,

                "anomaly_status":
                    "Normal",

                "status":
                    "Normal"

            })


    # ========================================================
    # CURRENCY API
    # ========================================================

    df = load_api_csv(
        "api_currency.csv"
    )

    if not df.empty:

        for index, row in df.iterrows():

            base = safe_text(
                row.get(
                    "base_currency"
                )
            )

            target = safe_text(
                row.get(
                    "target_currency"
                )
            )

            amount = safe_number(
                row.get(
                    "amount",
                    0
                )
            )

            rate = safe_number(
                row.get(
                    "exchange_rate",
                    0
                )
            )

            converted_amount = safe_number(
                row.get(
                    "converted_amount",
                    0
                )
            )

            timestamp = safe_date(
                row.get(
                    "timestamp"
                )
            )

            records.append({

                "id":
                    f"currency-{index}",

                "date":
                    timestamp,

                "source":
                    "Currency API",

                "source_type":
                    "api",

                "data_source":
                    "API",

                "type":
                    "Currency",

                "category":
                    "Currency Conversion",

                "description":
                    f"{base} → {target}",

                "amount":
                    amount,

                "payment_method":
                    "API",

                "notes":
                    (
                        f"Rate: {rate} | "
                        f"Converted: {converted_amount}"
                    ),

                "base_currency":
                    base,

                "target_currency":
                    target,

                "exchange_rate":
                    rate,

                "converted_amount":
                    converted_amount,

                "anomaly_status":
                    "Normal",

                "status":
                    "Normal"

            })


    # ========================================================
    # EXCHANGE RATE API
    # ========================================================

    df = load_api_csv(
        "api_exchange_rate.csv"
    )

    if not df.empty:

        for index, row in df.iterrows():

            date_value = safe_date(
                row.get(
                    "date"
                )
            )

            timestamp = safe_date(
                row.get(
                    "timestamp"
                )
            )

            final_date = (
                date_value
                or timestamp
            )

            base = safe_text(
                row.get(
                    "base_currency"
                )
            )

            target = safe_text(
                row.get(
                    "target_currency"
                )
            )

            rate = safe_number(
                row.get(
                    "exchange_rate",
                    0
                )
            )

            records.append({

                "id":
                    f"exchange-{index}",

                "date":
                    final_date,

                "source":
                    "Exchange Rate API",

                "source_type":
                    "api",

                "data_source":
                    "API",

                "type":
                    "Exchange Rate",

                "category":
                    "Exchange Rate",

                "description":
                    f"{base} → {target}",

                "amount":
                    rate,

                "payment_method":
                    "API",

                "notes":
                    f"Exchange rate: {rate}",

                "base_currency":
                    base,

                "target_currency":
                    target,

                "exchange_rate":
                    rate,

                "anomaly_status":
                    "Normal",

                "status":
                    "Normal"

            })


    # ========================================================
    # RECEIPT OCR
    # ========================================================

    df = load_api_csv(
        "api_ocr.csv"
    )

    if not df.empty:

        for index, row in df.iterrows():

            date_value = safe_date(
                row.get(
                    "date"
                )
            )

            timestamp = safe_date(
                row.get(
                    "timestamp"
                )
            )

            final_date = (
                date_value
                or timestamp
            )

            merchant = safe_text(
                row.get(
                    "merchant"
                ),
                "Receipt"
            )

            category = safe_text(
                row.get(
                    "category"
                ),
                "Other"
            )

            amount = safe_number(
                row.get(
                    "amount",
                    0
                )
            )

            payment_method = safe_text(
                row.get(
                    "payment_method"
                ),
                "OCR"
            )

            records.append({

                "id":
                    f"ocr-{index}",

                "date":
                    final_date,

                "source":
                    "Receipt OCR",

                "source_type":
                    "api",

                "data_source":
                    "API",

                "type":
                    "Expense",

                "category":
                    category,

                "description":
                    merchant,

                "amount":
                    amount,

                "payment_method":
                    payment_method,

                "notes":
                    "",

                "anomaly_status":
                    "Normal",

                "status":
                    "Normal"

            })


    # ========================================================
    # SORT API RECORDS
    # ========================================================

    def api_date_key(item):

        try:

            return pd.to_datetime(
                item.get(
                    "date"
                )
            )

        except Exception:

            return pd.Timestamp.min


    records.sort(
        key=api_date_key,
        reverse=True
    )


    print(
        "============================================"
    )

    print(
        "API RECORDS LOADED:",
        len(records)
    )

    print(
        "============================================"
    )

    return records


# ============================================================
# USER CATEGORY DATA
# ============================================================

def calculate_categories(
    expenses
):

    grouped = {}

    for expense in expenses:

        category = (
            expense.get(
                "category"
            )
            or "Other"
        )

        amount = safe_number(
            expense.get(
                "amount"
            )
        )

        grouped[category] = (
            grouped.get(
                category,
                0
            )
            + amount
        )

    result = [

        {
            "category":
                category,

            "amount":
                round(
                    amount,
                    2
                )

        }

        for category, amount
        in grouped.items()

    ]

    result.sort(
        key=lambda x:
            x["amount"],
        reverse=True
    )

    return result


# ============================================================
# USER MONTHLY DATA
# ============================================================

def calculate_monthly(
    expenses
):

    grouped = {}

    for expense in expenses:

        date_value = expense.get(
            "date"
        )

        if not date_value:

            continue

        try:

            date = pd.to_datetime(
                date_value
            )

            month = date.strftime(
                "%Y-%m"
            )

        except Exception:

            continue

        amount = safe_number(
            expense.get(
                "amount"
            )
        )

        grouped[month] = (
            grouped.get(
                month,
                0
            )
            + amount
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
            grouped.items()
        )

    ]


# ============================================================
# USER ANOMALIES
# ============================================================

def calculate_anomalies(
    expenses
):

    if not expenses:

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

    mean = series.mean()

    std = series.std()

    if pd.isna(std) or std == 0:

        threshold = mean * 2

    else:

        threshold = (
            mean
            + (2 * std)
        )

    result = []

    for expense in expenses:

        amount = safe_number(
            expense.get(
                "amount"
            )
        )

        row = dict(
            expense
        )

        if amount > threshold:

            row[
                "anomaly_status"
            ] = "Anomaly"

        else:

            row[
                "anomaly_status"
            ] = "Normal"

        row[
            "status"
        ] = row[
            "anomaly_status"
        ]

        result.append(
            row
        )

    return result


# ============================================================
# CREATE FUSED DATA
# ============================================================

def create_fused_data(
    user_expenses,
    api_data,
    historical_data
):

    combined = [

        *user_expenses,

        *api_data,

        *historical_data

    ]

    def date_key(item):

        try:

            date_value = item.get(
                "date"
            )

            if not date_value:

                return pd.Timestamp.min

            return pd.to_datetime(
                date_value
            )

        except Exception:

            return pd.Timestamp.min


    combined.sort(
        key=date_key,
        reverse=True
    )

    return combined[:27]


# ============================================================
# DASHBOARD
# ============================================================

@router.get("/dashboard")
async def get_dashboard(
    current_user=Depends(
        get_current_user
    )
):

    try:

        # ====================================================
        # USER ID
        # ====================================================

        user_id = current_user.get(
            "user_id"
        )

        if not user_id:

            raise HTTPException(
                status_code=401,
                detail="User ID missing from token."
            )


        # ====================================================
        # OBJECT ID
        # ====================================================

        try:

            user_object_id = ObjectId(
                user_id
            )

        except (
            InvalidId,
            TypeError
        ):

            raise HTTPException(
                status_code=401,
                detail="Invalid user ID."
            )


        # ====================================================
        # USER
        # ====================================================

        user = await database.users.find_one(
            {
                "_id":
                    user_object_id
            }
        )

        if user is None:

            raise HTTPException(
                status_code=404,
                detail="User not found."
            )


        # ====================================================
        # INCOME
        # ====================================================

        user_income = safe_number(
            user.get(
                "monthly_income",
                0
            )
        )


        # ====================================================
        # USER EXPENSES
        # ====================================================

        user_expenses = await get_user_expenses(
            user_id
        )


        # ====================================================
        # USER EXPENSE TOTAL
        # ====================================================

        user_total_expense = sum(

            safe_number(
                item.get(
                    "amount"
                )
            )

            for item in user_expenses

        )


        # ====================================================
        # USER CATEGORIES
        # ====================================================

        user_categories = calculate_categories(
            user_expenses
        )


        # ====================================================
        # USER MONTHLY
        # ====================================================

        user_monthly = calculate_monthly(
            user_expenses
        )


        # ====================================================
        # USER ANOMALIES
        # ====================================================

        user_anomalies = calculate_anomalies(
            user_expenses
        )

        user_anomaly_count = sum(

            1

            for item in user_anomalies

            if str(
                item.get(
                    "anomaly_status",
                    ""
                )
            ).lower()
            == "anomaly"

        )


        # ====================================================
        # HISTORICAL
        # ====================================================

        historical_data = get_historical_data()

        historical_anomaly_count = sum(

            1

            for item in historical_data

            if str(
                item.get(
                    "anomaly_status",
                    ""
                )
            ).lower()
            == "anomaly"

        )


        # ====================================================
        # API DATA
        # ====================================================

        api_records = get_api_data()


        # ====================================================
        # API AMOUNT
        # ====================================================

        api_amount = sum(

            safe_number(
                item.get(
                    "amount"
                )
            )

            for item in api_records

        )


        # ====================================================
        # HISTORICAL AMOUNT
        # ====================================================

        historical_amount = sum(

            safe_number(
                item.get(
                    "amount"
                )
            )

            for item in historical_data

        )


        # ====================================================
        # FUSED
        # ====================================================

        fused_data = create_fused_data(

            user_expenses,

            api_records,

            historical_data

        )


        # ====================================================
        # RESPONSE
        # ====================================================

        return {

            "success":
                True,

            "overview": {

                "user_income":
                    round(
                        user_income,
                        2
                    ),

                "user_expense":
                    round(
                        user_total_expense,
                        2
                    ),

                "user_transactions":
                    len(
                        user_expenses
                    ),

                "user_anomalies":
                    user_anomaly_count,

                "historical_transactions":
                    len(
                        historical_data
                    ),

                "historical_anomalies":
                    historical_anomaly_count,

                "api_transactions":
                    len(
                        api_records
                    ),

                "api_amount":
                    round(
                        api_amount,
                        2
                    ),

                "historical_amount":
                    round(
                        historical_amount,
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
                    user_categories,

                "monthly":
                    user_monthly,

                "anomalies":
                    user_anomalies,

                "anomaly_summary": {

                    "normal":
                        len(
                            user_expenses
                        )
                        -
                        user_anomaly_count,

                    "anomaly":
                        user_anomaly_count

                }

            },

            "historical": {

                "data":
                    historical_data

            },

            "api": {

                "data":
                    api_records

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
                        api_records
                    )

            },

            "fused_data":
                fused_data

        }


    except HTTPException:

        raise

    except Exception as error:

        print(
            "ANALYTICS DASHBOARD ERROR:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# USER EXPENSES
# ============================================================

@router.get("/user-expenses")
async def get_user_expenses_api(
    current_user=Depends(
        get_current_user
    )
):

    user_id = current_user[
        "user_id"
    ]

    data = await get_user_expenses(
        user_id
    )

    return {

        "success":
            True,

        "total_records":
            len(data),

        "data":
            data

    }


# ============================================================
# SUMMARY
# ============================================================

@router.get("/summary")
async def summary(
    current_user=Depends(
        get_current_user
    )
):

    dashboard = await get_dashboard(
        current_user
    )

    return {

        "success":
            True,

        "data": [

            {
                "metric":
                    "User Income",

                "value":
                    dashboard[
                        "overview"
                    ][
                        "user_income"
                    ]

            },

            {
                "metric":
                    "User Expense",

                "value":
                    dashboard[
                        "overview"
                    ][
                        "user_expense"
                    ]

            },

            {
                "metric":
                    "Transactions",

                "value":
                    dashboard[
                        "overview"
                    ][
                        "user_transactions"
                    ]

            },

            {
                "metric":
                    "API Records",

                "value":
                    dashboard[
                        "overview"
                    ][
                        "api_transactions"
                    ]

            },

            {
                "metric":
                    "Historical Records",

                "value":
                    dashboard[
                        "overview"
                    ][
                        "historical_transactions"
                    ]

            }

        ]

    }


# ============================================================
# CATEGORIES
# ============================================================

@router.get("/categories")
async def categories(
    current_user=Depends(
        get_current_user
    )
):

    dashboard = await get_dashboard(
        current_user
    )

    return {

        "success":
            True,

        "data":
            dashboard[
                "user"
            ][
                "categories"
            ]

    }


# ============================================================
# MONTHLY
# ============================================================

@router.get("/monthly")
async def monthly(
    current_user=Depends(
        get_current_user
    )
):

    dashboard = await get_dashboard(
        current_user
    )

    return {

        "success":
            True,

        "data":
            dashboard[
                "user"
            ][
                "monthly"
            ]

    }


# ============================================================
# YEARLY HISTORICAL
# ============================================================

@router.get("/yearly")
async def yearly():

    df = load_csv(
        "yearly_expense_eda.csv"
    )

    return {

        "success":
            True,

        "data":
            dataframe_to_records(
                df
            )

    }


# ============================================================
# SOURCES
# ============================================================

@router.get("/sources")
async def sources(
    current_user=Depends(
        get_current_user
    )
):

    dashboard = await get_dashboard(
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
                    dashboard[
                        "sources"
                    ][
                        "user"
                    ]

            },

            {
                "source":
                    "Historical",

                "records":
                    dashboard[
                        "sources"
                    ][
                        "historical"
                    ]

            },

            {
                "source":
                    "API",

                "records":
                    dashboard[
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

@router.get("/anomalies")
async def anomalies(
    current_user=Depends(
        get_current_user
    )
):

    dashboard = await get_dashboard(
        current_user
    )

    return {

        "success":
            True,

        "data":
            dashboard[
                "user"
            ][
                "anomalies"
            ]

    }


# ============================================================
# API DATA
# ============================================================

@router.get("/api-data")
async def api_data():

    print()
    print(
        "================================================"
    )
    print(
        "API DATA ENDPOINT"
    )
    print(
        "================================================"
    )

    print(
        "API directory:",
        get_api_data_directory()
    )

    data = get_api_data()

    print(
        "Total API records:",
        len(data)
    )

    print(
        "================================================"
    )

    return {

        "success":
            True,

        "total_records":
            len(data),

        "data":
            data

    }


# ============================================================
# FINANCIAL SUMMARY
# ============================================================

@router.get("/financial-summary")
async def financial_summary():

    df = load_csv(
        "financial_summary.csv"
    )

    return {

        "success":
            True,

        "data":
            dataframe_to_records(
                df
            )

    }


# ============================================================
# FUSED DATA
# ============================================================

@router.get("/data")
async def fused_data(
    current_user=Depends(
        get_current_user
    )
):

    dashboard = await get_dashboard(
        current_user
    )

    data = dashboard[
        "fused_data"
    ]

    return {

        "success":
            True,

        "total_records":
            len(data),

        "user_records":
            dashboard[
                "sources"
            ][
                "user"
            ],

        "api_records":
            dashboard[
                "sources"
            ][
                "api"
            ],

        "historical_records":
            dashboard[
                "sources"
            ][
                "historical"
            ],

        "data":
            data

    }