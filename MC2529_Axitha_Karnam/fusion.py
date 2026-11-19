import os
import json
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# FOLDERS
# ============================================================

CSV_FOLDER = "csv"
FUSION_FOLDER = "csv/fused"
API_FOLDER = "csv/api_results"

os.makedirs(FUSION_FOLDER, exist_ok=True)
os.makedirs(API_FOLDER, exist_ok=True)


# ============================================================
# API KEYS
# ============================================================

ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
FRED_KEY = os.getenv("FRED_API_KEY")
MARKETAUX_API_KEY = os.getenv("MARKETAUX_API_KEY")


# ============================================================
# DATASET PATHS
# ============================================================

ALPHA_FILE = os.path.join(
    CSV_FOLDER,
    "stock_dataset.csv"
)

FRANKFURTER_FILE = os.path.join(
    CSV_FOLDER,
    "economic_dataset.csv"
)

COINGECKO_FILE = os.path.join(
    CSV_FOLDER,
    "crypto_dataset.csv"
)

FRED_FILE = os.path.join(
    CSV_FOLDER,
    "Economic Indicators And Inflations.csv"
)

NEWS_FILE = os.path.join(
    CSV_FOLDER,
    "raw_partner_headlines.csv"
)


# ============================================================
# API RESULT FILES
# ============================================================

ALPHA_API_FILE = os.path.join(
    API_FOLDER,
    "alpha_vantage_api.csv"
)

FRANKFURTER_API_FILE = os.path.join(
    API_FOLDER,
    "frankfurter_api.csv"
)

COINGECKO_API_FILE = os.path.join(
    API_FOLDER,
    "coingecko_api.csv"
)

FRED_API_FILE = os.path.join(
    API_FOLDER,
    "fred_api.csv"
)

NEWS_API_FILE = os.path.join(
    API_FOLDER,
    "financial_news_api.csv"
)


# ============================================================
# FUSED FILES
# ============================================================

ALPHA_FUSED_FILE = os.path.join(
    FUSION_FOLDER,
    "fused_alpha_vantage.csv"
)

FRANKFURTER_FUSED_FILE = os.path.join(
    FUSION_FOLDER,
    "fused_frankfurter.csv"
)

COINGECKO_FUSED_FILE = os.path.join(
    FUSION_FOLDER,
    "fused_coingecko.csv"
)

FRED_FUSED_FILE = os.path.join(
    FUSION_FOLDER,
    "fused_fred.csv"
)

NEWS_FUSED_FILE = os.path.join(
    FUSION_FOLDER,
    "fused_financial_news.csv"
)


# ============================================================
# COMMON HELPERS
# ============================================================

def clean_columns(df):
    """
    Remove accidental spaces from CSV column names.
    """

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    return df


def save_json_response(response, filename):
    """
    Save complete API response for debugging/audit.
    """

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            response,
            file,
            indent=4
        )


def request_json(url, params=None):
    """
    Perform GET request and return JSON.
    """

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def add_api_metadata(df, api_name):
    """
    Add information identifying the API source.
    """

    df = df.copy()

    df["API_Source"] = api_name

    df["API_Fetched_At"] = datetime.now().isoformat()

    return df


# ============================================================
# 1. ALPHA VANTAGE
# ============================================================

def call_alpha_vantage():

    print("\n======================================")
    print("1. ALPHA VANTAGE")
    print("======================================")

    if not ALPHA_VANTAGE_KEY:

        print(
            "ERROR: ALPHA_VANTAGE_API_KEY is missing."
        )

        return False

    if not os.path.exists(ALPHA_FILE):

        print(
            "ERROR: stock_dataset.csv not found."
        )

        return False

    df = pd.read_csv(
        ALPHA_FILE
    )

    df = clean_columns(df)

    print("Dataset loaded.")
    print("Columns:", list(df.columns))

    symbol = os.getenv(
        "ALPHA_VANTAGE_SYMBOL",
        "IBM"
    )

    url = (
        "https://www.alphavantage.co/query"
    )

    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": "compact",
        "apikey": ALPHA_VANTAGE_KEY
    }

    print(
        f"Calling Alpha Vantage for: {symbol}"
    )

    try:

        response = request_json(
            url,
            params
        )

    except Exception as error:

        print(
            "Alpha Vantage API error:",
            error
        )

        return False

    if "Error Message" in response:

        print(
            "Alpha Vantage:",
            response["Error Message"]
        )

        return False

    if "Note" in response:

        print(
            "Alpha Vantage:",
            response["Note"]
        )

        return False

    time_series = response.get(
        "Time Series (Daily)",
        {}
    )

    if not time_series:

        print(
            "No Alpha Vantage time-series data returned."
        )

        print(response)

        return False

    api_rows = []

    for date, values in time_series.items():

        api_rows.append(
            {
                "Date": date,

                "Symbol": symbol,

                "API_Open": values.get(
                    "1. open"
                ),

                "API_High": values.get(
                    "2. high"
                ),

                "API_Low": values.get(
                    "3. low"
                ),

                "API_Close": values.get(
                    "4. close"
                ),

                "API_Volume": values.get(
                    "5. volume"
                )
            }
        )

    api_df = pd.DataFrame(
        api_rows
    )

    api_df = add_api_metadata(
        api_df,
        "Alpha Vantage"
    )

    api_df.to_csv(
        ALPHA_API_FILE,
        index=False
    )

    original = df.copy()

    original["Date"] = pd.to_datetime(
        original["Date"],
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    api_df["Date"] = pd.to_datetime(
        api_df["Date"],
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    fused = original.merge(
        api_df,
        on="Date",
        how="left",
        suffixes=(
            "_CSV",
            "_API"
        )
    )

    fused.to_csv(
        ALPHA_FUSED_FILE,
        index=False
    )

    print(
        f"✓ API result saved: {ALPHA_API_FILE}"
    )

    print(
        f"✓ Fused file saved: {ALPHA_FUSED_FILE}"
    )

    return True


# ============================================================
# 2. FRANKFURTER
# ============================================================

def call_frankfurter():

    print("\n======================================")
    print("2. FRANKFURTER")
    print("======================================")

    if not os.path.exists(FRANKFURTER_FILE):

        print(
            "ERROR: economic_dataset.csv not found."
        )

        return False

    df = pd.read_csv(
        FRANKFURTER_FILE
    )

    df = clean_columns(df)

    print("Dataset loaded.")
    print("Columns:", list(df.columns))

    base = os.getenv(
        "FRANKFURTER_BASE",
        "USD"
    )

    target = os.getenv(
        "FRANKFURTER_TARGET",
        "EUR"
    )

    url = (
        "https://api.frankfurter.dev/v1/latest"
    )

    params = {
        "base": base,
        "symbols": target
    }

    print(
        f"Calling Frankfurter: "
        f"{base} -> {target}"
    )

    try:

        response = request_json(
            url,
            params
        )

    except Exception as error:

        print(
            "Frankfurter API error:",
            error
        )

        return False

    if "rates" not in response:

        print(
            "Invalid Frankfurter response:"
        )

        print(response)

        return False

    rate = response["rates"].get(
        target
    )

    api_df = pd.DataFrame(
        [
            {
                "Date": response.get(
                    "date"
                ),

                "Base_Currency": base,

                "Target_Currency": target,

                "Exchange_Rate": rate
            }
        ]
    )

    api_df = add_api_metadata(
        api_df,
        "Frankfurter"
    )

    api_df.to_csv(
        FRANKFURTER_API_FILE,
        index=False
    )

    fused = df.copy()

    fused["API_Base_Currency"] = base

    fused["API_Target_Currency"] = target

    fused["API_Exchange_Rate"] = rate

    fused["API_Source"] = "Frankfurter"

    fused["API_Fetched_Date"] = response.get(
        "date"
    )

    fused.to_csv(
        FRANKFURTER_FUSED_FILE,
        index=False
    )

    print(
        f"✓ API result saved: {FRANKFURTER_API_FILE}"
    )

    print(
        f"✓ Fused file saved: {FRANKFURTER_FUSED_FILE}"
    )

    return True


# ============================================================
# 3. COINGECKO
# ============================================================

def call_coingecko():

    print("\n======================================")
    print("3. COINGECKO")
    print("======================================")

    if not os.path.exists(COINGECKO_FILE):

        print(
            "ERROR: crypto_dataset.csv not found."
        )

        return False

    df = pd.read_csv(
        COINGECKO_FILE
    )

    df = clean_columns(df)

    print("Dataset loaded.")
    print("Columns:", list(df.columns))

    symbols = (
        df["Symbol"]
        .dropna()
        .astype(str)
        .str.lower()
        .unique()
        .tolist()
    )

    symbol_to_id = {

        "btc": "bitcoin",

        "eth": "ethereum",

        "usdt": "tether",

        "usdc": "usd-coin",

        "bnb": "binancecoin",

        "xrp": "ripple",

        "ada": "cardano",

        "sol": "solana",

        "doge": "dogecoin"

    }

    coin_ids = []

    for symbol in symbols:

        if symbol in symbol_to_id:

            coin_ids.append(
                symbol_to_id[symbol]
            )

    if not coin_ids:

        print(
            "No supported CoinGecko symbols found."
        )

        return False

    url = (
        "https://api.coingecko.com/api/v3/"
        "simple/price"
    )

    params = {

        "ids":
            ",".join(coin_ids),

        "vs_currencies":
            "usd",

        "include_market_cap":
            "true",

        "include_24hr_vol":
            "true",

        "include_24hr_change":
            "true",

        "include_last_updated_at":
            "true"

    }

    print(
        "Calling CoinGecko for:",
        coin_ids
    )

    try:

        response = request_json(
            url,
            params
        )

    except Exception as error:

        print(
            "CoinGecko API error:",
            error
        )

        return False

    if not response:

        print(
            "CoinGecko returned an empty response."
        )

        return False

    api_rows = []

    reverse_mapping = {

        value: key

        for key, value
        in symbol_to_id.items()

    }

    for coin_id, values in response.items():

        api_rows.append(
            {

                "Symbol":
                    reverse_mapping.get(
                        coin_id,
                        coin_id
                    ).upper(),

                "CoinGecko_ID":
                    coin_id,

                "API_Price_USD":
                    values.get(
                        "usd"
                    ),

                "API_Market_Cap":
                    values.get(
                        "usd_market_cap"
                    ),

                "API_24h_Volume":
                    values.get(
                        "usd_24h_vol"
                    ),

                "API_24h_Change":
                    values.get(
                        "usd_24h_change"
                    ),

                "API_Last_Updated":
                    values.get(
                        "last_updated_at"
                    )

            }
        )

    api_df = pd.DataFrame(
        api_rows
    )

    if api_df.empty:

        print(
            "CoinGecko returned no usable data."
        )

        return False

    api_df = add_api_metadata(
        api_df,
        "CoinGecko"
    )

    api_df.to_csv(
        COINGECKO_API_FILE,
        index=False
    )

    fused = df.merge(
        api_df,
        on="Symbol",
        how="left",
        suffixes=(
            "_CSV",
            "_API"
        )
    )

    fused.to_csv(
        COINGECKO_FUSED_FILE,
        index=False
    )

    print(
        f"✓ API result saved: {COINGECKO_API_FILE}"
    )

    print(
        f"✓ Fused file saved: {COINGECKO_FUSED_FILE}"
    )

    return True


# ============================================================
# 4. FRED
# ============================================================

def call_fred():

    print("\n======================================")
    print("4. FRED")
    print("======================================")

    if not FRED_KEY:

        print(
            "ERROR: FRED_API_KEY is missing."
        )

        return False

    if not os.path.exists(FRED_FILE):

        print(
            "ERROR: Economic Indicators And "
            "Inflations.csv not found."
        )

        return False

    df = pd.read_csv(
        FRED_FILE
    )

    df = clean_columns(df)

    print("Dataset loaded.")
    print("Columns:", list(df.columns))

    series_id = os.getenv(
        "FRED_SERIES_ID",
        "GDPA"
    )

    url = (
        "https://api.stlouisfed.org/"
        "fred/series/observations"
    )

    params = {

        "series_id":
            series_id,

        "api_key":
            FRED_KEY,

        "file_type":
            "json",

        "observation_start":
            "2010-01-01",

        "observation_end":
            "2026-12-31",

        "sort_order":
            "asc"

    }

    print(
        f"Calling FRED series: {series_id}"
    )

    try:

        response = request_json(
            url,
            params
        )

    except Exception as error:

        print(
            "FRED API error:",
            error
        )

        return False

    if "error_code" in response:

        print(
            "FRED API error:",
            response.get(
                "error_message"
            )
        )

        return False

    observations = response.get(
        "observations",
        []
    )

    if not observations:

        print(
            "No FRED observations returned."
        )

        print(response)

        return False

    api_rows = []

    for observation in observations:

        value = observation.get(
            "value"
        )

        if value == ".":

            value = None

        date_value = pd.to_datetime(
            observation.get("date"),
            errors="coerce"
        )

        year = (
            date_value.year
            if not pd.isna(date_value)
            else None
        )

        api_rows.append(
            {

                "Year":
                    year,

                "FRED_Date":
                    observation.get(
                        "date"
                    ),

                "FRED_Series_ID":
                    series_id,

                "FRED_Value":
                    value

            }
        )

    api_df = pd.DataFrame(
        api_rows
    )

    api_df = add_api_metadata(
        api_df,
        "FRED"
    )

    api_df.to_csv(
        FRED_API_FILE,
        index=False
    )

    df["Year"] = pd.to_numeric(
        df["Year"],
        errors="coerce"
    )

    api_df["Year"] = pd.to_numeric(
        api_df["Year"],
        errors="coerce"
    )

    fused = df.merge(
        api_df,
        on="Year",
        how="left",
        suffixes=(
            "_CSV",
            "_API"
        )
    )

    fused.to_csv(
        FRED_FUSED_FILE,
        index=False
    )

    print(
        f"✓ API result saved: {FRED_API_FILE}"
    )

    print(
        f"✓ Fused file saved: {FRED_FUSED_FILE}"
    )

    return True


# ============================================================
# 5. MARKETAUX FINANCIAL NEWS
# ============================================================

def call_financial_news():

    print("\n======================================")
    print("5. MARKETAUX FINANCIAL NEWS")
    print("======================================")

    # --------------------------------------------------------
    # CHECK API KEY
    # --------------------------------------------------------

    if not MARKETAUX_API_KEY:

        print(
            "ERROR: MARKETAUX_API_KEY is missing."
        )

        return False

    # --------------------------------------------------------
    # CHECK DATASET
    # --------------------------------------------------------

    if not os.path.exists(NEWS_FILE):

        print(
            "ERROR: financial news dataset not found:"
        )

        print(NEWS_FILE)

        return False

    # --------------------------------------------------------
    # LOAD ORIGINAL DATASET
    # --------------------------------------------------------

    try:

        df = pd.read_csv(
            NEWS_FILE,
            low_memory=False
        )

    except Exception as error:

        print(
            "ERROR loading financial news dataset:",
            error
        )

        return False

    df = clean_columns(df)

    print("Dataset loaded.")

    print(
        "Columns:",
        list(df.columns)
    )

    print(
        f"Original dataset rows: {len(df)}"
    )

    # --------------------------------------------------------
    # VERIFY REQUIRED COLUMNS
    #
    # Your dataset contains:
    #
    # headline
    # url
    # publisher
    # date
    # stock
    # --------------------------------------------------------

    required_columns = [
        "date",
        "stock"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        print(
            "ERROR: Required columns missing:"
        )

        print(
            missing_columns
        )

        return False

    # --------------------------------------------------------
    # DETERMINE STOCK SYMBOL
    # --------------------------------------------------------

    symbol = os.getenv(
        "MARKETAUX_SYMBOL"
    )

    if symbol:

        symbol = symbol.strip().upper()

    else:

        stock_values = (
            df["stock"]
            .dropna()
            .astype(str)
            .str.strip()
        )

        stock_values = stock_values[
            stock_values != ""
        ]

        if len(stock_values) > 0:

            symbol = (
                stock_values
                .iloc[0]
                .upper()
            )

        else:

            symbol = "AAPL"

            print(
                "WARNING: No stock symbol found."
            )

            print(
                "Using default Marketaux symbol: AAPL"
            )

    print(
        f"Calling Marketaux for: {symbol}"
    )

    # --------------------------------------------------------
    # MARKETAUX API
    # --------------------------------------------------------

    url = (
        "https://api.marketaux.com/"
        "v1/news/all"
    )

    params = {

        "api_token":
            MARKETAUX_API_KEY,

        "symbols":
            symbol,

        "filter_entities":
            "true",

        "language":
            "en",

        "limit":
            10
    }

    # --------------------------------------------------------
    # API REQUEST
    # --------------------------------------------------------

    try:

        response = request_json(
            url,
            params
        )

    except Exception as error:

        print(
            "Marketaux API error:",
            error
        )

        return False

    # --------------------------------------------------------
    # CHECK API ERROR
    # --------------------------------------------------------

    if response.get("error"):

        print(
            "Marketaux API error:"
        )

        print(
            response.get(
                "error"
            )
        )

        return False

    # --------------------------------------------------------
    # GET ARTICLES
    # --------------------------------------------------------

    articles = response.get(
        "data",
        []
    )

    if not articles:

        print(
            "No Marketaux articles returned."
        )

        print(response)

        return False

    # --------------------------------------------------------
    # CREATE API ROWS
    # --------------------------------------------------------

    api_rows = []

    for article in articles:

        # ----------------------------------------------
        # Article date
        # ----------------------------------------------

        published_at = article.get(
            "published_at"
        )

        api_date = pd.to_datetime(
            published_at,
            errors="coerce"
        )

        if pd.isna(api_date):

            api_date = None

        else:

            api_date = (
                api_date
                .strftime("%Y-%m-%d")
            )

        # ----------------------------------------------
        # Entity information
        # ----------------------------------------------

        entities = article.get(
            "entities",
            []
        )

        api_ticker = symbol
        api_company = ""
        sentiment = None
        sentiment_score = None

        if entities:

            # Prefer the entity matching
            # the requested symbol.

            selected_entity = None

            for entity in entities:

                entity_symbol = str(
                    entity.get(
                        "symbol",
                        ""
                    )
                ).strip().upper()

                if entity_symbol == symbol:

                    selected_entity = entity

                    break

            # If exact symbol wasn't found,
            # use the first entity.

            if selected_entity is None:

                selected_entity = entities[0]

            api_ticker = (
                selected_entity.get(
                    "symbol"
                )
                or symbol
            )

            api_company = (
                selected_entity.get(
                    "name"
                )
                or ""
            )

            sentiment = (
                selected_entity.get(
                    "sentiment"
                )
            )

            sentiment_score = (
                selected_entity.get(
                    "sentiment_score"
                )
            )

        # ----------------------------------------------
        # Save API row
        # ----------------------------------------------

        api_rows.append(
            {
                "Date": api_date,

                "Ticker": str(
                    api_ticker
                ).strip().upper(),

                "API_Company": api_company,

                "API_Title": article.get(
                    "title"
                ),

                "API_Description": article.get(
                    "description"
                ),

                "API_Source_Name": article.get(
                    "source"
                ),

                "API_URL": article.get(
                    "url"
                ),

                "API_Sentiment": sentiment,

                "API_Sentiment_Score":
                    sentiment_score,

                "API_Type":
                    "Financial News",

                "API_Name":
                    "Marketaux"
            }
        )

    # --------------------------------------------------------
    # CREATE API DATAFRAME
    # --------------------------------------------------------

    api_df = pd.DataFrame(
        api_rows
    )

    if api_df.empty:

        print(
            "Marketaux returned no usable articles."
        )

        return False

    # --------------------------------------------------------
    # SAVE API RESULT
    # --------------------------------------------------------

    api_df.to_csv(
        NEWS_API_FILE,
        index=False
    )

    print(
        f"✓ API result saved: {NEWS_API_FILE}"
    )

    print(
        f"✓ Articles received: {len(api_df)}"
    )

    # ========================================================
    # NORMALIZE ORIGINAL DATASET
    # ========================================================

    original = df.copy()

    # --------------------------------------------------------
    # date -> Date
    # --------------------------------------------------------

    original["Date"] = pd.to_datetime(
        original["date"],
        errors="coerce"
    ).dt.strftime(
        "%Y-%m-%d"
    )

    # --------------------------------------------------------
    # stock -> Ticker
    # --------------------------------------------------------

    original["Ticker"] = (
        original["stock"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Remove invalid ticker values.

    original.loc[
        original["stock"].isna(),
        "Ticker"
    ] = None

    # --------------------------------------------------------
    # NORMALIZE API DATA
    # --------------------------------------------------------

    api_df["Date"] = pd.to_datetime(
        api_df["Date"],
        errors="coerce"
    ).dt.strftime(
        "%Y-%m-%d"
    )

    api_df["Ticker"] = (
        api_df["Ticker"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # --------------------------------------------------------
    # REMOVE DUPLICATE API KEYS
    #
    # Multiple news articles can have the same
    # Date + Ticker.
    #
    # Keeping one row per key prevents the merge
    # from multiplying the 1.8M original rows.
    # --------------------------------------------------------

    api_for_merge = (
        api_df
        .drop_duplicates(
            subset=[
                "Date",
                "Ticker"
            ],
            keep="first"
        )
    )

    # --------------------------------------------------------
    # FUSION KEY
    # --------------------------------------------------------

    print(
        "Fusion key: Date + Ticker"
    )

    # --------------------------------------------------------
    # NORMAL FUSION
    #
    # Original dataset is LEFT side.
    #
    # Therefore ALL original rows are preserved.
    # --------------------------------------------------------

    fused = original.merge(
        api_for_merge,
        on=[
            "Date",
            "Ticker"
        ],
        how="left",
        suffixes=(
            "_CSV",
            "_API"
        )
    )

    # --------------------------------------------------------
    # COUNT MATCHES
    # --------------------------------------------------------

    if "API_Title" in fused.columns:

        matched_rows = (
            fused["API_Title"]
            .notna()
            .sum()
        )

    else:

        matched_rows = 0

    print(
        f"Original dataset rows: {len(original)}"
    )

    print(
        f"Rows matched with API data: "
        f"{matched_rows}"
    )

    # ========================================================
    # IF EXACT MATCHES ARE ZERO
    #
    # This is expected when the uploaded dataset contains
    # historical news dates while Marketaux returns current
    # news.
    #
    # We still create a useful fused CSV.
    # ========================================================

    if matched_rows == 0:

        print(
            "No exact Date + Ticker matches found."
        )

        print(
            "Creating current Marketaux API snapshot "
            "inside the fused dataset."
        )

        # ----------------------------------------------------
        # Add current API information as snapshot columns.
        #
        # This does NOT destroy the original dataset.
        # ----------------------------------------------------

        latest_article = api_df.iloc[0]

        fused["Latest_API_Ticker"] = (
            latest_article["Ticker"]
        )

        fused["Latest_API_Date"] = (
            latest_article["Date"]
        )

        fused["Latest_API_Company"] = (
            latest_article["API_Company"]
        )

        fused["Latest_API_Title"] = (
            latest_article["API_Title"]
        )

        fused["Latest_API_Description"] = (
            latest_article["API_Description"]
        )

        fused["Latest_API_Source"] = (
            latest_article["API_Source_Name"]
        )

        fused["Latest_API_URL"] = (
            latest_article["API_URL"]
        )

        fused["Latest_API_Sentiment"] = (
            latest_article["API_Sentiment"]
        )

        fused["Latest_API_Sentiment_Score"] = (
            latest_article[
                "API_Sentiment_Score"
            ]
        )

        fused["Latest_API_Name"] = (
            "Marketaux"
        )

        fused["Fusion_Status"] = (
            "API snapshot - no exact "
            "historical Date+Ticker match"
        )

    else:

        fused["Fusion_Status"] = (
            "Date+Ticker matched"
        )

    # --------------------------------------------------------
    # SAVE FUSED CSV
    # --------------------------------------------------------

    try:

        fused.to_csv(
            NEWS_FUSED_FILE,
            index=False
        )

    except Exception as error:

        print(
            "ERROR saving fused financial news CSV:",
            error
        )

        return False

    # --------------------------------------------------------
    # FINAL REPORT
    # --------------------------------------------------------

    print(
        f"✓ Fused file saved: "
        f"{NEWS_FUSED_FILE}"
    )

    print(
        f"✓ Original rows: "
        f"{len(original)}"
    )

    print(
        f"✓ API rows: "
        f"{len(api_df)}"
    )

    print(
        f"✓ Fused rows: "
        f"{len(fused)}"
    )

    print(
        f"✓ Matched rows: "
        f"{matched_rows}"
    )

    return True

# ============================================================
# MAIN FUSION PIPELINE
# ============================================================

def run_all_fusions():

    print()
    print("======================================")
    print("FINANCE AI - API FUSION PIPELINE")
    print("======================================")

    results = {}

    # ========================================================
    # 1. ALPHA VANTAGE
    # ========================================================

    try:

        results["alpha_vantage"] = (
            call_alpha_vantage()
        )

    except Exception as error:

        print(
            "Alpha Vantage failed:",
            error
        )

        results["alpha_vantage"] = False

    # ========================================================
    # 2. FRANKFURTER
    # ========================================================

    try:

        results["frankfurter"] = (
            call_frankfurter()
        )

    except Exception as error:

        print(
            "Frankfurter failed:",
            error
        )

        results["frankfurter"] = False

    # ========================================================
    # 3. COINGECKO
    # ========================================================

    try:

        results["coingecko"] = (
            call_coingecko()
        )

    except Exception as error:

        print(
            "CoinGecko failed:",
            error
        )

        results["coingecko"] = False

    # ========================================================
    # 4. FRED
    # ========================================================

    try:

        results["fred"] = (
            call_fred()
        )

    except Exception as error:

        print(
            "FRED failed:",
            error
        )

        results["fred"] = False

    # ========================================================
    # 5. MARKETAUX
    # ========================================================

    try:

        results["financial_news"] = (
            call_financial_news()
        )

    except Exception as error:

        print(
            "Financial News failed:",
            error
        )

        results["financial_news"] = False

    # ========================================================
    # FINAL REPORT
    # ========================================================

    print()
    print("======================================")
    print("FUSION COMPLETE")
    print("======================================")

    successful = 0
    failed = 0

    for api_name, status in results.items():

        if status:

            print(
                f"✓ {api_name}"
            )

            successful += 1

        else:

            print(
                f"✗ {api_name}"
            )

            failed += 1

    print()
    print(
        f"Successful APIs: {successful}/5"
    )

    print(
        f"Failed APIs: {failed}/5"
    )

    print()
    print(
        "API result files:"
    )

    print(
        f"  {API_FOLDER}"
    )

    print()
    print(
        "Fused files:"
    )

    print(
        f"  {FUSION_FOLDER}"
    )

    print()
    print("Expected API result files:")

    print(
        f"  ✓ {ALPHA_API_FILE}"
    )

    print(
        f"  ✓ {FRANKFURTER_API_FILE}"
    )

    print(
        f"  ✓ {COINGECKO_API_FILE}"
    )

    print(
        f"  ✓ {FRED_API_FILE}"
    )

    print(
        f"  ✓ {NEWS_API_FILE}"
    )

    print()
    print("Expected fused files:")

    print(
        f"  ✓ {ALPHA_FUSED_FILE}"
    )

    print(
        f"  ✓ {FRANKFURTER_FUSED_FILE}"
    )

    print(
        f"  ✓ {COINGECKO_FUSED_FILE}"
    )

    print(
        f"  ✓ {FRED_FUSED_FILE}"
    )

    print(
        f"  ✓ {NEWS_FUSED_FILE}"
    )

    return results


# ============================================================
# RUN SCRIPT
# ============================================================

if __name__ == "__main__":

    run_all_fusions()