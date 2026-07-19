# Recommendation Cleanup Plan (Office Converters)

Goal: Keep the recommendation set small, reliable, and useful. Disable or fix converters that are unreliable or incorrectly mapped.

KEEP
- `xlsx-to-pdf` — stable, uses `DocumentEngine` spreadsheet->PDF path, VERIFIED (CERTIFIED).
- `word-to-pdf`, `pdf-to-word`, `pdf-to-xlsx`, `pdf-to-ppt` — core PDF↔Office flows verified.
- Image→Office and Office→PDF flows that passed manual tests (JPG/PNG/WEBP families).

DISABLE (temporary)
- `xlsx-to-ods` (XLSX→ODS): plugin registered but engine does not support `ods` target — disabled temporarily until engine support or a safe conversion path is implemented.

REVIEW / POSSIBLE ACTION
- `ppt-to-pdf`: local test passes but user reported failures; investigate environment (missing python-pptx, PyMuPDF, reportlab) and consider adding CI regression coverage and hardening deployment images.

DISABLE candidates (if stability required immediately)
- Converters that rely on untested or rarely used transformations and have no regression coverage OR produce low-quality results on sample data. (List to be generated from analytics/usage data.)

Next steps:
1. Remove or mark `xlsx-to-ods` as inactive in converter metadata until engine supports `ods` target (or implement engine support).
2. Add runtime regression for `pptx->pdf` in CI using generated sample to detect environment dependency failures.
3. Re-evaluate low-usage office converters via telemetry before re-enabling.
