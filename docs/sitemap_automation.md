# Sitemap Automation

## Architecture

- The sitemap workflow uses the existing converter registry as the single source of truth.
- Each active converter contributes one canonical URL entry.
- Entries are grouped by category into dedicated sitemap files:
  - video
  - image
  - pdf
  - audio
- A parent sitemap index links the category sitemaps for discovery.

## Validation Rules

- Every active converter must appear exactly once.
- Landing paths are required for all active converters.
- Canonical URLs must match the contract path.
- Duplicate URLs are rejected to prevent index conflicts.
