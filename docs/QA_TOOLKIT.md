# QA Toolkit (canonical)

This document summarizes the canonical QA tools in `qa_tools/` and how to run the common checks used by Converigo engineers.

## Location
- Canonical toolkit: `qa_tools/`

## Key scripts
- `qa_tools/route_inspector.py` — lists FastAPI routes and validates `/health`.
- `qa_tools/workspace_inspector.py` — Playwright-based smoke checks and DOM assertions.
- `qa_tools/hero_capture.py` — capture full-page screenshots at specified breakpoints.
- `qa_tools/image_parity.py` — image diff util (Pillow-based).
- `qa_tools/large_upload_test.py` — large-file upload harness (modes: `dummy`, `ffmpeg_bytes`, `ffmpeg_duration`).

## Common commands
Run from the repository root and ensure `CONVERIGO_BASE_URL` is set when needed.

```powershell
# route listing and health
$env:PYTHONPATH='.'; python qa_tools\route_inspector.py

# Playwright smoke (requires Playwright installed and browsers installed)
$env:CONVERIGO_BASE_URL='http://127.0.0.1:8000'; python qa_tools\workspace_inspector.py

# Capture pages at multiple breakpoints
$env:CONVERIGO_BASE_URL='http://127.0.0.1:8000'; python qa_tools\hero_capture.py --pages / /formats /blog --breakpoints 375x812 360x800
```

## Notes
- Prefer the toolkit scripts over ad-hoc `tmp_*` scripts.
- Do not hardcode URLs; use `CONVERIGO_BASE_URL`.
- If Playwright is not available locally, capture via the running server and a browser manually or use CI-based Playwright.
