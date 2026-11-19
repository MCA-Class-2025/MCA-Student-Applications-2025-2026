import os
import re
import requests
import pandas as pd

from rag import save_api_answer_and_fuse

API_NAME = "alpha_vantage"
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
STOCK_DATASET_CSV = "csv/stock_dataset.csv"

COMPANY_TO_TICKER = {
    "apple": "AAPL",
    "microsoft": "MSFT",
    "tesla": "TSLA",
    "amazon": "AMZN",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "meta": "META",
    "facebook": "META",
    "nvidia": "NVDA",
    "netflix": "NFLX",
    "intel": "INTC",
    "amd": "AMD",
    "ibm": "IBM",
    "oracle": "ORCL",
    "salesforce": "CRM",
    "adobe": "ADBE",
    "walmart": "WMT",
    "jpmorgan": "JPM",
    "bank of america": "BAC",
    "goldman sachs": "GS",
    "boeing": "BA",
    "ford": "F",
    "general motors": "GM"
}


# ============================================================
# 1. QUESTION DETECTION
# ============================================================

def is_alpha_vantage_question(question: str) -> bool:
    q = str(question).lower()
    av_patterns = [
        r"\balpha\s*vantage\b",
        r"\bsma_10\b", r"\bema_10\b", r"\bsma\b", r"\bema\b",
        r"\bvolatility\b",
        r"\beconomic_score\b", r"\beconomic score\b",
        r"\bmarket_sentiment\b", r"\bmarket sentiment\b",
        r"\bnews_tag\b", r"\bnews tag\b",
        r"\bwavelet_noise\b", r"\bwavelet_highfreq\b", r"\bwavelet\b",
        r"\bclose_next\b", r"\bclose next\b",
        r"\btrading volume\b", r"\bvolume\b",
        r"\bopen\b.*\bclose\b", r"\bclose\b.*\bopen\b",
        r"\bopen,\s*high,\s*low\b", r"\bohlc\b",
        r"\bhighest close\b", r"\blowest close\b", r"\baverage close\b",
        r"\btagged as earnings\b", r"\btagged as merger\b",
        r"\bwhich categories are available\b",
        r"\bhow many records are available for each category\b",
        r"\bearliest and latest date\b",
        r"\bstock price\b", r"\bshare price\b", r"\bstock quote\b",
        r"\b(aapl|msft|tsla|amzn|googl|nvda|meta|nflx|ibm)\b"
    ]
    return any(re.search(pattern, q) for pattern in av_patterns)


def can_handle(question: str) -> bool:
    return is_alpha_vantage_question(question)


# ============================================================
# 2. EXTRACTION & DATASET LOADING HELPERS
# ============================================================

def _norm_col(col):
    return re.sub(r"\s+", " ", str(col).replace("\ufeff", "").replace("\xa0", " ")).strip()


def load_stock_dataset() -> tuple:
    if not os.path.exists(STOCK_DATASET_CSV):
        return None, f"Stock dataset not found at {STOCK_DATASET_CSV}."

    try:
        df = pd.read_csv(STOCK_DATASET_CSV, low_memory=False, encoding="utf-8-sig")
        df.columns = [_norm_col(c) for c in df.columns]
        return df, None
    except Exception as error:
        return None, f"Unable to read stock_dataset.csv: {error}"


def _col(df: pd.DataFrame, *candidates):
    lookup = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lookup:
            return lookup[cand.lower()]
    return None


def _num_series(df: pd.DataFrame, col_name: str) -> pd.Series:
    if not col_name or col_name not in df.columns:
        return pd.Series(dtype="float64")
    cleaned = (
        df[col_name]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.strip()
    )
    return pd.to_numeric(cleaned, errors="coerce")


def _fmt(val, decimals: int = 2) -> str:
    if val is None or pd.isna(val):
        return "N/A"
    try:
        num = float(val)
        if num.is_integer():
            return f"{int(num):,}"
        return f"{num:,.{decimals}f}"
    except Exception:
        return str(val)


def extract_ticker(question: str):
    q_str = str(question)
    q_lower = q_str.lower()

    for comp, sym in sorted(COMPANY_TO_TICKER.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(r"\b" + re.escape(comp) + r"\b", q_lower):
            return sym

    stop = {
        "A", "I", "IN", "ON", "AT", "TO", "BY", "OF", "OR", "AND", "THE", "FOR",
        "ARE", "ANY", "WHAT", "SHOW", "GIVE", "FIND", "HOW", "WHICH", "OPEN",
        "HIGH", "LOW", "CLOSE", "SMA", "EMA", "API", "CSV", "USD", "EUR", "GDP",
        "DATE", "NEWS", "TAG"
    }
    for match in re.finditer(r"\b([A-Z]{2,5})\b", q_str):
        sym = match.group(1)
        if sym not in stop:
            return sym
    return None


def extract_category(question: str, df: pd.DataFrame):
    cat_col = _col(df, "Category", "Sector")
    if not cat_col:
        return None
    q_lower = str(question).lower()
    categories = [str(c).strip() for c in df[cat_col].dropna().unique() if str(c).strip()]
    for cat in sorted(categories, key=len, reverse=True):
        if re.search(r"\b" + re.escape(cat.lower()) + r"\b", q_lower):
            return cat
    return None


def extract_date_str(question: str):
    # ISO YYYY-MM-DD
    iso = re.search(r"\b(19\d{2}|20\d{2})-(\d{2})-(\d{2})\b", str(question))
    if iso:
        return iso.group(0)
    # Slash MM/DD/YYYY or YYYY/MM/DD
    slash = re.search(r"\b(\d{4}/\d{2}/\d{2}|\d{1,2}/\d{1,2}/\d{4})\b", str(question))
    if slash:
        return slash.group(0)
    return None


# ============================================================
# 3. LIVE ALPHA VANTAGE API CALL
# ============================================================

def fetch_alpha_vantage_quote(symbol: str) -> dict:
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
    try:
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol.upper(),
            "apikey": api_key
        }
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=20)
        response.raise_for_status()
        payload = response.json()
        quote = payload.get("Global Quote", {})
        if not quote:
            return {
                "success": False,
                "message": payload.get("Note") or payload.get("Information") or f"No live quote returned for {symbol}.",
                "quote": {}
            }
        return {
            "success": True,
            "symbol": quote.get("01. symbol", symbol.upper()),
            "open": quote.get("02. open"),
            "high": quote.get("03. high"),
            "low": quote.get("04. low"),
            "price": quote.get("05. price"),
            "volume": quote.get("06. volume"),
            "latest_trading_day": quote.get("07. latest trading day"),
            "change_percent": quote.get("10. change percent")
        }
    except Exception as error:
        print("Alpha Vantage API error:", error)
        return {"success": False, "message": str(error), "quote": {}}


# ============================================================
# 4. DATASET ANALYTICS BUILDER (ALL 30 QUESTIONS + GENERAL)
# ============================================================

def _format_records_list(sub_df: pd.DataFrame, cols_to_show: list, limit: int = 10) -> list:
    lines = []
    valid_cols = [c for c in cols_to_show if c and c in sub_df.columns]
    for idx, (_, row) in enumerate(sub_df.head(limit).iterrows(), start=1):
        parts = [f"**{c}:** {_fmt(row[c]) if isinstance(row[c], (int, float)) else row[c]}" for c in valid_cols]
        lines.append(f"{idx}. " + " | ".join(parts))
    return lines


def answer_stock_dataset_question(question: str, df: pd.DataFrame) -> tuple:
    q = str(question).lower()

    date_col = _col(df, "Date", "Timestamp")
    cat_col = _col(df, "Category", "Sector")
    open_col = _col(df, "Open")
    high_col = _col(df, "High")
    low_col = _col(df, "Low")
    close_col = _col(df, "Close")
    vol_col = _col(df, "Volume")
    volat_col = _col(df, "Volatility")
    sma_col = _col(df, "SMA_10", "SMA")
    ema_col = _col(df, "EMA_10", "EMA")
    econ_col = _col(df, "Economic_Score", "Economic Score")
    sent_col = _col(df, "Market_Sentiment", "Market Sentiment", "Sentiment")
    tag_col = _col(df, "News_Tag", "News Tag")
    wnoise_col = _col(df, "Wavelet_Noise", "Wavelet Noise")
    whigh_col = _col(df, "Wavelet_HighFreq", "Wavelet HighFreq")
    cnext_col = _col(df, "Close_Next", "Close Next")

    selected_cat = extract_category(question, df)
    selected_date = extract_date_str(question)

    # ------------------------------------------------------------
    # Q1: Which categories are available in the dataset?
    # ------------------------------------------------------------
    if "which categories" in q or "categories are available" in q:
        cats = sorted(df[cat_col].dropna().astype(str).unique().tolist())
        sample_rows = df.drop_duplicates(subset=[cat_col]).copy()
        lines = [
            "### Available Categories in Stock Dataset",
            f"- **Total Categories:** {len(cats)}",
            f"- **Categories:** {', '.join(cats)}"
        ]
        return "\n".join(lines), sample_rows, {"categories": cats, "count": len(cats)}

    # ------------------------------------------------------------
    # Q2: How many records are available for each category?
    # ------------------------------------------------------------
    if "how many records" in q and "category" in q:
        counts = df[cat_col].astype(str).value_counts()
        sample_rows = df.drop_duplicates(subset=[cat_col]).copy()
        lines = ["### Record Count per Category", f"- **Total Dataset Records:** {len(df):,}"]
        for cat, cnt in counts.items():
            lines.append(f"- **{cat}:** {int(cnt):,} records")
        return "\n".join(lines), sample_rows, {"category_counts": counts.to_dict()}

    # ------------------------------------------------------------
    # Q3: Earliest and latest date covered by the dataset
    # ------------------------------------------------------------
    if "earliest" in q and "latest" in q and "date" in q:
        parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
        min_idx = parsed_dates.idxmin()
        max_idx = parsed_dates.idxmax()
        min_dt = str(df.loc[min_idx, date_col])
        max_dt = str(df.loc[max_idx, date_col])
        fused = df.loc[[min_idx, max_idx]].drop_duplicates().copy()
        lines = [
            "### Date Coverage of Stock Dataset",
            f"- **Earliest Date:** `{min_dt}`",
            f"- **Latest Date:** `{max_dt}`",
            f"- **Total Records:** {len(df):,}"
        ]
        return "\n".join(lines), fused, {"earliest_date": min_dt, "latest_date": max_dt}

    # ------------------------------------------------------------
    # Q4: Open, High, Low and Close values for category on a date
    # ------------------------------------------------------------
    if all(w in q for w in ("open", "high", "low", "close")):
        sub = df.copy()
        if selected_cat:
            sub = sub[sub[cat_col].astype(str).str.lower() == selected_cat.lower()]
        if selected_date:
            sub_dt = sub[sub[date_col].astype(str).str.contains(selected_date, na=False)]
            if not sub_dt.empty:
                sub = sub_dt
        if sub.empty:
            sub = df.head(1)
        row = sub.iloc[[0]].copy()
        r = row.iloc[0]
        lines = [
            f"### OHLC Values — {r.get(cat_col, 'N/A')} (`{r.get(date_col, 'N/A')}`)",
            f"- **Open:** {_fmt(r.get(open_col))}",
            f"- **High:** {_fmt(r.get(high_col))}",
            f"- **Low:** {_fmt(r.get(low_col))}",
            f"- **Close:** {_fmt(r.get(close_col))}"
        ]
        return "\n".join(lines), row, {"Category": r.get(cat_col), "Date": str(r.get(date_col)), "Close": r.get(close_col)}

    # ------------------------------------------------------------
    # Q5 & Q6: Highest / Lowest Close value
    # ------------------------------------------------------------
    if ("highest close" in q or "lowest close" in q) and "average" not in q:
        c_num = _num_series(df, close_col)
        is_high = "highest close" in q
        idx = c_num.idxmax() if is_high else c_num.idxmin()
        row = df.loc[[idx]].copy()
        r = row.iloc[0]
        label = "Highest" if is_high else "Lowest"
        lines = [
            f"### {label} Close Value in Dataset",
            f"- **Category:** {r.get(cat_col, 'N/A')}",
            f"- **Date:** `{r.get(date_col, 'N/A')}`",
            f"- **Close:** {_fmt(r.get(close_col))}",
            f"- **Open / High / Low:** {_fmt(r.get(open_col))} / {_fmt(r.get(high_col))} / {_fmt(r.get(low_col))}"
        ]
        return "\n".join(lines), row, {"type": label, "Category": r.get(cat_col), "Date": str(r.get(date_col)), "Close": r.get(close_col)}

    # ------------------------------------------------------------
    # Q7: Average Close value for each category
    # ------------------------------------------------------------
    if "average close" in q and "sentiment" not in q:
        tmp = df.copy()
        tmp["_c"] = _num_series(tmp, close_col)
        grp = tmp.groupby(cat_col)["_c"].mean().sort_values(ascending=False)
        sample_rows = df.drop_duplicates(subset=[cat_col]).copy()
        lines = ["### Average Close Value by Category"]
        for cat, avg_v in grp.items():
            lines.append(f"- **{cat}:** {_fmt(avg_v)}")
        return "\n".join(lines), sample_rows, {"average_close_by_category": grp.round(2).to_dict()}

    # ------------------------------------------------------------
    # Q8: Average trading Volume for each category
    # ------------------------------------------------------------
    if "average" in q and "volume" in q:
        tmp = df.copy()
        tmp["_v"] = _num_series(tmp, vol_col)
        grp = tmp.groupby(cat_col)["_v"].mean().sort_values(ascending=False)
        sample_rows = df.drop_duplicates(subset=[cat_col]).copy()
        lines = ["### Average Trading Volume by Category"]
        for cat, avg_v in grp.items():
            lines.append(f"- **{cat}:** {_fmt(avg_v)}")
        return "\n".join(lines), sample_rows, {"average_volume_by_category": grp.round(2).to_dict()}

    # ------------------------------------------------------------
    # Q9 & Q10: Highest / Lowest trading Volume date
    # ------------------------------------------------------------
    if "highest" in q and "volume" in q or ("lowest" in q and "volume" in q):
        v_num = _num_series(df, vol_col)
        is_high = "highest" in q
        idx = v_num.idxmax() if is_high else v_num.idxmin()
        row = df.loc[[idx]].copy()
        r = row.iloc[0]
        label = "Highest" if is_high else "Lowest"
        lines = [
            f"### {label} Trading Volume Record",
            f"- **Date:** `{r.get(date_col, 'N/A')}`",
            f"- **Category:** {r.get(cat_col, 'N/A')}",
            f"- **Volume:** {_fmt(r.get(vol_col))}",
            f"- **Close:** {_fmt(r.get(close_col))}"
        ]
        return "\n".join(lines), row, {"type": label, "Date": str(r.get(date_col)), "Volume": r.get(vol_col)}

    # ------------------------------------------------------------
    # Q11, Q12, Q13: Compare Open & Close / Close > Open / Close < Open
    # ------------------------------------------------------------
    if "open" in q and "close" in q:
        o_num = _num_series(df, open_col)
        c_num = _num_series(df, close_col)

        if "higher than open" in q:
            sub = df[c_num > o_num].copy()
            lines = [
                "### Records Where Close > Open",
                f"- **Matching Records:** {len(sub):,} out of {len(df):,}",
                "\n**Sample Matching Records:**"
            ]
            lines.extend(_format_records_list(sub, [date_col, cat_col, open_col, close_col], limit=8))
            return "\n".join(lines), sub.head(10), {"close_gt_open_count": int(len(sub))}

        if "lower than open" in q:
            sub = df[c_num < o_num].copy()
            lines = [
                "### Records Where Close < Open",
                f"- **Matching Records:** {len(sub):,} out of {len(df):,}",
                "\n**Sample Matching Records:**"
            ]
            lines.extend(_format_records_list(sub, [date_col, cat_col, open_col, close_col], limit=8))
            return "\n".join(lines), sub.head(10), {"close_lt_open_count": int(len(sub))}

        # Compare Open and Close for a selected category and date
        sub = df.copy()
        if selected_cat:
            sub = sub[sub[cat_col].astype(str).str.lower() == selected_cat.lower()]
        if selected_date:
            sub_dt = sub[sub[date_col].astype(str).str.contains(selected_date, na=False)]
            if not sub_dt.empty:
                sub = sub_dt
        row = sub.iloc[[0]].copy()
        r = row.iloc[0]
        o_v = float(_num_series(row, open_col).iloc[0])
        c_v = float(_num_series(row, close_col).iloc[0])
        diff = c_v - o_v
        direction = "Higher (Bullish)" if diff > 0 else ("Lower (Bearish)" if diff < 0 else "Unchanged")
        lines = [
            f"### Open vs Close Comparison — {r.get(cat_col, 'N/A')} (`{r.get(date_col, 'N/A')}`)",
            f"- **Open:** {_fmt(o_v)}",
            f"- **Close:** {_fmt(c_v)}",
            f"- **Difference (Close - Open):** {_fmt(diff)} ({direction})"
        ]
        return "\n".join(lines), row, {"Category": r.get(cat_col), "Date": str(r.get(date_col)), "diff": round(diff, 4)}

    # ------------------------------------------------------------
    # Q14, Q15, Q26: Volatility & Merger Volatility comparison
    # ------------------------------------------------------------
    if "volatility" in q:
        if "merger" in q and tag_col:
            sub = df[df[tag_col].astype(str).str.lower().str.contains("merger", na=False)].copy()
            lines = [
                "### Merger-Tagged Records & Volatility Comparison",
                f"- **Total Merger Records:** {len(sub):,}"
            ]
            if not sub.empty:
                v_s = _num_series(sub, volat_col)
                lines.append(f"- **Average Merger Volatility:** {_fmt(v_s.mean(), 4)}")
                lines.append(f"- **Max / Min Merger Volatility:** {_fmt(v_s.max(), 4)} / {_fmt(v_s.min(), 4)}")
                lines.append("\n**Sample Merger Records:**")
                lines.extend(_format_records_list(sub, [date_col, cat_col, tag_col, volat_col, close_col], limit=8))
            return "\n".join(lines), sub.head(10), {"merger_records": int(len(sub))}

        if "average volatility" in q:
            tmp = df.copy()
            tmp["_vol"] = _num_series(tmp, volat_col)
            grp = tmp.groupby(cat_col)["_vol"].mean().sort_values(ascending=False)
            sample_rows = df.drop_duplicates(subset=[cat_col]).copy()
            lines = ["### Average Volatility by Category"]
            for cat, avg_v in grp.items():
                lines.append(f"- **{cat}:** {_fmt(avg_v, 4)}")
            return "\n".join(lines), sample_rows, {"avg_volatility_by_category": grp.round(4).to_dict()}

        # Highest Volatility
        tmp = df.copy()
        tmp["_vol"] = _num_series(tmp, volat_col)
        top_df = tmp.sort_values(by="_vol", ascending=False).drop(columns=["_vol"]).head(5)
        lines = ["### Highest Volatility Records in Dataset"]
        lines.extend(_format_records_list(top_df, [date_col, cat_col, volat_col, close_col], limit=5))
        return "\n".join(lines), top_df, {"top_volatility_count": len(top_df)}

    # ------------------------------------------------------------
    # Q16, Q17, Q18: SMA_10 & EMA_10 Technical Indicator Queries
    # ------------------------------------------------------------
    if "sma" in q or "ema" in q:
        c_num = _num_series(df, close_col)
        s_num = _num_series(df, sma_col)
        e_num = _num_series(df, ema_col)

        if "above both" in q:
            sub = df[(c_num > s_num) & (c_num > e_num)].copy()
            lines = [
                "### Records Where Close > SMA_10 and Close > EMA_10",
                f"- **Matching Records:** {len(sub):,} out of {len(df):,}",
                "\n**Sample Bullish Technical Records:**"
            ]
            lines.extend(_format_records_list(sub, [date_col, cat_col, close_col, sma_col, ema_col], limit=8))
            return "\n".join(lines), sub.head(10), {"above_both_count": int(len(sub))}

        if "below both" in q:
            sub = df[(c_num < s_num) & (c_num < e_num)].copy()
            lines = [
                "### Records Where Close < SMA_10 and Close < EMA_10",
                f"- **Matching Records:** {len(sub):,} out of {len(df):,}",
                "\n**Sample Bearish Technical Records:**"
            ]
            lines.extend(_format_records_list(sub, [date_col, cat_col, close_col, sma_col, ema_col], limit=8))
            return "\n".join(lines), sub.head(10), {"below_both_count": int(len(sub))}

        # Compare SMA_10 and EMA_10 for selected category & date
        sub = df.copy()
        if selected_cat:
            sub = sub[sub[cat_col].astype(str).str.lower() == selected_cat.lower()]
        if selected_date:
            sub_dt = sub[sub[date_col].astype(str).str.contains(selected_date, na=False)]
            if not sub_dt.empty:
                sub = sub_dt
        row = sub.iloc[[0]].copy()
        r = row.iloc[0]
        s_v = float(_num_series(row, sma_col).iloc[0])
        e_v = float(_num_series(row, ema_col).iloc[0])
        lines = [
            f"### SMA_10 vs EMA_10 — {r.get(cat_col, 'N/A')} (`{r.get(date_col, 'N/A')}`)",
            f"- **SMA_10:** {_fmt(s_v, 4)}",
            f"- **EMA_10:** {_fmt(e_v, 4)}",
            f"- **Close:** {_fmt(r.get(close_col))}",
            f"- **Difference (EMA_10 - SMA_10):** {_fmt(e_v - s_v, 4)}"
        ]
        return "\n".join(lines), row, {"SMA_10": s_v, "EMA_10": e_v}

    # ------------------------------------------------------------
    # Q19 & Q20: Economic_Score Queries
    # ------------------------------------------------------------
    if "economic_score" in q or "economic score" in q:
        if "average" in q:
            tmp = df.copy()
            tmp["_es"] = _num_series(tmp, econ_col)
            grp = tmp.groupby(cat_col)["_es"].mean().sort_values(ascending=False)
            sample_rows = df.drop_duplicates(subset=[cat_col]).copy()
            lines = ["### Average Economic_Score by Category"]
            for cat, avg_v in grp.items():
                lines.append(f"- **{cat}:** {_fmt(avg_v, 4)}")
            return "\n".join(lines), sample_rows, {"avg_economic_score": grp.round(4).to_dict()}

        tmp = df.copy()
        tmp["_es"] = _num_series(tmp, econ_col)
        top_df = tmp.sort_values(by="_es", ascending=False).drop(columns=["_es"]).head(5)
        lines = ["### Highest Economic_Score Records"]
        lines.extend(_format_records_list(top_df, [date_col, cat_col, econ_col, close_col], limit=5))
        return "\n".join(lines), top_df, {"top_economic_score_records": len(top_df)}

    # ------------------------------------------------------------
    # Q21, Q22, Q23, Q27: Market_Sentiment Queries
    # ------------------------------------------------------------
    if "sentiment" in q:
        if "average close" in q:
            tmp = df.copy()
            tmp["_c"] = _num_series(tmp, close_col)
            grp = tmp.groupby(sent_col)["_c"].mean().sort_values(ascending=False)
            sample_rows = df.drop_duplicates(subset=[sent_col]).copy()
            lines = ["### Average Close Value by Market_Sentiment"]
            for s_lbl, avg_v in grp.items():
                lines.append(f"- **{s_lbl}:** {_fmt(avg_v)}")
            return "\n".join(lines), sample_rows, {"avg_close_by_sentiment": grp.round(2).to_dict()}

        if "most positive" in q:
            pos_df = df[df[sent_col].astype(str).str.lower() == "positive"]
            counts = pos_df[cat_col].astype(str).value_counts()
            top_cat = counts.index[0] if not counts.empty else "N/A"
            lines = [
                f"### Category with Most Positive Sentiment: **{top_cat}**",
                "\n**Positive Sentiment Breakdown by Category:**"
            ]
            for cat, cnt in counts.items():
                lines.append(f"- **{cat}:** {int(cnt):,} records")
            return "\n".join(lines), pos_df.head(10), {"top_positive_category": top_cat}

        if "most negative" in q:
            neg_df = df[df[sent_col].astype(str).str.lower() == "negative"]
            counts = neg_df[cat_col].astype(str).value_counts()
            top_cat = counts.index[0] if not counts.empty else "N/A"
            lines = [
                f"### Category with Most Negative Sentiment: **{top_cat}**",
                "\n**Negative Sentiment Breakdown by Category:**"
            ]
            for cat, cnt in counts.items():
                lines.append(f"- **{cat}:** {int(cnt):,} records")
            return "\n".join(lines), neg_df.head(10), {"top_negative_category": top_cat}

        # General counts of Positive, Negative, Neutral Market_Sentiment
        counts = df[sent_col].astype(str).value_counts()
        sample_rows = df.drop_duplicates(subset=[sent_col]).copy()
        lines = ["### Market_Sentiment Record Counts"]
        for s_lbl, cnt in counts.items():
            lines.append(f"- **{s_lbl}:** {int(cnt):,} records")
        return "\n".join(lines), sample_rows, {"sentiment_counts": counts.to_dict()}

    # ------------------------------------------------------------
    # Q24 & Q25: News_Tag & Earnings Records
    # ------------------------------------------------------------
    if "news_tag" in q or "news tag" in q or "tagged as earnings" in q or "earnings" in q:
        if "earnings" in q:
            sub = df[df[tag_col].astype(str).str.lower().str.contains("earnings", na=False)].copy()
            lines = [
                "### Records Tagged as Earnings",
                f"- **Total Earnings Records:** {len(sub):,}",
                "\n**Sample Earnings Records (Date, Category, Close, Market_Sentiment):**"
            ]
            lines.extend(_format_records_list(sub, [date_col, cat_col, close_col, sent_col, tag_col], limit=10))
            return "\n".join(lines), sub.head(10), {"earnings_records": int(len(sub))}

        counts = df[tag_col].astype(str).value_counts()
        sample_rows = df.drop_duplicates(subset=[tag_col]).copy()
        lines = ["### Record Counts by News_Tag"]
        for tag_lbl, cnt in counts.items():
            lines.append(f"- **{tag_lbl}:** {int(cnt):,} records")
        return "\n".join(lines), sample_rows, {"news_tag_counts": counts.to_dict()}

    # ------------------------------------------------------------
    # Q28 & Q29: Wavelet_Noise & Wavelet_HighFreq Queries
    # ------------------------------------------------------------
    if "wavelet_noise" in q or "wavelet noise" in q:
        wn_num = _num_series(df, wnoise_col)
        sub = df[wn_num > 0].copy()
        trend_cols = [c for c in [date_col, cat_col, wnoise_col, sma_col, ema_col, close_col] if c]
        lines = [
            "### Records Where Wavelet_Noise > 0 (with Trend Indicators)",
            f"- **Total Positive Wavelet_Noise Records:** {len(sub):,}",
            "\n**Sample Records:**"
        ]
        lines.extend(_format_records_list(sub, trend_cols, limit=10))
        return "\n".join(lines), sub.head(10), {"positive_wavelet_noise_count": int(len(sub))}

    if "wavelet_highfreq" in q or "wavelet highfreq" in q or "wavelet" in q:
        wh_num = _num_series(df, whigh_col)
        sub = df[wh_num < 0].copy()
        lines = [
            "### Records Where Wavelet_HighFreq < 0",
            f"- **Total Negative Wavelet_HighFreq Records:** {len(sub):,}",
            "\n**Sample Records (Dates & Categories):**"
        ]
        lines.extend(_format_records_list(sub, [date_col, cat_col, whigh_col, close_col], limit=10))
        return "\n".join(lines), sub.head(10), {"negative_wavelet_highfreq_count": int(len(sub))}

    # ------------------------------------------------------------
    # Q30: Compare Close with Close_Next
    # ------------------------------------------------------------
    if "close_next" in q or "close next" in q or "next close" in q:
        c_num = _num_series(df, close_col)
        cn_num = _num_series(df, cnext_col)
        higher_df = df[cn_num > c_num].copy()
        lower_df = df[cn_num < c_num].copy()
        sample_df = pd.concat([higher_df.head(5), lower_df.head(5)], ignore_index=True)
        lines = [
            "### Close vs Close_Next Comparison",
            f"- **Next Close Higher (`Close_Next > Close`):** {len(higher_df):,} records",
            f"- **Next Close Lower (`Close_Next < Close`):** {len(lower_df):,} records",
            "\n**Sample Higher Next-Close Records:**"
        ]
        lines.extend(_format_records_list(higher_df, [date_col, cat_col, close_col, cnext_col], limit=4))
        lines.append("\n**Sample Lower Next-Close Records:**")
        lines.extend(_format_records_list(lower_df, [date_col, cat_col, close_col, cnext_col], limit=4))
        return "\n".join(lines), sample_df, {"next_higher": int(len(higher_df)), "next_lower": int(len(lower_df))}

    # Fallback: general category or dataset summary
    if selected_cat:
        sub = df[df[cat_col].astype(str).str.lower() == selected_cat.lower()].head(5)
        lines = [f"### Stock Dataset Records — {selected_cat}"]
        lines.extend(_format_records_list(sub, [date_col, cat_col, open_col, close_col, vol_col, sent_col], limit=5))
        return "\n".join(lines), sub, {"category": selected_cat, "rows": len(sub)}

    return None, pd.DataFrame(), {}


# ============================================================
# 5. MAIN ROUTE HANDLER (CALLED BY rag.py)
# ============================================================

def handle(question: str):
    df, err = load_stock_dataset()
    if err:
        return err, []

    ticker = extract_ticker(question)

    # 1. Try answering from stock_dataset.csv first
    answer, matched_df, api_summary = answer_stock_dataset_question(question, df)

    # 2. If ticker is mentioned (e.g. AAPL, MSFT, TSLA) or dataset didn't cover the query, query Live Alpha Vantage API
    if ticker or answer is None:
        target_sym = ticker or "AAPL"
        live_res = fetch_alpha_vantage_quote(target_sym)
        if live_res.get("success"):
            live_block = "\n".join([
                f"### Alpha Vantage Live Quote — {live_res.get('symbol')}",
                f"- **Latest Trading Day:** `{live_res.get('latest_trading_day')}`",
                f"- **Open:** {_fmt(live_res.get('open'))}",
                f"- **High:** {_fmt(live_res.get('high'))}",
                f"- **Low:** {_fmt(live_res.get('low'))}",
                f"- **Price (Close):** {_fmt(live_res.get('price'))}",
                f"- **Volume:** {_fmt(live_res.get('volume'))}",
                f"- **Change Percent:** {live_res.get('change_percent')}"
            ])
            answer = f"{answer}\n\n{live_block}" if answer else live_block
            api_summary["live_quote"] = live_res
        elif answer is None:
            answer = f"Alpha Vantage API: {live_res.get('message', 'No quote data available.')}"
            api_summary["live_error"] = live_res.get("message")

    # 3. Save history and fuse ONLY genuine dataset rows into csv/fused/fused_alpha_vantage.csv
    save_api_answer_and_fuse(
        api_name=API_NAME,
        question=question,
        api_result=api_summary,
        answer=answer,
        key_mapping={"original": ["Date", "Category"], "api": ["Date", "Category"]},
        original_csv=STOCK_DATASET_CSV,
        selected_original_df=matched_df
    )

    return answer, []