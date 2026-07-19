# Pytest Failure Classification Report

## Objective
Classify the 8 pytest failures captured in `build/pytest_output.txt` as one of:
- CLASS A: Production blocking
- CLASS B: Metadata / contract
- CLASS C: Test maintenance

This report does not fix any tests.

## Failure Classification

| Test | File | Category | Root Cause | Impact |
|---|---|---|---|---|
| `test_converter_contract_example_exists_and_has_required_fields` | `tests/test_converter_contract.py` | CLASS B | The contract validation test expects `lifecycle_status` only in `{"active","deprecated","beta"}` while actual contract metadata includes `"certified"`. | Metadata validation mismatch; may break contract quality checks but not core converter runtime. |
| `test_all_converter_contract_files_in_data_dir_have_required_fields` | `tests/test_converter_contract.py` | CLASS B | Same root cause as above: the lifecycle status validator is not aligned with current contract metadata values. | Metadata/contract issue in contract schema enforcement. |
| `test_engine_dedupes_same_target` | `tests/test_engine_dedupe.py` | CLASS A | Recommendation engine deduplication logic returns no valid `best_choice` when duplicate target candidates are filtered, causing an internal regression. | Production-impacting if the recommendation engine path is used to choose converters. |
| `test_mp4_to_mp3_landing_page_renders_with_seo_and_faq` | `tests/test_mp4_to_mp3_landing.py` | CLASS C | Landing page content no longer contains the expected `href="#how-to-use"` anchor, indicating a page structure or SEO test expectation drift. | Test maintenance / page content expectation issue; does not block converter runtime. |
| `test_contracts_loadable` | `tests/test_office_converter_cluster.py` | CLASS B | The test expects `xlsx-to-ods` to be present in active contract listings, but the active registry does not include it. | Metadata/catalog issue affecting contract discovery and registry completeness. |
| `test_hub_and_sitemap_and_audit` | `tests/test_office_converter_cluster.py` | CLASS B | `xlsx-to-ods` is missing from generated hub pages despite being expected by the converter slug list. | Metadata/catalog issue in sitemap/hub generation and contract classification. |
| `test_pdf_to_jpg_landing_page_renders_with_seo_and_faq` | `tests/test_pdf_to_jpg_landing.py` | CLASS C | Page HTML lacks the expected `href="#how-to-use"` anchor, showing a test expectation drift for page content. | Test maintenance / SEO content regression; not core conversion blocking. |
| `test_png_to_jpg_landing_page_renders_with_seo_and_faq` | `tests/test_png_to_jpg_landing.py` | CLASS C | Same issue as the other landing page tests: missing anchor in rendered HTML. | Test maintenance / page content expectation issue. |

## Summary

- CLASS A: 1 failure
  - `test_engine_dedupes_same_target`
- CLASS B: 4 failures
  - `test_converter_contract_example_exists_and_has_required_fields`
  - `test_all_converter_contract_files_in_data_dir_have_required_fields`
  - `test_contracts_loadable`
  - `test_hub_and_sitemap_and_audit`
- CLASS C: 3 failures
  - `test_mp4_to_mp3_landing_page_renders_with_seo_and_faq`
  - `test_pdf_to_jpg_landing_page_renders_with_seo_and_faq`
  - `test_png_to_jpg_landing_page_renders_with_seo_and_faq`

## Recommendation

- Treat the contract / metadata failures as a metadata alignment issue, not converter runtime failures.
- Treat the landing page failures as test-maintenance or content/SEO expectation drift.
- The critical failure is `test_engine_dedupes_same_target`, which should be investigated as a possible production-impacting recommendation-engine defect.
