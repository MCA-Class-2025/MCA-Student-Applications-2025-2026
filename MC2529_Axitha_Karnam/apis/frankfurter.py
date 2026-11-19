import os
import re
import requests
import pandas as pd

from rag import save_api_answer_and_fuse

API_NAME = "frankfurter"
FRANKFURTER_LATEST_URL = "https://api.frankfurter.dev/v1/latest"
FRANKFURTER_HISTORICAL_URL = "https://api.frankfurter.dev/v1"
ECONOMIC_DATASET_CSV = "csv/economic_dataset.csv"

ECONOMIC_COLUMNS = [
    "Country",
    "Year",
    "GDP (in billion USD)",
    "Inflation Rate (%)",
    "Unemployment Rate (%)",
    "Economic Growth (%)"
]

COUNTRY_ALIASES = {
    "usa": "United States", "u.s.a": "United States", "u.s.a.": "United States", "u.s.": "United States", "us": "United States", "united states": "United States", "united states of america": "United States",
    "uk": "United Kingdom", "u.k.": "United Kingdom", "great britain": "United Kingdom", "united kingdom": "United Kingdom",
    "india": "India", "china": "China", "japan": "Japan", "germany": "Germany", "france": "France",
    "italy": "Italy", "spain": "Spain", "canada": "Canada", "australia": "Australia", "brazil": "Brazil",
    "mexico": "Mexico", "russia": "Russia", "south africa": "South Africa", "singapore": "Singapore",
    "switzerland": "Switzerland", "netherlands": "Netherlands", "belgium": "Belgium", "ireland": "Ireland",
    "portugal": "Portugal", "new zealand": "New Zealand", "norway": "Norway", "sweden": "Sweden",
    "denmark": "Denmark", "finland": "Finland", "austria": "Austria", "south korea": "South Korea",
    "korea": "South Korea", "saudi arabia": "Saudi Arabia", "indonesia": "Indonesia", "malaysia": "Malaysia",
    "turkey": "Turkey", "pakistan": "Pakistan", "thailand": "Thailand", "vietnam": "Vietnam"
}

COUNTRY_CURRENCY_MAPPING = {
    "United States": "USD", "India": "INR", "China": "CNY", "Japan": "JPY", "Germany": "EUR",
    "France": "EUR", "Italy": "EUR", "Spain": "EUR", "United Kingdom": "GBP", "Canada": "CAD",
    "Australia": "AUD", "Brazil": "BRL", "South Korea": "KRW", "Saudi Arabia": "SAR", "Indonesia": "IDR",
    "Malaysia": "MYR", "Turkey": "TRY", "Pakistan": "PKR", "Switzerland": "CHF", "Netherlands": "EUR",
    "Belgium": "EUR", "Ireland": "EUR", "Portugal": "EUR", "New Zealand": "NZD", "Norway": "NOK",
    "Sweden": "SEK", "Denmark": "DKK", "Austria": "EUR", "Thailand": "THB", "Vietnam": "VND"
}


# ============================================================
# 1. QUESTION DETECTION
# ============================================================

def is_frankfurter_question(question: str) -> bool:
    question_lower = str(question).lower()
    frankfurter_patterns = [
        r"\bfrankfurter\b", r"\bexchange rate\b", r"\brate\b", r"\bcurrency\b",
        r"\beur\b", r"\busd\b", r"\bgbp\b", r"\bcad\b", r"\baud\b", r"\binr\b",
        r"\bcny\b", r"\bjpy\b", r"\bthb\b", r"\bgdp\b", r"\binflation\b", r"\bunemployment\b",
        r"\beconomic growth\b", r"\beconomic dataset\b", r"\bconvert\b", r"\bconversion\b"
    ]
    return any(re.search(pattern, question_lower) for pattern in frankfurter_patterns)


def can_handle(question: str) -> bool:
    return is_frankfurter_question(question)


# ============================================================
# 2. EXTRACTION HELPERS
# ============================================================

def normalize_country(country_str: str) -> str:
    if not country_str:
        return ""
    cleaned = str(country_str).strip().lower()
    for alias, canonical in COUNTRY_ALIASES.items():
        if alias in cleaned or cleaned in alias:
            return canonical
    return str(country_str).strip().title()


def extract_countries(question: str) -> list:
    question_lower = str(question).lower()
    found = []
    for alias in sorted(COUNTRY_ALIASES.keys(), key=len, reverse=True):
        if re.search(r"\b" + re.escape(alias) + r"\b", question_lower):
            canonical = COUNTRY_ALIASES[alias]
            if canonical not in found:
                found.append(canonical)
    return found


def extract_year(question: str):
    match = re.search(r"\b(19\d{2}|20\d{2})\b", str(question))
    return int(match.group(1)) if match else None


def extract_currencies(question: str):
    question_upper = str(question).upper()
    common_currencies = [
        "USD", "EUR", "GBP", "JPY", "INR", "CNY", "CAD", "AUD",
        "CHF", "BRL", "KRW", "SAR", "IDR", "MYR", "TRY", "PKR", "NZD", "THB", "VND"
    ]
    detected = [c for c in common_currencies if re.search(r"\b" + c + r"\b", question_upper)]
    return detected


# ============================================================
# 3. LIVE & HISTORICAL FRANKFURTER API CALLS
# ============================================================

def fetch_exchange_rates(base: str = "USD", symbols: list = None, date: str = None) -> dict:
    try:
        url = f"{FRANKFURTER_HISTORICAL_URL}/{date}" if date else FRANKFURTER_LATEST_URL
        params = {"base": base.upper()}
        if symbols:
            params["symbols"] = ",".join([s.upper() for s in symbols])

        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        return {
            "success": True,
            "base": data.get("base", base.upper()),
            "date": data.get("date", date or "latest"),
            "rates": data.get("rates", {})
        }
    except Exception as error:
        print("Frankfurter API error:", error)
        return {
            "success": False,
            "message": f"Unable to fetch exchange rates from Frankfurter: {error}",
            "base": base.upper(),
            "rates": {}
        }


# ============================================================
# 4. DATASET LOOKUP
# ============================================================

def load_economic_dataset() -> tuple:
    if not os.path.exists(ECONOMIC_DATASET_CSV):
        return None, f"Economic dataset not found at {ECONOMIC_DATASET_CSV}."

    try:
        df = pd.read_csv(ECONOMIC_DATASET_CSV, low_memory=False, encoding="utf-8-sig")
        df.columns = [str(col).replace("\ufeff", "").replace("\xa0", " ").strip() for col in df.columns]
        df["_norm_country"] = df["Country"].apply(lambda c: str(c).strip().lower())
        df["_year_num"] = pd.to_numeric(df["Year"], errors="coerce")
        return df, None
    except Exception as error:
        return None, f"Unable to read economic_dataset.csv: {error}"


def _to_float(val):
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
        cleaned = str(val).replace(",", "").replace("$", "").replace("%", "").strip()
        if cleaned == "" or cleaned.lower() == "null":
            return None
        return float(cleaned)
    except Exception:
        return None


def _format_val(val, suffix: str = ""):
    num = _to_float(val)
    if num is None:
        return "N/A"
    if num.is_integer():
        return f"{int(num):,}{suffix}"
    return f"{num:,.2f}{suffix}"


# ============================================================
# 5. ANSWER BUILDERS (FALLBACK TO FRANKFURTER API IF NOT IN DATASET)
# ============================================================

def handle_frankfurter_question(question: str, df: pd.DataFrame):
    q = str(question).lower()
    countries = extract_countries(question)
    year = extract_year(question)
    currencies = extract_currencies(question)

    # CASE 1: Pure Currency / Exchange Rate Question
    if not countries and currencies:
        base_curr = "USD"
        if "eur to" in q or "euro to" in q:
            base_curr = "EUR"
        elif "gbp to" in q:
            base_curr = "GBP"

        symbols = [c for c in currencies if c != base_curr]
        if not symbols:
            symbols = ["EUR", "USD", "INR", "GBP", "CAD", "AUD", "THB"]

        date_str = f"{year}-12-31" if year and year <= 2024 else None
        rate_res = fetch_exchange_rates(base=base_curr, symbols=symbols, date=date_str)
        rates = rate_res.get("rates", {})

        lines = [f"### Frankfurter Exchange Rates (Base: {base_curr})" + (f" for {year}" if year else " (Latest)")]
        for cur, val in rates.items():
            lines.append(f"- **{base_curr} to {cur}:** {val}")

        return "\n".join(lines), pd.DataFrame(columns=ECONOMIC_COLUMNS)

    # CASE 2: Country & Year Questions
    if not countries:
        return "Please specify a valid country or currency for economic and exchange rate analysis.", pd.DataFrame(columns=ECONOMIC_COLUMNS)

    matched_frames = []
    blocks = []

    date_str = f"{year}-12-31" if year and year <= 2024 else None
    all_target_currencies = list(COUNTRY_CURRENCY_MAPPING.values())
    rates_bundle = fetch_exchange_rates(base="USD", symbols=all_target_currencies, date=date_str)
    rates = rates_bundle.get("rates", {})

    for country in countries:
        canonical_country = normalize_country(country)
        sub = df[df["_norm_country"] == canonical_country.lower()].copy()

        if year:
            sub_year = sub[sub["_year_num"] == year]
            if not sub_year.empty:
                sub = sub_year
            else:
                sub = pd.DataFrame() # Force API fallback if year not in CSV

        # IF NOT IN DATASET (OR YEAR NOT FOUND), FALLBACK TO FRANKFURTER API FOR CURRENCY RATE!
        if sub.empty:
            local_curr = COUNTRY_CURRENCY_MAPPING.get(canonical_country, "USD")
            currency_rate = rates.get(local_curr, "Unavailable")

            lines = [
                f"### {canonical_country}" + (f" ({year})" if year else ""),
                f"- **Economic Dataset (`economic_dataset.csv`):** Record not found for {canonical_country}.",
                f"- **Frankfurter API Currency:** {local_curr}",
                f"- **Exchange Rate (USD to {local_curr}):** {currency_rate}",
                f"- **Note:** Economic indicators (GDP, inflation) are not available in the dataset for {canonical_country}, but live/historical exchange rates are provided via Frankfurter API."
            ]
            blocks.append("\n".join(lines))
            continue

        for _, row in sub.iterrows():
            c_name = row["Country"]
            c_year = row["Year"]
            gdp_usd = row["GDP (in billion USD)"]
            inflation = row["Inflation Rate (%)"]
            unemployment = row["Unemployment Rate (%)"]
            growth = row["Economic Growth (%)"]

            local_curr = COUNTRY_CURRENCY_MAPPING.get(c_name, "USD")
            rate = rates.get(local_curr) or rates.get("EUR")

            lines = [
                f"### {c_name} ({c_year})",
                f"- **GDP (Dataset):** ${_format_val(gdp_usd)} billion USD",
                f"- **Inflation Rate:** {_format_val(inflation, '%')}",
                f"- **Unemployment Rate:** {_format_val(unemployment, '%')}",
                f"- **Economic Growth:** {_format_val(growth, '%')}"
            ]

            if rate:
                lines.append(f"- **Frankfurter Exchange Rate (USD to {local_curr}):** {rate}")
                if _to_float(gdp_usd):
                    converted = _to_float(gdp_usd) * rate
                    lines.append(f"- **Converted GDP ({local_curr}):** {_format_val(converted)} billion {local_curr}")

            blocks.append("\n".join(lines))
            match_row = df[(df["Country"] == c_name) & (df["Year"] == c_year)].drop(columns=["_norm_country", "_year_num"], errors="ignore")
            matched_frames.append(match_row)

    combined_df = pd.concat(matched_frames, ignore_index=True) if matched_frames else pd.DataFrame(columns=ECONOMIC_COLUMNS)
    return "\n\n".join(blocks), combined_df


# ============================================================
# 6. MAIN ROUTE HANDLER
# ============================================================

def handle(question: str):
    df, err = load_economic_dataset()
    if err:
        return err, []

    answer, matched_df = handle_frankfurter_question(question, df)

    save_api_answer_and_fuse(
        api_name=API_NAME,
        question=question,
        api_result={"Question": question},
        answer=answer,
        key_mapping={"original": ["Country", "Year"], "api": ["Country", "Year"]},
        original_csv=ECONOMIC_DATASET_CSV,
        selected_original_df=matched_df
    )

    return answer, []