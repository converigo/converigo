# PDF Test Path Normalization Report

## Problem

PDF certification tests used a hardcoded relative output path `outputs/document` while the engine uses `settings.OUTPUT_DIR` in production. This mismatch risks tests passing locally but failing in production.

## Fix

Updated all PDF certification tests to use `settings.OUTPUT_DIR` for output paths.

Example replacement:

Before:

```
output_path = Path("outputs/document") / filename
```

After:

```
from app.core.settings import settings
output_path = settings.OUTPUT_DIR / "document" / filename
```

## Files Changed

- tests/certified/pdf/test_pdf_to_docx_certified.py
- tests/certified/pdf/test_pdf_to_excel_certified.py
- tests/certified/pdf/test_pdf_to_jpg_certified.py
- tests/certified/pdf/test_pdf_to_odt_certified.py
- tests/certified/pdf/test_pdf_to_ppt_certified.py

## Validation

- Ran targeted PDF tests: `pytest -q tests/certified/pdf` → `38 passed, 0 failed`.
- Ran full test suite: `pytest -q` → `439 passed, 2 skipped`.

## Risk

LOW — changes are limited to tests and align tests with production settings.
