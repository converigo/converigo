# Converigo Development Policy (Locked)

This document defines mandatory local development rules for Converigo. Follow these rules for all engineering work to ensure environment parity, reproducible QA, and safe local testing.

## Development server
- Official development URL: `http://127.0.0.1:8000`
- Never run a second development server on a different port. Port 8001 is forbidden.
- Before running Playwright or other UI tooling:
  1. Check `http://127.0.0.1:8000/health`.
  2. If healthy, reuse the running server.
  3. If not healthy, start a single server bound to port `8000` only.

## During UI work
- Keep the server running during development (hot reload enabled when available).
- After each UI modification:
  - Save files.
  - Wait for hot reload to complete.
  - Verify the page loads in desktop and mobile views.
  - Check browser console for errors.
  - Capture before/after screenshots for desktop and mobile.

## Reporting checklist (after each visual change)
- Server Running — `http://127.0.0.1:8000`
- Hot Reload — observed and complete
- Console Clean — no new errors/warnings
- Desktop Updated — visual verification and screenshot
- Mobile Updated — visual verification and screenshot

Pause for review after reporting. Do not proceed until review passes.

## Pre-completion steps
Before marking a task complete run the following in the workspace root:

```powershell
python -m compileall .
python qa_tools/route_inspector.py
python -m pytest tests -q  # QA smoke (where applicable)
python qa_tools/workspace_inspector.py  # Playwright smoke (requires Playwright installed)
```

All steps must PASS before a change is considered complete.

## Rationale
Centralizing the dev server and enforcing checks reduces accidental automation against production-like endpoints, ensures Playwright captures a single canonical environment, and keeps CI and local results consistent.
