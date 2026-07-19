| Converter | Registry | Plugin | Engine | Runtime Test | Decision | Reason |
|---|---|---|---|---|---|---|
| XLSX → PDF | Contract: `app/data/converters/excel-to-pdf.contract.json` (active, regression sample `tests/sample.xlsx`) | `excel-to-pdf` plugin: `app/plugins/document/excel_to_pdf.py` | `document` engine: supports spreadsheet→PDF via `openpyxl` + `reportlab` (_DocumentEngine._convert_spreadsheet_to_pdf_) | FAIL — test run errored: `BadZipFile: File is not a zip file` (existing `tests/sample.xlsx` is a placeholder/corrupted) | KEEP (conditional) | Registered & implemented. Engine supports conversion; ensure `openpyxl` present and replace `tests/sample.xlsx` with a valid sample before CI. |
| XLSX → CSV | No direct contract/plugin found | No plugin implemented | No dedicated engine path (would be derived from spreadsheet read APIs) | FAIL — `UnsupportedConversionError: XLSX to CSV conversion is not supported yet` | BETA | High utility (CSV is common). Recommend implement small plugin or expose a pipeline using `openpyxl` to emit CSV and add regression test. |
| XLSX → ODS | Contract: `app/data/converters/xlsx-to-ods.contract.json` exists (currently `deprecated`) | `xlsx-to-ods` plugin: `app/plugins/document/xlsx_to_ods.py` (registered) | `document` engine currently rejects non-PDF targets for spreadsheets; runtime raises `UnsupportedConversionError` | FAIL — engine mapping missing; plugin calls engine but engine doesn't implement `xlsx->ods` | DISABLE (temporary) | Plugin exists but engine lacks support; earlier decision set lifecycle to `deprecated`. Keep disabled until `DocumentEngine` implements ODS target or plugin handles conversion independently. |
| XLSX → DOCX | No direct contract/plugin | No plugin implemented | Not applicable (semantically uncommon) | FAIL — `UnsupportedConversionError: XLSX to DOCX conversion is not supported yet` | DISABLE | Low value and potentially confusing; not typical user expectation. If product requests, consider special-case extraction workflow. |
| XLSX → PPT | No direct contract/plugin | No plugin implemented | No direct engine path; would require content-to-slides mapping | FAIL — `UnsupportedConversionError: XLSX to PPT conversion is not supported yet` | DISABLE | Low demand and complex mapping; avoid exposing until clear product need.

Evidence & notes
- Recommendation API: `/recommend/xlsx` returns `best_choice` targeting `pdf` (matches `excel-to-pdf`).
- Logs: conversion service selected `excel-to-pdf` plugin for PDF target; failure due to invalid sample file (`zipfile.BadZipFile`).
- Key files inspected:
  - `app/data/converters/excel-to-pdf.contract.json` ([path](app/data/converters/excel-to-pdf.contract.json))
  - `app/data/converters/xlsx-to-ods.contract.json` ([path](app/data/converters/xlsx-to-ods.contract.json))
  - `app/plugins/document/excel_to_pdf.py` ([path](app/plugins/document/excel_to_pdf.py))
  - `app/plugins/document/xlsx_to_ods.py` ([path](app/plugins/document/xlsx_to_ods.py))
  - `app/engines/document_engine.py` ([path](app/engines/document_engine.py))

Recommendations (next steps)
1. Replace or regenerate a valid `tests/sample.xlsx` (small fixture) so runtime XLSX→PDF test can be validated in CI. This is a test data change only, not a converter implementation.
2. KEEP `xlsx->pdf` as primary XLSX experience once sample/CI is validated and ensure `openpyxl` and `reportlab` are included in production images.
3. For CSV output, promote to BETA by adding a minimal `excel-to-csv` plugin that reads sheets via `openpyxl` and writes CSV, plus a small regression test.
4. Keep `xlsx-to-ods` disabled until `DocumentEngine` either supports `ods` target or the plugin implements an independent conversion path; do not re-enable in UI until QA passes.
5. Do not expose XLSX→DOCX/PPT unless a clear product signal arises.

Decision summary
- KEEP: `XLSX→PDF` (conditional on valid regression sample and dependencies)
- BETA: `XLSX→CSV`
- DISABLE: `XLSX→ODS` (temporary), `XLSX→DOCX`, `XLSX→PPT`
