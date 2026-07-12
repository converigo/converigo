# Changelog

## [Unreleased]

### Added
- Added a universal converter route that resolves converter slugs via converter JSON metadata while preserving existing public URLs.
- Added regression coverage for the universal route and legacy tool route compatibility.

### Changed
- Legacy landing wrappers now delegate to the shared universal tool renderer so route behavior remains consistent.
- Updated release and brain documentation to describe the new compatibility approach.
