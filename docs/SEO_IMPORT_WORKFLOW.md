# SEO Import Workflow

Purpose
- Describe the operational workflow for importing SEO CSV exports into the analysis pipeline, including upload, validation, error handling, and approval steps.

1) CSV upload process
- Authorized exporters (analytics, SEO analyst) place raw exports into a secure ingestion location (S3, GCS, secure file share). Do NOT commit raw exports to the repository.
- Expected folder structure for inbound transfers (example): `incoming/gsc/`, `incoming/ga4/`, `incoming/indexing/`.
- File naming convention: `<source>_<type>_<startdate>_<enddate>_<exporter>.csv` (example: `gsc_performance_20260801_20260831_analytics.csv`). Use `YYYYMMDD` for dates and lowercase, hyphen/underscore separators only.
- Alongside each CSV, include a small metadata file `<filename>.meta` containing: `exporter`, `property`, `start_date`, `end_date`, `timezone`, `sampling` (if any), and `export_timestamp`.
- Include a checksum file `<filename>.sha256` for integrity verification.

2) Validation flow
- Trigger: manual upload or automated watcher detects new file in `incoming/`.
- Step A — Pre-validate:
  - Verify checksum matches `<filename>.sha256`.
  - Confirm UTF-8 encoding and presence of a header row.
- Step B — Run validator (see `docs/SEO_DATA_VALIDATION_RULES.md`):
  - Header mapping and normalization.
  - Row-level parsing and type checks.
  - URL normalization and sitemap cross-check where sitemap available.
  - Deduplication and aggregation as configured.
- Outputs:
  - `seo_data/validated/<filename>.clean.csv` — cleaned CSV for analysis.
  - `seo_data/validated/<filename>.validation.md` — detailed validation report with error classification and mapping confidence.
- Halt on fatal validation errors; notify exporter and halt further processing until resolved.

3) Error handling
- Classification (applies per `docs/SEO_DATA_VALIDATION_RULES.md`): `fatal`, `critical`, `warning`, `info`.
- Fatal:
  - Action: stop pipeline, create ticket, notify exporter with validation report, request corrected export.
- Critical:
  - Action: flag dataset for manual review by analyst; limited auto-corrections allowed (e.g., percent → decimal conversion), otherwise request corrected export.
- Warning:
  - Action: log warnings in validation report and proceed with cleaned CSV; include caveats in downstream reports.
- Transient errors (e.g., partial upload failure): retry according to operational retry policy (e.g., 3 attempts with backoff), then escalate.

4) Approval checklist
- Before marking a cleaned dataset as `approved` for analysis, an analyst must verify and record the following:
  - [ ] Checksum verified and stored in metadata.
  - [ ] Header row validated and any alias mappings documented.
  - [ ] No `fatal` errors present.
  - [ ] Critical error rate below threshold (configurable; default 5%).
  - [ ] URL normalization confidence acceptable (majority `exact` or `heuristic` mappings; review `fuzzy` mappings manually).
  - [ ] PII check completed (no personal data in query values or URL query params).
  - [ ] Validation report attached to the clean CSV.
  - [ ] Ownership assigned (data owner and analyst) and pipeline run timestamp recorded.
- Approved datasets are moved or copied to `seo_data/validated/` and referenced by analysis jobs. Record approval in `seo_data/validation_log.md` with signer and timestamp.

Operational notes
- Retention and privacy: raw exports should be retained only in secure storage for the retention window; do not store raw exports in the code repository unless explicitly approved.
- Idempotency: use checksum and file provenance to avoid reprocessing the same export twice.

