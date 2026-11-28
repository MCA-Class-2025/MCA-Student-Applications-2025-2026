"""Routing for the seven configured external APIs.

Gemini/OpenAI keys are retained for optional integrations, but the chatbot itself
runs in local/offline mode so it does not depend on LLM quotas.
"""
from typing import Any
import re

NEWS_QUERY_KEYWORDS={"latest","recent","current","news","updates","headline","headlines","today","breaking","trending"}
FRED_KEYWORDS={"fred","federal reserve","interest rate","inflation","cpi","gdp","unemployment","economic","economy","treasury","federal funds"}
FX_KEYWORDS={"exchange rate","exchange rates","currency","forex","usd","eur","gbp","inr","dollar","rupee","convert currency"}
WORLDBANK_KEYWORDS={"world bank","worldbank","development indicator","poverty rate","population","gdp growth","country data","indicator"}
ALPHAVANTAGE_KEYWORDS={"alpha vantage","stock price","share price","stock quote","ticker","equity","nasdaq","nyse","market price","trading"}

def _active(reason): return {"active": True, "status": "Active", "reason": reason}
def _inactive(reason): return {"active": False, "status": "Not needed", "reason": reason}

def route_api(document_text: str, user_query: str, entities: dict[str,Any]|None=None, task_hint: str|None=None)->dict[str,Any]:
    q=(user_query or "").lower()
    news=any(k in q for k in NEWS_QUERY_KEYWORDS)
    fred=any(k in q for k in FRED_KEYWORDS)
    fx=any(k in q for k in FX_KEYWORDS)
    worldbank=any(k in q for k in WORLDBANK_KEYWORDS)
    alphavantage=any(k in q for k in ALPHAVANTAGE_KEYWORDS)
    # Gemini/OpenAI are intentionally NOT selected for chatbot answers.
    apis={
      "gemini": _inactive("Available as a configured API, but disabled for chatbot answering to avoid quota dependence."),
      "openai": _inactive("Available as a configured API, but disabled for chatbot answering to avoid quota dependence."),
      "newsapi": _active("Query asks for current/recent news.") if news else _inactive("Not required for this query."),
      "fred": _active("Query asks for economic/FRED data.") if fred else _inactive("Not required for this query."),
      "exchangerate": _active("Query asks for currency/exchange-rate data.") if fx else _inactive("Not required for this query."),
      "worldbank": _active("Query asks for World Bank development/country indicators.") if worldbank else _inactive("Not required for this query."),
      "alphavantage": _active("Query asks for stock/market price data.") if alphavantage else _inactive("Not required for this query."),
    }
    news_terms=[user_query] if news else []
    # Common FRED defaults; user can type a series ID directly (e.g. GDP, CPIAUCSL, UNRATE).
    fred_series=[]
    m=re.search(r"\b[A-Z]{3,12}\b", user_query or "")
    if fred and m: fred_series=[m.group(0)]
    elif fred: fred_series=["GDP"]
    base="USD"
    target="INR"
    if fx:
        currencies=re.findall(r"\b[A-Z]{3}\b", user_query.upper())
        if len(currencies)>=1: base=currencies[0]
        if len(currencies)>=2: target=currencies[1]
    wb_country="IND"
    wb_indicator="NY.GDP.MKTP.CD"
    country_match=re.search(r"\b([A-Z]{2,3})\b", user_query.upper() or "")
    if country_match and country_match.group(1) in {"IN","IND","US","USA","GB","UK","CN","CHN"}:
        code=country_match.group(1)
        wb_country={"IN":"IND","IND":"IND","US":"USA","USA":"USA","GB":"GBR","UK":"GBR","CN":"CHN","CHN":"CHN"}.get(code,"IND")
    indicator_match=re.search(r"\b[A-Z]{2}\.[A-Z0-9._]+\b", user_query.upper() or "")
    if indicator_match:
        wb_indicator=indicator_match.group(0)
    av_symbol="IBM"
    symbol_match=re.search(r"\b[A-Z]{1,5}\b", user_query.upper() or "")
    if alphavantage and symbol_match and symbol_match.group(0) not in {"USD","EUR","GBP","INR","GDP","CPI","API"}:
        av_symbol=symbol_match.group(0)
    return {
        "apis":apis,"news_terms":news_terms,"fred_series":fred_series,"fx_base":base,"fx_target":target,
        "wb_country":wb_country,"wb_indicator":wb_indicator,"av_symbol":av_symbol,
        "task_hint":task_hint or "document_qa",
    }

def format_api_status_sidebar(routing:dict[str,Any])->str:
    labels={"gemini":"Gemini","openai":"OpenAI","newsapi":"NewsAPI","fred":"FRED","exchangerate":"ExchangeRate","worldbank":"World Bank","alphavantage":"Alpha Vantage"}
    lines=["**Configured APIs**\n"]
    for key,label in labels.items():
        info=routing["apis"][key]
        lines.append(f"{'🟢' if info['active'] else '⚪'} **{label}**: {info['status']}")
    return "\n".join(lines)

def fetch_external_context(
    routing:dict[str,Any],
    news_api_key:str,
    fred_api_key:str,
    exchangerate_api_key:str,
    alphavantage_api_key:str="",
)->dict[str,str]:
    from api_helpers import (
        fetch_alpha_vantage_quote,
        fetch_fred_series,
        fetch_news_articles,
        fetch_exchange_rates,
        fetch_world_bank_indicator,
    )
    news_blocks=[]; fred_blocks=[]; fx_blocks=[]; wb_blocks=[]; av_blocks=[]
    if routing["apis"]["newsapi"]["active"]:
        for term in routing.get("news_terms",[])[:1]:
            ok,content=fetch_news_articles(term,news_api_key); news_blocks.append(content if ok else f"[NewsAPI] {content}")
    if routing["apis"]["fred"]["active"]:
        for series in routing.get("fred_series",[])[:1]:
            ok,content=fetch_fred_series(series,fred_api_key); fred_blocks.append(content if ok else f"[FRED] {content}")
    if routing["apis"]["exchangerate"]["active"]:
        ok,content=fetch_exchange_rates(routing.get("fx_base","USD"),exchangerate_api_key,routing.get("fx_target","INR")); fx_blocks.append(content if ok else f"[ExchangeRate] {content}")
    if routing["apis"]["worldbank"]["active"]:
        ok,content=fetch_world_bank_indicator(routing.get("wb_country","IND"),routing.get("wb_indicator","NY.GDP.MKTP.CD"))
        wb_blocks.append(content if ok else f"[World Bank] {content}")
    if routing["apis"]["alphavantage"]["active"]:
        ok,content=fetch_alpha_vantage_quote(routing.get("av_symbol","IBM"),alphavantage_api_key)
        av_blocks.append(content if ok else f"[Alpha Vantage] {content}")
    return {
        "news":"\n\n".join(news_blocks),
        "fred":"\n\n".join(fred_blocks),
        "exchange_rate":"\n\n".join(fx_blocks),
        "worldbank":"\n\n".join(wb_blocks),
        "alphavantage":"\n\n".join(av_blocks),
        "external_insights":"\n\n".join(fred_blocks+fx_blocks+wb_blocks+av_blocks),
    }

def build_combined_response(document_answer:str, external_insights:str="", news_section:str="", sources:list[str]|None=None, routing:dict[str,Any]|None=None)->str:
    parts=["## Document Answer\n", document_answer.strip() if document_answer else "_No document answer generated._"]
    if external_insights.strip(): parts += ["\n\n## Economic / Financial Insights\n",external_insights.strip()]
    if news_section.strip(): parts += ["\n\n## Latest News\n",news_section.strip()]
    parts += ["\n\n## Sources\n"]
    src=list(sources or [])
    if routing:
        for key,label in [("newsapi","NewsAPI"),("fred","FRED"),("exchangerate","ExchangeRate"),("worldbank","World Bank"),("alphavantage","Alpha Vantage")]:
            if routing["apis"][key]["active"]: src.append(f"{label} — {routing['apis'][key]['reason']}")
    parts += ["\n".join(f"{i}. {s}" for i,s in enumerate(dict.fromkeys(src),1)) if src else "1. FAISS vector retrieval + local synthesis"]
    return "".join(parts)
