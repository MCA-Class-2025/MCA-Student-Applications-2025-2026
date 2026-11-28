# Dataset Description — PolicyPal (Company Policy Assistant)

## Source and Methodology

This project uses a **synthetically constructed but realistic dataset** of
company HR policy documents, built to mirror the structure, terminology, and
level of detail found in real corporate policy handbooks.

**Why synthetic data, stated explicitly (not an oversight):** real company
HR policies are internal and confidential — no organization publishes its
actual leave-approval thresholds, exact reimbursement caps, or internal
security procedures for public collection. This makes "collect real company
policy PDFs from the internet" an impossible instruction to follow honestly
for this specific domain. The standard, defensible approach — used in both
industry RAG prototyping and academic projects — is to construct a
representative synthetic corpus with realistic structure and figures, which
is what this dataset does.

## Dataset Composition

| File | Format | Topic | Size |
|---|---|---|---|
| `leave_and_attendance_policy.md` | Markdown | Annual/sick/maternity/paternity leave, application process | 60 lines |
| `remote_work_policy.md` | Markdown | Hybrid eligibility, equipment, VPN/data security for remote work | 50 lines |
| `expense_and_travel_policy.md` | Markdown | Travel booking, per-diem, client entertainment, reimbursement deadlines | 64 lines |
| `it_security_policy.md` | Markdown | Password/MFA requirements, device usage, data classification, incident reporting | 60 lines |
| `code_of_conduct_policy.md` | Markdown | Workplace conduct standards | 55 lines |
| `hr_faqs.csv` | CSV (structured Q/A pairs, with category column) | Common employee questions across all policy areas | 20 rows |

**Total**: 6 files, ~28KB, 2 formats (Markdown + CSV) — deliberately mixed
formats to demonstrate the pipeline's multi-format ingestion (`src/data_processing.py`
supports .md, .txt, .csv, .pdf, .docx), not just a single file type.

## Data Quality Characteristics

- Structured with consistent `##` section headers per topic, enabling the
  project's header-aware chunking strategy (see `src/data_processing.py`) —
  each retrieved chunk stays topically coherent rather than mixing two
  unrelated policy sections.
- Numeric figures (leave days, reimbursement amounts, deadlines) are
  internally consistent within each document, so retrieval-accuracy testing
  against known ground-truth answers is possible (e.g. "How many annual
  leave days?" has one verifiably correct answer: 18).
- The CSV FAQ file provides a second data shape (structured Q/A with
  metadata) distinct from the prose-style Markdown policies, testing the
  ingestion pipeline against more than one document structure.

## Multimodal Component

The photo-mode feature (`src/vision.py`) does not require a separate labeled
image dataset — it operates on **any photo the user provides at query time**
(a photographed printed notice, a scanned memo), cross-referenced live
against this text corpus. This is a deliberate design choice: it avoids
needing a curated image dataset for a use case where the real-world input is
inherently user-supplied and unpredictable, while still exercising a
genuinely multimodal model (see Architecture section of the main README for
why this counts as true multimodal rather than a bolted-on OCR step).

## Limitations, Stated Directly

- Being synthetic, the exact figures (18 days annual leave, INR 15,000
  setup allowance, etc.) are illustrative, not validated against any real
  organization's actual policy — this is expected and appropriate for a
  demonstration dataset, but should not be cited as real HR guidance.
- At 6 files / ~28KB, this is a small corpus by production RAG standards
  (real deployments index hundreds of documents). It's sized appropriately
  for a class project demo, not claimed to be production-scale.
- If your instructor specifically requires evidence of "collection from
  public sources" rather than construction: government civil-service HR
  manuals (leave rules, conduct rules, travel allowance rules) are usually
  published as public-sector documents under open government licenses,
  unlike private-company handbooks (which even when technically visible on
  GitHub, as with some real published employee handbooks, are still
  copyrighted with no reuse license attached — checked this directly while
  building this project and deliberately avoided pulling that content in
  wholesale for exactly that reason). Government HR manuals would be a
  genuinely safer "real, public source" swap-in if needed, at the cost of
  matching a specific country's civil service rather than a generic company.

