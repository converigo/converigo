# PHASE 014 — CONVERTER RUNTIME REPORT

Summary
-------
- Scope: collect runtime evidence for failing conversions (PDF→JPG, JPG→PNG, PNG→JPG).
- Short conclusion: frontend is functional; backend failures are due to invalid test assets (placeholder files) causing signature validation failures (HTTP 400) and missing native dependencies for document conversions (poppler for pdf2image and native GTK libs for WeasyPrint) causing HTTP 500 errors.

Evidence collected
------------------

1) Test sample inspection (workspace: `tests/`)

- `tests/sample.jpg` — size: 22 bytes
  - Hex (first bytes): 706C616365686F6C6465722D6A70672D73616D706C65
  - ASCII: "placeholder-jpg-sample" — not a real JPEG file; no JPEG magic bytes (\xFF\xD8\xFF).
- `tests/sample.png` — size: 22 bytes (placeholder content)
- `tests/sample.pdf` — size: 49 bytes (placeholder content)

Command used to inspect sizes: `Get-Item 'c:\converigo\tests\sample.jpg','c:\converigo\tests\sample.png','c:\converigo\tests\sample.pdf'` (returned sizes above).

2) Upload / validation failures (HTTP 400)

- Log evidence (excerpt from `app/logs/app.log`):

  2026-07-10 21:08:04,327 WARNING app.routers.convert Upload failed during conversion: Uploaded file contents do not match the file type.

  (This message appears repeatedly during test runs where placeholder/invalid files were submitted.)

- Root cause: `app.utils.file_validator.validate_signature()` reads the uploaded file header and rejects files that do not start with expected magic bytes for the declared extension. The placeholder test files lack correct magic bytes, so validation raises FileValidationError and the router responds 400.

3) PDF → JPG runtime failures (HTTP 500)

- Log traceback (excerpt from `app/logs/app.log`):

  FileNotFoundError: [WinError 2] The system cannot find the file specified

  ...

  pdf2image.exceptions.PDFInfoNotInstalledError: Unable to get page count. Is poppler installed and in PATH?

  Result: 500 Internal Server Error returned by `/convert` when pdf2image attempted to call native Poppler utilities (pdfinfo / pdftoppm) but could not find them on the system PATH.

4) DOCX → PDF (related evidence)

- WeasyPrint/Weasy-related failures seen during other conversions (500) — log shows:

  OSError: cannot load library 'libgobject-2.0-0' ... ctypes.util.find_library() did not manage to locate a library called 'libgobject-2.0-0'

- Implication: native GTK/Pango/Cairo libraries required by WeasyPrint are not available in the environment.

5) Output folders

- Current `uploads/` directory: no persistent entries found during inspection (no saved placeholder outputs visible).
- Current `outputs/image/` directory: empty for top-level listing at inspection (no new outputs from the failing test runs).

Key root-cause hypotheses
-------------------------

- HTTP 400 cases: caused by invalid/placeholder test files that do not have correct magic bytes. The validator correctly rejects these — tests should use real sample assets, or tests should run with a relaxed validation flag.
- HTTP 500 (PDF): missing native Poppler utilities required by `pdf2image` (pdfinfo/pdftoppm). Installing Poppler and ensuring it is on PATH resolves pdf2image PDF→image failures.
- HTTP 500 (DOCX→PDF): missing GTK/Pango/Cairo native libraries (libgobject etc.) required by WeasyPrint. Installing the platform-specific system packages (or using an alternative conversion approach) will resolve these errors.

Recommendations (no code changes applied yet)
-------------------------------------------

1. Replace placeholder test assets with real sample files (valid JPEG/PNG/PDF) for Playwright/automated tests. Confirm magic bytes and file size > 1KB for realistic samples.
2. For PDF conversions, install Poppler (Windows: download Poppler binaries and add to PATH; Linux: apt install poppler-utils) so `pdf2image` can call `pdfinfo`/`pdftoppm`.
3. For docx→pdf or other WeasyPrint flows, install native GTK/Pango/Cairo dependencies required by WeasyPrint (or choose a different headless conversion tool that has fewer native deps).
4. Improve logging at the router boundary: log saved upload path, computed SHA256, and plugin resolved name before invoking engine — this makes it easier to correlate HTTP requests to saved files and engine errors.
5. Add a lightweight test-mode flag/setting to relax strict signature validation for CI/local tests where placeholder fixtures are used — or include proper binary fixtures in the test suite.

Next steps I can take (pick any):

- Run conversion requests locally with real sample assets and capture full request payload + server-side logs and engine outputs to produce a detailed timeline.
- Add enhanced request logging (saved_path + size + sha256 + plugin) to `app/routers/convert.py` and re-run tests to produce end-to-end evidence.
- Assist with platform-specific install instructions for Poppler and WeasyPrint native dependencies.

Files & logs referenced
-----------------------
- [app/logs/app.log](app/logs/app.log)
- [app/utils/file_validator.py](app/utils/file_validator.py)
- [app/routers/convert.py](app/routers/convert.py)
- Test assets: `tests/sample.jpg`, `tests/sample.png`, `tests/sample.pdf`

---

Prepared by: GitHub Copilot (GPT-5 mini) — Phase 014 initial runtime analysis.
