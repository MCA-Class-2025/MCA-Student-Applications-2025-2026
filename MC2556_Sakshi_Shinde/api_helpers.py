import requests


def fetch_news_articles(query: str, api_key: str) -> tuple[bool, str]:
    """Fetch top news articles from NewsAPI."""
    if not api_key:
        return False, "NewsAPI key is missing."
    try:
        response = requests.get(
            "https://newsapi.org/v2/everything",
            params={"q": query, "pageSize": 5, "sortBy": "relevance", "apiKey": api_key},
            timeout=10,
        )
        data = response.json()
        if response.status_code != 200:
            return False, f"NewsAPI Error: {data.get('message', response.status_code)}"
        articles = data.get("articles", [])
        if not articles:
            return False, f"No articles found for '{query}'."
        out = [f"=== NEWS RESULTS: {query} ===", f"Source: NewsAPI | Total Results: {data.get('totalResults', 0)}"]
        for i, art in enumerate(articles, 1):
            out += [
                f"--- Article {i} ---",
                f"Title: {art.get('title', 'No Title')}",
                f"Source: {art.get('source', {}).get('name', 'Unknown')}",
                f"Published: {art.get('publishedAt', 'Unknown')}",
                f"Summary: {art.get('description') or 'No description available.'}",
            ]
        return True, "\n".join(out)
    except Exception as exc:
        return False, f"NewsAPI request failed: {exc}"


def fetch_fred_series(series_id: str, api_key: str) -> tuple[bool, str]:
    """Fetch recent observations for a FRED economic series."""
    if not api_key:
        return False, "FRED API key is missing."
    try:
        response = requests.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={
                "series_id": series_id.strip().upper(),
                "api_key": api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 12,
            },
            timeout=10,
        )
        data = response.json()
        if response.status_code != 200:
            return False, f"FRED Error: {data.get('error_message', response.status_code)}"
        observations = data.get("observations", [])
        if not observations:
            return False, f"No FRED observations found for {series_id}."
        out = [f"=== FRED SERIES: {series_id.upper()} ===", "Source: Federal Reserve Bank of St. Louis (FRED)"]
        for obs in observations:
            out.append(f"Date: {obs.get('date')} | Value: {obs.get('value')}")
        return True, "\n".join(out)
    except Exception as exc:
        return False, f"FRED request failed: {exc}"


def fetch_exchange_rates(base_currency: str, api_key: str, target_currency: str = "INR") -> tuple[bool, str]:
    """Fetch current exchange-rate data using ExchangeRate-API."""
    if not api_key:
        return False, "ExchangeRate API key is missing."
    base = base_currency.strip().upper()
    target = target_currency.strip().upper()
    try:
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if response.status_code != 200 or data.get("result") != "success":
            return False, f"ExchangeRate API Error: {data.get('error-type', response.status_code)}"
        rates = data.get("conversion_rates", {})
        if target not in rates:
            return False, f"Target currency {target} is unavailable for base {base}."
        return True, (
            f"=== EXCHANGE RATE ===\n"
            f"Source: ExchangeRate-API\n"
            f"1 {base} = {rates[target]} {target}\n"
            f"Last update: {data.get('time_last_update_utc', 'Unknown')}"
        )
    except Exception as exc:
        return False, f"ExchangeRate request failed: {exc}"


def fetch_world_bank_indicator(
    country_code: str,
    indicator_code: str,
    per_page: int = 10,
) -> tuple[bool, str]:
    """Fetch recent World Bank indicator observations (no API key required)."""
    country = country_code.strip().upper()
    indicator = indicator_code.strip().upper()
    try:
        response = requests.get(
            f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}",
            params={"format": "json", "per_page": per_page, "date": "2015:2024"},
            timeout=15,
        )
        if response.status_code != 200:
            return False, f"World Bank API Error: HTTP {response.status_code}"
        data = response.json()
        if not isinstance(data, list) or len(data) < 2:
            return False, f"No World Bank data returned for {country}/{indicator}."
        meta, observations = data[0], data[1]
        if not observations:
            return False, f"No observations found for {country}/{indicator}."
        indicator_name = observations[0].get("indicator", {}).get("value", indicator)
        country_name = observations[0].get("country", {}).get("value", country)
        out = [
            f"=== WORLD BANK INDICATOR: {indicator} ===",
            f"Source: World Bank Open Data API",
            f"Country: {country_name} ({country})",
            f"Indicator: {indicator_name}",
            f"Total available records: {meta.get('total', len(observations))}",
        ]
        for obs in observations:
            value = obs.get("value")
            value_str = f"{value:,.4f}" if isinstance(value, (int, float)) else (value or "N/A")
            out.append(f"Year: {obs.get('date')} | Value: {value_str}")
        return True, "\n".join(out)
    except Exception as exc:
        return False, f"World Bank request failed: {exc}"


def fetch_alpha_vantage_quote(symbol: str, api_key: str) -> tuple[bool, str]:
    """Fetch a live stock quote from Alpha Vantage."""
    if not api_key:
        return False, "Alpha Vantage API key is missing."
    sym = symbol.strip().upper()
    try:
        response = requests.get(
            "https://www.alphavantage.co/query",
            params={"function": "GLOBAL_QUOTE", "symbol": sym, "apikey": api_key},
            timeout=15,
        )
        data = response.json()
        if "Error Message" in data:
            return False, f"Alpha Vantage Error: {data['Error Message']}"
        if "Note" in data:
            return False, f"Alpha Vantage Rate Limit: {data['Note']}"
        quote = data.get("Global Quote", {})
        if not quote:
            return False, f"No quote data found for symbol '{sym}'."
        out = [
            f"=== ALPHA VANTAGE QUOTE: {sym} ===",
            "Source: Alpha Vantage GLOBAL_QUOTE",
            f"Symbol: {quote.get('01. symbol', sym)}",
            f"Open: {quote.get('02. open', 'N/A')}",
            f"High: {quote.get('03. high', 'N/A')}",
            f"Low: {quote.get('04. low', 'N/A')}",
            f"Price: {quote.get('05. price', 'N/A')}",
            f"Volume: {quote.get('06. volume', 'N/A')}",
            f"Latest Trading Day: {quote.get('07. latest trading day', 'N/A')}",
            f"Previous Close: {quote.get('08. previous close', 'N/A')}",
            f"Change: {quote.get('09. change', 'N/A')} ({quote.get('10. change percent', 'N/A')})",
        ]
        return True, "\n".join(out)
    except Exception as exc:
        return False, f"Alpha Vantage request failed: {exc}"


def convert_currency(amount: float, base_currency: str, target_currency: str, api_key: str) -> tuple[bool, str, float | None]:
    """Convert an entered amount using the live ExchangeRate-API rate."""
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return False, "Amount must be numeric.", None
    if amount < 0:
        return False, "Amount cannot be negative.", None
    base = base_currency.strip().upper(); target = target_currency.strip().upper()
    ok, raw = fetch_exchange_rates(base, api_key, target)
    if not ok:
        return False, raw, None
    # Re-request structured rate so conversion isn't parsed from display text.
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base}"
    try:
        response = requests.get(url, timeout=10); data=response.json()
        rate=float(data['conversion_rates'][target]); converted=amount*rate
        return True, f"{amount:,.2f} {base} = {converted:,.2f} {target}\n1 {base} = {rate:,.6f} {target}\nUpdated: {data.get('time_last_update_utc','Unknown')}", converted
    except Exception as exc:
        return False, f"Conversion failed: {exc}", None
