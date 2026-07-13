# Converigo Release Notes

## Sprint C3.8 — Dynamic Platform

### Summary
- Added import-time validation hooks so new converter definitions can be checked before they are persisted.
- Reused the existing PluginValidationService and ConverterDataService workflow to keep validation data-driven and aligned with the JSON-first architecture.
- Activated six Batch B1 image converters for JPG, WEBP, and TIFF workflows as part of image converter coverage milestone.
- Added regression tests to ensure valid payloads continue to pass while invalid imports are blocked.

### Validation
- 97/97 tests passing across the full suite.
- New regression tests for payload validation and import blocking passed.

### Key Capabilities
- Validate converter payloads before disk write
- Reuse existing metadata, plugin, route, SEO, and recommendation checks
- Keep application runtime behavior unchanged while strengthening data integrity

## Sprint C3.7 — Plugin Validation Framework

### Summary
- Implemented PluginValidationService framework that validates converters across all integration points without breaking existing functionality.
- Built 8 integrated validators: JSON, Metadata, Plugin, Route, SEO, Hub, Recommendation, and Sitemap.
- Created comprehensive unit test suite (27 tests) covering all validators and integration scenarios.
- Implemented validation report generation showing converter validity percentage and validation results.

### Validation
- All 13 production converters pass validation
- 27/27 new validation tests passing
- 95/95 total tests passing (68 existing + 27 new)
- No regressions detected

### Key Capabilities
- Automatically detect duplicate converter slugs
- Validate metadata fields (slug, source, target, category)
- Verify plugins exist in registry
- Ensure routes can be rendered
- Confirm SEO metadata generation
- Check hub inclusion
- Validate recommendation participation
- Verify sitemap inclusion

## Sprint C3.6 — Recommendation Engine

### Summary
- Implemented RecommendationService that generates recommendation groups from converter JSON metadata automatically.
- Built deduplication strategy that prevents duplicate recommendations across priority groups.
- Created regression tests for category matching, workflow detection, and automatic inclusion of new converters.
- Verified all existing tests pass alongside new recommendation tests.

### Validation
- 2 new recommendation tests passing
- 68/68 total tests passing (66 existing + 2 new)
- No regressions detected

### Key Features
- Related converters from explicit related_tools configuration
- Same-category converters for related workflows
- Workflow recommendations based on source/target matching
- Next-step recommendations for conversion chains
- Popular converters as fallback
- Auto-inclusion of new converters without code changes

## Sprint C3.5 — Hub Automation

### Summary
- Added a data-driven hub generator that builds Image, PDF, Audio, Video, and Document hubs from active converter JSON definitions.
- Ensured each hub includes hero content, featured/popular/related converter sections, internal links, CTA, SEO metadata, and structured data.
- Kept hub generation aligned with ConverterDataService and the shared Architecture V4 rendering approach.
- Verified that new converters are surfaced in the correct hub automatically and the full regression suite passes.

### Validation
- 5 category hubs implemented and routed
- Hub content derived from converter JSON without manual converter lists
- Full pytest suite passed

## Sprint C3.3.2 — JSON Enrichment

### Summary
- Enriched every converter JSON file with hero, features, supported formats, how-to-use, about formats, and CTA data.
- Kept routing, templates, SEO, and pipeline logic unchanged while ensuring the universal tool page uses structured content instead of fallback text.
- Verified the renderer and full regression suite remain stable.

### Validation
- 13 converter files updated.
- 6 enrichment fields added per converter.
- Full pytest suite passed.

## Checkpoint C1 — Image Foundation

### Release Summary

Checkpoint C1 delivers the first official production image converter packages for Converigo, marking the Image Foundation milestone.

### Included Packages

- `IMG-001` PNG→WEBP
- `IMG-002` WEBP→PNG

### What is included

- Fully built landing pages for both image packages
- SEO metadata and structured data support
- Related tool linking for image conversion flows
- Package-specific QA tests for landing and conversion endpoints
- Final release audit and blocker resolution

### Key Changes

- Added `WEBP→PNG` landing page and route
- Updated `PNG→WEBP` landing page metadata and page content
- Added or updated converter metadata for both image packages
- Added a shared universal converter route with legacy URL compatibility for existing landing URLs
- Migrated universal tool page rendering to JSON-driven sections for hero, upload, benefits, features, supported formats, how-to-use, FAQ, related tools, use cases, about formats, CTA, and structured data
- Moved legacy landing templates into a dedicated legacy folder to simplify repository structure without changing URLs, routes, SEO, or behavior
- Fixed accessibility issue in upload preview image alt text
- Verified the full regression suite with 60 passing tests

### Release Notes

- `app/templates/pages/webp_to_png_landing.html` created
- `app/templates/pages/png_to_webp_landing.html` updated
- `app/routers/home.py` updated for image landing route and metadata
- `app/data/converters/png-to-webp.json` updated
- `app/data/converters/webp-to-png.json` updated
- `app/services/converter_data_service.py` updated for sitemap landing overrides
- `app/routers/tools.py` updated with a shared universal renderer
- `app/routers/home.py` updated with compatibility wrappers and a universal converter route
- `app/templates/components/upload_card.html` updated for accessibility alt text
- `tests/test_universal_route.py` added
- `tests/test_webp_to_png_landing.py` added

### Checkpoint Status

- **Checkpoint:** C1
- **Milestone:** Image Foundation
- **Status:** Ready for GitHub Push

### Notes

This release is the first official milestone for Converigo and establishes the image conversion category as a production-ready product foundation.
