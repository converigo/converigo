# Format Knowledge Service Import Investigation

## Summary

- The application startup failure is caused by a missing Python module: `app.services.format_knowledge_service`.
- `app/routers/formats.py` imports `FormatKnowledgeService` from this missing module and attempts to instantiate it for format knowledge enrichment.
- The current repository workspace does not contain `app/services/format_knowledge_service.py`.
- Git history also contains no commits referencing `app/services/format_knowledge_service.py`, indicating the file was likely never added or was removed before the current branch.

## Evidence

- `app/routers/formats.py` contains:
  - `from app.services.format_knowledge_service import FormatKnowledgeService`
  - `knowledge_service = _format_knowledge_service()`
  - `enrichment = knowledge_service.build_enrichment(normalized)`

- `app/services/` directory contents do not include `format_knowledge_service.py`.
- `git log --all --oneline -- app/services/format_knowledge_service.py` returned no results.
- Repository-wide search for `FormatKnowledgeService`, `build_enrichment`, or `format_knowledge_service` only found the import and route usage in `app/routers/formats.py`.

## Impact

- Any request to `/formats/{format_name}` will fail if the code path reaches the knowledge enrichment step, because the missing import prevents the application from loading.
- This blocks the intended render and SEO validation of format knowledge pages such as `/formats/png`.
- The underlying data file `app/data/format_knowledge/png.json` is structurally valid, but the runtime path cannot load until the missing service module is restored.

## Recommendations

1. Restore or add `app/services/format_knowledge_service.py`.
2. Ensure the service exposes `FormatKnowledgeService` and a `build_enrichment(format_name: str) -> dict[str, Any]` method.
3. Confirm the service reads JSON files from `app/data/format_knowledge`, validates them, and returns the expected `format_knowledge` enrichment payload.
4. Re-run app startup and `/formats/png` validation once the service module is available.

## Notes

- The missing service is a runtime dependency, not a content issue with `png.json`.
- Existing format knowledge schema definitions live in `app/services/knowledge_schema.py`, which can provide validation guidance for the restored service.
