# XLSX Test Fixture Update

Summary:
- Created a valid XLSX regression fixture: `tests/fixtures/sample_valid.xlsx`.
- Updated `tests/test_runtime_image_and_doc_conversion.py` to prefer the fixture for XLSX→PDF runtime test.
- Ran `pytest tests/certified/` — result: `60 passed, 1 skipped` (certified suite clean).

Fixture contents:
- Sheet name: `Data`
- Columns: `id` (numeric), `text` (text), `amount` (numeric), `date` (date)
- 10 rows of sample data (id 1..10), `amount` increments of 10.5, sequential dates from 2020-01-02.

Purpose:
- Ensure XLSX→PDF failures are not caused by an invalid sample file. The previous placeholder `tests/sample.xlsx` was a non-zip placeholder causing `BadZipFile` during `openpyxl.load_workbook`.

Next steps:
1. (Optional) Replace any other legacy sample XLSX files with the validated fixture.
2. Add the fixture-based XLSX→PDF test to CI (certified suite already runs and passed locally).

