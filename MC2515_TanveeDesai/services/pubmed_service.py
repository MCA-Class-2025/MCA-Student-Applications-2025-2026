"""
services/pubmed_service.py — PubMed / NCBI E-utilities API service.

Purpose:
- Retrieve scientific literature and research papers
- Publication metadata, abstracts, publication dates
- Research trends for a given medicine / ingredient

API: https://eutils.ncbi.nlm.nih.gov/entrez/eutils
No key required; PUBMED_EMAIL reduces rate-limit chance.
"""

import time
from typing import Any, Dict, List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config.settings import PUBMED_BASE_URL, PUBMED_EMAIL, REQUEST_TIMEOUT, MAX_RETRIES, PUBMED_MAX_RESULTS
from utils.logging import logger
from utils.caching import get_cached, set_cached

_session = requests.Session()
_session.headers.update({"Accept": "application/json"})

_BASE_PARAMS = {"email": PUBMED_EMAIL, "tool": "MedicineSafetyAI"}


class PubMedServiceError(Exception):
    pass


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(requests.RequestException),
    reraise=True,
)
def _get(endpoint: str, params: Dict) -> Any:
    url = f"{PUBMED_BASE_URL}/{endpoint}"
    all_params = {**_BASE_PARAMS, **params}
    resp = _session.get(url, params=all_params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp


# ── Search ────────────────────────────────────────────────────────────────────

def search_pubmed(
    drug_name: str,
    max_results: int = PUBMED_MAX_RESULTS,
    sort: str = "relevance",
) -> List[str]:
    """
    Search PubMed for articles about a drug.
    Returns list of PMIDs.
    """
    cache_key = f"{drug_name.lower()}_{max_results}_{sort}"
    cached = get_cached("pubmed_search", cache_key)
    if cached:
        return cached

    pmids: List[str] = []
    try:
        query = f'"{drug_name}"[Title/Abstract] AND (drug[MeSH Terms] OR pharmacology[MeSH Terms] OR safety[Title/Abstract])'
        resp = _get(
            "esearch.fcgi",
            {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "sort": sort,
            },
        )
        data = resp.json()
        pmids = data.get("esearchresult", {}).get("idlist", [])
        set_cached("pubmed_search", cache_key, pmids)
        logger.info(f"PubMed search for '{drug_name}': {len(pmids)} PMIDs")
    except Exception as e:
        logger.error(f"PubMed search failed for '{drug_name}': {e}")

    return pmids


# ── Fetch Details ─────────────────────────────────────────────────────────────

def fetch_article_details(pmids: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch article metadata + abstracts for a list of PMIDs.
    Returns list of article dicts.
    """
    if not pmids:
        return []

    cache_key = "_".join(sorted(pmids))
    cached = get_cached("pubmed_details", cache_key)
    if cached:
        return cached

    articles: List[Dict[str, Any]] = []
    try:
        # Use efetch with XML, then parse; or use esummary for JSON metadata
        resp = _get(
            "esummary.fcgi",
            {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "json",
            },
        )
        data = resp.json()
        result = data.get("result", {})
        uids = result.get("uids", pmids)

        for uid in uids:
            article_data = result.get(str(uid), {})
            if not article_data or article_data.get("error"):
                continue

            authors = article_data.get("authors", [])
            author_names = [a.get("name", "") for a in authors[:5]]

            articles.append({
                "pmid": uid,
                "title": article_data.get("title", ""),
                "authors": author_names,
                "journal": article_data.get("fulljournalname", ""),
                "pub_date": article_data.get("pubdate", ""),
                "pub_year": _extract_year(article_data.get("pubdate", "")),
                "doi": article_data.get("elocationid", ""),
                "pub_types": article_data.get("pubtype", []),
                "source_url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
            })

        # Fetch abstracts separately using efetch
        if pmids:
            time.sleep(0.3)  # Respect rate limits
            abstract_resp = _get(
                "efetch.fcgi",
                {
                    "db": "pubmed",
                    "id": ",".join(pmids[:10]),  # Limit abstract fetches
                    "retmode": "text",
                    "rettype": "abstract",
                },
            )
            abstract_text = abstract_resp.text
            # Parse abstracts from plain text (each separated by blank lines)
            abstract_blocks = abstract_text.split("\n\n\n")
            for i, article in enumerate(articles[:len(abstract_blocks)]):
                if i < len(abstract_blocks):
                    block = abstract_blocks[i].strip()
                    # Extract abstract portion (after "Abstract" label)
                    if "Abstract" in block:
                        abstract_part = block[block.find("Abstract") + 8:].strip()
                        article["abstract"] = abstract_part[:1500]
                    else:
                        article["abstract"] = ""
                else:
                    article["abstract"] = ""

        set_cached("pubmed_details", cache_key, articles)
        logger.info(f"PubMed fetched details for {len(articles)} articles")

    except Exception as e:
        logger.error(f"PubMed fetch_article_details failed: {e}")

    return articles


def _extract_year(pub_date: str) -> Optional[int]:
    """Extract 4-digit year from PubMed date string."""
    import re
    match = re.search(r"\b(19|20)\d{2}\b", pub_date)
    if match:
        return int(match.group())
    return None


# ── Full Drug Info ────────────────────────────────────────────────────────────

def get_full_drug_info(drug_name: str, ingredient_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Collect PubMed research information for a drug.
    Uses ingredient name for broader search if available.
    """
    search_term = ingredient_name or drug_name

    result: Dict[str, Any] = {
        "source": "PubMed",
        "source_url": "https://pubmed.ncbi.nlm.nih.gov",
        "drug_name": drug_name,
        "search_term": search_term,
        "articles": [],
        "total_found": 0,
        "pub_year_distribution": {},
        "error": None,
        "retrieval_ok": False,
    }

    try:
        pmids = search_pubmed(search_term)
        result["total_found"] = len(pmids)

        if pmids:
            articles = fetch_article_details(pmids)
            result["articles"] = articles
            result["retrieval_ok"] = True

            # Year distribution
            year_dist: Dict[int, int] = {}
            for art in articles:
                year = art.get("pub_year")
                if year:
                    year_dist[year] = year_dist.get(year, 0) + 1
            result["pub_year_distribution"] = year_dist

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"PubMed full info failed for '{drug_name}': {e}")

    return result
