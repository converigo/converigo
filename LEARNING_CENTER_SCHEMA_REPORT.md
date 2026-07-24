# Learning Center Schema Report

## Summary
- Added a reusable validator at app/services/article_schema.py for Learning Center article JSON.
- Moved article validation responsibility out of ArticleService so the service now reuses the shared validator.
- Added regression tests covering required fields, slug rules, section validation, FAQ validation, and service integration.

## What Was Added
### ArticleSchemaValidator
- Validates required fields.
- Validates optional fields.
- Enforces type validation.
- Validates slug format.
- Validates section structure.
- Validates FAQ structure.

### ArticleService
- Reuses the shared validator instead of embedding validation logic.

## Files Added
- app/services/article_schema.py
- tests/test_article_schema.py

## Verification
- Ran: .\.venv\Scripts\python.exe -m pytest -q tests/test_article_schema.py tests/test_article_service.py
- Result: 4 passed in 1.69s
