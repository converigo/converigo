# Office Final Decision Report

Decisions implemented:

- DISABLED (temporary): `xlsx-to-ods`
  - Reason: plugin existed but engine mapping prevented runtime conversion. Demand low; disabling reduces user confusion and avoids recommending a broken conversion.

- KEEP: `xlsx-to-pdf`, `ppt-to-pdf`, `docx-to-pdf`
  - Reason: verified stability (XLSX→PDF certified; PPT→PDF local pass + regression test added; DOCX→PDF certified earlier).

Actions taken in repo:
- `app/data/converters/xlsx-to-ods.contract.json` — set `lifecycle_status` to `inactive`.
- `RECOMMENDATION_CLEANUP_PLAN.md` — updated to list `xlsx-to-ods` under DISABLE (temporary).
- Added regression: `tests/certified/office/test_ppt_to_pdf_certified.py` to assert PPTX→PDF conversion end-to-end with `tests/sample.pptx`.

Next recommended steps (separate PRs):
1. Add CI job running `tests/certified/office/test_ppt_to_pdf_certified.py` on PRs to catch environment regressions.
2. If `xlsx-to-ods` should be re-enabled later, implement `DocumentEngine` support for `ods` target and add regression coverage `tests/certified/office/test_xlsx_to_ods_certified.py`.
