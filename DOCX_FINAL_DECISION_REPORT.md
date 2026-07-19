| Converter | Registry | Engine | Test | Decision | Reason |
|---|---|---|---|---|---|
| DOCX → PDF | Contract: `app/data/converters/docx-to-pdf.contract.json`<br>Plugin: `word-to-pdf` (app/plugins/document/word_to_pdf.py) | Plugin-level: uses `document` engine metadata but converts internally using `reportlab` and optionally `python-docx` | PASS — produced `outputs/document/sample.pdf` in runtime test | KEEP | Stable, high quality, direct plugin exists; dependencies: `reportlab`, optional `python-docx`. Ready for production. |
| DOCX → ODT | No direct contract/plugin (no `docx-to-odt.contract.json`) | Indirect: `document` engine supports PDF→ODT (requires `pdfplumber`, `odfpy`) — would require multi-step (DOCX→PDF then PDF→ODT) or new plugin | FAIL — direct conversion unsupported (UnsupportedConversionError) | BETA | Useful alternative format; feasible via DOCX→PDF then PDF→ODT. Needs explicit orchestration, quality checks, and CI before enabling. |
| DOCX → JPG | No direct contract/plugin | Indirect: PDF→JPG supported by `document` engine (requires `PyMuPDF`) — would require multi-step | FAIL — direct conversion unsupported | DISABLE | Low demand and lossy; conversion possible via multi-step but quality/UX concerns. Recommend not exposing until a clear product need. |
| DOCX → XLSX | No direct contract/plugin | Indirect: PDF→XLSX supported by `document` engine (`pdfplumber`, `openpyxl`) — would require multi-step | FAIL — direct conversion unsupported | DISABLE | Semantically unusual; often low value and prone to poor extraction. Defer or remove from roadmap. |
| DOCX → PPT | No direct contract/plugin | Indirect: PDF→PPTX supported by `document` engine (`PyMuPDF`, `python-pptx`) — would require multi-step | FAIL — direct conversion unsupported | DISABLE | Rare use-case; multi-step may work but results are unreliable. Do not surface in recommendations now. |

Notes and evidence
- Recommendation endpoint: `/recommend/docx` returns `best_choice: docx->pdf` and no alternatives (recommendation aligns with KEEP decision).
- Runtime tests executed against `tests/sample.docx` in workspace. Only `DOCX→PDF` produced an output file `outputs/document/sample.pdf`.
- Key files inspected:
  - [app/data/converters/docx-to-pdf.contract.json](app/data/converters/docx-to-pdf.contract.json)
  - [app/plugins/document/word_to_pdf.py](app/plugins/document/word_to_pdf.py)
  - [app/engines/document_engine.py](app/engines/document_engine.py)
  - Conversion service behavior observed in logs during test runs (plugin selection and errors).

Recommended next steps (no code changes yet):
1. KEEP `docx->pdf` as primary DOCX experience; ensure `reportlab` and `python-docx` are present in production images.
2. Add a small CI job exercising `DOCX→PDF` certified regression sample to prevent regressions (fast unit test already present).
3. For ODT, consider a tracked BETA initiative to implement a documented multi-step path (DOCX→PDF→ODT) with quality thresholds and a regression sample before flipping to `active`.
4. Do not enable DOCX→JPG/XLSX/PPT conversions in recommendations or UI until either a clear product request or a proven multi-step pipeline with regression coverage exists.
