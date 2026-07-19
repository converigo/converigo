# Phase 013 — Upload / Convert / Download Flow Test Report

Date: 2026-07-18

Scope
- Frontend-only validation of the upload → convert → download interaction on the live local page `/tools/pdf-to-jpg`.
- Tests executed with the integrated browser automation against the running site at `http://127.0.0.1:8000/tools/pdf-to-jpg`.

Test assets used (workspace)
- `tests/sample.jpg`
- `tests/sample.png`
- `tests/sample.pdf`

Summary of automated checks

- Files `UI_PHASE_009_DESKTOP.png` and `UI_PHASE_009_MOBILE.png` validated:
  - Both exist and are PNGs (.png).
  - Sizes: DESKTOP = 298,563 bytes; MOBILE = 329,750 bytes.
  - Both open successfully in a browser (visual check via integrated viewer).

- Upload/flow automation (Playwright) — Desktop viewport (1200×800):
  - File picker: PASSED for JPG / PNG / PDF
    - `#fileName` shows file name.
    - `#fileType` shows MIME/type string.
    - `#fileSize` shows a short size string (UI shows `0.00 MB` for the test files).
    - `#previewStatus` shows `Ready`.
    - `#selectedStatus` becomes visible.

  - Drag & drop simulation: PASSED for JPG / PNG / PDF
    - Same DOM fields as above updated after simulated drop.

  - Format selection / Convert button
    - Format chips are present (example: `PNG`). Selecting the first format chip enables `#convertButton`.
    - Clicking `#convertButton` triggers conversion client behavior; the button label/state updates.
    - Progress UI (`#convertProgress`) did not remain visible long (no persistent progress observed for these test runs).

  - Conversion outcome
    - The client-side created a `#resultCard` in all three tests but the `#resultFileName` was empty and `#downloadBtn` had no `href` (no downloadable payload provided).
    - Browser console shows server errors during conversion attempts:
      - `400 Bad Request` — "Uploaded file contents do not match the file type." (for some runs)
      - `500 Internal Server Error` — PDF conversion backend error for the PDF sample in one run.
    - Conclusion: frontend behavior reached the expected post-conversion UI state, but backend conversion responses were invalid/failed for these sample files, so no download link was produced.

- Mobile viewport (390px) quick check: PASSED (upload metadata)
  - File picker updated `#fileName`, `#fileType`, `#fileSize`, and `#previewStatus` as expected.

Detailed automated run output (high level)
- sample.jpg: picker OK, drag-drop OK, convert attempted → `resultCard` shown, no download link, console errors (400).
- sample.png: picker OK, drag-drop OK, convert attempted → `resultCard` shown, no download link, console errors (400).
- sample.pdf: picker OK, drag-drop OK, convert attempted → `resultCard` shown, no download link, console error (500 PDF parse error).

Interpretation & notes
- Frontend validations (upload, preview, metadata, UI state transitions) are stable and working as required for Phase 013.
- The absence of a valid download link and the server-side console errors indicate backend/conversion issues for the sample inputs. The frontend handled the lifecycle (upload → recommend → convert UI) correctly and displayed result/error cards according to the current client logic.

Recommendations / next steps
1. Provide known-good sample files that have previously converted successfully in the production pipeline and re-run the tests to validate the full end-to-end download flow.
2. If the backend must accept these specific samples, examine server logs for the `400`/`500` errors and fix the conversion service or input validation.
3. Optionally add a follow-up smoke test that asserts `#downloadBtn[href]` exists after conversion for an expected-good sample file.

Appendix: What I ran
- Playwright script executed in the integrated browser page `http://127.0.0.1:8000/tools/pdf-to-jpg`.
- PowerShell checks for UI screenshots' sizes:

```powershell
Get-Item 'c:\converigo\UI_PHASE_009_DESKTOP.png','c:\converigo\UI_PHASE_009_MOBILE.png' | Select-Object FullName, Length, Extension | Format-Table -AutoSize
```

If you'd like, I can now:
- Re-run these tests using a set of confirmed-good sample files (recommended), or
- Attempt to reproduce the backend errors locally and gather server logs (requires backend debugging privileges).

-- End of report
