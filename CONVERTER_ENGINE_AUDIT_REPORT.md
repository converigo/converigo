# CONVERTER ENGINE AUDIT REPORT

Scope: Audit focused on CLASS A converters (see CONVERTER_PRIORITY_CLASSIFICATION.md).

---

Converter: JPG -> PDF

1. Input
- Path: `tests/assets/regression/sample.jpg`
- Type: image/jpeg

2. Plugin
- File: `app/plugins/document/jpg_to_pdf.py`
- Class: `JPGToPDFPlugin`
- Behavior: Uses Pillow to open the source image, converts to RGB if needed, creates a temporary PNG, and uses ReportLab (`reportlab.pdfgen.canvas`) to draw the image onto a single PDF `letter` page.

3. Engine
- Engine: `document` (plugin embeds image into a PDF via ReportLab directly; no separate engine abstraction used)

4. Dependency
- `Pillow` (PIL) — required to open and process source image
- `reportlab` — required to generate PDF output

5. Output
- Path: `outputs/document/{source_stem}.pdf` (e.g., `outputs/document/sample.pdf`)
- Expected: valid PDF containing the image rendered onto a page
- Observed: plugin produced a valid PDF file (non-empty).

Audit Notes / Evidence
- The plugin explicitly requires `reportlab` and `Pillow` and will raise clear errors if missing.
- The validation script `scripts/real_conversion_validation.py` currently labels the `JPG -> PDF` case as type `image` and runs Pillow open/verify on the produced output. That fails because Pillow cannot open PDF documents — causing the FAIL observed in `build/real_conversion_results.json` even though conversion was successful.

Findings
- Error from run: `PIL open failed: cannot identify image file 'outputs\\document\\sample.pdf'`
- Root cause: Validation logic mismatch (test case classified as `image` instead of `document`) rather than conversion engine/plugin bug.

Recommended Fix
- Short-term: Update `scripts/real_conversion_validation.py` to set the `JPG -> PDF` case `type` to `document`, or update validation branch to choose validation by `target` format (if target is `pdf` treat as document). This is a minimal script change; no runtime library changes required.
- Medium-term: Make validation selection deterministic: derive validation approach from `target_format` rather than the ad-hoc `type` field in the cases list.

Risk
- Low: Changing the audit script or its case classification is non-invasive and does not touch conversion code, engines, or frontend. It only affects reporting/validation of conversions.

---

CLASS A Summary
- Only `JPG -> PDF` qualified for CLASS A. The required remediation is to fix the validation classification in the audit script or validation logic.

---

Before:

- Validation classification: incorrect — `JPG -> PDF` was classified under `image` validation and the script attempted to open the produced PDF with Pillow.

After:

- Validation updated in `scripts/real_conversion_validation.py` to select validation by `target` format. For `pdf` outputs the script attempts to use PyMuPDF (`fitz`) to open and count pages; if PyMuPDF is not installed it falls back to checking file existence and non-zero size.

Result:

- `JPG -> PDF` re-run: PASS — `PyMuPDF open OK pages=1` (script detected and used PyMuPDF in the environment).

Evidence:

- `build/real_conversion_results.json` contains entry for `JPG -> PDF` with `status: PASS` and `validation: PyMuPDF open OK pages=1`.

