import os
import re
import io
import requests
import pandas as pd

from rag import save_api_answer_and_fuse

API_NAME = "fred"
FRED_OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"
FRED_PUBLIC_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
FRED_DATASET_CSV = "csv/fred_dataset.csv"

COUNTRY_ALIASES = {
    "usa": "United States",
    "u.s.a": "United States",
    "u.s.a.": "United States",
    "u.s.": "United States",
    "us": "United States",
    "united states": "United States",
    "united states of america": "United States",
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "great britain": "United Kingdom",
    "united kingdom": "United Kingdom",
    "india": "India",
    "china": "China",
    "japan": "Japan",
    "germany": "Germany",
    "france": "France",
    "canada": "Canada",
    "australia": "Australia",
    "brazil": "Brazil",
    "south korea": "South Korea",
    "korea": "South Korea",
    "saudi arabia": "Saudi Arabia",
    "italy": "Italy",
    "spain": "Spain",
    "mexico": "Mexico",
    "russia": "Russia",
    "south africa": "South Africa",
    "indonesia": "Indonesia",
    "malaysia": "Malaysia",
    "turkey": "Turkey",
    "pakistan": "Pakistan",
    "thailand": "Thailand",
    "vietnam": "Vietnam",
    "argentina": "Argentina",
    "egypt": "Egypt",
    "nigeria": "Nigeria",
    "bangladesh": "Bangladesh",
    "singapore": "Singapore",
    "switzerland": "Switzerland",
    "sweden": "Sweden",
    "norway": "Norway",
    "netherlands": "Netherlands",
    "new zealand": "New Zealand"
}

# Equivalent spellings in CSV datasets
CSV_COUNTRY_VARIANTS = {
    "United States": ["united states", "usa", "us", "u.s.a.", "u.s."],
    "United Kingdom": ["united kingdom", "uk", "u.k.", "great britain"],
    "South Korea": ["south korea", "korea", "republic of korea"],
    "Russia": ["russia", "russian federation"],
    "Turkey": ["turkey", "turkiye"]
}

# High-precision World Bank / IMF / US FRED Series IDs (Annual / Standard)
FRED_SERIES_MAPPING = {
    ("United States", "gdp"): "MKTGDPUSA646NWDB",
    ("United States", "inflation"): "FPCPITOTLZGUSA",
    ("United States", "unemployment"): "SLUEM1524ZSUSA",
    ("United States", "growth"): "NYGDPPCAPKDUSA",

    ("India", "gdp"): "MKTGDPINA646NWDB",
    ("India", "inflation"): "FPCPITOTLZGIND",
    ("India", "unemployment"): "SLUEM1524ZSIND",
    ("India", "growth"): "NYGDPPCAPKDIND",

    ("China", "gdp"): "MKTGDPCNA646NWDB",
    ("China", "inflation"): "FPCPITOTLZGCHN",
    ("China", "unemployment"): "SLUEM1524ZSCHN",
    ("China", "growth"): "NYGDPPCAPKDCHN",

    ("Japan", "gdp"): "MKTGDPJPA646NWDB",
    ("Japan", "inflation"): "FPCPITOTLZGJPN",
    ("Japan", "unemployment"): "SLUEM1524ZSJPN",
    ("Japan", "growth"): "NYGDPPCAPKDJPN",

    ("Germany", "gdp"): "MKTGDPDEA646NWDB",
    ("Germany", "inflation"): "FPCPITOTLZGDEU",
    ("Germany", "unemployment"): "SLUEM1524ZSDEU",
    ("Germany", "growth"): "NYGDPPCAPKDDEU",

    ("United Kingdom", "gdp"): "MKTGDPGBA646NWDB",
    ("United Kingdom", "inflation"): "FPCPITOTLZGGBA",
    ("United Kingdom", "unemployment"): "SLUEM1524ZSGBA",
    ("United Kingdom", "growth"): "NYGDPPCAPKDGBA",

    ("Canada", "gdp"): "MKTGDPCAA646NWDB",
    ("Canada", "inflation"): "FPCPITOTLZGCAN",
    ("Canada", "unemployment"): "SLUEM1524ZSCAN",
    ("Canada", "growth"): "NYGDPPCAPKDCAN",

    ("Australia", "gdp"): "MKTGDPAYA646NWDB",
    ("Australia", "inflation"): "FPCPITOTLZGAUS",
    ("Australia", "unemployment"): "SLUEM1524ZSAUS",
    ("Australia", "growth"): "NYGDPPCAPKDAUS",

    ("France", "gdp"): "MKTGDPFRA646NWDB",
    ("France", "inflation"): "FPCPITOTLZGFRA",
    ("France", "unemployment"): "SLUEM1524ZSFRA",
    ("France", "growth"): "NYGDPPCAPKDFRA",

    ("Brazil", "gdp"): "MKTGDPBRA646NWDB",
    ("Brazil", "inflation"): "FPCPITOTLZGBRA",
    ("Brazil", "unemployment"): "SLUEM1524ZSBRA",
    ("Brazil", "growth"): "NYGDPPCAPKDBRA",

    ("South Korea", "gdp"): "MKTGDPKRA646NWDB",
    ("South Korea", "inflation"): "FPCPITOTLZGKOR",
    ("South Korea", "unemployment"): "SLUEM1524ZSKOR",
    ("South Korea", "growth"): "NYGDPPCAPKDKOR",

    ("Saudi Arabia", "gdp"): "MKTGDPSAA646NWDB",
    ("Saudi Arabia", "inflation"): "FPCPITOTLZGSAU",
    ("Saudi Arabia", "unemployment"): "SLUEM1524ZSSAU",
    ("Saudi Arabia", "growth"): "NYGDPPCAPKDSAU"
}

COUNTRY_ISO3_MAP = {
    "United States": "USA", "United Kingdom": "GBR", "India": "IND", "China": "CHN",
    "Japan": "JPN", "Germany": "DEU", "France": "FRA", "Canada": "CAN",
    "Australia": "AUS", "Brazil": "BRA", "South Korea": "KOR", "Saudi Arabia": "SAU",
    "Italy": "ITA", "Spain": "ESP", "Mexico": "MEX", "Russia": "RUS",
    "South Africa": "ZAF", "Indonesia": "IDN", "Malaysia": "MYS", "Turkey": "TUR",
    "Pakistan": "PAK", "Thailand": "THA", "Vietnam": "VNM", "Argentina": "ARG",
    "Egypt": "EGY", "Nigeria": "NGA", "Bangladesh": "BGD", "Singapore": "SGP",
    "Switzerland": "CHE", "Sweden": "SWE", "Norway": "NOR", "Netherlands": "NLD",
    "New Zealand": "NZL"
}

COUNTRY_ISO2_MAP = {
    "United States": "US", "United Kingdom": "GB", "India": "IN", "China": "CN",
    "Japan": "JP", "Germany": "DE", "France": "FR", "Canada": "CA",
    "Australia": "AU", "Brazil": "BR", "South Korea": "KR", "Saudi Arabia": "SA",
    "Italy": "IT", "Spain": "ES", "Mexico": "MX", "Russia": "RU",
    "South Africa": "ZA", "Indonesia": "ID", "Malaysia": "MY", "Turkey": "TR",
    "Pakistan": "PK", "Thailand": "TH", "Vietnam": "VN", "Argentina": "AR",
    "Egypt": "EG", "Nigeria": "NG", "Bangladesh": "BD", "Singapore": "SG",
    "Switzerland": "CH", "Sweden": "SE", "Norway": "NO", "Netherlands": "NL",
    "New Zealand": "NZ"
}


# ============================================================
# 1. QUESTION DETECTION
# ============================================================

def is_fred_question(question: str) -> bool:
    question_lower = str(question).lower()
    fred_patterns = [
        r"\bfred\b",
        r"\bfederal reserve\b",
        r"\bfed funds\b",
        r"\bfedfunds\b",
        r"\bcpiaucsl\b",
        r"\bunrate\b",
        r"\bdgs10\b"
    ]
    if any(re.search(pattern, question_lower) for pattern in fred_patterns):
        return True

    # Also route general macro queries without Frankfurter/currency conversion keywords
    has_macro = any(
        re.search(p, question_lower)
        for p in [r"\bgdp\b", r"\binflation\b", r"\bunemployment\b", r"\beconomic growth\b", r"\beconomic indicator"]
    )
    has_fx = any(
        re.search(p, question_lower)
        for p in [r"\bfrankfurter\b", r"\bexchange rate\b", r"\bcurrency\b", r"\bconvert\b", r"\beur\b", r"\binr\b", r"\bgbp\b"]
    )
    return has_macro and not has_fx


def can_handle(question: str) -> bool:
    return is_fred_question(question)


# ============================================================
# 2. EXTRACTION HELPERS
# ============================================================

def normalize_country(country_str: str) -> str:
    if not country_str:
        return ""
    cleaned = str(country_str).strip().lower()
    return COUNTRY_ALIASES.get(cleaned, str(country_str).strip().title())


def extract_countries(question: str) -> list:
    question_lower = str(question).lower()
    found = []

    for alias in sorted(COUNTRY_ALIASES.keys(), key=len, reverse=True):
        if re.search(r"\b" + re.escape(alias) + r"\b", question_lower):
            canonical = COUNTRY_ALIASES[alias]
            if canonical not in found:
                found.append(canonical)

    if not found:
        words = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b", question)
        stopwords = {
            "what", "was", "were", "the", "for", "in", "of", "and", "with", "from",
            "gdp", "dataset", "fred", "api", "compare", "show", "me", "all",
            "inflation", "unemployment", "economic", "growth", "rate", "csv", "my",
            "data", "value", "values", "indicator", "indicators", "difference", "between"
        }
        for w in words:
            if w.lower() not in stopwords:
                canonical = normalize_country(w)
                if canonical not in found:
                    found.append(canonical)

    return found


def extract_year(question: str):
    match = re.search(r"\b(19\d{2}|20\d{2})\b", str(question))
    return int(match.group(1)) if match else None


def detect_indicators(question: str) -> list:
    q = str(question).lower()
    if any(k in q for k in ("economic indicator", "economic indicators", "all indicator", "all economic")):
        return ["gdp", "inflation", "unemployment", "growth"]

    indicators = []
    if "gdp" in q:
        indicators.append("gdp")
    if "inflation" in q or "cpi" in q:
        indicators.append("inflation")
    if "unemployment" in q:
        indicators.append("unemployment")
    if "growth" in q:
        indicators.append("growth")

    if not indicators:
        indicators = ["gdp", "inflation", "unemployment", "growth"]
    return indicators


# ============================================================
# 3. LIVE FRED API + PUBLIC GRAPH CSV FALLBACK
# ============================================================

def get_fred_series_id(country: str, indicator: str) -> str:
    specific = FRED_SERIES_MAPPING.get((country, indicator))
    if specific:
        return specific

    iso3 = COUNTRY_ISO3_MAP.get(country, country[:3].upper())
    iso2 = COUNTRY_ISO2_MAP.get(country, country[:2].upper())

    if indicator == "gdp":
        return f"MKTGDP{iso2}A646NWDB"
    if indicator == "inflation":
        return f"FPCPITOTLZG{iso3}"
    if indicator == "unemployment":
        return f"SLUEM1524ZS{iso3}"
    if indicator == "growth":
        return f"NYGDPPCAPKD{iso3}"
    return f"MKTGDP{iso2}A646NWDB"


def fetch_fred_observation_for_year(series_id: str, year: int, indicator: str = "gdp"):
    """
    Fetches observation for a specific series ID and year from FRED.
    1. Tries official FRED API if FRED_API_KEY is available.
    2. Falls back automatically to FRED's public fredgraph.csv endpoint (no API key needed).
    """
    api_key = os.getenv("FRED_API_KEY")
    raw_val = None

    # Method 1: Official FRED JSON API (if key exists)
    if api_key and api_key != "abcdef1234567890":
        try:
            params = {
                "series_id": series_id,
                "api_key": api_key,
                "file_type": "json",
                "observation_start": f"{year}-01-01",
                "observation_end": f"{year}-12-31"
            }
            resp = requests.get(FRED_OBSERVATIONS_URL, params=params, timeout=15)
            resp.raise_for_status()
            observations = resp.json().get("observations", [])
            valid_vals = [float(o["value"]) for o in observations if o.get("value") not in (".", None, "")]
            if valid_vals:
                raw_val = valid_vals[-1]
        except Exception as err:
            print(f"FRED JSON API warning ({series_id}):", err)

    # Method 2: Public FRED Graph CSV endpoint (works with zero API key!)
    if raw_val is None:
        try:
            csv_resp = requests.get(FRED_PUBLIC_CSV_URL, params={"id": series_id}, timeout=15)
            csv_resp.raise_for_status()
            text = csv_resp.text
            if text and "<html" not in text.lower():
                series_df = pd.read_csv(io.StringIO(text))
                if len(series_df.columns) >= 2:
                    date_col, val_col = series_df.columns[0], series_df.columns[1]
                    series_df["_yr"] = pd.to_datetime(series_df[date_col], errors="coerce").dt.year
                    yr_rows = series_df[series_df["_yr"] == int(year)]
                    valid_vals = pd.to_numeric(yr_rows[val_col], errors="coerce").dropna().tolist()
                    if valid_vals:
                        raw_val = float(valid_vals[-1])
        except Exception as csv_err:
            print(f"FRED public CSV fallback warning ({series_id}):", csv_err)

    if raw_val is None:
        return None

    # World Bank GDP on FRED (MKTGDP...NWDB) is reported in exact USD; convert to Billions USD to match dataset
    if indicator == "gdp" and series_id.startswith("MKTGDP") and abs(raw_val) > 1e7:
        raw_val = raw_val / 1e9

    return raw_val


# ============================================================
# 4. DATASET LOOKUP (csv/fred_dataset.csv)
# ============================================================

def load_fred_dataset() -> tuple:
    if not os.path.exists(FRED_DATASET_CSV):
        return None, None, f"FRED dataset not found at {FRED_DATASET_CSV}."

    try:
        df = pd.read_csv(FRED_DATASET_CSV, low_memory=False, encoding="utf-8-sig")
        df.columns = [
            str(col).replace("\ufeff", "").replace("\xa0", " ").strip()
            for col in df.columns
        ]
        original_cols = list(df.columns)

        df["_norm_country"] = df["Country"].astype(str).str.strip().str.lower()
        df["_year_num"] = pd.to_numeric(df["Year"], errors="coerce")
        return df, original_cols, None
    except Exception as error:
        return None, None, f"Unable to read fred_dataset.csv: {error}"


def _to_float(val):
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
        cleaned = str(val).replace(",", "").replace("$", "").replace("%", "").strip()
        if cleaned == "" or cleaned.lower() in ("null", "nan", "n/a", "."):
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


def _find_matching_csv_rows(df: pd.DataFrame, canonical_country: str, year: int) -> pd.DataFrame:
    """Matches country in CSV even if stored as 'USA' vs 'United States' or 'UK' vs 'United Kingdom'."""
    variants = CSV_COUNTRY_VARIANTS.get(canonical_country, [canonical_country.lower()])
    variants_lower = [v.lower() for v in variants]

    sub = df[
        (df["_norm_country"].isin(variants_lower)) &
        (df["_year_num"] == int(year))
    ].copy()
    return sub


# ============================================================
# 5. ANSWER BUILDERS (FULL ORIGINAL ROW + CONDITIONAL FUSION)
# ============================================================

def handle_fred_question(question: str, df: pd.DataFrame, original_cols: list):
    countries = extract_countries(question)
    year = extract_year(question)
    indicators = detect_indicators(question)

    if not countries:
        countries = ["United States"]
    if not year:
        year = 2010

    matched_frames = []
    blocks = []

    for country in countries:
        canonical_country = normalize_country(country)
        sub = _find_matching_csv_rows(df, canonical_country, year)

        # ONLY append to matched_frames if a genuine record exists in fred_dataset.csv!
        if not sub.empty:
            clean_row_df = sub[original_cols].iloc[[0]].copy()
            matched_frames.append(clean_row_df)
            rec = clean_row_df.iloc[0].to_dict()
            dataset_display_name = rec.get("Country", canonical_country)
        else:
            rec = {}
            dataset_display_name = canonical_country

        lines = [f"### {dataset_display_name} ({year})"]

        csv_col_map = {
            "gdp": "GDP (in billion USD)",
            "inflation": "Inflation Rate (%)",
            "unemployment": "Unemployment Rate (%)",
            "growth": "Economic Growth (%)"
        }

        for ind in indicators:
            series_id = get_fred_series_id(canonical_country, ind)
            fred_val = fetch_fred_observation_for_year(series_id, year, indicator=ind)

            col_name = csv_col_map.get(ind)
            csv_val = rec.get(col_name) if rec else None

            suffix = "%" if ind in ("inflation", "unemployment", "growth") else " billion USD"

            if not sub.empty:
                lines.append(
                    f"- **{ind.upper()} — Dataset (`fred_dataset.csv`):** {_format_val(csv_val, suffix)}"
                )
            else:
                lines.append(
                    f"- **{ind.upper()} — Dataset (`fred_dataset.csv`):** Not present in dataset"
                )

            lines.append(
                f"- **{ind.upper()} — FRED API (`{series_id}`):** {_format_val(fred_val, suffix)}"
            )

            ds_num = _to_float(csv_val)
            fred_num = _to_float(fred_val)
            if ds_num is not None and fred_num is not None:
                diff = abs(fred_num - ds_num)
                lines.append(
                    f"- **Difference (FRED vs Dataset):** {_format_val(diff, suffix)}"
                )

        blocks.append("\n".join(lines))

    combined_df = (
        pd.concat(matched_frames, ignore_index=True)
        if matched_frames
        else pd.DataFrame(columns=original_cols)
    )
    return "\n\n".join(blocks), combined_df


# ============================================================
# 6. MAIN ROUTE HANDLER (CALLED BY rag.py)
# ============================================================

def handle(question: str):
    df, original_cols, err = load_fred_dataset()
    if err:
        return err, []

    answer, matched_df = handle_fred_question(question, df, original_cols)

    # Fuse ONLY when genuine records exist in fred_dataset.csv
    if not matched_df.empty:
        save_api_answer_and_fuse(
            api_name=API_NAME,
            question=question,
            api_result={"Question": question},
            answer=answer,
            key_mapping={"original": ["Country", "Year"], "api": ["Country", "Year"]},
            original_csv=FRED_DATASET_CSV,
            selected_original_df=matched_df
        )

    return answer, []


handle_question = handle