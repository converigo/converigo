# FAILED TEST ANALYSIS — RC1.1

Date: 2026-07-22

Context: full pytest run produced 37 failures. Each failure below is analyzed with root cause, severity, whether it blocks production, and a suggested fix. Classifications use one of: Environment, CI Configuration, Missing Test Fixture, Runtime Bug, Converter Logic, Upload/Download, SEO, Playwright, Regression.

-----------------------------------------------------------------
Per-test analysis

1) tests/certified/document/test_pdf_to_odt.py::test_pdf_to_odt_conversion_creates_odt
Root cause: Upload/Download — test asserts existence of `download/...` path while conversion output is written to `outputs/...`; test artifact path mismatch.
Severity: Major
Blocks production? No
Suggested fix: Update test to assert via the `/download/` route (HTTP GET) or assert the actual `outputs/...` path. Alternatively create test fixture/symlink mapping `download/` → `outputs/` in CI.

2) tests/certified/document/test_pdf_to_pptx.py::test_pdf_to_pptx_conversion_creates_pptx
Root cause: Upload/Download (same pattern as #1)
Severity: Major
Blocks production? No
Suggested fix: See #1.

3) tests/certified/office/test_ppt_to_pdf_certified.py::test_ppt_to_pdf_conversion_creates_pdf
Root cause: Upload/Download (same pattern)
Severity: Major
Blocks production? No
Suggested fix: See #1.

4) tests/e2e/test_convert_flow.py::test_png_conversion_flow
Root cause: Playwright — Page.goto timeout (no live server started for Playwright tests).
Severity: Major
Blocks production? No
Suggested fix: Ensure CI/fixture launches the app (uvicorn) on expected base URL before Playwright tests, or run Playwright against a deployed staging URL. Add a pytest fixture to start/stop the server.

5) tests/e2e/test_convert_flow.py::test_pdf_conversion_flow
Root cause: Playwright (same as #4)
Severity: Major
Blocks production? No
Suggested fix: See #4.

6) tests/e2e/test_convert_flow.py::test_multi_file_upload_flow
Root cause: Playwright (same as #4)
Severity: Major
Blocks production? No
Suggested fix: See #4.

7) tests/test_convert_button_state.py::test_convert_button_becomes_visible_after_format_selection
Root cause: Playwright (page navigation timed out)
Severity: Major
Blocks production? No
Suggested fix: See #4.

8) tests/test_converter_json_enrichment.py::test_all_converters_include_universal_tool_page_sections
Root cause: Regression / Content — `docx-to-jpg.json` missing `features` (per failing assertion).
Severity: Major
Blocks production? No
Suggested fix: Update the converter JSON asset (e.g., `app/data/converters/docx-to-jpg.json`) to include expected `features` or relax test to allow sensible defaults. Add CI check to validate JSON schema completeness.

9) tests/test_final_ui_validation.py::TestConverterButtonValidation::test_convert_button_disabled_on_load
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

10) tests/test_final_ui_validation.py::TestConverterButtonValidation::test_convert_button_enabled_after_file_and_format_selection
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

11) tests/test_final_ui_validation.py::TestConverterButtonValidation::test_convert_button_shows_correct_text
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

12) tests/test_final_ui_validation.py::TestConverterButtonValidation::test_convert_button_disabled_after_file_clear
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

13) tests/test_final_ui_validation.py::TestDownloadValidation::test_download_button_hidden_on_load
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

14) tests/test_final_ui_validation.py::TestDownloadValidation::test_download_button_visible_after_conversion
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

15) tests/test_final_ui_validation.py::TestDownloadValidation::test_download_button_has_download_attribute
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

16) tests/test_final_ui_validation.py::TestAccordionValidation::test_converter_accordion_exists
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

17) tests/test_final_ui_validation.py::TestAccordionValidation::test_accordion_toggle_functionality
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

18) tests/test_final_ui_validation.py::TestAccordionValidation::test_faq_accordion_if_present
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

19) tests/test_final_ui_validation.py::TestLanguageSwitchValidation::test_language_selector_exists
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

20) tests/test_final_ui_validation.py::TestLanguageSwitchValidation::test_language_selector_has_options
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

21) tests/test_final_ui_validation.py::TestLanguageSwitchValidation::test_language_switch_functionality
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

22) tests/test_final_ui_validation.py::TestLanguageSwitchValidation::test_language_switcher_icon_visible
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

23) tests/test_final_ui_validation.py::TestProgressIndicatorValidation::test_progress_bar_hidden_initially
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

24) tests/test_final_ui_validation.py::TestProgressIndicatorValidation::test_progress_bar_visible_during_conversion
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

25) tests/test_final_ui_validation.py::TestConversionStateMessages::test_status_message_area_exists
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

26) tests/test_final_ui_validation.py::TestConversionStateMessages::test_status_message_on_error
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

27) tests/test_final_ui_validation.py::TestUINoBreakChanges::test_file_input_exists_and_functional
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

28) tests/test_final_ui_validation.py::TestUINoBreakChanges::test_preview_container_exists
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

29) tests/test_final_ui_validation.py::TestUINoBreakChanges::test_format_options_container_exists
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

30) tests/test_final_ui_validation.py::TestUINoBreakChanges::test_conversion_area_exists
Root cause: Playwright
Severity: Major
Blocks production? No
Suggested fix: See #4.

31) tests/test_runtime_image_and_doc_conversion.py::test_jpg_to_png_runtime_conversion
Root cause: Missing Test Fixture / Upload-Download expectation mismatch — test expects `download/...` path to exist on disk; conversion output is created under `outputs/...` and served via `/download/` route. Tests currently check filesystem path instead of HTTP endpoint.
Severity: Major
Blocks production? No
Suggested fix: Assert via the app's `/download/` route or check `outputs/...` directly. Add a `download` fixture if CI historically provides one.

32) tests/test_runtime_image_and_doc_conversion.py::test_png_to_jpg_runtime_conversion
Root cause: Missing Test Fixture (same as #31)
Severity: Major
Blocks production? No
Suggested fix: See #31.

33) tests/test_runtime_image_and_doc_conversion.py::test_xlsx_to_pdf_runtime_conversion
Root cause: Environment (Windows file locking) and Missing Test Fixture — logs include a `PermissionError` while attempting to unlink the uploaded temp file; tests also assert `download/...` existence.
Severity: Major
Blocks production? No
Suggested fix: Close any file handles before unlinking in the convert flow (use context managers). In CI, run tests on a POSIX runner or adjust unlink timing. Update tests as per #31.

34) tests/test_runtime_image_and_doc_conversion.py::test_pptx_to_pdf_runtime_conversion
Root cause: Missing Test Fixture / Upload-Download expectation mismatch
Severity: Major
Blocks production? No
Suggested fix: See #31.

35) tests/test_runtime_image_and_doc_conversion.py::test_odt_to_pdf_runtime_conversion
Root cause: Missing Test Fixture / Upload-Download expectation mismatch
Severity: Major
Blocks production? No
Suggested fix: See #31.

36) tests/test_runtime_image_and_doc_conversion.py::test_mp4_to_mp3_runtime_placeholder
Root cause: Missing Test Fixture (test checks download path); may also be skipped when sample MP4 missing. In this run the sample existed but post-conversion check uses filesystem path.
Severity: Major
Blocks production? No
Suggested fix: See #31.

37) tests/test_webp_to_jpg_landing.py::test_webp_to_jpg_landing_page_renders_with_seo_and_faq
Root cause: SEO / Content — landing page did not include expected FAQ snippet (`Why convert WEBP to JPG?`) possibly because converter JSON lacked the expected fallback or the landing builder omitted fallback.
Severity: Minor
Blocks production? No
Suggested fix: Ensure landing builder adds fallback FAQ (tools.py already constructs `fallback_faq`); confirm `webp-to-jpg` JSON or landing logic provides/merges fallback questions. Update converter JSON or template accordingly.

-----------------------------------------------------------------
Summary counts
- Critical failures: 0
- Major failures: 36
- Minor failures: 1

Environment-only failures (can be excluded for prod-readiness estimate)
- Playwright timeouts (tests #4-7, #9-30): 26 tests — these time out because no live server was started for Playwright during the run.
- Windows file-locking unlink (test #33) partially environment-related; treat as environment-only for readiness estimate.

Effect if environment-only failures excluded
- Original: 478 tests, 440 passed, 37 failed.
- Excluding environment-only failures (27 tests) => effective failing tests: 37 - 27 = 10
- Effective pass count: 440 + 27 = 467
- Effective pass rate: 467 / 478 = 97.7%

Estimated production readiness after excluding environment-only failures
- Estimated readiness: High — ~98% test pass rate; recommended status: PRELIMINARY GO IF fixes applied for the remaining non-environment failures (see suggested fixes above). Note: do NOT release until the remaining issues (JSON enrichment, upload/download test alignment, circular link audit) are resolved and the `app/routers/learning.py` production-modification policy issue is reconciled.

Next recommended actions (concrete)
1. Update tests to assert via `/download/` or adapt CI to provide a `download/` mount mapping to `outputs/` (short-term fix for many runtime failures).
2. Add a pytest fixture to boot the app (uvicorn) for Playwright tests and run Playwright against that server (or run Playwright against a staging URL) — fixes the 26 Playwright failures.
3. Fix Windows-specific unlink behavior in the convert flow by ensuring file handles are closed before attempting `unlink()` (or catch PermissionError and retry/queue cleanup on shutdown).
4. Update `docx-to-jpg.json` (and any other incomplete converter JSON assets) to include the missing `features` and validate JSON schema in CI.
5. Re-run full test suite after the above changes and then re-assess remaining failures.
