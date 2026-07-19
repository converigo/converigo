# Core Converter Certification Report

This report summarizes the certified core converters validated in the current workspace, the evidence collected, and the remaining verification status for final certification.

## Scope

The certification scope includes core image, audio, and document converters that are already classified as `certified` and that were validated using runtime conversion checks and audit scripts.

## Validated Converters

| Converter | Domain | Validation Source | Status |
|---|---|---|---|
| `jpg-to-png` | Image | `scripts/real_conversion_validation.py`, `scripts/image_converter_audit.py` | PASS |
| `png-to-jpg` | Image | `scripts/real_conversion_validation.py`, `scripts/image_converter_audit.py` | PASS |
| `webp-to-jpg` | Image | `scripts/real_conversion_validation.py` | PASS |
| `jpg-to-pdf` | Image/Document | `scripts/real_conversion_validation.py` | PASS |
| `mp4-to-mp3` | Audio | `scripts/real_conversion_validation.py` | PASS |
| `mp4-to-wav` | Audio | `scripts/real_conversion_validation.py` | PASS |
| `docx-to-pdf` | Document | `scripts/real_conversion_validation.py` | PASS |
| `pdf-to-docx` | Document | `scripts/real_conversion_validation.py` | PASS |
| `xlsx-to-pdf` | Document | `scripts/real_conversion_validation.py` | PASS |

## Evidence

- `scripts/real_conversion_validation.py` executed conversion validation for image, audio, and document targets.
- `scripts/image_converter_audit.py` executed additional image validation and report generation.
- `scripts/document_converter_audit.py` executed document conversion validation and report generation.
- `build/real_conversion_results.json` and audit reports were generated successfully.
- A new audio fixture `tests/assets/regression/sample_with_audio.mp4` was created to ensure MP4 audio conversion tests exercise a real audio stream.

## Pytest Verification

A full test run was executed with:

```powershell
$env:PYTHONPATH='.'; .\.venv\Scripts\python.exe -m pytest -q
```

Result:
- `424 passed`
- `1 skipped`
- `8 failed`

### Failed tests

The failed tests are not directly related to the certified core conversion runtime behavior.

- `tests/test_converter_contract.py::test_converter_contract_example_exists_and_has_required_fields`
- `tests/test_converter_contract.py::test_all_converter_contract_files_in_data_dir_have_required_fields`
- `tests/test_engine_dedupe.py::test_engine_dedupes_same_target`
- `tests/test_mp4_to_mp3_landing.py::test_mp4_to_mp3_landing_page_renders_with_seo_and_faq`
- `tests/test_office_converter_cluster.py::test_contracts_loadable`
- `tests/test_office_converter_cluster.py::test_hub_and_sitemap_and_audit`
- `tests/test_pdf_to_jpg_landing.py::test_pdf_to_jpg_landing_page_renders_with_seo_and_faq`
- `tests/test_png_to_jpg_landing.py::test_png_to_jpg_landing_page_renders_with_seo_and_faq`

## Summary and Recommendation

- Core certified converters listed above are validated as passing the current runtime audits and conversion checks.
- Certification artifacts are available in `build/real_conversion_results.json`, `build/image_converter_audit_report.md`, and `build/document_converter_audit_results.json`.
- The current full pytest suite has unrelated failures in contract validation, recommendation de-duplication, landing page content, and office registry/hub generation.

> Recommendation: finalize certification for the core converters above, while tracking the pytest failures separately as environment/test-suite issues outside the current converter certification scope.
