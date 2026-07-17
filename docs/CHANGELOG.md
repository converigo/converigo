# Changelog

## [Unreleased]

### Added
- Added a universal converter route that resolves converter slugs via converter JSON metadata while preserving existing public URLs.
- Added regression coverage for the universal route and legacy tool route compatibility.

### Changed
- Legacy landing wrappers now delegate to the shared universal tool renderer so route behavior remains consistent.
- Universal tool page sections now render from converter JSON for hero, upload, benefits, features, supported formats, how-to-use, FAQ, related tools, use cases, about formats, CTA, and structured data.
- Legacy landing templates were moved into a dedicated legacy folder to simplify repository structure without changing URLs, routes, SEO, or application behavior.
- Updated release and brain documentation to describe the new compatibility and cleanup approach.
