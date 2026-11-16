"""
llm/intelligence.py — LLM Intelligence Layer.

Sits ON TOP of the existing pipeline: it understands the medicine and the data
returned by all five APIs, extracts structured drug intelligence with the LLM,
and fuses everything into a single CSV file.

Two CSV outputs are produced in data/fused/:
  1. <drug>_llm_intelligence.csv  — one row per drug, LLM-curated fields from all 5 sources
  2. <drug>_all_sources.csv       — every cleaned record from all 5 sources merged
                                    into a single flat CSV (with source attribution)

Gracefully falls back to a heuristic (rule-based) record when the LLM is
unavailable or fails, so the fused CSV is always produced.
"""

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from config.settings import FUSED_DIR
from llm.client import LLMClient
from llm.prompts import INTELLIGENCE_SYSTEM_PROMPT, INTELLIGENCE_USER_PROMPT
from preprocessing.normalization import normalize_drug_name
from utils.logging import logger
from utils.validation import truncate_text


# ── Schema of the LLM-extracted record ────────────────────────────────────────

RECORD_SCHEMA: List[str] = [
    "drug_name", "generic_name", "brand_names", "drug_class",
    "mechanism_of_action", "therapeutic_uses", "boxed_warning",
    "warnings", "contraindications", "precautions", "drug_interactions",
    "storage_instructions", "dosage_forms", "top_adverse_reactions",
    "safety_summary", "recall_summary", "research_highlights",
    "trial_highlights", "known_risks", "data_gaps", "sources_used",
]

_LIST_FIELDS = {
    "brand_names", "therapeutic_uses", "dosage_forms", "known_risks",
    "data_gaps", "sources_used",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v) for v in value if v is not None and str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value).strip()


def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_json_response(content: str) -> Optional[Dict[str, Any]]:
    """Robustly extract a JSON object from an LLM response."""
    if not content:
        return None
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else None
    except (ValueError, TypeError):
        pass
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group())
            return parsed if isinstance(parsed, dict) else None
        except (ValueError, TypeError):
            return None
    return None


# ── Data digest builder ───────────────────────────────────────────────────────

def build_data_digest(
    drug_name: str,
    rxnorm_data: Dict,
    openfda_data: Dict,
    dailymed_data: Dict,
    pubmed_data: Dict,
    ct_data: Dict,
    max_chars: int = 9000,
) -> str:
    """
    Build a compact, LLM-friendly textual digest of every API payload.
    Long fields are truncated so the whole digest stays inside the model context.
    """
    lines: List[str] = []
    lines.append(f"DRUG QUERIED: {drug_name}")

    # ── RxNorm ──────────────────────────────────────────────────────────
    norm = rxnorm_data.get("normalized", {}) if rxnorm_data else {}
    lines.append("\n[1] RxNorm (drug identity)")
    lines.append(f"  Canonical name: {norm.get('name') or 'N/A'}")
    lines.append(f"  RxCUI: {norm.get('rxcui') or 'N/A'} | match status: {norm.get('status') or 'N/A'}")
    ingredients = rxnorm_data.get("active_ingredients", []) if rxnorm_data else []
    lines.append(f"  Active ingredients: {', '.join(i.get('name', '') for i in ingredients[:8]) or 'N/A'}")
    brands = rxnorm_data.get("brand_names", []) if rxnorm_data else []
    lines.append(f"  Brand names: {', '.join(b.get('name', '') for b in brands[:12]) or 'N/A'}")
    classes = rxnorm_data.get("drug_classes", []) if rxnorm_data else []
    class_names = list(dict.fromkeys(c.get("class_name", "") for c in classes if c.get("class_name")))
    lines.append(f"  Drug classes: {', '.join(class_names[:10]) or 'N/A'}")

    # ── openFDA ─────────────────────────────────────────────────────────
    lines.append("\n[2] openFDA (FDA labels, adverse events, recalls)")
    labels = openfda_data.get("labels", {}) if openfda_data else {}
    label_records = labels.get("records", [])
    lines.append(f"  Label records retrieved: {len(label_records)}")
    if label_records:
        rec = label_records[0]
        for key, label in (
            ("brand_name", "Brand name"), ("generic_name", "Generic name"),
            ("manufacturer_name", "Manufacturer"), ("substance_name", "Substances"),
        ):
            val = rec.get(key)
            if val:
                val_text = ", ".join(val) if isinstance(val, list) else str(val)
                lines.append(f"  {label}: {truncate_text(val_text, 200)}")
        boxed = rec.get("boxed_warning", "")
        if boxed:
            lines.append(f"  BOXED WARNING: {truncate_text(boxed, 400)}")

    adverse = openfda_data.get("adverse_events", {}) if openfda_data else {}
    ae_total = adverse.get("total")
    lines.append(f"  Adverse events: total in DB={ae_total if ae_total is not None else len(adverse.get('records', []))}, records retrieved={len(adverse.get('records', []))}")
    top_ae = openfda_data.get("top_adverse_reactions", []) if openfda_data else []
    if top_ae:
        ae_line = ", ".join(
            f"{r.get('term', '')} ({r.get('count', 0)})" for r in top_ae[:15]
        )
        lines.append(f"  Top adverse reactions (term, count): {ae_line}")

    recalls = openfda_data.get("recalls", {}) if openfda_data else {}
    recall_records = recalls.get("records", [])
    lines.append(f"  Recalls: total in DB={recalls.get('total') or len(recall_records)}, records retrieved={len(recall_records)}")
    for r in recall_records[:5]:
        lines.append(
            f"    - [{r.get('classification', '?')}] {truncate_text(r.get('recalling_firm', ''), 60)}: "
            f"{truncate_text(r.get('reason_for_recall', ''), 160)}"
        )

    # ── DailyMed ────────────────────────────────────────────────────────
    lines.append("\n[3] DailyMed (official FDA-approved labeling)")
    if dailymed_data and dailymed_data.get("retrieval_ok"):
        lines.append(f"  Labeler: {dailymed_data.get('labeler') or 'N/A'} | published: {dailymed_data.get('published_date') or 'N/A'} | SPLs: {len(dailymed_data.get('spls', []))}")
        for key in ("indications", "dosage", "warnings", "contraindications",
                    "precautions", "adverse_reactions", "interactions", "storage"):
            val = dailymed_data.get(key, "")
            if val:
                lines.append(f"  {key.replace('_', ' ').capitalize()}: {truncate_text(val, 500)}")
    else:
        lines.append("  No DailyMed label retrieved.")

    # ── PubMed ──────────────────────────────────────────────────────────
    articles = pubmed_data.get("articles", []) if pubmed_data else []
    lines.append(f"\n[4] PubMed (research literature) — articles retrieved: {len(articles)}")
    for art in articles[:10]:
        year = str(art.get("pub_year") or art.get("pub_date") or "?")
        title = truncate_text(art.get("title", ""), 140)
        lines.append(f"  - [{year}] {title} (journal: {truncate_text(art.get('journal', ''), 40)})")

    # ── ClinicalTrials.gov ──────────────────────────────────────────────
    trials = ct_data.get("trials", []) if ct_data else []
    total_trials = ct_data.get("total", len(trials)) if ct_data else len(trials)
    lines.append(f"\n[5] ClinicalTrials.gov — total in registry: {total_trials}, records retrieved: {len(trials)}")
    for t in trials[:10]:
        lines.append(
            f"  - [{t.get('status', '?')}] {t.get('phase', '?')} | "
            f"{truncate_text(t.get('title', ''), 120)} | sponsor: {truncate_text(t.get('lead_sponsor', ''), 50)}"
        )

    digest = "\n".join(lines)
    return digest[:max_chars]


# ── Heuristic fallback (no LLM available) ─────────────────────────────────────

def build_heuristic_record(
    drug_name: str,
    rxnorm_data: Dict,
    openfda_data: Dict,
    dailymed_data: Dict,
    pubmed_data: Dict,
    ct_data: Dict,
) -> Dict[str, Any]:
    """Build a best-effort intelligence record from the raw payloads directly."""
    norm = rxnorm_data.get("normalized", {}) if rxnorm_data else {}
    ingredients = rxnorm_data.get("active_ingredients", []) if rxnorm_data else []
    brands = rxnorm_data.get("brand_names", []) if rxnorm_data else []
    classes = rxnorm_data.get("drug_classes", []) if rxnorm_data else []
    label_records = (openfda_data.get("labels", {}).get("records", []) or []) if openfda_data else []
    top_ae = openfda_data.get("top_adverse_reactions", []) if openfda_data else []
    recall_records = (openfda_data.get("recalls", {}).get("records", []) or []) if openfda_data else []
    articles = pubmed_data.get("articles", []) if pubmed_data else []
    trials = ct_data.get("trials", []) if ct_data else []

    first_label = label_records[0] if label_records else {}

    def _list_join(items: List[Any], key: str) -> List[str]:
        return [i.get(key, "") for i in items if i.get(key, "")]

    def _dedupe(names: List[str]) -> List[str]:
        seen = set()
        out = []
        for n in names:
            key = n.strip().lower()
            if key and key not in seen:
                seen.add(key)
                out.append(n.strip())
        return out

    def _first_sentences(text: str, max_chars: int = 300, n_sentences: int = 2) -> str:
        text = re.sub(r"\s+", " ", text or "").strip()
        if not text:
            return ""
        parts = re.split(r"(?<=[.!?])\s+", text)
        short = " ".join(parts[:n_sentences]).strip()
        return truncate_text(short, max_chars)

    reactions = [
        {
            "reaction": r.get("term", ""),
            "report_count": r.get("count"),
            "signal_strength": "high" if (r.get("count") or 0) >= 50 else (
                "moderate" if (r.get("count") or 0) >= 10 else "low"
            ),
            "notes": "Reported count in FAERS database.",
        }
        for r in top_ae[:15] if r.get("term")
    ]

    ae_total = 0
    if openfda_data:
        ae_total = openfda_data.get("adverse_events", {}).get("total") or 0

    recall_text = "No recall records found in the openFDA enforcement database."
    if recall_records:
        recall_text = f"{len(recall_records)} recall record(s) retrieved; top reasons: " + "; ".join(
            truncate_text(r.get("reason_for_recall", ""), 120) for r in recall_records[:3]
        )

    # Clean therapeutic uses: prefer DailyMed indications, else label text,
    # always condensed to a few sentences — never raw label dumps.
    generic_name = norm.get("name") or first_label.get("generic_name", "")
    uses: List[str] = []
    if dailymed_data and dailymed_data.get("indications"):
        uses.append(_first_sentences(dailymed_data["indications"]))
    for r in label_records:
        ind = r.get("indications_and_usage", "")
        if ind:
            uses.append(_first_sentences(ind))
    uses = _dedupe(uses)[:5]

    brand_names = _dedupe([b.get("name", "") for b in brands] + _list_join(label_records, "brand_name"))
    brand_names = [b for b in brand_names if b.lower() != generic_name.lower()][:10]

    return {
        "drug_name": drug_name,
        "generic_name": generic_name,
        "brand_names": brand_names,
        "drug_class": " ".join(dict.fromkeys(c.get("class_name", "") for c in classes)) or "",
        "mechanism_of_action": "",
        "therapeutic_uses": uses,
        "boxed_warning": first_label.get("boxed_warning", "") or "",
        "warnings": (dailymed_data.get("warnings", "") if dailymed_data else "") or first_label.get("warnings", ""),
        "contraindications": (dailymed_data.get("contraindications", "") if dailymed_data else "") or first_label.get("contraindications", ""),
        "precautions": (dailymed_data.get("precautions", "") if dailymed_data else "") or first_label.get("precautions", ""),
        "drug_interactions": (dailymed_data.get("interactions", "") if dailymed_data else "") or "",
        "storage_instructions": (dailymed_data.get("storage", "") if dailymed_data else "") or first_label.get("storage_and_handling", ""),
        "dosage_forms": [],
        "top_adverse_reactions": reactions,
        "safety_summary": (
            f"Retrieved {ae_total:,} adverse event report(s) and {len(recall_records)} recall "
            f"record(s) for {drug_name}. "
            f"Reporting activity classification and safety analysis are available in the "
            f"Safety Analytics page. This is informational analysis only — consult a "
            f"qualified healthcare professional for medical decisions."
        ),
        "recall_summary": recall_text,
        "research_highlights": (
            f"{len(articles)} research article(s) retrieved from PubMed. "
            "See Research & Trials page for literature analysis."
            if articles else "No research articles retrieved from PubMed."
        ),
        "trial_highlights": (
            f"{len(trials)} clinical trial record(s) retrieved from ClinicalTrials.gov "
            f"(total in registry: {ct_data.get('total', len(trials)) if ct_data else len(trials)}). "
            "See Research & Trials page for trial analysis."
            if trials else "No clinical trial records retrieved."
        ),
        "known_risks": [],
        "data_gaps": [
            "LLM intelligence layer unavailable (no GROQ_API_KEY or OPENAI_API_KEY configured); record built heuristically from raw API data."
        ],
        "sources_used": sorted([
            s for s, ok in (
                ("RxNorm", bool(rxnorm_data and rxnorm_data.get("retrieval_ok"))),
                ("openFDA", bool(openfda_data and openfda_data.get("retrieval_ok"))),
                ("DailyMed", bool(dailymed_data and dailymed_data.get("retrieval_ok"))),
                ("PubMed", bool(pubmed_data and pubmed_data.get("retrieval_ok"))),
                ("ClinicalTrials.gov", bool(ct_data and ct_data.get("retrieval_ok"))),
            ) if ok
        ]),
    }


# ── Record → CSV row (with source-attributed column names) ────────────────────

# Provenance of every LLM-intelligence field (which API(s) it was derived from)
FIELD_SOURCES: Dict[str, str] = {
    "drug_name": "User input",
    "generic_name": "RxNorm + openFDA labels",
    "brand_names": "RxNorm (brand relationships) + openFDA labels",
    "drug_class": "RxNorm (RxClass)",
    "mechanism_of_action": "LLM synthesis from DailyMed/openFDA labeling",
    "therapeutic_uses": "DailyMed SPL + openFDA labels",
    "boxed_warning": "openFDA (FDA SPL)",
    "warnings": "DailyMed SPL (+ openFDA labels)",
    "contraindications": "DailyMed SPL (+ openFDA labels)",
    "precautions": "DailyMed SPL (+ openFDA labels)",
    "drug_interactions": "DailyMed SPL",
    "storage_instructions": "DailyMed SPL (+ openFDA labels)",
    "dosage_forms": "LLM synthesis from labels + trials",
    "top_adverse_reactions": "openFDA (FAERS)",
    "safety_summary": "LLM synthesis across all sources",
    "recall_summary": "openFDA (enforcement database)",
    "research_highlights": "PubMed (research literature)",
    "trial_highlights": "ClinicalTrials.gov",
    "known_risks": "LLM synthesis from labeling + FAERS",
    "data_gaps": "LLM synthesis",
    "sources_used": "Pipeline source-status report",
}

_SOURCE_NAMES = {
    "identity": "RxNorm",
    "labels": "openFDA (drug labels)",
    "adverse_events": "openFDA (FAERS adverse events)",
    "recalls": "openFDA (enforcement recalls)",
    "dailymed": "DailyMed (official SPL)",
    "articles": "PubMed (research articles)",
    "trials": "ClinicalTrials.gov",
}

_SOURCE_PREFIXES = {
    "identity": "rxnorm",
    "labels": "openfda_labels",
    "adverse_events": "openfda_adverse_events",
    "recalls": "openfda_recalls",
    "dailymed": "dailymed",
    "articles": "pubmed",
    "trials": "clinicaltrials",
}

# Columns that are already source-agnostic in the source DataFrames
_SHARED_COLUMNS = {"drug_name", "source", "source_type", "source_url", "retrieved_at", "source_dataset"}


def _format_value(value: Any) -> str:
    """Flatten any JSON value into a readable CSV cell."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict):
                bits = []
                for k, v in item.items():
                    if v is None or v == "":
                        continue
                    bits.append(f"{k}: {v}")
                parts.append(" | ".join(bits))
            else:
                parts.append(str(item))
        return "; ".join(parts)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def record_to_row(record: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, str]:
    """
    Flatten the LLM record into a single CSV row.

    Every column name carries its provenance:
      - llm_<field>     → LLM-curated field (FIELD_SOURCES explains which APIs)
      - source_<stat>   → raw count/status from that API
      - intelligence_*  → layer metadata
    """
    row: Dict[str, str] = {}
    for key in RECORD_SCHEMA:
        if key == "drug_name":
            row["drug_name"] = _format_value(record.get(key))
        else:
            row[f"llm_{key}"] = _format_value(record.get(key))
    row["intelligence_field_sources"] = json.dumps(
        {f"llm_{k}": v for k, v in FIELD_SOURCES.items()}, ensure_ascii=False
    )
    for key, value in (extra or {}).items():
        row[key] = _format_value(value)
    return row


# ── The LLM Intelligence Layer ────────────────────────────────────────────────

class DrugIntelligenceExtractor:
    """
    Understands the medicine + all five API payloads and fuses them into one CSV.

    run() → {
        "record": {...LLM-extracted intelligence...},
        "csv_path": str,            # single-row fused CSV (LLM record)
        "all_sources_csv_path": str,  # every source record merged into one CSV
        "used_llm": bool,
        "latency_ms": int,
        "error": str|None,
    }
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    # ── Public API ──────────────────────────────────────────────────────

    def run(
        self,
        drug_name: str,
        rxnorm_data: Dict,
        openfda_data: Dict,
        dailymed_data: Dict,
        pubmed_data: Dict,
        ct_data: Dict,
        dataset: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        t0 = time.time()
        safe_name = normalize_drug_name(drug_name).replace(" ", "_")
        logger.info(f"LLM Intelligence Layer: starting for '{drug_name}'")

        result: Dict[str, Any] = {
            "record": {},
            "csv_path": "",
            "all_sources_csv_path": "",
            "used_llm": False,
            "latency_ms": 0,
            "error": None,
        }

        digest = build_data_digest(
            drug_name, rxnorm_data, openfda_data, dailymed_data, pubmed_data, ct_data
        )

        # ── 1. LLM extraction ───────────────────────────────────────────
        record, used_llm, error = self._extract(
            drug_name, digest, rxnorm_data, openfda_data, dailymed_data, pubmed_data, ct_data
        )

        # ── 2. Source statistics for the fused CSV ──────────────────────
        extra = self._source_stats(
            drug_name, rxnorm_data, openfda_data, dailymed_data, pubmed_data, ct_data,
            used_llm=used_llm,
        )

        # ── 3. Fuse everything into ONE CSV (single row per drug) ───────
        row = record_to_row(record, extra)
        csv_path = FUSED_DIR / f"{safe_name}_llm_intelligence.csv"
        try:
            pd.DataFrame([row]).to_csv(csv_path, index=False)
            result["csv_path"] = str(csv_path)
            logger.info(f"LLM intelligence CSV written: {csv_path}")
        except Exception as e:
            logger.warning(f"Could not write intelligence CSV: {e}")
            result["error"] = f"CSV write failed: {e}"

        # ── 4. Clean per-source records fused into ONE CSV ──────────────
        all_sources_path, column_sources = self._write_all_sources_csv(dataset, safe_name)
        if all_sources_path:
            result["all_sources_csv_path"] = all_sources_path
        result["column_sources"] = column_sources

        result["record"] = record
        result["used_llm"] = used_llm
        result["latency_ms"] = round((time.time() - t0) * 1000)
        if error:
            result["error"] = error
        logger.info(
            f"LLM Intelligence Layer complete for '{drug_name}' "
            f"(used_llm={used_llm}, {result['latency_ms']}ms)"
        )
        return result

    # ── Internals ───────────────────────────────────────────────────────

    def _extract(
        self,
        drug_name: str,
        digest: str,
        rxnorm_data: Dict,
        openfda_data: Dict,
        dailymed_data: Dict,
        pubmed_data: Dict,
        ct_data: Dict,
    ) -> Any:
        """LLM extraction with heuristic fallback. Returns (record, used_llm, error)."""
        if not self.llm.is_available:
            logger.info("LLM unavailable — building heuristic intelligence record")
            return build_heuristic_record(
                drug_name, rxnorm_data, openfda_data, dailymed_data, pubmed_data, ct_data
            ), False, "LLM API key not configured"

        messages = [
            {"role": "system", "content": INTELLIGENCE_SYSTEM_PROMPT},
            {"role": "user", "content": INTELLIGENCE_USER_PROMPT.format(
                drug_name=drug_name, digest=digest
            )},
        ]
        try:
            response = self.llm.chat(messages, max_tokens=2000, temperature=0.0)
            if response.get("error"):
                raise RuntimeError(response["error"])
            parsed = _parse_json_response(response.get("content", ""))
            if not parsed:
                raise RuntimeError("LLM returned unparseable content")

            record = {k: parsed.get(k, "") for k in RECORD_SCHEMA}
            for list_field in _LIST_FIELDS:
                record[list_field] = _safe_list(parsed.get(list_field))
            record["top_adverse_reactions"] = _safe_list(parsed.get("top_adverse_reactions"))
            record["drug_name"] = drug_name
            logger.info(f"LLM intelligence extraction OK ({response.get('usage', {}).get('total_tokens', 0)} tokens)")
            return record, True, None
        except Exception as e:
            logger.warning(f"LLM intelligence extraction failed: {e}. Using heuristic fallback.")
            return build_heuristic_record(
                drug_name, rxnorm_data, openfda_data, dailymed_data, pubmed_data, ct_data
            ), False, str(e)

    @staticmethod
    def _source_stats(
        drug_name: str,
        rxnorm_data: Dict,
        openfda_data: Dict,
        dailymed_data: Dict,
        pubmed_data: Dict,
        ct_data: Dict,
        used_llm: bool,
    ) -> Dict[str, Any]:
        """Source-level statistics appended to the fused CSV row."""
        ae_records = (openfda_data.get("adverse_events", {}).get("records", []) or []) if openfda_data else []
        recall_records = (openfda_data.get("recalls", {}).get("records", []) or []) if openfda_data else []
        label_records = (openfda_data.get("labels", {}).get("records", []) or []) if openfda_data else []
        articles = pubmed_data.get("articles", []) if pubmed_data else []
        trials = ct_data.get("trials", []) if ct_data else []

        boxed = any(
            bool(r.get("boxed_warning", "")) for r in label_records
        ) or bool(dailymed_data and dailymed_data.get("warnings", ""))

        active_trials = sum(
            1 for t in trials
            if t.get("status", "") in ("RECRUITING", "ACTIVE_NOT_RECRUITING", "ENROLLING_BY_INVITATION")
        )

        return {
            "rxnorm_rxcui": (rxnorm_data.get("normalized", {}).get("rxcui") if rxnorm_data else None),
            "rxnorm_canonical_name": (rxnorm_data.get("normalized", {}).get("name") if rxnorm_data else ""),
            "source_adverse_event_total": (openfda_data.get("adverse_events", {}).get("total") if openfda_data else 0),
            "source_adverse_event_records": len(ae_records),
            "source_label_records": len(label_records),
            "source_recall_total": (openfda_data.get("recalls", {}).get("total") if openfda_data else 0),
            "source_recall_records": len(recall_records),
            "source_dailymed_ok": bool(dailymed_data and dailymed_data.get("retrieval_ok")),
            "source_pubmed_articles": len(articles),
            "source_trials_total": (ct_data.get("total", len(trials)) if ct_data else len(trials)),
            "source_trials_records": len(trials),
            "source_trials_active": active_trials,
            "has_boxed_warning": boxed,
            "intelligence_used_llm": used_llm,
            "intelligence_generated_at": _now_iso(),
        }

    @staticmethod
    def _write_all_sources_csv(dataset: Optional[Dict], safe_name: str):
        """
        Fuse every CLEAN source DataFrame into ONE flat CSV (long format).

        Rules (per the product requirement — clean, no random data, and the
        source of every attribute is visible):
          - Only columns that actually contain data are kept (no all-NaN blob
            columns from a blind outer-join merge).
          - Every data column is renamed with its source prefix, e.g.
            dailymed_warnings, openfda_labels_brand_name, pubmed_title,
            clinicaltrials_nct_id, rxnorm_rxcui.
          - Every row carries source / source_type attribution.

        Returns (csv_path, column_sources_legend_dict).
        """
        if not dataset:
            return None, {}
        frames = []
        column_sources: Dict[str, str] = {}
        for name, df in (dataset.get("dataframes") or {}).items():
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue
            prefix = _SOURCE_PREFIXES.get(name, name)
            source_name = _SOURCE_NAMES.get(name, name)

            # Keep only columns that have at least one non-null value
            populated = [c for c in df.columns if df[c].notna().any() and df[c].astype(str).str.strip().str.len().sum() > 0]
            sub = df[populated].copy()

            # Rename data columns with their source prefix; keep shared cols as-is
            renamed = {}
            for c in sub.columns:
                if c in _SHARED_COLUMNS:
                    renamed[c] = c
                    column_sources[c] = "All sources (shared metadata column)"
                else:
                    renamed[c] = f"{prefix}_{c}"
                    column_sources[renamed[c]] = source_name
            sub = sub.rename(columns=renamed)

            # Drop redundant per-source columns now duplicated by our attribution
            for c in ("source", "source_type", "source_url", "source_dataset"):
                if c in sub.columns:
                    sub = sub.drop(columns=[c])

            sub.insert(0, "source", source_name)
            sub.insert(1, "source_type", prefix)
            frames.append(sub)

        if not frames:
            return None, {}
        try:
            merged = pd.concat(frames, join="outer", sort=False, ignore_index=True)
            # Replace empty strings/NaN with blank for cleanliness
            merged = merged.fillna("")
            path = FUSED_DIR / f"{safe_name}_all_sources.csv"
            merged.to_csv(path, index=False)
            logger.info(
                f"All-sources fused CSV written: {path} "
                f"({len(merged)} rows, {len(merged.columns)} cols)"
            )
            return str(path), column_sources
        except Exception as e:
            logger.warning(f"Could not write all-sources CSV: {e}")
            return None, {}
