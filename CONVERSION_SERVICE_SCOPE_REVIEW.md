# Conversion Service Scope Review

## Changes

- `app/services/conversion_service.py`
  - Added `PDFEmptyError`, `PDFPasswordProtectedError`, and `PDFValidationError` subclasses of `UnsupportedConversionError`.
  - Extended `UnsupportedConversionError` to accept a custom message.
  - Preserved `UnsupportedConversionError` propagation from conversion plugins to API response handling.

## Reason

- `app/engines/document_engine.py` now performs explicit PDF validation before PDF-to-DOCX conversion.
- The new exceptions are required to represent PDF-specific validation failures clearly and allow the API layer to return the proper `UNSUPPORTED_CONVERSION` error semantics.
- This change is directly tied to PDF engine recovery and the new validation/reporting logic.

## Impact

- Affects PDF conversion flow only, specifically PDF validation and error propagation.
- Does not introduce new conversion features for unrelated formats.
- Does not change frontend, deployment, SEO, or registry behavior.
- Supports cleaner API error handling for invalid PDF inputs.

## Decision

KEEP

## Risk

- Low: change is isolated to Fehler handling in `ConversionService` and is required by the updated `DocumentEngine` PDF validation path.
- Medium-low: if `UnsupportedConversionError` propagation is altered incorrectly, API clients may receive a generic 500 instead of the intended 422/UNSUPPORTED_CONVERSION response. Current implementation preserves the existing exception semantics.

## Validation

- `git diff origin/main --name-only` shows only PDF engine-related files changed.
- `app/engines/document_engine.py` and `tests/certified/pdf/*` are in scope.
- Continued developer tooling files, Continue/Ollama config, and unrelated reports are not present in the branch diff.
- `python -m pytest -q tests/certified/pdf` passed: `38 passed`.
- Full suite ran in `.venv` with current environment result: `416 passed, 1 skipped`.
