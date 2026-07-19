# Converter Lifecycle Update Report

Date: 2026-07-18

Scope: Phase 2 — Mark specified converters as `deprecated` in the contract registry so they are not surfaced to users. No metadata files were deleted. No engine changes or feature additions.

1) Converters marked `deprecated` (files added/updated)

- docx-to-jpg — `app/data/converters/docx-to-jpg.contract.json` (added)
- docx-to-xlsx — `app/data/converters/docx-to-xlsx.contract.json` (added)
- docx-to-ppt — `app/data/converters/docx-to-ppt.contract.json` (added)
- xlsx-to-ods — `app/data/converters/xlsx-to-ods.contract.json` (already deprecated)
- xlsx-to-docx — `app/data/converters/xlsx-to-docx.contract.json` (added)
- xlsx-to-ppt — `app/data/converters/xlsx-to-ppt.contract.json` (added)
- ppt-to-jpg — `app/data/converters/ppt-to-jpg.contract.json` (added)
- ppt-to-docx — `app/data/converters/ppt-to-docx.contract.json` (added)
- ppt-to-xlsx — `app/data/converters/ppt-to-xlsx.contract.json` (added)

Reason: These converters are not certified, have no tested engine path (direct conversions unsupported), or would require multi-step conversions that are unreliable for production recommendations. Marking them `deprecated` prevents them from appearing in recommendations while preserving files for audit/history.

2) Recommendation engine behavior changes

- `app/services/converter_registry_service.py`: `get_active()` now returns contracts whose `lifecycle_status` is either `active` or conceptually `certified` (so deprecated entries are excluded).
- `app/services/converter_data_service.py`: `_is_production_ready()` now treats `active` and `certified` as production-ready; deprecated contracts are excluded from public/recommendation listings.

Note: I did not change the contract validation allowed values set in `ConverterRegistryService.VALID_LIFECYCLE_STATUSES` to avoid breaking existing contract validation tests. If you plan to start using `certified` as a literal lifecycle_status in contract files, we should add `certified` to `VALID_LIFECYCLE_STATUSES` and update contract files accordingly in a follow-up.

3) Files changed/added

- Modified: `app/services/converter_registry_service.py`
- Modified: `app/services/converter_data_service.py`
- Added: `app/data/converters/docx-to-jpg.contract.json`
- Added: `app/data/converters/docx-to-xlsx.contract.json`
- Added: `app/data/converters/docx-to-ppt.contract.json`
- (Confirmed existing) `app/data/converters/xlsx-to-ods.contract.json` (already deprecated)
- Added: `app/data/converters/xlsx-to-docx.contract.json`
- Added: `app/data/converters/xlsx-to-ppt.contract.json`
- Added: `app/data/converters/ppt-to-jpg.contract.json`
- Added: `app/data/converters/ppt-to-docx.contract.json`
- Added: `app/data/converters/ppt-to-xlsx.contract.json`
- Added: `CONVERTER_REGISTRY_CLEANUP_REPORT.md` (summary)
- Added earlier: `PPT_FINAL_DECISION_REPORT.md`

4) Testing

- Ran: `c:\converigo\.venv\Scripts\python.exe -m pytest -q tests/certified/`
- Result: `60 passed, 1 skipped` (certified suite unchanged)

5) Certification validator

- Command requested: `python -m app.validators.certification_validator`
- Outcome: module not found — there is no `app.validators.certification_validator` module in the workspace. I attempted `c:\converigo\.venv\Scripts\python.exe -m app.validators.certification_validator` and received `No module named app.validators.certification_validator`.

Recommendation: if you have a validator module path/name, provide it and I will run it; or add a validator implementation under `app/validators/` and I can run it in a follow-up.

6) Compliance with constraints

- No UI or SEO changes made.
- No new converter implementations were added.
- No metadata files were deleted.
- Converter engines were not modified.

Next steps (awaiting review):

- Confirm you want the new `.contract.json` files committed as-is (they are deprecated — safe to add). If you prefer to set existing non-contract metadata JSON entries (`app/data/converters/*.json`) `active: false`, provide a list and I will update them.
- If you want `certified` to be an accepted contract lifecycle value, I can update `VALID_LIFECYCLE_STATUSES` and migrate any contracts in a follow-up.

