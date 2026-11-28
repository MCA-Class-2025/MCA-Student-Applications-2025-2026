"""
PolicyPal - Phase 1 (Parts A-E) assets.

Uses ONLY files already in the project (no API calls):
  data/raw/*                         original policy knowledge base (Part A)
  vectorstore/metadata.pkl           RAG chunks built from the knowledge base
  data/api_cache/*.json              raw API responses saved by src/policy_data_fusion.py
  data/PolicyPal_Master_Dataset.xlsx fused dataset (Part C output)

Writes:
  data/PolicyPal_Before_Fusion_Source_Tables.xlsx   one sheet per source, before fusion
  reports/phase1/figures/*.png                      charts
  reports/phase1/stats.json                         every number quoted in the report

The NewsData request log is reconstructed by recomputing the cache file name of
every (country, topic) request. That needs NEWSDATA_API_KEY in the environment
(the same variable the pipeline uses); the key is only hashed locally.
"""
from __future__ import annotations

import hashlib
import json
import os
import pickle
import re
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.fusion_config import COUNTRIES, POLICY_TOPICS  # noqa: E402

RAW = ROOT / "data" / "raw"
CACHE = ROOT / "data" / "api_cache"
MASTER_XLSX = ROOT / "data" / "PolicyPal_Master_Dataset.xlsx"
BEFORE_XLSX = ROOT / "data" / "PolicyPal_Before_Fusion_Source_Tables.xlsx"
OUT = Path(__file__).resolve().parent
FIG = OUT / "figures"
FIG.mkdir(parents=True, exist_ok=True)

NAGER_URL = "https://nagerholidays.com/api/v4/Holidays/{country}/{year}"
COUNTRY_URL = "https://countries.dev/alpha/{country_code}"
GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WX_URL = "https://api.open-meteo.com/v1/forecast"
FX_URL = "https://open.er-api.com/v6/latest/USD"
NEWS_URL = "https://newsdata.io/api/1/news"

BLUE, ORANGE, GREY, RED, GREEN = "#2a78d6", "#eb6834", "#b5b3ad", "#e34948", "#1baf7a"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e0"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID,
    "axes.labelcolor": INK2, "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.titlecolor": INK, "axes.titlelocation": "left", "xtick.color": INK2,
    "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": .8,
    "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 150, "savefig.bbox": "tight", "figure.facecolor": "white",
})
S: dict = {}


def key_path(prefix, url, params=None):
    raw = json.dumps({"url": url, "params": params or {}}, sort_keys=True, default=str).encode()
    return CACHE / f"{prefix}_{hashlib.sha256(raw).hexdigest()[:24]}.json"


def load(p):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def save(fig, name):
    fig.savefig(FIG / name)
    plt.close(fig)


def hbar(series, title, xlabel, fname, color=BLUE, fmt="{:,.0f}", size=(7.5, 3.4)):
    s = series[::-1]
    fig, ax = plt.subplots(figsize=size)
    ax.barh([str(i) for i in s.index], s.values, color=color, height=.65)
    for y, v in enumerate(s.values):
        ax.text(v, y, " " + fmt.format(v), va="center", color=INK2, fontsize=9)
    ax.set_xlim(0, max(s.max(), 1) * 1.15)
    ax.set_title(title); ax.set_xlabel(xlabel); ax.grid(axis="y", visible=False)
    save(fig, fname)


# =========================================================== Part A: original knowledge base
docs = []
for p in sorted(RAW.glob("*.md")):
    txt = p.read_text(encoding="utf-8")
    words = len(re.findall(r"\w+", txt))
    sections = len(re.findall(r"^\s*(?:#{1,6}\s|\d+\.\s+[A-Z])", txt, flags=re.M))
    numbers = len(re.findall(r"\b\d[\d,.]*\b", txt))
    docs.append({"file": p.name, "lines": txt.count("\n") + 1, "words": words,
                 "characters": len(txt), "sections": sections, "numeric_values": numbers,
                 "title": txt.strip().splitlines()[0].lstrip("# ").strip()})
docs_df = pd.DataFrame(docs)
faq = pd.read_csv(RAW / "hr_faqs.csv")
faq["question_words"] = faq["question"].str.split().str.len()
faq["answer_words"] = faq["answer"].str.split().str.len()
meta = pickle.load(open(ROOT / "vectorstore" / "metadata.pkl", "rb"))
chunks = pd.DataFrame([{"source_file": m.get("source_file"), "chars": len(m.get("text", ""))} for m in meta])
vcfg = json.loads((ROOT / "vectorstore" / "config.json").read_text())
log_path = ROOT / "data" / "analytics" / "interaction_log.jsonl"
inter = pd.DataFrame([json.loads(l) for l in log_path.read_text(encoding="utf-8").splitlines() if l.strip()])

S["kb_docs"] = docs_df.to_dict("records")
S["kb_total_words"] = int(docs_df.words.sum() + faq.answer_words.sum() + faq.question_words.sum())
S["kb_files"] = len(docs_df) + 1
S["kb_size_kb"] = round(sum(p.stat().st_size for p in RAW.iterdir()) / 1024, 1)
S["faq_rows"], S["faq_cols"] = faq[["question", "answer", "category"]].shape
S["faq_categories"] = faq.category.value_counts().to_dict()
S["faq_missing"] = int(faq[["question", "answer", "category"]].isna().sum().sum())
S["faq_dup_questions"] = int(faq.question.str.lower().str.strip().duplicated().sum())
S["faq_answer_words"] = {k: round(float(v), 1) for k, v in faq.answer_words.describe().items()}
S["faq_sample"] = faq[["question", "answer", "category"]].head(4).to_dict("records")
S["chunks_total"] = len(chunks)
S["chunks_by_source"] = chunks.source_file.value_counts().to_dict()
S["chunk_chars"] = {k: round(float(v), 1) for k, v in chunks.chars.describe().items()}
S["embedding_dim"] = vcfg.get("embedding_dim")
S["interactions"] = len(inter)
S["interaction_coverage"] = inter.coverage.value_counts().to_dict() if "coverage" in inter else {}

fig, ax = plt.subplots(figsize=(7.5, 3.2))
d = docs_df.sort_values("words")
lab = [f.replace("_policy.md", "").replace("_", " ") for f in d.file]
ax.barh(lab, d.words, color=BLUE, height=.6)
for y, (w, s_) in enumerate(zip(d.words, d.sections)):
    ax.text(w, y, f" {w} words · {s_} sections", va="center", color=INK2, fontsize=9)
ax.set_xlim(0, d.words.max() * 1.45); ax.set_title("Policy documents — size and structure")
ax.set_xlabel("Words"); ax.grid(axis="y", visible=False)
save(fig, "a1_policy_documents.png")
hbar(faq.category.value_counts(), "HR FAQ questions by category (hr_faqs.csv, n = 20)", "Questions", "a2_faq_categories.png", size=(7.5, 2.8))
hbar(chunks.source_file.value_counts(), "RAG chunks per source file (FAISS index, 48 vectors)", "Chunks", "a3_chunks_per_source.png", size=(7.5, 3.0))

# =========================================================== Part B: rebuild per-source tables from cache
year = int(pd.read_excel(MASTER_XLSX, sheet_name="Master_Dataset", usecols=["observation_date"])["observation_date"].iloc[0][:4])
S["collection_year"] = year
calls = []  # one row per API request

# 1 countries.dev
crow = []
for cc in COUNTRIES:
    p = key_path("country", COUNTRY_URL.format(country_code=cc)); d = load(p)
    calls.append({"api": "countries.dev", "request": f"/alpha/{cc}", "status": "Success" if d else "Failed / not cached", "records": 1 if d else 0})
    if d:
        cur = (d.get("currencies") or [{}])[0]
        crow.append({"country_code": cc, "country_name": d.get("name"), "alpha3_code": d.get("alpha3Code"),
                     "capital": d.get("capital"), "region": d.get("region"), "subregion": d.get("subregion"),
                     "timezone": (d.get("timezones") or [None])[0], "population": d.get("population"),
                     "area_km2": d.get("area"), "currency_code": cur.get("code"), "currency_name": cur.get("name"),
                     "currency_symbol": cur.get("symbol"), "languages": "; ".join(l.get("name", "") for l in d.get("languages") or [])})
countries = pd.DataFrame(crow)

# 2 ExchangeRate-API
fx = load(key_path("currency_usd", FX_URL)) or {}
calls.append({"api": "ExchangeRate-API", "request": "/v6/latest/USD", "status": "Success" if fx.get("result") == "success" else "Failed", "records": len(fx.get("rates", {}))})
rates = pd.DataFrame([{"currency_code": k, "usd_to_local_rate": v} for k, v in (fx.get("rates") or {}).items()])
rates["base"] = "USD"; rates["last_update_utc"] = fx.get("time_last_update_utc")
S["fx_total_rates"] = len(rates); S["fx_last_update"] = fx.get("time_last_update_utc")

# 3 Open-Meteo geocoding + weather
geo_rows, wx_rows = [], []
for cc, cfg in COUNTRIES.items():
    for city in cfg["cities"]:
        gp = {"name": city, "count": 10, "language": "en", "format": "json"}
        g = load(key_path("geocode", GEO_URL, gp))
        res = (g or {}).get("results") or []
        pref = [x for x in res if str(x.get("country_code", "")).upper() == cc] or res
        top = pref[0] if pref else {}
        calls.append({"api": "Open-Meteo (geocoding)", "request": f"name={city}", "status": "Success" if top else ("No match" if g else "Failed"), "records": len(res)})
        geo_rows.append({"country_code": cc, "city": city, "candidates_returned": len(res),
                         "resolved_name": top.get("name"), "resolved_country_code": top.get("country_code"),
                         "resolved_admin1": top.get("admin1"), "latitude": top.get("latitude"),
                         "longitude": top.get("longitude"), "population": top.get("population")})
        if top:
            wp = {"latitude": top["latitude"], "longitude": top["longitude"],
                  "current": "temperature_2m,precipitation,weather_code,wind_speed_10m", "timezone": "auto"}
            w = load(key_path("weather", WX_URL, wp)) or {}
            cur = w.get("current") or {}
            calls.append({"api": "Open-Meteo (forecast)", "request": f"{city} current", "status": "Success" if cur else "Failed", "records": 1 if cur else 0})
            wx_rows.append({"country_code": cc, "city": city, "observed_at_local": cur.get("time"),
                            "timezone": w.get("timezone"), "temperature_c": cur.get("temperature_2m"),
                            "precipitation_mm": cur.get("precipitation"), "wind_speed_kmh": cur.get("wind_speed_10m"),
                            "weather_code": cur.get("weather_code")})
geo = pd.DataFrame(geo_rows); wx = pd.DataFrame(wx_rows)

# 4 Nager holidays
hol_rows, hol_status = [], {}
for cc in COUNTRIES:
    d = load(key_path("holidays", NAGER_URL.format(country=cc, year=year)))
    ok = isinstance(d, list) and len(d) > 0
    hol_status[cc] = len(d) if ok else 0
    calls.append({"api": "Nager.Date", "request": f"/Holidays/{cc}/{year}", "status": "Success" if ok else "No data (HTTP 204)", "records": len(d) if ok else 0})
    for h in d or []:
        hol_rows.append({"country_code": cc, "date": h.get("date"), "name": h.get("name"),
                         "national_holiday": h.get("nationalHoliday"),
                         "holiday_types": "; ".join(h.get("holidayTypes") or []),
                         "subdivisions": "; ".join(h.get("subdivisionCodes") or []) if h.get("subdivisionCodes") else None})
hol = pd.DataFrame(hol_rows)
S["holiday_counts"] = hol_status
S["holiday_type_values"] = hol.holiday_types.value_counts().to_dict()

# 5 NewsData
news_key = os.getenv("NEWSDATA_API_KEY", "").strip()
S["news_log_reconstructed"] = bool(news_key)
news_rows, req_rows = [], []
for cc in COUNTRIES:
    for topic in POLICY_TOPICS:
        params = {"apikey": news_key, "q": topic, "country": cc.lower(), "language": "en"}
        d = load(key_path("news", NEWS_URL, params)) if news_key else None
        n = len((d or {}).get("results") or [])
        st = "Success" if n else ("Success, 0 articles" if d else "No successful response")
        req_rows.append({"country_code": cc, "policy_topic": topic, "status": st, "articles": n,
                         "total_results_reported": (d or {}).get("totalResults")})
        calls.append({"api": "NewsData.io", "request": f"q={topic}; country={cc}", "status": st, "records": n})
        for a in (d or {}).get("results") or []:
            news_rows.append({"country_code": cc, "policy_topic": topic, "article_id": a.get("article_id"),
                              "title": a.get("title"), "source_id": a.get("source_id"), "link": a.get("link"),
                              "pubDate": a.get("pubDate"), "article_countries": "; ".join(a.get("country") or []),
                              "category": "; ".join(a.get("category") or []), "language": a.get("language"),
                              "has_description": bool(a.get("description"))})
news = pd.DataFrame(news_rows); newsreq = pd.DataFrame(req_rows)
calls_df = pd.DataFrame(calls)

summ = (calls_df.assign(ok=calls_df.status.str.startswith("Success") & (calls_df.records > 0))
        .groupby("api").agg(requests=("status", "size"), with_data=("ok", "sum"), records=("records", "sum")))
order = ["countries.dev", "ExchangeRate-API", "Open-Meteo (geocoding)", "Open-Meteo (forecast)", "Nager.Date", "NewsData.io"]
summ = summ.reindex(order)
S["api_calls"] = {k: {kk: int(vv) for kk, vv in v.items()} for k, v in summ.to_dict("index").items()}
S["api_status_counts"] = {a: calls_df[calls_df.api == a].status.value_counts().to_dict() for a in order}
S["news_by_country"] = newsreq.groupby("country_code").articles.sum().to_dict()
S["news_success_by_country"] = newsreq[newsreq.status == "Success"].groupby("country_code").size().to_dict()
S["news_first_failure_index"] = int(next((i for i, r in enumerate(req_rows) if r["status"] == "No successful response"), -1)) + 1
S["news_articles"] = len(news)
S["news_empty_success"] = newsreq[newsreq.status == "Success, 0 articles"][["country_code", "policy_topic"]].to_dict("records")

# examples for B.4
S["ex_country"] = countries[countries.country_code == "IN"].iloc[0].to_dict() if len(countries) else {}
S["ex_fx_inr"] = float(rates.set_index("currency_code").usd_to_local_rate.get("INR", np.nan))
S["ex_geo"] = geo[(geo.city == "Pune")].iloc[0].to_dict()
S["ex_wx"] = wx[(wx.city == "Pune")].iloc[0].to_dict()
S["ex_holiday"] = hol[hol.country_code == "US"].head(2).to_dict("records")
S["ex_news"] = news[(news.country_code == "IN")].head(1).to_dict("records")
_rel = news[(news.country_code == "IN") & news.title.str.lower().str.contains("leave|remote|maternity", na=False)]
S["ex_news_relevant"] = _rel.head(1).to_dict("records")

# write before-fusion workbook
kb_df = pd.concat([docs_df.assign(format="Markdown"),
                   pd.DataFrame([{"file": "hr_faqs.csv", "format": "CSV", "lines": len(faq) + 1,
                                  "words": int(faq.question_words.sum() + faq.answer_words.sum()), "title": "HR FAQs (Q/A pairs)"}])], ignore_index=True)
with pd.ExcelWriter(BEFORE_XLSX, engine="openpyxl") as xw:
    pd.DataFrame([
        ["Purpose", "PolicyPal source tables BEFORE data fusion (Phase 1, Part B)"],
        ["Built from", "data/raw (knowledge base) and data/api_cache (raw API JSON saved during collection)"],
        ["API calls made by this file", "None — rebuilt from cached responses"],
        ["Collection date", str(year) + " (see API_Request_Log)"],
        ["Fused output", "data/PolicyPal_Master_Dataset.xlsx (Master_Dataset sheet)"],
    ], columns=["item", "value"]).to_excel(xw, sheet_name="README", index=False)
    kb_df.to_excel(xw, sheet_name="KB_Policy_Documents", index=False)
    faq[["question", "answer", "category"]].to_excel(xw, sheet_name="KB_HR_FAQs", index=False)
    countries.to_excel(xw, sheet_name="API1_Countries", index=False)
    rates.to_excel(xw, sheet_name="API2_Exchange_Rates", index=False)
    geo.to_excel(xw, sheet_name="API3a_City_Geocode", index=False)
    wx.to_excel(xw, sheet_name="API3b_City_Weather", index=False)
    hol.to_excel(xw, sheet_name="API4_Holidays", index=False)
    news.to_excel(xw, sheet_name="API5_News_Articles", index=False)
    newsreq.to_excel(xw, sheet_name="NewsData_Request_Log", index=False)
    calls_df.to_excel(xw, sheet_name="API_Request_Log", index=False)
    for ws in xw.book.worksheets:
        ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(max(len(str(c.value or "")) for c in col) + 2, 50)
S["before_sheets"] = {"KB_Policy_Documents": len(kb_df), "KB_HR_FAQs": len(faq), "API1_Countries": len(countries),
                      "API2_Exchange_Rates": len(rates), "API3a_City_Geocode": len(geo), "API3b_City_Weather": len(wx),
                      "API4_Holidays": len(hol), "API5_News_Articles": len(news), "NewsData_Request_Log": len(newsreq),
                      "API_Request_Log": len(calls_df)}

# chart B1: outcome per API
fig, ax = plt.subplots(figsize=(7.5, 3.4))
y = np.arange(len(order))[::-1]
ok = np.array([summ.loc[a, "with_data"] for a in order]); tot = np.array([summ.loc[a, "requests"] for a in order])
ok_pct = ok / tot * 100; bad_pct = 100 - ok_pct
ax.barh(y, ok_pct, color=BLUE, height=.6, label="Returned data", edgecolor="white", linewidth=2)
ax.barh(y, bad_pct, left=ok_pct, color=RED, height=.6, label="No data / failed", edgecolor="white", linewidth=2)
for yy, o, t in zip(y, ok, tot):
    ax.text(101, yy, f" {o}/{t}", va="center", color=INK2, fontsize=9)
ax.set_yticks(y, order); ax.set_xlim(0, 112); ax.set_xlabel("% of requests")
ax.set_title("API requests that returned data, by source"); ax.grid(axis="y", visible=False)
ax.legend(loc="upper center", bbox_to_anchor=(.45, -.2), ncol=2, frameon=False, fontsize=9)
save(fig, "b1_api_outcomes.png")

# chart B2: NewsData request grid
grid = newsreq.pivot(index="country_code", columns="policy_topic", values="articles").reindex(index=list(COUNTRIES), columns=POLICY_TOPICS)
stat = newsreq.pivot(index="country_code", columns="policy_topic", values="status").reindex(index=list(COUNTRIES), columns=POLICY_TOPICS)
fig, ax = plt.subplots(figsize=(8.2, 4.4))
col = np.where(stat.values == "No successful response", 0, np.where(grid.values > 0, 2, 1))
cmap = matplotlib.colors.ListedColormap(["#f6d3d3", "#e6e5e0", "#cfe1f7"])
ax.imshow(col, cmap=cmap, aspect="auto", vmin=0, vmax=2)
for i in range(grid.shape[0]):
    for j in range(grid.shape[1]):
        ax.text(j, i, "×" if col[i, j] == 0 else int(grid.values[i, j]), ha="center", va="center", fontsize=8.5,
                color=RED if col[i, j] == 0 else INK)
ax.set_xticks(range(len(POLICY_TOPICS)), [t.replace(" ", "\n") for t in POLICY_TOPICS], fontsize=8)
ax.set_yticks(range(len(COUNTRIES)), list(COUNTRIES)); ax.grid(False)
ax.set_title("NewsData requests: articles returned per country × topic (× = no successful response)")
save(fig, "b2_news_request_grid.png")

# =========================================================== Part C: fusion validation
m = pd.read_excel(MASTER_XLSX, sheet_name="Master_Dataset")
xl = pd.read_excel(MASTER_XLSX, sheet_name=None)
S["master_rows"], S["master_cols"] = m.shape
S["master_sheets"] = {k: list(v.shape) for k, v in xl.items()}
S["master_by_country"] = m.country_code.value_counts().reindex(list(COUNTRIES), fill_value=0).to_dict()
S["expected_rows"] = int(len(news) * 5)
S["record_id_unique"] = bool(m.record_id.is_unique)
chk = m.merge(countries[["country_code", "country_name", "population", "currency_code"]], on="country_code", suffixes=("", "_src"))
S["chk_country_attr_mismatch"] = int(((chk.country_name != chk.country_name_src) | (chk.population != chk.population_src) | (chk.currency_code != chk.currency_code_src)).sum())
r = rates.set_index("currency_code").usd_to_local_rate
S["chk_fx_mismatch"] = int((~np.isclose(m.usd_to_local_rate, m.currency_code.map(r))).sum())
wk = m.merge(wx, on=["country_code", "city"], suffixes=("", "_src"))
S["chk_weather_mismatch"] = int((~np.isclose(wk.temperature_c, wk.temperature_c_src)).sum())
S["chk_weather_joined"] = len(wk)
S["geo_country_mismatch"] = geo[geo.resolved_country_code != geo.country_code][["country_code", "city", "resolved_name", "resolved_country_code"]].to_dict("records")
S["geo_name_differs"] = geo[geo.resolved_name.fillna("") != geo.city][["country_code", "city", "resolved_name"]].to_dict("records")
first_h = hol.sort_values("date").groupby("country_code").first()
S["chk_holiday_first_ok"] = bool((m.dropna(subset=["holiday_date"]).apply(lambda r_: str(r_.holiday_date)[:10] == first_h.loc[r_.country_code, "date"], axis=1)).all())
S["countries_without_rows"] = [c for c, v in S["master_by_country"].items() if v == 0]

# =========================================================== Part D: quality
miss = m.isna().sum()
S["master_missing"] = {k: int(v) for k, v in miss[miss > 0].items()}
S["quality_flag"] = m.data_quality_flag.value_counts().to_dict()
S["status_patterns"] = m.api_collection_status.value_counts().to_dict()
art = m.drop_duplicates(["country_code", "policy_topic", "news_url"])
S["article_rows"] = len(art)
S["dup_article_across_topics"] = int(art.duplicated(["country_code", "news_url"]).sum())
S["unique_articles_global"] = int(m.news_url.nunique())
S["dup_full_rows"] = int(m.drop(columns=["record_id"]).duplicated().sum())
S["dup_title_diff_url"] = int(art.drop_duplicates(["news_url"]).duplicated(["news_title"]).sum())
S["country_name_long"] = [n for n in countries.country_name if len(n) > 25]
S["news_country_other"] = int((~news.apply(lambda r_: COUNTRIES[r_.country_code]["name"].lower().split()[-1] in r_.article_countries.lower()
                                               or r_.country_code.lower() in r_.article_countries.lower(), axis=1)).sum())
kw = {t: [w for w in re.split(r"\s+", t) if len(w) > 3] for t in POLICY_TOPICS}
art_t = art.assign(rel=art.apply(lambda r_: any(w[:6] in str(r_.news_title).lower() for w in kw[r_.policy_topic]), axis=1))
rel = art_t.groupby("policy_topic").rel.mean().mul(100).round(0).sort_values()
S["topic_relevance_overall"] = round(float(art_t.rel.mean() * 100), 1)
S["topic_relevance"] = rel.to_dict()
pub = pd.to_datetime(m.news_published_at, errors="coerce")
S["pub_unparsed"] = int(pub.isna().sum())
S["pub_range"] = [str(pub.min()), str(pub.max())]
pub_art = pd.to_datetime(art.news_published_at, errors="coerce")
S["pub_age_days"] = {k: round(float(v), 1) for k, v in ((pd.Timestamp(f"{year}-08-24") - pub_art).dt.days).describe().items()}
num = ["temperature_c", "precipitation_mm", "wind_speed_kmh", "population", "area_km2", "usd_to_local_rate"]
out = {}
for c in ["temperature_c", "precipitation_mm", "wind_speed_kmh"]:
    v = wx[c].dropna(); q1, q3 = v.quantile([.25, .75]); i = q3 - q1
    o = wx[(v < q1 - 1.5 * i) | (v > q3 + 1.5 * i)]
    out[c] = {"n": int(len(v)), "min": float(v.min()), "median": float(v.median()), "max": float(v.max()),
              "outliers": o[["city", c]].to_dict("records")}
S["weather_stats"] = out
S["severe_weather_cities"] = int(m.drop_duplicates(["country_code", "city"]).is_severe_weather.sum())
S["weather_conditions"] = m.drop_duplicates(["country_code", "city"]).weather_condition.value_counts().to_dict()
S["fx_rates_10"] = rates.set_index("currency_code").usd_to_local_rate.reindex(countries.currency_code).to_dict()

fig, ax = plt.subplots(figsize=(7.5, 2.6))
s = pd.Series(S["master_missing"]).sort_values()
ax.barh(s.index, s.values, color=ORANGE, height=.55)
for yy, v in enumerate(s.values):
    ax.text(v, yy, f" {v:,} ({v / len(m):.0%})", va="center", color=INK2, fontsize=9)
ax.set_xlim(0, len(m) * 1.25); ax.set_title(f"Columns with missing values (Master_Dataset, {len(m):,} rows)")
ax.set_xlabel("Rows missing"); ax.grid(axis="y", visible=False)
save(fig, "d1_missing_values.png")
hbar(rel, "Topic relevance: % of article titles containing the topic keyword", "% of articles", "d2_topic_relevance.png", fmt="{:.0f}%", size=(7.5, 3.4))

fig, ax = plt.subplots(figsize=(7.5, 3.0))
order_c = wx.groupby("country_code").temperature_c.median().sort_values().index
data = [wx[wx.country_code == c].temperature_c.values for c in order_c]
ax.boxplot(data, orientation="horizontal", widths=.5, patch_artist=True, boxprops=dict(facecolor="#d6e6f8", edgecolor=BLUE),
           medianprops=dict(color=INK), whiskerprops=dict(color=BLUE), capprops=dict(color=BLUE),
           flierprops=dict(marker="o", markersize=4, markerfacecolor=ORANGE, markeredgecolor="none"))
ax.set_yticks(range(1, len(order_c) + 1), list(order_c)); ax.set_xlabel("Temperature (°C) at collection time")
ax.set_title("City temperature by country (Open-Meteo, 50 cities)")
save(fig, "d3_temperature_outliers.png")

# =========================================================== Part E: EDA charts
hbar(pd.Series(S["master_by_country"]).sort_values(ascending=False), "Fused rows per country (Master_Dataset)", "Rows", "e1_rows_by_country.png", size=(7.5, 3.3))
hbar(art.policy_topic.value_counts(), "News articles per policy topic (before city expansion)", "Articles", "e2_articles_by_topic.png", size=(7.5, 3.3))
hbar(art.drop_duplicates("news_url").news_source.value_counts().head(10), "Top 10 news sources (unique articles)", "Articles", "e3_top_sources.png", size=(7.5, 3.3))
hbar(pd.Series(S["weather_conditions"]), "Weather condition across the 30 fused cities", "Cities", "e4_weather_conditions.png", size=(7.5, 2.6))
hc = pd.Series(S["holiday_counts"]).sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(7.5, 3.0))
ax.bar(hc.index, hc.values, color=[BLUE if v else RED for v in hc.values], width=.6)
for x_, v in enumerate(hc.values):
    ax.text(x_, v, str(v) if v else "no data", ha="center", va="bottom", fontsize=9, color=INK2 if v else RED)
ax.set_title(f"Public holidays returned by Nager.Date per country ({year})"); ax.set_ylabel("Holidays")
save(fig, "e5_holidays_by_country.png")

(OUT / "stats.json").write_text(json.dumps(S, indent=2, default=str), encoding="utf-8")
print("ok", BEFORE_XLSX)
