"""
Shared text/PDF helpers used across modules.
No heavy ML dependencies here on purpose (Phase 1) -- everything is
pure-Python / pymupdf / regex so the app stays fast to install and run.
"""

import re
from collections import Counter

import fitz  # pymupdf


def extract_pdf(file_bytes: bytes) -> dict:
    """Extract text + basic metadata from an uploaded PDF (in-memory)."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")

    pages_text = [page.get_text("text") for page in doc]
    full_text = "\n".join(pages_text)

    metadata = doc.metadata or {}
    title_guess = metadata.get("title") or guess_company_name(full_text)

    result = {
        "page_count": doc.page_count,
        "full_text": full_text,
        "pages_text": pages_text,
        "title_guess": title_guess,
        "char_count": len(full_text),
        "word_count": len(full_text.split()),
    }
    doc.close()
    return result


def guess_company_name(text: str) -> str:
    """Very light heuristic: first non-empty, reasonably short line near
    the top of the document is often the filer/company name on SEC-style
    filings and annual reports. This is a placeholder heuristic for
    Phase 1 -- Phase 2 (LLM) can do this far more reliably."""
    for line in text.splitlines():
        clean = line.strip()
        if 3 < len(clean) < 80 and not clean.isdigit():
            return clean
    return "Unknown Company"


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_WORD_RE = re.compile(r"[A-Za-z]{3,}")

_STOPWORDS = set(
    """the a an and or but if while is are was were be been being to of in on for
    with as by at from this that these those it its it's their his her they we you
    your i not no can may will would could should shall must than then so such which
    what when where who whom whose also into over under between within without about
    all any some each other more most any""".split()
)


def naive_summary(text: str, num_sentences: int = 5) -> list:
    """A dependency-free extractive summarizer: scores sentences by the
    frequency of their non-stopword terms and returns the top N in their
    original order. Good enough for a Phase-1 placeholder; swap for a
    proper LLM-based summary in Phase 3/4."""
    sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if len(s.strip()) > 40]
    if not sentences:
        return []

    word_freq = Counter()
    for sentence in sentences:
        for word in _WORD_RE.findall(sentence.lower()):
            if word not in _STOPWORDS:
                word_freq[word] += 1

    scored = []
    for idx, sentence in enumerate(sentences):
        words = [w for w in _WORD_RE.findall(sentence.lower()) if w not in _STOPWORDS]
        score = sum(word_freq[w] for w in words) / (len(words) + 1)
        scored.append((score, idx, sentence))

    top = sorted(scored, reverse=True)[:num_sentences]
    top_in_order = [s for _, _, s in sorted(top, key=lambda x: x[1])]
    return top_in_order


_NUMBER_RE = re.compile(
    r"[\$₹]?\s?\d{1,3}(?:,\d{3})*(?:\.\d+)?\s?(?:million|billion|thousand|crore|lakh|%)?",
    re.IGNORECASE,
)

_FIN_KEYWORDS = [
    "revenue", "profit", "loss", "net income", "assets", "liabilities",
    "equity", "cash flow", "expenses", "ebitda", "margin", "growth",
    "debt", "earnings", "dividend", "operating income",
]


def keyword_frequencies(text: str) -> dict:
    lower = text.lower()
    return {kw: lower.count(kw) for kw in _FIN_KEYWORDS if lower.count(kw) > 0}


def extract_numeric_mentions(text: str, limit: int = 30) -> list:
    matches = [m.strip() for m in _NUMBER_RE.findall(text) if m.strip()]
    # keep only ones that look like real figures (avoid stray page numbers etc.)
    filtered = [m for m in matches if any(c.isdigit() for c in m) and len(m) > 1]
    return filtered[:limit]


def simple_keyword_search(text: str, query: str, context_chars: int = 160) -> list:
    """Phase-1 'AI assistant' fallback: plain keyword search with
    surrounding context, before real embeddings/RAG land in Phase 2."""
    if not query.strip():
        return []
    results = []
    lower_text = text.lower()
    lower_query = query.lower().strip()
    start = 0
    while True:
        idx = lower_text.find(lower_query, start)
        if idx == -1:
            break
        snippet_start = max(0, idx - context_chars // 2)
        snippet_end = min(len(text), idx + len(query) + context_chars // 2)
        snippet = text[snippet_start:snippet_end].replace("\n", " ").strip()
        results.append(f"...{snippet}...")
        start = idx + len(query)
        if len(results) >= 8:
            break
    return results
