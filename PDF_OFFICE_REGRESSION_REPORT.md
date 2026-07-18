# PDF_OFFICE_REGRESSION_REPORT

## Problem

Run full test suite after PDF→office changes to ensure no regressions and that PDF Office changes did not break other converters.

## Changes

Git working tree (uncommitted) snapshot at test time:

- Modified tracked files:
  - `app/engines/archive_engine.py` (M)
  - `app/engines/document_engine.py` (M)
  - `app/routers/convert.py` (M)
  - `app/routers/home.py` (M)
  - `app/services/conversion_service.py` (M)

- Untracked / added files (examples):
  - `PDF_OFFICE_VALIDATION_REPORT.md`
  - many PDF_OFFICE_* reports and docs
  - `scripts/manual_pdf_office_tests.py`
  - `scripts/collect_output_info.py`
  - new/added `tests/certified/pdf/*` and related test helpers

Allowed change set per instruction:
- `app/engines/document_engine.py` — ALLOWED
- PDF_OFFICE reports — ALLOWED
- optional PDF test files — ALLOWED

Observed violations (files changed but NOT in allowed list):
- `app/engines/archive_engine.py`
- `app/routers/convert.py`
- `app/routers/home.py`
- `app/services/conversion_service.py`

## Tests

- Command executed: `.venv\Scripts\python.exe -m pytest -q`
- Results: 439 passed, 2 skipped, 9 warnings
- Test duration: ~4m37s

## Result

- All tests passed (no failing tests observed).
- However, the git-diff shows modifications to multiple files outside the allowed change list. These are potential unintended modifications and must be reviewed before approving or committing any changes.

## Risk

- Low functional risk from test run (suite green).
- Moderate repository risk: unapproved modifications to router and service files (`app/routers/*`, `app/services/*`) may affect API behavior or registry and must be audited. If these were not intended, revert them.
- Additional untracked test/docs/scripts present in working tree increase risk of accidental commits; tidy working tree before merging.

## Approval Status

- Tests: PASS
- Change audit: FAIL (non-allowed files modified: see Observed violations)

Action items before approval:

- Review diffs for `app/engines/archive_engine.py`, `app/routers/convert.py`, `app/routers/home.py`, and `app/services/conversion_service.py` and confirm whether changes are intended.
- If unintended, revert those files to HEAD.
- Remove or move untracked helper scripts if they should not be committed.
