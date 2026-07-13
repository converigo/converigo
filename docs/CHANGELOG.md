# Changelog

## [Unreleased]

### Added (C3.8)
- Added import-time payload validation hooks for converter definitions through the shared validation service.
- Extended converter persistence to reject invalid payloads before they are written to disk.
- Added regression tests for valid import payloads and invalid import blocking.

### Added (C3.7)
- Added PluginValidationService framework that validates converters across all integration points (JSON, Metadata, Plugin, Route, SEO, Hub, Recommendation, Sitemap).
- Added ValidationResult container for organized error and warning tracking.
- Added comprehensive validation report generation with validity percentage and check summary.
- Added 27 unit tests covering all validator scenarios and integration cases.

### Added (C3.6)
- Added RecommendationService that generates recommendation groups from converter JSON metadata without manual configuration.
- Added regression tests for deduplication, category matching, workflow detection, and automatic inclusion of new converters.
- Verified that all existing tests pass alongside new validation and recommendation tests.

### Added (C3.5)
- Added a universal converter route that resolves converter slugs via converter JSON metadata while preserving existing public URLs.
- Added regression coverage for the universal route, legacy tool route compatibility, and the new hub automation behavior.
- Added a hub generator that builds Image, PDF, Audio, Video, and Document hubs from active converter JSON.

### Changed (C3.7)
- ConverterDataService now serves as the single source of truth for all validators.
- HubService, RecommendationService, and SeoService are fully integrated into validation workflow.

### Changed (C3.5)
- Legacy landing wrappers now delegate to the shared universal tool renderer so route behavior remains consistent.
- Universal tool page sections now render from converter JSON for hero, upload, benefits, features, supported formats, how-to-use, FAQ, related tools, use cases, about formats, CTA, and structured data.
- Added comprehensive JSON enrichment for every converter so the universal tool page uses structured content instead of fallback defaults.
- Category hubs now use a shared generator that derives featured, popular, related, and all-converter lists from the converter dataset and keeps SEO/structured data consistent.
- Legacy landing templates were moved into a dedicated legacy folder to simplify repository structure without changing URLs, routes, SEO, or application behavior.
- Updated release and brain documentation to describe the new hub automation and compatibility approach.
