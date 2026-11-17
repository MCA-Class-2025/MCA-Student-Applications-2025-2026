from pathlib import Path
from datetime import datetime

import pandas as pd
from bson import ObjectId
from bson.errors import InvalidId

from app.database.mongodb import database


class AnalyticsService:

    # ============================================================
    # PATHS
    # ============================================================

    # ============================================================
    # PROJECT ROOT
    # ============================================================

    SERVICE_PATH = Path(__file__).resolve()

    PROJECT_ROOT_CANDIDATES = [
        SERVICE_PATH.parents[3],
        SERVICE_PATH.parents[2],
        Path.cwd(),
        Path.cwd().parent,
    ]

    # The ML folder is outside backend/app in this project.
    # Always prefer the project root that actually contains ml/.
    PROJECT_ROOT = next(
        (
            path.resolve()
            for path in PROJECT_ROOT_CANDIDATES
            if (path / "ml").is_dir()
        ),
        SERVICE_PATH.parents[3],
    )

    DATASET_DIR = (
        PROJECT_ROOT
        / "ml"
        / "dataset"
    )

    EDA_RESULTS = (
        PROJECT_ROOT
        / "ml"
        / "eda"
        / "results"
    )

    # ============================================================
    # API CSV FILES
    # ============================================================

    API_FILES = {
        "groq": DATASET_DIR / "api_groq.csv",
        "news": DATASET_DIR / "api_news.csv",
        "currency": DATASET_DIR / "api_currency.csv",
        "exchange": DATASET_DIR / "api_exchange_rate.csv",
        "ocr": DATASET_DIR / "api_ocr.csv",
    }

    # ============================================================
    # SAFE NUMBER
    # ============================================================

    @staticmethod
    def safe_float(value, default=0.0):

        try:

            if value is None:
                return default

            if pd.isna(value):
                return default

            return float(value)

        except Exception:

            return default

    # ============================================================
    # SAFE DATE
    # ============================================================

    @staticmethod
    def date_value(value):

        if value is None:
            return ""

        try:

            if isinstance(value, datetime):

                return value.isoformat()

            return str(value)

        except Exception:

            return ""

    # ============================================================
    # READ CSV
    # ============================================================

    @classmethod
    def read_csv(cls, path):

        candidates = [
            path,
            cls.PROJECT_ROOT / "ml" / "dataset" / path.name,
            cls.PROJECT_ROOT / "dataset" / path.name,
            Path.cwd() / "ml" / "dataset" / path.name,
            Path.cwd() / "dataset" / path.name,
        ]

        checked = set()

        for candidate in candidates:

            try:
                candidate = candidate.resolve()
            except Exception:
                continue

            if candidate in checked:
                continue

            checked.add(candidate)

            if not candidate.exists():
                continue

            try:

                df = pd.read_csv(candidate)

                print(
                    f"Analytics CSV loaded: "
                    f"{candidate} ({len(df)} rows)"
                )

                return df

            except Exception as error:

                print(
                    f"Analytics CSV error: "
                    f"{candidate}: {error}"
                )

        print(
            f"Analytics CSV not found: {path.name}"
        )

        return pd.DataFrame()

    # ============================================================
    # GET USER
    # ============================================================

    @classmethod
    async def get_user(cls, user_id):

        try:

            object_id = ObjectId(user_id)

        except (
            InvalidId,
            TypeError
        ):

            return None

        return await database.users.find_one(
            {
                "_id": object_id
            },
            {
                "password": 0
            }
        )

    # ============================================================
    # GET USER EXPENSES
    # ============================================================

    @classmethod
    async def get_user_expenses(cls, user_id):

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

                "_id":
                    str(
                        expense.get(
                            "_id",
                            ""
                        )
                    ),

                "user_id":
                    expense.get(
                        "user_id",
                        user_id
                    ),

                "title":
                    expense.get(
                        "title",
                        ""
                    ),

                "amount":
                    cls.safe_float(
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
                    cls.date_value(
                        expense.get(
                            "date",
                            ""
                        )
                    ),

                "notes":
                    expense.get(
                        "notes",
                        ""
                    ),

                "source":
                    "User Expense",

                "source_type":
                    "user",

                "type":
                    "Expense",

                "description":
                    expense.get(
                        "title",
                        ""
                    ),

                "anomaly_status":
                    "Normal",

                "anomaly_score":
                    None,

            })

        return result

    # ============================================================
    # USER ANOMALY DETECTION
    # ============================================================

    @classmethod
    def calculate_user_anomalies(
        cls,
        expenses
    ):

        if not expenses:

            return []

        amounts = [
            cls.safe_float(
                item.get("amount")
            )
            for item in expenses
        ]

        valid_amounts = [
            amount
            for amount in amounts
            if amount > 0
        ]

        if len(valid_amounts) < 4:

            for item in expenses:

                item["anomaly_status"] = "Normal"
                item["anomaly_score"] = None

            return []

        series = pd.Series(
            valid_amounts
        )

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        iqr = q3 - q1

        if iqr == 0:

            threshold = q3 * 2

        else:

            threshold = q3 + (
                1.5 * iqr
            )

        anomalies = []

        for item in expenses:

            amount = cls.safe_float(
                item.get("amount")
            )

            if amount > threshold:

                item["anomaly_status"] = "Anomaly"

                score = (
                    amount / threshold
                    if threshold > 0
                    else 1
                )

                item["anomaly_score"] = round(
                    score,
                    3
                )

                anomalies.append({

                    **item,

                    "anomaly_status":
                        "Anomaly",

                    "anomaly_score":
                        round(
                            score,
                            3
                        )

                })

            else:

                item["anomaly_status"] = "Normal"

                item["anomaly_score"] = None

        return anomalies

    # ============================================================
    # USER CATEGORY ANALYTICS
    # ============================================================

    @classmethod
    def get_user_categories(
        cls,
        expenses
    ):

        grouped = {}

        for expense in expenses:

            if (
                str(
                    expense.get(
                        "type",
                        "Expense"
                    )
                ).lower()
                == "income"
            ):
                continue

            category = (
                expense.get(
                    "category",
                    "Other"
                )
                or "Other"
            )

            amount = cls.safe_float(
                expense.get(
                    "amount",
                    0
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
            key=lambda item:
                item["amount"],
            reverse=True
        )

        return result

    # ============================================================
    # USER MONTHLY DATA
    # ============================================================

    @classmethod
    def get_user_monthly(
        cls,
        expenses
    ):

        grouped = {}

        for expense in expenses:

            date_value = (
                expense.get(
                    "date"
                )
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

            amount = cls.safe_float(
                expense.get(
                    "amount",
                    0
                )
            )

            grouped[month] = (
                grouped.get(
                    month,
                    0
                )
                + amount
            )

        result = [

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
            in grouped.items()

        ]

        result.sort(
            key=lambda item:
                item["month"]
        )

        return result

    # ============================================================
    # USER ANOMALY SUMMARY
    # ============================================================

    @classmethod
    def get_user_anomaly_summary(
        cls,
        expenses
    ):

        anomalies = [
            item
            for item in expenses
            if str(
                item.get(
                    "anomaly_status",
                    ""
                )
            ).lower()
            == "anomaly"
        ]

        return {

            "normal":
                max(
                    len(expenses)
                    - len(anomalies),
                    0
                ),

            "anomaly":
                len(anomalies),

            "total":
                len(expenses)

        }

    # ============================================================
    # HISTORICAL DATA
    # ============================================================

    @classmethod
    def get_historical_data(cls):

        # Historical EDA source is the real project dataset.
        # personal_finance.csv is generated/kept under:
        # <project-root>/ml/dataset/personal_finance.csv
        path = (
            cls.DATASET_DIR
            / "personal_finance.csv"
        )

        df = cls.read_csv(
            path
        )

        print(
            "Historical dataset path:",
            path.resolve()
        )

        print(
            "Historical dataset exists:",
            path.exists()
        )

        print(
            "Historical dataset rows:",
            len(df)
        )

        if df.empty:

            return []

        result = []

        for _, row in df.iterrows():

            transaction_type = (
                row.get(
                    "Type",
                    "Expense"
                )
            )

            result.append({

                "id":
                    f"historical-{len(result)}",

                "source":
                    "Historical Finance Dataset",

                "source_type":
                    "historical",

                "date":
                    cls.date_value(
                        row.get(
                            "Date",
                            ""
                        )
                    ),

                "category":
                    row.get(
                        "Category",
                        row.get(
                            "category",
                            "Other"
                        )
                    ),

                "amount":
                    cls.safe_float(
                        row.get(
                            "Amount",
                            row.get(
                                "amount",
                                0
                            )
                        )
                    ),

                "type":
                    transaction_type,

                "description":
                    row.get(
                        "Transaction Description",
                        row.get(
                            "Description",
                            row.get(
                                "description",
                                ""
                            )
                        )
                    ),

                "additional_data":
                    "",

                "anomaly_status":
                    row.get(
                        "Status",
                        "Normal"
                    ),

                "anomaly_score":
                    cls.safe_float(
                        row.get(
                            "Anomaly_Score"
                        ),
                        None
                    )

            })

        result.sort(
            key=lambda item:
                item.get(
                    "date",
                    ""
                ),
            reverse=True
        )

        return result

    # ============================================================
    # API DATA
    # ============================================================

    @classmethod
    def get_api_data(cls):

        result = []

        # --------------------------------------------------------
        # GROQ
        # --------------------------------------------------------

        df = cls.read_csv(
            cls.API_FILES["groq"]
        )

        if not df.empty:

            for _, row in df.iterrows():

                result.append({

                    "id":
                        f"groq-{len(result)}",

                    "source":
                        "Groq AI",

                    "source_type":
                        "api",

                    "date":
                        cls.date_value(
                            row.get(
                                "timestamp",
                                ""
                            )
                        ),

                    "category":
                        "AI Query",

                    "amount":
                        0,

                    "type":
                        "AI",

                    "description":
                        row.get(
                            "user_message",
                            ""
                        ),

                    "additional_data":
                        row.get(
                            "response",
                            ""
                        ),

                    "anomaly_status":
                        "Normal",

                    "anomaly_score":
                        None

                })

        # --------------------------------------------------------
        # NEWS
        # --------------------------------------------------------

        df = cls.read_csv(
            cls.API_FILES["news"]
        )

        if not df.empty:

            for _, row in df.iterrows():

                result.append({

                    "id":
                        f"news-{len(result)}",

                    "source":
                        "Financial News API",

                    "source_type":
                        "api",

                    "date":
                        cls.date_value(
                            row.get(
                                "published_at",
                                ""
                            )
                        ),

                    "category":
                        "Financial News",

                    "amount":
                        0,

                    "type":
                        "API",

                    "description":
                        row.get(
                            "title",
                            ""
                        ),

                    "additional_data":
                        row.get(
                            "source",
                            ""
                        ),

                    "anomaly_status":
                        "Normal",

                    "anomaly_score":
                        None

                })

        # --------------------------------------------------------
        # CURRENCY
        # --------------------------------------------------------

        df = cls.read_csv(
            cls.API_FILES["currency"]
        )

        if not df.empty:

            for _, row in df.iterrows():

                base = row.get(
                    "base_currency",
                    ""
                )

                target = row.get(
                    "target_currency",
                    ""
                )

                result.append({

                    "id":
                        f"currency-{len(result)}",

                    "source":
                        "Currency API",

                    "source_type":
                        "api",

                    "date":
                        cls.date_value(
                            row.get(
                                "timestamp",
                                ""
                            )
                        ),

                    "category":
                        "Currency Conversion",

                    "amount":
                        cls.safe_float(
                            row.get(
                                "amount",
                                0
                            )
                        ),

                    "type":
                        "API",

                    "description":
                        f"{base} to {target}",

                    "additional_data":
                        row.get(
                            "converted_amount",
                            ""
                        ),

                    "anomaly_status":
                        "Normal",

                    "anomaly_score":
                        None

                })

        # --------------------------------------------------------
        # EXCHANGE RATE
        # --------------------------------------------------------

        df = cls.read_csv(
            cls.API_FILES["exchange"]
        )

        if not df.empty:

            for _, row in df.iterrows():

                base = row.get(
                    "base_currency",
                    ""
                )

                target = row.get(
                    "target_currency",
                    ""
                )

                result.append({

                    "id":
                        f"exchange-{len(result)}",

                    "source":
                        "Exchange Rate API",

                    "source_type":
                        "api",

                    "date":
                        cls.date_value(
                            row.get(
                                "timestamp",
                                row.get(
                                    "date",
                                    ""
                                )
                            )
                        ),

                    "category":
                        "Exchange Rate",

                    "amount":
                        cls.safe_float(
                            row.get(
                                "exchange_rate",
                                0
                            )
                        ),

                    "type":
                        "API",

                    "description":
                        f"{base} to {target}",

                    "additional_data":
                        "",

                    "anomaly_status":
                        "Normal",

                    "anomaly_score":
                        None

                })

        # --------------------------------------------------------
        # OCR
        # --------------------------------------------------------

        df = cls.read_csv(
            cls.API_FILES["ocr"]
        )

        if not df.empty:

            for _, row in df.iterrows():

                result.append({

                    "id":
                        f"ocr-{len(result)}",

                    "source":
                        "Receipt OCR",

                    "source_type":
                        "api",

                    "date":
                        cls.date_value(
                            row.get(
                                "date",
                                row.get(
                                    "timestamp",
                                    ""
                                )
                            )
                        ),

                    "category":
                        row.get(
                            "category",
                            "Other"
                        ),

                    "amount":
                        cls.safe_float(
                            row.get(
                                "amount",
                                0
                            )
                        ),

                    "type":
                        "Expense",

                    "description":
                        row.get(
                            "merchant",
                            ""
                        ),

                    "additional_data":
                        row.get(
                            "payment_method",
                            ""
                        ),

                    "anomaly_status":
                        "Normal",

                    "anomaly_score":
                        None

                })

        result.sort(
            key=lambda item:
                item.get(
                    "date",
                    ""
                ),
            reverse=True
        )

        return result

    # ============================================================
    # BUILD FUSED DATA
    # ============================================================

    @classmethod
    async def build_fused_data(
        cls,
        user_id
    ):

        # --------------------------------------------------------
        # USER
        # --------------------------------------------------------

        user_expenses = (
            await cls.get_user_expenses(
                user_id
            )
        )

        user_anomalies = (
            cls.calculate_user_anomalies(
                user_expenses
            )
        )

        # --------------------------------------------------------
        # HISTORICAL
        # --------------------------------------------------------

        historical = (
            cls.get_historical_data()
        )

        # --------------------------------------------------------
        # API
        # --------------------------------------------------------

        api_data = (
            cls.get_api_data()
        )

        # --------------------------------------------------------
        # COMBINE ALL REAL RECORDS
        # --------------------------------------------------------

        combined = [
            *user_expenses,
            *historical,
            *api_data
        ]

        # --------------------------------------------------------
        # SORT ALL RECORDS
        # --------------------------------------------------------

        def sort_key(item):
            try:
                value = item.get("date", "")

                if not value:
                    return pd.Timestamp.min

                return pd.to_datetime(value)

            except Exception:
                return pd.Timestamp.min

        combined.sort(
            key=sort_key,
            reverse=True
        )

        # No artificial limit is applied here.
        # Every real user, historical and API record
        # is returned to the frontend.

        return {

            "user_expenses":
                user_expenses,

            "user_anomalies":
                user_anomalies,

            "historical_data":
                historical,

            "api_data":
                api_data,

            "fused_data":
                combined

        }

    # ============================================================
    # DASHBOARD DATA
    # ============================================================

    @classmethod
    async def get_dashboard_data(
        cls,
        user_id
    ):

        user = await cls.get_user(
            user_id
        )

        if user is None:

            return {

                "success": False,

                "message":
                    "User not found."

            }

        data = await cls.build_fused_data(
            user_id
        )

        user_expenses = data[
            "user_expenses"
        ]

        user_anomalies = data[
            "user_anomalies"
        ]

        # --------------------------------------------------------
        # USER INCOME
        # --------------------------------------------------------

        monthly_income = cls.safe_float(
            user.get(
                "monthly_income",
                0
            )
        )

        # --------------------------------------------------------
        # USER EXPENSE
        # --------------------------------------------------------

        total_expense = sum(

            cls.safe_float(
                item.get(
                    "amount",
                    0
                )
            )

            for item in user_expenses

            if str(
                item.get(
                    "type",
                    "Expense"
                )
            ).lower()
            != "income"

        )

        # --------------------------------------------------------
        # HISTORICAL TOTAL
        # --------------------------------------------------------

        historical = data[
            "historical_data"
        ]

        historical_expense = sum(

            cls.safe_float(
                item.get(
                    "amount",
                    0
                )
            )

            for item in historical

            if str(
                item.get(
                    "type",
                    "Expense"
                )
            ).lower()
            == "expense"

        )

        # --------------------------------------------------------
        # HISTORICAL ANOMALIES
        # --------------------------------------------------------

        historical_anomalies = sum(

            1

            for item in historical

            if str(
                item.get(
                    "anomaly_status",
                    ""
                )
            ).lower()
            == "anomaly"

        )

        # --------------------------------------------------------
        # SOURCE COUNTS
        # --------------------------------------------------------

        api_records = data["api_data"]

        api_source_counts = {

            "groq":
                sum(
                    1
                    for item in api_records
                    if item.get("source") == "Groq AI"
                ),

            "news":
                sum(
                    1
                    for item in api_records
                    if item.get("source") == "Financial News API"
                ),

            "currency":
                sum(
                    1
                    for item in api_records
                    if item.get("source") == "Currency API"
                ),

            "exchange":
                sum(
                    1
                    for item in api_records
                    if item.get("source") == "Exchange Rate API"
                ),

            "ocr":
                sum(
                    1
                    for item in api_records
                    if item.get("source") == "Receipt OCR"
                ),

        }

        source_counts = {

            "user":
                len(user_expenses),

            "historical":
                len(historical),

            "api":
                len(api_records),

            "fused":
                len(
                    data["fused_data"]
                ),

            "api_sources":
                api_source_counts

        }

        return {

            "success":
                True,

            "overview": {

                "user_income":
                    monthly_income,

                "user_expense":
                    round(
                        total_expense,
                        2
                    ),

                "user_transactions":
                    len(user_expenses),

                "user_anomalies":
                    len(user_anomalies),

                "historical_expense":
                    round(
                        historical_expense,
                        2
                    ),

                "historical_transactions":
                    len(historical),

                "historical_anomalies":
                    historical_anomalies,

                "fused_records":
                    len(
                        data[
                            "fused_data"
                        ]
                    )

            },

            "user": {

                "expenses":
                    user_expenses,

                "categories":
                    cls.get_user_categories(
                        user_expenses
                    ),

                "monthly":
                    cls.get_user_monthly(
                        user_expenses
                    ),

                "anomalies":
                    user_anomalies,

                "anomaly_summary":
                    cls.get_user_anomaly_summary(
                        user_expenses
                    )

            },

            "historical": {

                "data":
                    historical

            },

            "api": {

                "data":
                    data["api_data"]

            },

            "sources":
                source_counts,

            "fused_data":
                data["fused_data"]

        }