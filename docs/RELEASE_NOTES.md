# Converigo Release Notes

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
