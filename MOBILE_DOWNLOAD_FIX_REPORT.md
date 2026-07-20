# Mobile Download Fix Report

Date: 2026-07-21

## Scope

This fix targets the mobile download flow for converted files without changing the converter engine.

## What changed

### Backend
- Added a dedicated download route at /download/{path:path}
- The route serves files from the configured output directory with:
  - Content-Disposition: attachment; filename=...
  - MIME type based on file extension
  - a predictable filename from the server side

### Frontend
- Updated [app/static/js/download/download_manager.js](app/static/js/download/download_manager.js) to trigger download through a direct anchor click from a user gesture
- Added a fallback navigation to the same URL if the browser blocks the initial click
- Kept the flow compatible with the existing download button behavior

## Why this addresses the issue

Android browsers are stricter about download handling than desktop browsers. The previous flow relied on a plain anchor link to a static file path, which often resulted in inline/open behavior instead of a real saved download. The new route forces the browser to treat the response as a file attachment, and the frontend attempts the download directly from a click event.

## Verification

### Automated regression test
Command run:
- .\.venv\Scripts\python.exe -m pytest -q tests/test_mobile_download_flow.py

Result:
- 1 passed

## Notes

This fix does not modify conversion logic. It only improves the download response and the client-side trigger path.
