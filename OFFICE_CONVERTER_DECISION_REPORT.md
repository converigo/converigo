# Office Converter Decision Report

Summary decisions for office converters after audit.

Decisions:

- XLSX→ODS: FIX (engine mapping) — Reason: plugin exists but `DocumentEngine` rejects non-`pdf` targets. This is an internal mapping/implementation bug. Options: (A) implement `DocumentEngine` support for `ods` (preferred), or (B) change plugin to generate ODS via a separate, well-tested path; until fixed mark converter inactive.

- PPT→PDF: REVIEW — Reason: local runtime conversion succeeds but user reported failures. Likely environmental (missing dependency or permissions). Action: add CI regression (create sample `tests/sample.pptx` and run), verify runtime dependencies in production image, and add clear error logging to detect missing libs. Do not disable yet until CI reproduction confirms instability.

- KEEP: core certified converters (XLSX→PDF, DOCX↔PDF, PDF→XLSX/PPTX/ODT, JPG/PNG→PDF and vice versa) — Reason: verified manual tests, stable engine implementations, and available regression samples.

Rationale:
- Prioritize user experience and reliability; prefer temporarily disabling misbehaving converters rather than keeping them in recommendations if they are broken.
- Avoid adding converters until engine support and regression coverage exist.

Recommended immediate actions (no code changes to be made in this audit step):
1. Mark `xlsx-to-ods` as REVIEW/INACTIVE in admin dashboard or converter metadata until fixed.
2. Add a CI certified test for `pptx->pdf` using `tests/sample.pptx` to reproduce environment failures.
3. Update documentation and `app/data/converters/xlsx-to-ods.metadata.json` to mark current status.
