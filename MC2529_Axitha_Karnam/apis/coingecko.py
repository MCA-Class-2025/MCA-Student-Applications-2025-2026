import os
import re
import requests
import pandas as pd

from rag import save_api_answer_and_fuse

API_NAME = "coingecko"
COINGECKO_MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"
COINGECKO_GLOBAL_URL = "https://api.coingecko.com/api/v3/global"
COINGECKO_CRYPTO_CSV = "csv/crypto_dataset.csv"

COINGECKO_CSV_COLUMNS = [
    "Name",
    "Symbol",
    "Price Usd",
    "Volume24h",
    "Volume30d",
    "MarketCap",
    "Dominance",
    "YtdPriceChangePercentage",
    "cmcRank",
    "marketPairCount",
    "circulatingSupply",
    "totalSupply"
]

CRYPTO_SYMBOL_MAPPING = {
    "bitcoin": "BTC", "btc": "BTC",
    "ethereum": "ETH", "eth": "ETH",
    "tether": "USDT", "usdt": "USDT",
    "usd coin": "USDC", "usdc": "USDC",
    "binance coin": "BNB", "binancecoin": "BNB", "bnb": "BNB",
    "ripple": "XRP", "xrp": "XRP",
    "cardano": "ADA", "ada": "ADA",
    "solana": "SOL", "sol": "SOL",
    "dogecoin": "DOGE", "doge": "DOGE",
    "polkadot": "DOT", "dot": "DOT",
    "polygon": "MATIC", "matic": "MATIC",
    "litecoin": "LTC", "ltc": "LTC",
    "shiba inu": "SHIB", "shib": "SHIB",
    "tron": "TRX", "trx": "TRX",
    "avalanche": "AVAX", "avax": "AVAX",
    "chainlink": "LINK", "link": "LINK",
    "uniswap": "UNI", "uni": "UNI",
    "cosmos": "ATOM", "atom": "ATOM",
    "stellar": "XLM", "xlm": "XLM",
    "monero": "XMR", "xmr": "XMR"
}

COINGECKO_ID_MAPPING = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "USDT": "tether",
    "USDC": "usd-coin",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "SOL": "solana",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "MATIC": "matic-network",
    "LTC": "litecoin",
    "SHIB": "shiba-inu",
    "TRX": "tron",
    "AVAX": "avalanche-2",
    "LINK": "chainlink",
    "UNI": "uniswap",
    "ATOM": "cosmos",
    "XLM": "stellar",
    "XMR": "monero"
}


# ============================================================
# 1. QUESTION DETECTION
# ============================================================

def is_crypto_question(question: str) -> bool:
    question_lower = question.lower()

    crypto_patterns = [
        r"\bcoingecko\b",
        r"\bcrypto\b", r"\bcryptocurrency\b", r"\bcryptocurrencies\b",
        r"\bbitcoin\b", r"\bbtc\b",
        r"\bethereum\b", r"\beth\b",
        r"\btether\b", r"\busdt\b",
        r"\busdc\b", r"\busd coin\b",
        r"\bdogecoin\b", r"\bdoge\b",
        r"\bsolana\b", r"\bsol\b",
        r"\bcardano\b", r"\bada\b",
        r"\bripple\b", r"\bxrp\b",
        r"\bbinance coin\b", r"\bbnb\b",
        r"\bpolygon\b", r"\bmatic\b",
        r"\blitecoin\b", r"\bltc\b",
        r"\bpolkadot\b", r"\bdot\b",
        r"\bavalanche\b", r"\bavax\b",
        r"\bchainlink\b", r"\blink\b",
        r"\bmarket dominance\b", r"\bdominance\b",
        r"\bcirculating supply\b", r"\btotal supply\b", r"\bmax supply\b",
        r"\bmarket rank\b", r"\bcmc rank\b",
        r"\b30-day\b", r"\b30 day\b", r"\bvolume30d\b", r"\bvolume24h\b",
        r"\bmarket pair\b", r"\bmarket pairs\b",
        r"\ball-time high\b", r"\ball time high\b", r"\bath\b"
    ]

    return any(re.search(pattern, question_lower) for pattern in crypto_patterns)


def can_handle(question: str) -> bool:
    return is_crypto_question(question)


# ============================================================
# 2. EXTRACTION HELPERS
# ============================================================

def extract_all_crypto_details(question: str):
    """Extract ALL mentioned crypto symbols in order of appearance + target currency."""
    question_lower = question.lower()
    found_matches = []

    for crypto_name, symbol in CRYPTO_SYMBOL_MAPPING.items():
        match = re.search(r"\b" + re.escape(crypto_name) + r"\b", question_lower)
        if match:
            found_matches.append((match.start(), symbol))

    found_matches.sort(key=lambda x: x[0])
    symbols = list(dict.fromkeys(sym for _, sym in found_matches))

    vs_currency = "usd"
    currency_mapping = {
        "inr": "inr", "rupee": "inr", "rupees": "inr",
        "usd": "usd", "dollar": "usd", "dollars": "usd",
        "eur": "eur", "euro": "eur", "euros": "eur",
        "gbp": "gbp", "pound": "gbp", "pounds": "gbp",
        "jpy": "jpy", "yen": "jpy",
        "aud": "aud", "cad": "cad", "chf": "chf",
        "sgd": "sgd", "aed": "aed"
    }

    for currency_name, currency_code in currency_mapping.items():
        if re.search(r"\b" + re.escape(currency_name) + r"\b", question_lower):
            vs_currency = currency_code
            break

    return symbols, vs_currency


def detect_metric(question: str) -> dict:
    """Identify the exact requested metric and its CSV + CoinGecko API field mappings."""
    q = question.lower()

    # 1. Check 30-day volume FIRST before generic "volume"
    if re.search(r"\b(volume30d|30[\s-]*day(?:\s+trading)?\s+volume)\b", q):
        return {
            "key": "volume_30d",
            "label": "30-Day Trading Volume",
            "csv_col": "Volume30d",
            "api_field": None,
            "is_currency": True
        }

    # 2. 24-hour trading volume
    if any(k in q for k in ("volume24h", "24-hour", "24 hour", "trading volume", "volume")):
        return {
            "key": "volume_24h",
            "label": "24-Hour Trading Volume",
            "csv_col": "Volume24h",
            "api_field": "total_volume",
            "is_currency": True
        }

    # 3. Market capitalization
    if any(k in q for k in ("market cap", "marketcap", "market capitalization")):
        return {
            "key": "market_cap",
            "label": "Market Capitalization",
            "csv_col": "MarketCap",
            "api_field": "market_cap",
            "is_currency": True
        }

    # 4. Market dominance
    if any(k in q for k in ("dominance", "market dominance")):
        return {
            "key": "dominance",
            "label": "Market Dominance (%)",
            "csv_col": "Dominance",
            "api_field": "dominance",
            "is_currency": False
        }

    # 5. Circulating supply
    if "circulating supply" in q:
        return {
            "key": "circulating_supply",
            "label": "Circulating Supply",
            "csv_col": "circulatingSupply",
            "api_field": "circulating_supply",
            "is_currency": False
        }

    # 6. Total supply / Max supply
    if "max supply" in q:
        return {
            "key": "max_supply",
            "label": "Max Supply",
            "csv_col": None,
            "api_field": "max_supply",
            "is_currency": False
        }
    if "total supply" in q:
        return {
            "key": "total_supply",
            "label": "Total Supply",
            "csv_col": "totalSupply",
            "api_field": "total_supply",
            "is_currency": False
        }

    # 7. Market rank
    if any(k in q for k in ("rank", "ranking", "rankings")):
        return {
            "key": "rank",
            "label": "Market Rank",
            "csv_col": "cmcRank",
            "api_field": "market_cap_rank",
            "is_currency": False
        }

    # 8. YTD / 1Y price change
    if any(k in q for k in ("ytd", "year-to-date", "year to date")):
        return {
            "key": "ytd",
            "label": "Year-to-Date / 1Y Price Change (%)",
            "csv_col": "YtdPriceChangePercentage",
            "api_field": "price_change_percentage_1y_in_currency",
            "is_currency": False
        }

    # 9. Market pairs
    if any(k in q for k in ("market pair", "market pairs", "pair count")):
        return {
            "key": "pairs",
            "label": "Market Pair Count",
            "csv_col": "marketPairCount",
            "api_field": None,
            "is_currency": False
        }

    # 10. Extra live-only CoinGecko metrics (for general CoinGecko questions)
    if any(k in q for k in ("all-time high", "all time high", "ath")):
        return {
            "key": "ath",
            "label": "All-Time High (ATH)",
            "csv_col": None,
            "api_field": "ath",
            "is_currency": True
        }
    if any(k in q for k in ("all-time low", "all time low", "atl")):
        return {
            "key": "atl",
            "label": "All-Time Low (ATL)",
            "csv_col": None,
            "api_field": "atl",
            "is_currency": True
        }
    if any(k in q for k in ("24h high", "24-hour high", "high_24h")):
        return {
            "key": "high_24h",
            "label": "24-Hour High",
            "csv_col": None,
            "api_field": "high_24h",
            "is_currency": True
        }
    if any(k in q for k in ("24h low", "24-hour low", "low_24h")):
        return {
            "key": "low_24h",
            "label": "24-Hour Low",
            "csv_col": None,
            "api_field": "low_24h",
            "is_currency": True
        }
    if any(k in q for k in ("24h change", "24-hour change", "price change")):
        return {
            "key": "change_24h",
            "label": "24-Hour Price Change (%)",
            "csv_col": None,
            "api_field": "price_change_percentage_24h",
            "is_currency": False
        }

    # Default: Price
    return {
        "key": "price",
        "label": "Price",
        "csv_col": "Price Usd",
        "api_field": "current_price",
        "is_currency": True
    }


def detect_query_mode(question: str, metric: dict) -> dict:
    """
    Determine whether the user wants:
      - 'dataset': Only dataset value (e.g., "What is Bitcoin's 30-day trading volume?")
      - 'live': Only live CoinGecko API value (e.g., "What is Bitcoin's current CoinGecko market rank?")
      - 'both': Comparison of Dataset vs Live CoinGecko (all 25 comparison questions)
    """
    q = question.lower()

    mentions_dataset = any(w in q for w in ("dataset", "csv", "my data", "historical", "stored"))
    mentions_live = any(w in q for w in ("coingecko", "current", "live", "today", "now", "latest"))
    mentions_compare = any(
        w in q for w in ("compare", "comparison", "difference", "biggest", "largest", "increased", "decreased", "vs", "versus")
    )

    # Metrics that ONLY exist in CSV (Volume30d, marketPairCount)
    if metric.get("api_field") is None and metric.get("csv_col") is not None:
        return {"source": "dataset", "should_fuse": True}

    # Metrics that ONLY exist in Live CoinGecko (ATH, ATL, 24h high/low, 24h change)
    if metric.get("csv_col") is None and metric.get("api_field") is not None:
        return {"source": "live", "should_fuse": False}

    # Explicit comparison or mentions both dataset & live
    if mentions_compare or (mentions_dataset and mentions_live):
        return {"source": "both", "should_fuse": True}

    # Explicit live-only question (e.g., "What is Bitcoin's current CoinGecko market rank?")
    if mentions_live and not mentions_dataset:
        return {"source": "live", "should_fuse": False}

    # Explicit dataset-only question (e.g., "What is Bitcoin's 30-day trading volume?")
    return {"source": "dataset", "should_fuse": True}


# ============================================================
# 3. LIVE COINGECKO API CALLS (/coins/markets + /global)
# ============================================================

def fetch_coingecko_markets_and_global(
    crypto_ids: list = None,
    vs_currency: str = "usd",
    include_dominance: bool = False
) -> dict:
    headers = {"accept": "application/json"}
    api_key = os.getenv("COINGECKO_API_KEY")
    if api_key:
        headers["x-cg-demo-api-key"] = api_key

    markets_by_id = {}
    markets_by_symbol = {}
    top_markets_list = []
    dominance_by_symbol = {}

    try:
        params = {
            "vs_currency": vs_currency.lower(),
            "order": "market_cap_desc",
            "per_page": 100,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "1y"
        }
        if crypto_ids:
            params["ids"] = ",".join(crypto_ids)

        resp = requests.get(COINGECKO_MARKETS_URL, params=params, headers=headers, timeout=20)
        resp.raise_for_status()
        market_data = resp.json()

        if isinstance(market_data, list):
            top_markets_list = market_data
            for item in market_data:
                cid = str(item.get("id", "")).lower()
                sym = str(item.get("symbol", "")).upper()
                markets_by_id[cid] = item
                if sym not in markets_by_symbol:
                    markets_by_symbol[sym] = item

    except Exception as error:
        print("CoinGecko /coins/markets error:", error)
        return {
            "success": False,
            "message": f"CoinGecko API error: {error}",
            "markets_by_id": {},
            "markets_by_symbol": {},
            "top_markets_list": [],
            "dominance_by_symbol": {}
        }

    if include_dominance:
        try:
            g_resp = requests.get(COINGECKO_GLOBAL_URL, headers=headers, timeout=20)
            g_resp.raise_for_status()
            g_data = g_resp.json().get("data", {})
            pct_map = g_data.get("market_cap_percentage", {})
            if isinstance(pct_map, dict):
                dominance_by_symbol = {
                    str(k).upper(): float(v)
                    for k, v in pct_map.items()
                    if v is not None
                }
        except Exception as error:
            print("CoinGecko /global error:", error)

    return {
        "success": True,
        "markets_by_id": markets_by_id,
        "markets_by_symbol": markets_by_symbol,
        "top_markets_list": top_markets_list,
        "dominance_by_symbol": dominance_by_symbol
    }


# ============================================================
# 4. DATASET LOOKUP & FORMATTING HELPERS
# ============================================================

def load_crypto_dataset() -> tuple:
    if not os.path.exists(COINGECKO_CRYPTO_CSV):
        return None, f"CoinGecko crypto dataset not found at {COINGECKO_CRYPTO_CSV}."

    try:
        df = pd.read_csv(COINGECKO_CRYPTO_CSV, low_memory=False, encoding="utf-8-sig")
        df.columns = [
            str(col).replace("\ufeff", "").replace("\xa0", " ").strip()
            for col in df.columns
        ]

        missing = [col for col in COINGECKO_CSV_COLUMNS if col not in df.columns]
        if missing:
            return None, "The CoinGecko CSV is missing required columns: " + ", ".join(missing)

        df["_norm_symbol"] = df["Symbol"].astype(str).str.strip().str.upper()
        return df, None
    except Exception as error:
        return None, f"Unable to read crypto_dataset.csv: {error}"


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


def _format_val(val, is_currency: bool = False, curr_upper: str = "USD") -> str:
    num = _to_float(val)
    if num is None:
        return "N/A"
    if is_currency:
        if abs(num) >= 1:
            return f"{num:,.2f} {curr_upper}"
        return f"{num:,.6f} {curr_upper}"
    if num.is_integer():
        return f"{int(num):,}"
    return f"{num:,.4f}"


def _extract_live_metric_value(sym_upper: str, cid: str, metric: dict, live_bundle: dict):
    if metric["key"] == "dominance":
        return live_bundle.get("dominance_by_symbol", {}).get(sym_upper)

    api_field = metric.get("api_field")
    if not api_field:
        return None

    item = (
        live_bundle.get("markets_by_id", {}).get(cid)
        or live_bundle.get("markets_by_symbol", {}).get(sym_upper)
    )
    if not item:
        return None
    return item.get(api_field)


# ============================================================
# 5. ANSWER BUILDERS
# ============================================================

def handle_dataset_wide_query(question: str, df: pd.DataFrame, metric: dict, mode: dict, vs_currency: str):
    q = question.lower()
    curr_upper = vs_currency.upper()
    is_diff_query = any(w in q for w in ("difference", "biggest", "largest gap", "discrepancy"))

    df_unique = df.drop_duplicates(subset=["_norm_symbol"]).copy()
    symbol_to_id = {
        sym: COINGECKO_ID_MAPPING[sym]
        for sym in df_unique["_norm_symbol"]
        if sym in COINGECKO_ID_MAPPING
    }

    fetch_ids = list(symbol_to_id.values()) if is_diff_query else None
    live_bundle = fetch_coingecko_markets_and_global(
        crypto_ids=fetch_ids,
        vs_currency=vs_currency,
        include_dominance=(metric["key"] == "dominance")
    )

    if not live_bundle.get("success"):
        return live_bundle.get("message", "CoinGecko live API unavailable."), pd.DataFrame(columns=COINGECKO_CSV_COLUMNS)

    # Case A: Highest according to CoinGecko
    if not is_diff_query:
        if metric["key"] == "dominance":
            dom_map = live_bundle.get("dominance_by_symbol", {})
            if not dom_map:
                return "Unable to retrieve global market dominance from CoinGecko.", pd.DataFrame(columns=COINGECKO_CSV_COLUMNS)
            top_sym, top_dom = max(dom_map.items(), key=lambda x: x[1])
            matched_rows = df[df["_norm_symbol"] == top_sym].drop(columns=["_norm_symbol"], errors="ignore")
            ds_val = matched_rows.iloc[0][metric["csv_col"]] if not matched_rows.empty else None

            lines = [f"**Highest {metric['label']} (Live CoinGecko):** {top_sym} at **{top_dom:.2f}%**"]
            if mode["source"] == "both" and not matched_rows.empty:
                lines.append(f"- **Dataset {metric['label']} (`{COINGECKO_CRYPTO_CSV}`):** {_format_val(ds_val, False)}%")
            return "\n".join(lines), matched_rows

        top_list = live_bundle.get("top_markets_list", [])
        api_field = metric.get("api_field")
        valid_items = [item for item in top_list if item.get(api_field) is not None]
        if not valid_items:
            return f"Unable to determine highest {metric['label']} from CoinGecko.", pd.DataFrame(columns=COINGECKO_CSV_COLUMNS)

        best_item = max(valid_items, key=lambda x: float(x[api_field]))
        best_sym = str(best_item.get("symbol", "")).upper()
        best_name = best_item.get("name", best_sym)
        best_live_val = best_item.get(api_field)

        matched_rows = df[df["_norm_symbol"] == best_sym].drop(columns=["_norm_symbol"], errors="ignore")
        ds_val = matched_rows.iloc[0][metric["csv_col"]] if (not matched_rows.empty and metric.get("csv_col")) else None

        lines = [
            f"**Highest {metric['label']} (Live CoinGecko):** {best_name} ({best_sym})",
            f"- **Live CoinGecko {metric['label']}:** {_format_val(best_live_val, metric['is_currency'], curr_upper)}"
        ]
        if mode["source"] == "both" and ds_val is not None:
            lines.append(f"- **Dataset {metric['label']} (`{COINGECKO_CRYPTO_CSV}`):** {_format_val(ds_val, metric['is_currency'], curr_upper)}")
        return "\n".join(lines), matched_rows

    # Case B: Largest difference between Dataset and Live CoinGecko across dataset coins
    comparisons = []
    for _, row in df_unique.iterrows():
        sym = row["_norm_symbol"]
        cid = symbol_to_id.get(sym)
        if not cid or not metric.get("csv_col"):
            continue

        ds_num = _to_float(row.get(metric["csv_col"]))
        live_raw = _extract_live_metric_value(sym, cid, metric, live_bundle)
        live_num = _to_float(live_raw)

        if ds_num is not None and live_num is not None:
            comparisons.append({
                "symbol": sym,
                "name": row.get("Name", sym),
                "ds_val": ds_num,
                "live_val": live_num,
                "diff": abs(live_num - ds_num)
            })

    if not comparisons:
        return (
            f"Could not compute {metric['label']} differences between {COINGECKO_CRYPTO_CSV} and CoinGecko.",
            pd.DataFrame(columns=COINGECKO_CSV_COLUMNS)
        )

    comparisons.sort(key=lambda x: x["diff"], reverse=True)
    winner = comparisons[0]
    matched_rows = df[df["_norm_symbol"] == winner["symbol"]].drop(columns=["_norm_symbol"], errors="ignore")

    lines = [
        f"**Largest {metric['label']} Difference (Dataset vs. CoinGecko):** {winner['name']} ({winner['symbol']})",
        f"- **Dataset {metric['label']}:** {_format_val(winner['ds_val'], metric['is_currency'], curr_upper)}",
        f"- **Live CoinGecko {metric['label']}:** {_format_val(winner['live_val'], metric['is_currency'], curr_upper)}",
        f"- **Absolute Difference:** {_format_val(winner['diff'], metric['is_currency'], curr_upper)}"
    ]

    if len(comparisons) > 1:
        lines.append("\n**Top Comparisons in Dataset:**")
        for item in comparisons[:5]:
            lines.append(
                f"- {item['name']} ({item['symbol']}): Dataset = {_format_val(item['ds_val'], metric['is_currency'], curr_upper)} | "
                f"Live = {_format_val(item['live_val'], metric['is_currency'], curr_upper)} | "
                f"Diff = {_format_val(item['diff'], metric['is_currency'], curr_upper)}"
            )

    return "\n".join(lines), matched_rows


def handle_specific_coins_query(
    question: str,
    df: pd.DataFrame,
    symbols: list,
    metric: dict,
    mode: dict,
    vs_currency: str
):
    curr_upper = vs_currency.upper()
    source_mode = mode["source"]

    live_bundle = {"success": False}
    if source_mode in ("live", "both"):
        crypto_ids = [COINGECKO_ID_MAPPING[s] for s in symbols if s in COINGECKO_ID_MAPPING]
        live_bundle = fetch_coingecko_markets_and_global(
            crypto_ids=crypto_ids,
            vs_currency=vs_currency,
            include_dominance=(metric["key"] == "dominance")
        )

    matched_frames = []
    blocks = []

    for sym in symbols:
        sym_upper = sym.upper()
        cid = COINGECKO_ID_MAPPING.get(sym_upper)

        sub_df = df[df["_norm_symbol"] == sym_upper].drop(columns=["_norm_symbol"], errors="ignore")
        rec = sub_df.iloc[0].to_dict() if not sub_df.empty else None
        if not sub_df.empty:
            matched_frames.append(sub_df[COINGECKO_CSV_COLUMNS].iloc[[0]])

        coin_name = rec.get("Name") if rec else (cid.title() if cid else sym_upper)
        coin_lines = [f"### {coin_name} ({sym_upper})"]

        ds_num = None
        if source_mode in ("dataset", "both") and metric.get("csv_col"):
            ds_raw = rec.get(metric["csv_col"]) if rec else None
            ds_num = _to_float(ds_raw)
            ds_str = _format_val(ds_raw, metric["is_currency"], curr_upper)
            coin_lines.append(f"- **Dataset {metric['label']} (`{COINGECKO_CRYPTO_CSV}`):** {ds_str}")

        live_num = None
        if source_mode in ("live", "both"):
            live_raw = _extract_live_metric_value(sym_upper, cid, metric, live_bundle) if live_bundle.get("success") else None
            live_num = _to_float(live_raw)
            live_str = _format_val(live_raw, metric["is_currency"], curr_upper)
            coin_lines.append(f"- **Live CoinGecko {metric['label']}:** {live_str}")

        if source_mode == "both" and ds_num is not None and live_num is not None:
            delta = live_num - ds_num
            direction = "increased" if delta > 0 else ("decreased" if delta < 0 else "remained unchanged")
            if metric["key"] == "rank":
                direction = "improved (higher rank)" if delta < 0 else ("dropped (lower rank)" if delta > 0 else "remained unchanged")
            coin_lines.append(
                f"- **Comparison:** Live value has **{direction}** by {_format_val(abs(delta), metric['is_currency'], curr_upper)} compared to the dataset."
            )

        blocks.append("\n".join(coin_lines))

    combined_df = (
        pd.concat(matched_frames, ignore_index=True)
        if matched_frames
        else pd.DataFrame(columns=COINGECKO_CSV_COLUMNS)
    )
    return "\n\n".join(blocks), combined_df


# ============================================================
# 6. MAIN ROUTE HANDLER (CALLED BY rag.py)
# ============================================================

def handle_question(question: str):
    df, err = load_crypto_dataset()
    if err:
        return err, []

    symbols, vs_currency = extract_all_crypto_details(question)
    metric = detect_metric(question)
    mode = detect_query_mode(question, metric)

    if symbols:
        answer, matched_df = handle_specific_coins_query(
            question=question,
            df=df,
            symbols=symbols,
            metric=metric,
            mode=mode,
            vs_currency=vs_currency
        )
    else:
        answer, matched_df = handle_dataset_wide_query(
            question=question,
            df=df,
            metric=metric,
            mode=mode,
            vs_currency=vs_currency
        )

    # Fuse ONLY when dataset records are involved
    if mode.get("should_fuse") and not matched_df.empty:
        save_api_answer_and_fuse(
            api_name=API_NAME,
            question=question,
            api_result={"Metric": metric["label"], "Symbols": ",".join(symbols) if symbols else "ALL"},
            answer=answer,
            key_mapping={"original": ["Symbol"], "api": ["Symbol"]},
            original_csv=COINGECKO_CRYPTO_CSV,
            selected_original_df=matched_df
        )

    return answer, []


handle = handle_question