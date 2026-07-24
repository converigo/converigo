# Format Master Database Design

## Purpose

Design a scalable master database for all supported file formats that centralizes format metadata, SEO signals, related links, and knowledge integration in a single authoritative source.

This database should support format encyclopedia pages, format knowledge enrichment, internal linking, SEO generation, and converter registry integration.

## Core record schema

Each format record should include:

- `slug`: string, canonical identifier (e.g. `png`, `pdf`, `mp4`)
- `name`: string, display name (e.g. `PNG`, `PDF`)
- `extension`: string, primary file extension (e.g. `.png`, `.pdf`, `.mp4`)
- `mime_type`: string, official MIME type (e.g. `image/png`, `application/pdf`)
- `category`: string, format category (e.g. `image`, `document`, `audio`, `video`, `archive`)
- `description`: string, short authoritative summary
- `advantages`: array of objects with `title` and `text`
- `limitations`: array of objects with `title` and `text`
- `related_formats`: array of string slugs for related format pages
- `related_converters`: array of converter slugs or objects linking to converter landing pages
- `primary_keywords`: array of strings for target SEO phrases
- `secondary_keywords`: array of strings for supporting search intents
- `search_intent`: array of strings or objects representing intent categories (e.g. `informational`, `transactional`, `comparative`, `conversion`, `optimization`)

Optional fields for richer integration:

- `alternate_extensions`: array of strings
- `common_problems`: array of objects
- `best_practices`: array of objects
- `faq`: array of question/answer objects
- `canonical_url`: string
- `seo_title`: string
- `seo_description`: string
- `hub_reference`: object with `title`, `href`, `description`
- `knowledge_status`: string (e.g. `draft`, `published`)

## Recommended storage format

- Primary format: `JSON`
- Use one of these patterns:
  - `app/data/formats/master.json` for a single consolidated master file
  - or a folder of one-record files: `app/data/formats/{slug}.json`

### Recommendation

Use `app/data/formats/{slug}.json`.

Reasons:

- aligns with existing converter and format knowledge layout
- supports incremental updates for single formats
- avoids monolithic file size growth as formats scale
- easy to diff, review, and generate with scripts

## Folder structure

Recommended layout:

- `app/data/formats/`
  - `png.json`
  - `pdf.json`
  - `webp.json`
  - ...
- `app/data/formats/_schema.json` or `app/data/formats/format_master_schema.json`
- `app/data/formats/index.json` (optional index manifest)

Alternative single-file layout:

- `app/data/formats/master.json`
- `app/data/formats/_schema.json`

## Validation strategy

### 1. JSON schema validation

- Provide a JSON Schema for format master records.
- Validate every record on load before use.
- Validate top-level manifest/index if present.
- Use the current pattern in `app/services/knowledge_schema.py` as a model.

Required validation rules:

- `slug`: non-empty string, slug format
- `name`: non-empty string
- `extension`: string starting with `.`
- `mime_type`: valid MIME string
- `category`: enum or string set
- `description`: non-empty string
- `advantages`: non-empty array of objects with `title` and `text`
- `limitations`: non-empty array of objects with `title` and `text`
- `related_formats`: array of valid format slugs
- `related_converters`: array of converter slugs or objects referencing converter metadata
- `primary_keywords`: non-empty array of strings
- `secondary_keywords`: array of strings
- `search_intent`: array of strings or objects describing intent

### 2. Runtime checks

- Ensure slug deduplication across `app/data/formats`
- Ensure referenced `related_formats` exist in master database
- Ensure referenced `related_converters` exist in converter registry
- Enforce category consistency with converter registry and authority service

### 3. Developer tooling

- Add a validation script or service for format master files.
- Integrate validation into tests and CI.
- Provide a generator helper for format metadata skeletons.

## Integration points

### Format Knowledge

- `FormatKnowledgeService` should use the master database as the canonical format metadata source for fields like `slug`, `name`, `description`, `advantages`, `limitations`, and `related_tools`.
- Format knowledge JSON can continue to hold page-specific enrichment fields (`quick_answer`, `definition`, `use_cases`, `comparisons`, `faq`, `related_tools`) but should use master record values for shared metadata.
- Master DB can provide a consistent format profile for new knowledge pages and avoid duplication of generic fields.

### InternalLinkService

- `InternalLinkService` should read `related_formats` and `related_converters` from the master database instead of hardcoded map data.
- The master database can drive format-page related link generation with normalized `/formats/{slug}` paths and converter landing links.
- `search_intent` and keyword fields can also feed internal link scoring, e.g. prioritize related links by shared intent.

### SEO

- Use master database fields for SEO metadata:
  - `primary_keywords`, `secondary_keywords`
  - `description` as meta description fallback
  - `canonical_url` if provided
  - page title generation from `name`
- Use `search_intent` to classify SEO page type and schema output.
- Generate structured data and Open Graph metadata from the master record.

### Converter Registry

- Cross-reference `related_converters` to converter slugs in `app/data/converters`.
- The master database should not duplicate full converter contract schema, but it can store converter slug references and optional descriptive text.
- Converter Registry should remain source of truth for converter page details, while format master data points to related tools.

## Scalability considerations

- Keep records flat and normalized where possible.
- Use `related_formats` as references, not embedded full page data.
- Keep converter references as slugs or lightweight objects.
- Use schema versioning to evolve master record fields without breaking existing consumers.
- Consider generating `app/data/formats/index.json` from individual files for fast lookup if needed.

## Recommended access pattern

- Load the master database through a dedicated service, e.g. `FormatMasterService`.
- Cache parsed JSON records in memory for runtime efficiency.
- Expose methods:
  - `get_format(slug)`
  - `list_formats()`
  - `validate_format(slug)`
  - `related_formats(slug)`
  - `related_converters(slug)`
  - `search_intents(slug)`

## Summary

A format master database in `app/data/formats/{slug}.json` provides a scalable, maintainable foundation for format metadata, SEO, knowledge enrichment, and link generation.

This design uses existing JSON conventions, adds rigorous validation, and integrates cleanly with the format knowledge layer, internal linking service, SEO system, and converter registry.
