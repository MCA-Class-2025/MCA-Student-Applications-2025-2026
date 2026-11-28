# Phase 2 report template notes

## Reference and authority

- Design authority: `report/phase1/FemCare_Phase_1_Report.docx`.
- Reference SHA-256: `E619E94620981F867D5D88F989DFD97DE3B3A2D6FB8C3D479006632F53E1939A`.
- Inspected reference: 18 pages, one portrait Letter section, 1-inch margins, first-page header/footer suppressed.
- Assignment authority for required content: pages 6-11 of `LLM–API–Data Fusion and Exploratory Data Analysis phase 1.pdf` (Parts F-K). The assignment is treated as requirements, not as evidence about the implementation.

## Page and typography system

- Letter portrait, 8.5 x 11 inches; 1-inch margins.
- Header after cover: `FemCare AI | Phase 2 Report`; right-aligned `Page` field in footer.
- Body: Times New Roman, 11 pt, 1.10 line spacing, dark gray.
- Heading 1: blue `#2E74B5`, approximately 16 pt, bold.
- Heading 2: blue `#2E74B5`, approximately 13 pt, bold.
- Heading 3: dark blue, approximately 11 pt, bold.
- Captions: Times New Roman 9 pt, centered, italic, muted gray.

## Component library

- Cover: centered report title, project name, phase subtitle, student metadata, report date.
- Evidence-first section opening: short purpose paragraph followed by a compact table or figure.
- Tables: Table Grid, bold centered header, light-blue header fill, repeat header, rows kept together.
- Figures: centered at up to 6.35 inches wide with alternative text and a caption.
- Code/path listings: compact bordered table rather than large source-code blocks.
- Insight pattern: three-row table containing Finding, Evidence, Interpretation.
- Page breaks: used before each major assignment part to maintain a predictable review flow.

## Slot map for this report

1. Cover and declaration of scope.
2. Executive summary and Phase 1 baseline.
3. Part F: before-versus-after fusion comparison.
4. Part G: at least five Finding-Evidence-Interpretation insights.
5. Part H: fused-data RAG integration and architecture.
6. Part I: ten-question LLM test with expected answers, sources, responses, and correctness.
7. Part J: measured before/after comparison and usefulness conclusion.
8. Part K: technical documentation, code/dataset inventory, run order, and limitations.
9. Conclusion, references, and reproducibility appendix.

## Preservation and deviations

- Preserve the Phase 1 visual identity, header/footer behavior, page geometry, heading hierarchy, table language, and restrained blue palette.
- The Phase 2 report is a separate deliverable, not an overwrite of Phase 1.
- The Phase 2 implementation uses a TF-IDF vector index for both comparison systems. This is stated explicitly because the older application used MiniLM/FAISS; using the same Phase 2 retrieval method on both sides isolates the value of the fused data.
- No decorative callout boxes; important results are expressed as ordinary paragraphs, tables, and figures.
