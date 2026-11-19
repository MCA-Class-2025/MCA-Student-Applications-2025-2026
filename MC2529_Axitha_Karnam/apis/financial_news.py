import os
import re
import requests
import pandas as pd
from datetime import datetime

from rag import save_api_answer_and_fuse

API_NAME = "financial_news"
MARKETAUX_NEWS_URL = "https://api.marketaux.com/v1/news/all"
PARTNER_HEADLINES_CSV = "csv/raw_partner_headlines.csv"

COMPANY_TO_TICKER = {
    "agilent technologies": "A",
    "agilent": "A",
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

MONTH_MAP = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12
}


# ============================================================
# 1. QUESTION DETECTION
# ============================================================

def is_financial_news_question(question: str) -> bool:
    q = str(question).lower()
    news_patterns = [
        r"\bmarketaux\b",
        r"\bheadline\b", r"\bheadlines\b",
        r"\bnews\b", r"\barticle\b", r"\barticles\b",
        r"\bpublisher\b", r"\bpublishers\b",
        r"\bnews source\b", r"\bnews sources\b",
        r"\bgurufocus\b", r"\bzacks\b",
        r"\bagilent\b",
        r"\bstock\s+a\b",
        r"\bfor\s+a\b",
        r"\babout\s+a\b"
    ]
    return any(re.search(pattern, q) for pattern in news_patterns)


def can_handle(question: str) -> bool:
    return is_financial_news_question(question)


# ============================================================
# 2. EXTRACTION HELPERS (TICKER, DATES, PUBLISHER, TOPIC)
# ============================================================

def extract_news_symbol(question: str):
    """
    Extract stock ticker from question, including single-letter ticker 'A'
    (Agilent Technologies) and standard 2-5 letter tickers.
    """
    q_str = str(question)
    q_lower = q_str.lower()

    # 1. Company name mapping (e.g., "Agilent Technologies" -> "A")
    for comp_name, ticker in sorted(COMPANY_TO_TICKER.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(r"\b" + re.escape(comp_name) + r"\b", q_lower):
            return ticker

    # 2. Explicit single-letter ticker "A" patterns: "stock A", "for A", "about A", "ticker A"
    if re.search(r"\b(?:stock|ticker|symbol|for|about)\s+A\b", q_str):
        return "A"

    # 3. Standard uppercase ticker symbols (excluding common English words)
    stop_words = {
        "A", "I", "IN", "ON", "AT", "TO", "BY", "OF", "OR", "AND", "THE", "FOR",
        "ARE", "ANY", "MAY", "JAN", "FEB", "MAR", "APR", "JUN", "JUL", "AUG",
        "SEP", "OCT", "NOV", "DEC", "WHAT", "SHOW", "GIVE", "FIND", "HOW",
        "WHICH", "NEWS", "API", "CSV", "USD", "EUR", "GDP", "FRED", "CEO", "IPO"
    }
    for match in re.finditer(r"\b([A-Z]{1,5})\b", q_str):
        sym = match.group(1)
        if sym == "A" and re.search(r"\b(?:stock|ticker|symbol|for|about)\s+A\b", q_str):
            return "A"
        if sym not in stop_words:
            return sym

    return None


def extract_publisher_filter(question: str):
    q = str(question).lower()
    known_publishers = [
        "gurufocus", "zacks", "benzinga", "seeking alpha", "motley fool",
        "reuters", "bloomberg", "cnbc", "marketwatch", "yahoo", "barrons"
    ]
    for pub in known_publishers:
        if pub in q:
            return pub
    return None


def extract_date_filters(question: str) -> dict:
    """
    Extract exact date (YYYY-MM-DD), date range (start_date, end_date),
    or month/year filter (e.g. May 2020 -> 2020-05).
    """
    q = str(question).lower()

    # 1. Range: "between May 1 and May 15, 2020"
    range_match = re.search(
        r"between\s+([a-z]+)\s+(\d{1,2})\s+and\s+([a-z]+)?\s*(\d{1,2}),?\s+(19\d{2}|20\d{2})",
        q
    )
    if range_match:
        m1_name = range_match.group(1)
        d1 = int(range_match.group(2))
        m2_name = range_match.group(3) or m1_name
        d2 = int(range_match.group(4))
        yr = int(range_match.group(5))
        m1 = MONTH_MAP.get(m1_name)
        m2 = MONTH_MAP.get(m2_name)
        if m1 and m2:
            return {
                "mode": "range",
                "start": f"{yr:04d}-{m1:02d}-{d1:02d}",
                "end": f"{yr:04d}-{m2:02d}-{d2:02d}",
                "label": f"{yr:04d}-{m1:02d}-{d1:02d} to {yr:04d}-{m2:02d}-{d2:02d}"
            }

    # 2. Exact date: "May 15, 2020" or "on May 5, 2020"
    exact_match = re.search(
        r"\b([a-z]+)\s+(\d{1,2}),?\s+(19\d{2}|20\d{2})\b",
        q
    )
    if exact_match:
        m_name = exact_match.group(1)
        day = int(exact_match.group(2))
        yr = int(exact_match.group(3))
        m_num = MONTH_MAP.get(m_name)
        if m_num:
            dt_str = f"{yr:04d}-{m_num:02d}-{day:02d}"
            return {
                "mode": "exact",
                "date": dt_str,
                "label": dt_str
            }

    # 3. ISO date: "2020-05-15"
    iso_match = re.search(r"\b(19\d{2}|20\d{2})-(\d{2})-(\d{2})\b", q)
    if iso_match:
        dt_str = iso_match.group(0)
        return {"mode": "exact", "date": dt_str, "label": dt_str}

    # 4. Month + Year: "May 2020" or "around May 2020"
    my_match = re.search(r"\b([a-z]+)\s+(19\d{2}|20\d{2})\b", q)
    if my_match:
        m_name = my_match.group(1)
        yr = int(my_match.group(2))
        m_num = MONTH_MAP.get(m_name)
        if m_num:
            ym_prefix = f"{yr:04d}-{m_num:02d}"
            return {
                "mode": "month",
                "prefix": ym_prefix,
                "label": f"{m_name.title()} {yr}"
            }

    return {"mode": "none"}


def detect_topic_keywords(question: str) -> list:
    q = str(question).lower()
    if "earnings" in q:
        return ["earnings", "q1", "q2", "q3", "q4", "quarter", "revenue", "eps", "profit", "results", "beat", "miss"]
    if any(w in q for w in ("buying", "selling", "investor", "investors", "stake", "shares", "boosts", "cuts", "buys", "sells")):
        return ["buy", "buys", "buying", "sell", "sells", "selling", "stake", "shares", "boost", "cut", "trim", "position", "holder", "investor"]
    return []


# ============================================================
# 3. LIVE MARKETAUX API CALLS
# ============================================================

def fetch_marketaux_news(symbol: str = None, search_query: str = None, published_on: str = None, limit: int = 5) -> dict:
    api_token = os.getenv("MARKETAUX_API_KEY") or os.getenv("MARKETAUX_API_TOKEN")
    if not api_token:
        return {
            "success": False,
            "message": "MARKETAUX_API_KEY not configured in environment.",
            "articles": []
        }

    try:
        params = {
            "api_token": api_token,
            "language": "en",
            "limit": limit
        }
        if symbol:
            params["symbols"] = symbol.upper()
            params["filter_entities"] = "true"
        if search_query:
            params["search"] = search_query
        if published_on:
            params["published_on"] = published_on

        response = requests.get(MARKETAUX_NEWS_URL, params=params, timeout=20)
        response.raise_for_status()
        payload = response.json()
        articles = payload.get("data", [])

        return {
            "success": True,
            "articles": articles
        }
    except Exception as error:
        print("Marketaux API error:", error)
        return {
            "success": False,
            "message": f"Marketaux API error: {error}",
            "articles": []
        }


# ============================================================
# 4. CHUNKED DATASET SEARCH (csv/raw_partner_headlines.csv)
# ============================================================

def _norm_col(col):
    return re.sub(r"\s+", " ", str(col).replace("\ufeff", "").replace("\xa0", " ")).strip()


def query_partner_headlines_dataset(
    symbol: str = None,
    publisher_filter: str = None,
    date_filter: dict = None,
    topic_keywords: list = None,
    max_scan_rows: int = 5000
) -> tuple:
    """
    Scans csv/raw_partner_headlines.csv safely in chunks to find matching records
    without loading a massive file into memory all at once.
    """
    if not os.path.exists(PARTNER_HEADLINES_CSV):
        return pd.DataFrame(), None, f"Dataset not found at {PARTNER_HEADLINES_CSV}."

    matched_chunks = []
    original_columns = None
    total_matched = 0

    try:
        for chunk in pd.read_csv(PARTNER_HEADLINES_CSV, chunksize=100000, low_memory=False, encoding="utf-8-sig"):
            chunk.columns = [_norm_col(c) for c in chunk.columns]
            if original_columns is None:
                original_columns = list(chunk.columns)

            col_lookup = {c.lower(): c for c in chunk.columns}
            stock_col = col_lookup.get("stock") or col_lookup.get("symbol") or col_lookup.get("ticker")
            title_col = col_lookup.get("title") or col_lookup.get("headline")
            pub_col = col_lookup.get("publisher") or col_lookup.get("source")
            date_col = col_lookup.get("date") or col_lookup.get("published_at")

            mask = pd.Series(True, index=chunk.index)

            # 1. Symbol filter
            if symbol and stock_col:
                sym_upper = symbol.strip().upper()
                mask = mask & (chunk[stock_col].astype(str).str.strip().str.upper() == sym_upper)
            elif symbol and title_col:
                mask = mask & chunk[title_col].astype(str).str.contains(r"\b" + re.escape(symbol) + r"\b", case=False, na=False)

            sub = chunk[mask].copy()
            if sub.empty:
                continue

            # 2. Publisher filter
            if publisher_filter and pub_col:
                sub = sub[sub[pub_col].astype(str).str.lower().str.contains(publisher_filter.lower(), na=False, regex=False)]
                if sub.empty:
                    continue

            # 3. Date filter
            if date_filter and date_filter.get("mode") != "none" and date_col:
                date_str_series = sub[date_col].astype(str).str.strip()
                # Extract YYYY-MM-DD prefix from timestamp strings like "2020-05-15 00:00:00"
                ymd_series = date_str_series.str.slice(0, 10)

                mode = date_filter["mode"]
                if mode == "exact":
                    sub = sub[ymd_series == date_filter["date"]]
                elif mode == "month":
                    sub = sub[ymd_series.str.startswith(date_filter["prefix"])]
                elif mode == "range":
                    sub = sub[(ymd_series >= date_filter["start"]) & (ymd_series <= date_filter["end"])]

                if sub.empty:
                    continue

            # 4. Topic keywords filter
            if topic_keywords and title_col:
                t_series = sub[title_col].astype(str).str.lower()
                t_mask = pd.Series(False, index=sub.index)
                for kw in topic_keywords:
                    t_mask = t_mask | t_series.str.contains(r"\b" + re.escape(kw) + r"\b", na=False)
                sub = sub[t_mask]
                if sub.empty:
                    continue

            matched_chunks.append(sub)
            total_matched += len(sub)
            if total_matched >= max_scan_rows:
                break

        if not matched_chunks:
            return pd.DataFrame(columns=original_columns or []), original_columns, None

        full_matches = pd.concat(matched_chunks, ignore_index=True)

        # Sort descending by date so most recent headlines come first
        col_lookup = {c.lower(): c for c in full_matches.columns}
        date_col = col_lookup.get("date") or col_lookup.get("published_at")
        if date_col:
            full_matches = full_matches.sort_values(by=date_col, ascending=False).reset_index(drop=True)

        return full_matches, original_columns, None

    except Exception as error:
        print("Error scanning raw_partner_headlines.csv:", error)
        return pd.DataFrame(), original_columns, f"Error reading headlines dataset: {error}"


# ============================================================
# 5. EVENT CLASSIFICATION & ANSWER FORMATTING
# ============================================================

def _classify_headline_event(title: str) -> str:
    t = str(title).lower()
    if any(w in t for w in ("earnings", "q1", "q2", "q3", "q4", "quarter", "revenue", "eps", "profit", "results")):
        return "Earnings & Financial Results"
    if any(w in t for w in ("buy", "buys", "buying", "sell", "sells", "selling", "stake", "shares", "boost", "cut", "trim", "position", "holder")):
        return "Institutional / Insider Trading & Holdings"
    if any(w in t for w in ("upgrade", "downgrade", "price target", "rating", "analyst", "outperform", "buy rating")):
        return "Analyst Ratings & Price Targets"
    if any(w in t for w in ("dividend", "repurchase", "buyback", "split")):
        return "Dividends & Capital Allocation"
    if any(w in t for w in ("acquire", "acquisition", "merger", "deal", "partner", "launch", "fda", "approval")):
        return "Corporate M&A / Product & Regulatory"
    return "General Market & Stock Commentary"


def build_financial_news_answer(
    question: str,
    symbol: str,
    publisher_filter: str,
    date_filter: dict,
    topic_keywords: list,
    matched_df: pd.DataFrame,
    live_bundle: dict
) -> tuple:
    q = str(question).lower()
    display_entity = f"Agilent Technologies ({symbol})" if symbol == "A" else (symbol or "General Market")

    col_lookup = {c.lower(): c for c in matched_df.columns} if not matched_df.empty else {}
    title_col = col_lookup.get("title") or col_lookup.get("headline") or "title"
    pub_col = col_lookup.get("publisher") or col_lookup.get("source") or "publisher"
    date_col = col_lookup.get("date") or col_lookup.get("published_at") or "date"

    lines = [f"### Financial News — {display_entity}"]

    # 1. Count question ("How many news articles are available...")
    if "how many" in q:
        count = len(matched_df)
        lines.append(f"- **Total Matching Articles in Dataset (`{PARTNER_HEADLINES_CSV}`):** **{count:,}** articles")
        if not matched_df.empty and date_col in matched_df.columns:
            min_dt = str(matched_df[date_col].iloc[-1])[:10]
            max_dt = str(matched_df[date_col].iloc[0])[:10]
            lines.append(f"- **Date Coverage:** {min_dt} to {max_dt}")
        return "\n".join(lines), matched_df.head(10)

    # 2. Publisher breakdown / Top publisher ("Which publishers reported...", "Which publisher has the most...")
    if any(w in q for w in ("which publisher", "which publishers", "which news source", "which news sources", "most articles")):
        if matched_df.empty or pub_col not in matched_df.columns:
            lines.append("- **Dataset Publishers:** No matching publisher records found in dataset.")
        else:
            pub_counts = matched_df[pub_col].astype(str).str.strip().value_counts()
            top_pub = pub_counts.index[0]
            top_cnt = int(pub_counts.iloc[0])
            lines.append(f"- **Top Publisher:** **{top_pub}** ({top_cnt:,} articles)")
            lines.append(f"- **Total Distinct Publishers:** {len(pub_counts)}")
            lines.append("\n**Publisher Breakdown (Dataset):**")
            for pub_name, cnt in pub_counts.head(10).items():
                lines.append(f"- **{pub_name}:** {int(cnt):,} articles")

        live_articles = live_bundle.get("articles", [])
        if live_articles:
            live_sources = sorted(set(str(a.get("source", "Unknown")) for a in live_articles))
            lines.append(f"\n- **Live Marketaux Publishers:** {', '.join(live_sources)}")

        return "\n".join(lines), matched_df.head(10)

    # 3. Financial event classification ("What types of financial events are mentioned...")
    if "types of financial events" in q or "financial events" in q:
        if matched_df.empty or title_col not in matched_df.columns:
            lines.append("- No dataset headlines found to classify financial events.")
            return "\n".join(lines), matched_df

        event_counts = {}
        sample_by_event = {}
        for _, row in matched_df.iterrows():
            title_txt = str(row.get(title_col, ""))
            ev = _classify_headline_event(title_txt)
            event_counts[ev] = event_counts.get(ev, 0) + 1
            if ev not in sample_by_event:
                sample_by_event[ev] = (title_txt, str(row.get(pub_col, "N/A")), str(row.get(date_col, "N/A"))[:10])

        lines.append(f"- **Analyzed Dataset Headlines:** {len(matched_df):,} articles")
        lines.append("\n**Financial Event Categories Found:**")
        for ev, cnt in sorted(event_counts.items(), key=lambda x: x[1], reverse=True):
            ex_title, ex_pub, ex_dt = sample_by_event[ev]
            lines.append(f"- **{ev}** ({cnt:,} articles) — e.g., *\"{ex_title}\"* ({ex_pub}, {ex_dt})")

        return "\n".join(lines), matched_df.head(10)

    # 4. Standard / Date / Publisher / Topic / Summary Headline Listing
    if date_filter and date_filter.get("mode") != "none":
        lines.append(f"- **Date Filter:** {date_filter.get('label')}")
    if publisher_filter:
        lines.append(f"- **Publisher Filter:** {publisher_filter.title()}")

    if not matched_df.empty:
        total_found = len(matched_df)
        top_df = matched_df.head(10)
        lines.append(f"- **Dataset Matches (`{PARTNER_HEADLINES_CSV}`):** Showing {len(top_df)} of {total_found:,} matching articles")

        for idx, (_, row) in enumerate(top_df.iterrows(), start=1):
            t_val = str(row.get(title_col, "Untitled")).strip()
            p_val = str(row.get(pub_col, "Unknown")).strip()
            d_val = str(row.get(date_col, "N/A")).strip()[:19]
            lines.append(f"{idx}. **{t_val}** — *{p_val}* (`{d_val}`)")

        if "summarize" in q or "summary" in q:
            event_types = sorted(set(_classify_headline_event(str(r.get(title_col, ""))) for _, r in top_df.iterrows()))
            lines.append(f"\n**Key Event Summary:** Coverage centers on **{', '.join(event_types)}** across {len(top_df)} recent articles.")
    else:
        lines.append(f"- **Dataset Matches (`{PARTNER_HEADLINES_CSV}`):** No matching articles found in dataset.")

    # 5. Append Live Marketaux API Articles (if available)
    live_articles = live_bundle.get("articles", [])
    if live_articles:
        lines.append(f"\n**Live Marketaux API Headlines ({len(live_articles)} articles):**")
        for idx, art in enumerate(live_articles[:5], start=1):
            l_title = str(art.get("title", "Untitled")).strip()
            l_source = str(art.get("source", "Marketaux")).strip()
            l_pub_at = str(art.get("published_at", ""))[:19]
            lines.append(f"{idx}. **{l_title}** — *{l_source}* (`{l_pub_at}`)")

    return "\n".join(lines), matched_df.head(10)


# ============================================================
# 6. MAIN ROUTE HANDLER (CALLED BY rag.py)
# ============================================================

def handle(question: str):
    symbol = extract_news_symbol(question)
    publisher_filter = extract_publisher_filter(question)
    date_filter = extract_date_filters(question)
    topic_keywords = detect_topic_keywords(question)

    matched_df, _, err = query_partner_headlines_dataset(
        symbol=symbol,
        publisher_filter=publisher_filter,
        date_filter=date_filter,
        topic_keywords=topic_keywords
    )
    if err:
        return err, []

    # Query live Marketaux API when asking for latest/recent news or when dataset has no match
    q_lower = str(question).lower()
    should_call_live = (
        matched_df.empty
        or "marketaux" in q_lower
        or ("latest" in q_lower and date_filter.get("mode") == "none")
        or ("recent" in q_lower and date_filter.get("mode") == "none")
    )

    live_bundle = {"success": False, "articles": []}
    if should_call_live:
        pub_on = date_filter.get("date") if date_filter.get("mode") == "exact" else None
        search_q = publisher_filter if publisher_filter else None
        live_bundle = fetch_marketaux_news(
            symbol=symbol,
            search_query=search_q,
            published_on=pub_on,
            limit=5
        )

    answer, rows_to_fuse = build_financial_news_answer(
        question=question,
        symbol=symbol,
        publisher_filter=publisher_filter,
        date_filter=date_filter,
        topic_keywords=topic_keywords,
        matched_df=matched_df,
        live_bundle=live_bundle
    )

    api_summary = {
        "symbol": symbol or "ALL",
        "publisher_filter": publisher_filter or "none",
        "date_filter": date_filter.get("label", "none"),
        "dataset_matches": int(len(matched_df)),
        "live_articles_returned": int(len(live_bundle.get("articles", [])))
    }

    # Fuse ONLY genuine rows from raw_partner_headlines.csv + API_Result + Gemma_Answer
    save_api_answer_and_fuse(
        api_name=API_NAME,
        question=question,
        api_result=api_summary,
        answer=answer,
        key_mapping={"original": ["stock"], "api": ["symbol"]},
        original_csv=PARTNER_HEADLINES_CSV,
        selected_original_df=rows_to_fuse
    )

    return answer, []