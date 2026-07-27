# Format Internal Linking Strategy

## Current state

- `app/templates/pages/format_page.html` renders:
  - `payload.related_formats` in a Related formats section
  - `related_converters` in a Related converters section
- `app/routers/formats.py` builds:
  - `payload` from `AuthorityService.generate_payload(normalized)`
  - `related_converters` from `_build_related_converters(normalized)` using converter contracts
- `app/services/authority_service.py` generates authority payload fields including:
  - `related_formats`
  - `related_tools`
  - `related_converters`
  - `internal_links`
- There is a separate `InternalLinkService` capable of generating related formats, related converters, related knowledge and deduplicated link groups, but the format route does not currently use it.

## Gaps

- `related_formats` URLs are inconsistent with actual format page routes:
  - `AuthorityService._build_related_formats()` generates `href: f"/{candidate}"`, while format pages are served at `/formats/{format_name}`.
  - This creates a risk of broken or non-SEO-optimal internal links.
- Format pages currently do not expose an explicit knowledge page link section:
  - `template` has no `related_knowledge` block, and the route does not provide a `related_knowledge` payload.
- `AuthorityService.internal_links` exists but is unused on format pages.
- The current related links strategy is partial and split across services:
  - format page links come from both `AuthorityService` and a custom `_build_related_converters()` helper in `formats.py`.
  - This fragmentation makes scaling harder and invites duplicate or inconsistent links.
- There is no clear deduplication layer for format page links beyond the custom `related_converters` logic.
- Knowledge enrichment content is merged into `payload.format_knowledge`, but that does not translate into format-specific internal link navigation.

## Proposed architecture

### 1. Use a single internal-link source for format pages

- Introduce a format page link provider that returns:
  - `related_formats`
  - `related_converters`
  - `related_knowledge`
  - optionally `related_hubs`
- Prefer `InternalLinkService.get_links_for_format(format_name)` because it already provides a standardized API for format pages and deduplicates link suggestions.
- If `InternalLinkService` is too broad, extract a smaller reusable provider from it specifically for format page contexts.

### 2. Normalize route targets consistently

- Ensure all format page link targets use `/formats/{slug}`.
- Keep converter links on `/tools/{slug}` or the existing landing path URL.
- Use knowledge pages on `/knowledge/{slug}` or whichever canonical path the site uses.

### 3. Add a knowledge page link section

- Render a new `related_knowledge` section on format pages when available.
- Generate these links from converter contracts and/or format knowledge inputs/outputs.
- This helps crawlability by explicitly connecting format pages to educational content.

### 4. Deduplicate and score links automatically

- Use an internal link service implementation to:
  - deduplicate URLs by normalized path
  - avoid duplicate anchor text and repeated targets
  - limit the number of links per section (e.g. 3–5)
- Prefer stronger internal links for same-category formats, direct converter tools, and knowledge pages with high relevance.

### 5. Keep format pages lightweight

- Only surface the most relevant links in page content.
- Use breadth for SEO by linking to multiple categories, but avoid overwhelming users with too many cards.
- Use the existing template sections rather than adding too many new link blocks.

## Implementation phases

### Phase 1: Audit and unify link generation

- Verify actual route naming conventions for format, tool, and knowledge pages.
- Replace `payload.related_formats` generation with a normalized internal link provider.
- Ensure format page templates only render links with canonical URL patterns.
- Add a `related_knowledge` payload to the format route, even if implemented as a small generated list.

### Phase 2: Integrate existing internal link service

- Use `InternalLinkService.get_links_for_format(format_name)` in `app/routers/formats.py`.
- Map the returned sections into the template context:
  - `related_formats`
  - `related_converters`
  - `related_knowledge`
- Preserve the page's current `payload` and `seo` behavior, but source links from one service.
- Remove or simplify duplicate helper logic in `_build_related_converters()` once the centralized service is trusted.

### Phase 3: Scale and harden

- Add audit coverage for link validity and deduplication:
  - confirm `/formats/{format}` pages link only to existing formats
  - confirm related converter links point to valid tool landing pages
  - confirm related knowledge links point to existing knowledge pages or format knowledge inputs
- Extend the link provider to include category hubs when format-specific page volume grows.
- Add a lightweight link validator or report to catch stale or duplicate targets across hundreds of format pages.

## Why this approach works

- Minimal code change: the route uses a single service instead of multiple ad hoc generators.
- Scales naturally: link decisions are based on converter contract relationships and content taxonomy rather than manual page-by-page curation.
- Improves crawlability: consistent internal link structure, explicit knowledge links, and canonical path patterns help search engines understand page relationships.
- Avoids duplicates: centralized deduplication and scoring prevent repeated targets across related sections.

## Specific recommendations

- Use `/formats/{slug}` for all related format links.
- Add a dedicated `related_knowledge` section in `format_page.html`.
- Consolidate link sources to `InternalLinkService` or a shared format-link helper.
- Keep the number of links per section bounded (e.g. 3–5) and prioritize relevance.
- Preserve current authority payload content, but do not rely on `AuthorityService.related_formats` URLs unless normalized.
