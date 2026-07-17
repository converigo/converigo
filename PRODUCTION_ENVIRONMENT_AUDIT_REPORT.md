# PRODUCTION_ENVIRONMENT_AUDIT_REPORT

## Environment Difference
- **Railway build method differs from Dockerfile expectation**
  - `railway.json` specifies `build.builder = "DOCKERFILE"` (so Dockerfile should be used), but **any fallback/misconfiguration** could lead to using Nixpacks instead.
  - `nixpacks.toml` installs only `["python311", "ffmpeg"]`—**no LibreOffice / system libs beyond ffmpeg**.
- **Output directory handling mismatch (highest likelihood)**
  - `railway.toml`/deploy docs recommend:
    - `UPLOAD_DIR=/app/uploads`
    - `OUTPUT_DIR=/app/outputs`
  - `app/core/settings.py` maps `settings.OUTPUT_DIR` from `OUTPUT_DIR` env var.
  - `app/main.py` creates `settings.OUTPUT_DIR` and mounts `/outputs` to that absolute directory.
  - **But** `DocumentEngine` hardcodes conversion output base as:
    - `output_dir = Path("outputs") / "document"`
  - This means conversion output is written to a **relative** `./outputs/document` (depends on CWD), not necessarily `/app/outputs/document`.
- **Current Working Directory (CWD) dependency**
  - `Dockerfile` sets `WORKDIR /app`.
  - If production runtime CWD differs (local vs Railway, or custom start command), then `Path("outputs")` resolves differently.
- **Filesystem permission / cleanup behavior**
  - `CleanupService.clean_old_files()` scans and deletes files in:
    - `settings.UPLOAD_DIR`
    - `settings.OUTPUT_DIR`
  - If output files are written to `./outputs/...` instead of `settings.OUTPUT_DIR`, they may:
    - not be mounted/persisted as expected
    - be cleaned up unexpectedly (if cleanup scans a relative directory differently than intended)
- **Temporary directory behavior (secondary)**
  - `tempfile.TemporaryDirectory(...)` usage exists in other conversion paths (e.g., PDF→PPTX uses `dir=str(output_dir)`), but **PDF→DOCX path doesn’t explicitly set temp dir**.
  - `pdf2docx` internally may create temp files under `/tmp` or via Python temp APIs; production containers can differ in `/tmp` size/permissions.
- **No converter logic difference detected**
  - PDF→DOCX uses `pdf2docx.Converter` (Python-level conversion), not LibreOffice/soffice.
  - Therefore missing LibreOffice packages are **less likely** to directly break PDF→DOCX compared to output path/CWD/permissions.

## Root Cause
- **Output path mismatch caused by hardcoded relative output directory in `DocumentEngine`**:
  - `DocumentEngine` writes to `./outputs/document` (relative path).
  - Production expects writes under `settings.OUTPUT_DIR` (recommended: `/app/outputs`).
  - If Railway run CWD differs or permissions differ, PDF→DOCX can fail to persist the expected output or can fail due to inability to create directories / write files.

## Evidence
- `Dockerfile`:
  - `WORKDIR /app`
  - Runs `uvicorn app.main:app ...`
- `railway.json`:
  - `build.builder = "DOCKERFILE"`
- `nixpacks.toml`:
  - Installs only `python311` and `ffmpeg` at setup; no extensive system libs (LibreOffice, Cairo/GTK/Pango, etc.)
- `app/core/settings.py`:
  - `OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "outputs"))`
  - `UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))`
- `app/main.py`:
  - Ensures `settings.OUTPUT_DIR` exists and mounts `/outputs` to `settings.OUTPUT_DIR`
- `app/engines/document_engine.py`:
  - `DocumentEngine.convert()` sets:
    - `output_dir = Path("outputs") / "document"`
  - For PDF→DOCX, `_convert_pdf_to_docx()` uses that `output_dir`.
- `app/services/conversion_service.py`:
  - Output validation allows roots:
    - `{resolved_output_dir, resolved_workdir, resolved_source_dir}`
  - `resolved_output_dir = settings.OUTPUT_DIR.resolve(...)`
  - `resolved_workdir = Path.cwd().resolve(...)`
  - If `./outputs/document` resolves outside expected directory roots (depending on CWD), conversion can error ("Output path is outside the allowed output directory") or produce output not found by caller.
- `app/services/cleanup_service.py`:
  - Cleanup only targets `settings.UPLOAD_DIR` and `settings.OUTPUT_DIR`.
  - If conversion writes to a relative `./outputs` not equal to `settings.OUTPUT_DIR`, persistence and cleanup behavior diverge from local.

## Recommended Fix
- Align `DocumentEngine` output base with `settings.OUTPUT_DIR` by ensuring the runtime CWD and/or `OUTPUT_DIR` mapping results in `Path("outputs") / "document"` landing under `/app/outputs/document`.
  - **Non-code options (preferred due to constraints):**
    - Ensure Railway container starts with `WORKDIR /app` (already in Dockerfile) and that the deployed command doesn’t override working directory.
    - Ensure environment variables are set on Railway:
      - `OUTPUT_DIR=/app/outputs`
      - `UPLOAD_DIR=/app/uploads`
    - Ensure mounted volume includes **both**:
      - `/app/outputs`
      - and that no unexpected relative output path is used.
- Confirm build method used by Railway is truly Dockerfile-based:
  - Validate Dockerfile execution logs during deployment.
  - If any stage uses Nixpacks, extend Nixpacks system packages to match Dockerfile requirements (especially if other formats rely on system libs).
- Validate runtime permissions for:
  - `/app/outputs`
  - the internal relative `./outputs/document` path resolved under container CWD.

## Risk
- Medium risk: adjusting only environment/build parameters can fix path/CWD issues but may not address issues originating from `pdf2docx` temp-file handling.
- If `pdf2docx` depends on temp filesystem capacity/permissions, failures may persist even with correct output paths.
- If Railway unintentionally uses Nixpacks instead of Dockerfile, dependency/system-lib availability may differ, affecting conversions beyond PDF→DOCX.

