# CONVERIGO CONVERTER REGRESSION REPORT

## Summary

Total converters (unique): 61

Automated tests run: pytest (local)

Test results summary:

- Passed: 424
- Failed: 8
- Skipped: 1

Status summary (by inspection):

- PASS: functional converters and engines exercised by tests (majority)
- FAIL: metadata / contract inconsistencies causing landing/hub/tests to fail
- BLOCKED: none

## Converter Detail

See `build/converter_inventory.json` for a complete per-converter inventory (source, target, contract/metadata presence).

Key findings:

- Unique converter slugs discovered: 61 (see inventory file).
- Several converter primary JSON files are missing expected metadata fields (`source`, `target`, `title`, `how_to_use`). Examples: `bmp-to-jpg.json` shows missing primary JSON (only contract/metadata present).
- Contract files use mixed `lifecycle_status` values (e.g. `certified`, `active`, `deprecated`). Some tests expect `certified` and fail when `active` is present.
- Hub/sitemap generation tests failed for converters missing complete metadata (e.g. `xlsx-to-ods` not found in hub pages).

Files of interest (examples):

- app/data/converters/bmp-to-jpg.contract.json (lifecycle_status: "active" in contract)
- app/data/converters/bmp-to-jpg.metadata.json (present) but primary JSON missing or invalid
- app/data/converters/xlsx-to-ods.json (present) — flagged by hub test


## Production Recommendation

Ready: []

Not Ready: []

Recommendations (short-term):

- Normalize converter metadata: ensure primary JSON files include `source`, `target`, `title`, and `how_to_use` arrays where applicable.
- Standardize contract `lifecycle_status` values (decide whether tests expect `certified` or `active`) and update contract files accordingly.
- Re-run `pytest` after metadata normalization; many failing tests are metadata-driven and should resolve.

Next steps (suggested):

1. Run targeted validation conversions for the priority list (image/audio/document) using existing sample assets. Document passes/fails per converter.
2. Normalize metadata and lifecycle status values, then re-run tests.
3. If conversion failures appear during targeted runs, collect stack traces and create detailed bug reports for the specific engine/plugin.

Detailed pytest failure list (from run):

- tests/test_converter_contract.py::test_converter_contract_example_exists_and_has_required_fields
- tests/test_converter_contract.py::test_all_converter_contract_files_in_data_dir_have_required_fields
- tests/test_engine_dedupe.py::test_engine_dedupes_same_target
- tests/test_mp4_to_mp3_landing.py::test_mp4_to_mp3_landing_page_renders_with_seo_and_faq
- tests/test_office_converter_cluster.py::test_contracts_loadable
- tests/test_office_converter_cluster.py::test_hub_and_sitemap_and_audit
- tests/test_pdf_to_jpg_landing.py::test_pdf_to_jpg_landing_page_renders_with_seo_and_faq
- tests/test_png_to_jpg_landing.py::test_png_to_jpg_landing_page_renders_with_seo_and_faq

Initial root-cause analysis:

- Several contract files use `lifecycle_status` values not expected by tests (e.g. `active` vs `certified`). Tests assert the presence of `certified` for some examples.
- Missing or incomplete primary converter JSON files lead to None/attribute errors in engine/plugin resolution — e.g., missing `target`/`source` fields cause `NoneType` attribute errors.
- Landing page tests expect certain sections (anchors like `#how-to-use`) present in template rendering; these are absent when `how_to_use` content is missing in the converter JSON.

Technical artifacts produced during audit:

- `build/converter_inventory.json` — full inventory of converters and file presence
- `CONVERTER_REGRESSION_MATRIX.md` — initial matrix with placeholders
- Pytest output: 8 failed, 424 passed, 1 skipped (full output available in terminal logs)

If you want, I can now proceed to run the priority conversion validations (Task 5) on a small set of sample files and populate the regression matrix with PASS/FAIL results. This will perform real conversions using the `ConversionManager` and available sample assets.

## Real Conversion Result

The following conversions were executed using `tests/assets/regression` samples. Results recorded in `build/real_conversion_results.json`.

| Converter | Input | Output | Status | Validation / Error |
|---|---:|---|---|---|

| JPG → PNG | sample.jpg | outputs/image/sample.png | PASS | PIL open OK |
| PNG → JPG | sample.png | outputs/image/sample.jpg | PASS | PIL open OK |
| WEBP → JPG | sample.webp | outputs/image/sample.jpg | PASS | PIL open OK |
| JPG → PDF | sample.jpg | outputs/document/sample.pdf | FAIL | Output is PDF; image validation (PIL) failed — expected image but target is document |
| MP4 → MP3 | sample.mp4 | - | FAIL | Source MP4 contains no audio stream; conversion aborted |
| MP4 → WAV | sample.mp4 | - | FAIL | FFmpeg reported no audio stream in source (video-only sample) |
| DOCX → PDF | sample.docx | outputs/document/sample.pdf | PASS | file exists and non-empty |
| PDF → DOCX | sample.pdf | outputs/document/sample.docx | PASS | file exists and non-empty |
| PDF → XLSX | sample.pdf | outputs/document/sample.xlsx | PASS | file exists and non-empty |
| PDF → PPT | sample.pdf | outputs/document/sample.pptx | PASS | file exists and non-empty |

Notes / Root Causes:

- `JPG → PDF` produced a valid PDF as expected; adjust validation rules to treat document outputs differently.
- `MP4 → MP3` and `MP4 → WAV` failed because `tests/assets/regression/sample.mp4` is video-only without audio. Use an audio-containing sample for audio conversions or mark as BLOCKED.

Outputs are available under `outputs/` and the full JSON results are in `build/real_conversion_results.json`.
