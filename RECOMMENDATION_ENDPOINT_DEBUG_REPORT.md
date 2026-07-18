# Recommendation Endpoint Debug Report

## Summary

The frontend requests `/recommend/pdf`, but the backend recommendation router was not registered in `app/main.py`. This caused FastAPI to return `404 NOT FOUND` for the recommendation endpoint, even though `app/routers/recommend.py` defines `GET /recommend/{source_format}` correctly.

## Missing Route Cause

- `app/routers/recommend.py` defines an APIRouter with `prefix="/recommend"`.
- `app/main.py` imported `recommend_router` but did not call `app.include_router(recommend_router)` before startup.
- As a result, the recommendation endpoint never became part of the application route table.

## Correct Endpoint

- The correct backend endpoint is:
  - `GET /recommend/{source_format}`
- For the frontend case, the specific route should be:
  - `GET /recommend/pdf`

## Required Fix

- Register the recommendation router in `app/main.py`:
  - add `app.include_router(recommend_router)` in the routers section.

## Regression Risk

- Low: this is a router registration issue rather than a logic or runtime bug.
- Impact: all recommendation endpoints were unavailable until the router was included.
- Risk factors:
  - If route ordering or path conflicts exist, ensure `recommend_router` is included in a position that does not interfere with other prefixes.
  - Add a regression test or integration check for `/recommend/pdf` to ensure route availability after future refactors.

## Recommended Regression Tests

- Integration test covering `GET /recommend/pdf` returns `200` and valid recommendation structure.
- Smoke test verifying `/recommend/{source_format}` is included in the app route table.
