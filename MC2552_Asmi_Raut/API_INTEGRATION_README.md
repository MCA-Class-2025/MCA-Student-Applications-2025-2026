# Threat Intelligence API Integration — Setup & Usage

This adds 5 external API integrations to SecureSense AI, fused with your
existing NSL-KDD dataset. **Nothing in your existing project was changed** —
this is a pure addition (new files only, plus 4 lines added to `app.py` to
register the new page, and 6 empty-value lines appended to `.env`).

## What was added

```
modules/api/
    base_client.py       shared HTTP client: retries, timeouts, logging
    mitre_attack.py       API 1 — MITRE ATT&CK   (no key needed)
    nvd.py                 API 2 — NVD (CVE)       (key optional)
    urlhaus.py             API 3 — URLhaus         (no key needed)
    virustotal.py          API 4 — VirusTotal      (key required)
    abuseipdb.py            API 5 — AbuseIPDB       (key required)

modules/threat_enrichment/
    config.py             seed IOC lists for VirusTotal / AbuseIPDB
    pipeline.py            loads dataset, runs your EXISTING model, calls all 5 APIs
    fusion.py               merges everything into the final fused CSV, with validation
    validation.py           row-count / duplicate-key / match-rate checks

run_pipeline.py           <- run this one file to do everything
app_pages/threat_intelligence.py   <- new Streamlit page (sidebar: "🌐 Threat Intelligence")

data/api_results/          <- output folder (created automatically)
    mitre_attack_data.csv
    nvd_data.csv
    urlhaus_data.csv
    virustotal_data.csv
    abuseipdb_data.csv
    fused_threat_dataset.csv   <- the final combined file
```

## 1. Get your free API keys (2 of the 5 APIs need one)

| API | Key needed? | Where to get it |
|---|---|---|
| MITRE ATT&CK | No | — |
| URLhaus | No | — |
| NVD | Optional (recommended) | https://nvd.nist.gov/developers/request-an-api-key |
| VirusTotal | **Yes** | https://www.virustotal.com/gui/my-apikey (free account) |
| AbuseIPDB | **Yes** | https://www.abuseipdb.com/account/api (free account) |

Open `.env` in the project root and fill in the blank values that were added
at the bottom:

```
NVD_API_KEY=your_key_here
VIRUSTOTAL_API_KEY=your_key_here
ABUSEIPDB_API_KEY=your_key_here
```

Your existing `GROQ_API_KEY` line is untouched.

## 2. Run the pipeline

From the project root, with your virtual environment active:

```
python run_pipeline.py
```

This will:
1. Load your existing `KDDTrain+.txt` (read-only, unchanged).
2. Run it through your **existing, already-trained** Isolation Forest model.
3. Reduce it to the 23 unique attack categories (not 125,973 individual API
   calls — see "Why 23 rows, not 125,973" below).
4. Call all 5 APIs and write one CSV per API to `data/api_results/`.
5. Fuse everything into `data/api_results/fused_threat_dataset.csv`.
6. Print a validation report (row counts, match rates, duplicate keys) to
   the console and to `logs/api_pipeline.log`.

Takes roughly 1–3 minutes, mostly waiting on the NVD API's rate limit
(faster if you set `NVD_API_KEY`).

## 3. View it in the app

```
streamlit run app.py
```

Open the new **🌐 Threat Intelligence** page in the sidebar. It shows live
status for each of the 5 APIs, previews the fused dataset, and lets you
download every CSV. There's also a "Run Pipeline Now" button if you'd
rather trigger it from the UI instead of the command line.

## How the fusion actually works (why it's not one flat table)

Your NSL-KDD dataset only has an `attack` category column — no IP
addresses, URLs, or file hashes. So:

- **MITRE ATT&CK** and **NVD** genuinely share `attack` as a join key →
  they're `LEFT JOIN`ed onto your 23 attack categories. Every category is
  preserved (0 rows lost, 0 duplicated).
- **URLhaus, VirusTotal, AbuseIPDB** have nothing in NSL-KDD to join
  against — so rather than inventing fake IPs/URLs/hashes and pretending
  they came from your dataset, they're kept as their own
  `threat_intel_ioc` rows in the same final CSV, clearly tagged and
  separate from the `network_traffic_category` rows. Look at the
  `record_type` column to tell them apart.

## Why 23 rows, not 125,973

`KDDTrain+.txt` has 125,973 rows but only 23 unique values in the `attack`
column. Calling an API once per unique category (23 calls) instead of once
per row (125,973 calls) avoids rate-limit failures and is the standard
"dimension table" pattern — every row still gets enriched, just via the
join on `attack`, not by 125,973 separate network requests.

## If something fails

- Every API call is wrapped so a failure never crashes the run — you'll
  see `api_status = api_error:...` or `missing_api_key` in the CSV instead.
- Full detail is in `logs/api_pipeline.log`.
- Common cause: missing/invalid API key, or no internet access from the
  machine running `run_pipeline.py`.
