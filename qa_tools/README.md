# QA Toolkit - Converigo

Purpose
- A single, canonical collection of QA utilities for local development and validation.

How to run
- Set `CONVERIGO_BASE_URL` environment variable if non-default. Default: `http://127.0.0.1:8000`
- Python scripts: run with the activated virtualenv in repo root, e.g.: 

```powershell
$env:CONVERIGO_BASE_URL = 'http://127.0.0.1:8000'
; .\.venv\Scripts\Activate.ps1
; python qa_tools\route_inspector.py
```

Expected output
- Each tool prints a concise human-readable summary and writes artifacts into `validation_assets/` when applicable.

Environment variables
- `CONVERIGO_BASE_URL` — base URL used by Playwright/TestClient checks. Defaults to `http://127.0.0.1:8000`.

Large upload test
- `qa_tools/large_upload_test.py` — generates test MP4s and posts to the `/convert` endpoint. Usage:

```powershell
$env:CONVERIGO_BASE_URL = 'http://127.0.0.1:8000'
; .\.venv\Scripts\Activate.ps1
; python qa_tools\large_upload_test.py --mode dummy
; python qa_tools\large_upload_test.py --mode ffmpeg_bytes --sizes 5 10 25
```

Modes:
- `dummy`: fast file creation by allocating bytes (no ffmpeg required).
- `ffmpeg_bytes`: uses `ffmpeg -fs` to try to create a file near target bytes.
- `ffmpeg_duration`: creates an audio duration-based MP4 via ffmpeg.

Notes:
- The temporary files are written under `tmp_large_upload_tests/`.
- This file consolidates previously duplicated `tmp_large_upload_tests*.py` scripts.

Notes
- These tools are intended for local dev and QA. They do not modify application code or production behavior.
