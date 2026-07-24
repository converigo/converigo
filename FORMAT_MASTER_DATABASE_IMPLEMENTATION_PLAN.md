# SEO Sprint 05B — Master Database Implementation Plan

## Goal

Implement the format master database as a scalable, central source of truth for file format metadata, SEO signals, internal links, and knowledge page enrichment without disrupting current format or converter page behavior.

## Implementation phases

1. **Discovery & schema definition**
   - Finalize the master record schema and folder structure.
   - Create `app/data/formats/_schema.json` and a small sample record such as `app/data/formats/png.json`.
   - Define required, optional, and internal-only fields for format pages, knowledge enrichment, and SEO.

2. **Master data service and validation design**
   - Define a new `FormatMasterService` interface conceptually with methods like `get_format(slug)`, `list_formats()`, `validate_format(slug)`, `related_formats(slug)`, and `related_converters(slug)`.
   - Define JSON schema validation and runtime checks aligned to `app/services/knowledge_schema.py` patterns.
   - Specify load/caching requirements and error reporting behavior for invalid master records.

3. **Phased integration with existing services**
   - Plan first-phase consumers: `FormatKnowledgeService`, `InternalLinkService`, and SEO metadata generation.
   - Identify fallback behavior for each integration point so current pages continue working until the master database is fully adopted.

4. **Data migration and authoring**
   - Migrate a small priority set of format entries into the master database to validate structure and integration.
   - Build authoring conventions and skeleton generators for new format records.

5. **Validation and rollout**
   - Implement validation tooling, tests, and CI gating for master format data.
   - Roll out master database support in a dark launch mode behind fallback logic.
   - Verify format pages, knowledge pages, and link generation continue to work with existing file-based format knowledge.

6. **Production cutover and cleanup**
   - Switch primary consumers from legacy sources to the format master database.
   - Remove or deprecate duplicated format metadata sources only after coverage proves correct.
   - Document usage and maintenance patterns for future contributors.

## Migration order

1. **Schema and sample files**
   - Establish `app/data/formats/` and add the schema file.
   - Create sample format records for the most important format types (image, document, video, audio).

2. **Validation and tooling**
   - Build schema validation and manifest checks.
   - Add test helpers and developer instructions for record creation.

3. **Read-only service adapter**
   - Plan a read-only service layer that can source format metadata from the new master database.
   - Keep existing format knowledge JSON and converter metadata untouched during this stage.

4. **InternalLinkService integration**
   - Adapt related format and converter link generation to consume master record references.
   - Preserve existing hardcoded fallback behavior during transition.

5. **FormatKnowledgeService integration**
   - Align shared metadata fields in format knowledge enrichment with the master database.
   - Use master record values for format identity, description, advantages, limitations, and related tools.

6. **SEO metadata integration**
   - Use `primary_keywords`, `secondary_keywords`, `description`, and `canonical_url` from the master database for SEO output.
   - Keep current SEO metadata fallback behavior until master data is stable.

7. **Wide release**
   - Roll out the master database as the primary source.
   - Decommission duplicated metadata only after verification.

## Affected services

- `app/services/format_knowledge_service.py`
- `app/services/internal_link_service.py`
- `app/services/knowledge_schema.py` (validation model)
- `app/services/seo_service.py` or wherever SEO metadata is generated
- `app/services/converter_registry_service.py` (for converter reference checks)
- `app/services/knowledge_service.py` when it builds content around formats
- `app/services/related_converter_service.py` for related converter linking
- Any page builder or route layer that renders format pages or related content

## Backward compatibility strategy

- Implement the master database as a graceful fallback rather than a hard replacement.
- Keep the existing `app/data/format_knowledge/` JSON files active for current format page content and learnings.
- Use master database values only when they exist and pass validation, otherwise retain legacy payloads.
- Maintain current `related_formats` and `related_converters` link generation behavior until master-driven links are confirmed.
- Avoid breaking page routes, slugs, templates, or converter references during rollout.

## Testing plan

1. **Unit tests**
   - Validate schema compliance for sample master records.
   - Test `FormatMasterService` read and lookup behavior.
   - Test fallback behavior when master data is incomplete or missing.

2. **Integration tests**
   - Verify `InternalLinkService` output using master-driven format references.
   - Verify `FormatKnowledgeService` uses master metadata for shared fields while preserving enrichment-specific fields.
   - Verify SEO metadata generation uses master record fields when available.

3. **Regression coverage**
   - Ensure existing tests for `tests/test_formats_pages.py` and `tests/test_internal_link_service.py` continue to pass.
   - Add coverage for edge cases around missing related formats, invalid converter references, and schema violations.

4. **Data validation tests**
   - Add tests for slug uniqueness and referenced format existence.
   - Add tests for `related_converters` cross-checking against converter registry slugs.

5. **Manual verification**
   - Confirm format pages render correctly for migrated formats.
   - Confirm internal link widgets still show expected related formats and converters.

## Rollback plan

- If issues arise, revert to legacy format knowledge sources and existing internal link generation.
- Keep the master database implementation behind a feature gate or fallback path during rollout.
- Ensure the old data path remains available until the cutover is fully validated.
- Use test and staging environments to validate rollback before production changes.
- If a master record is invalid, skip it and continue using the legacy source for that format until fixed.

## Risks

- **Data inconsistency**: mismatched `related_formats` or `related_converters` references could break page rendering or link generation.
- **Validation gaps**: incomplete schema validation may allow malformed master records to reach production.
- **Duplication drift**: parallel format metadata in legacy format knowledge and master database could become out of sync.
- **Service dependency errors**: master data may expose category or converter references that current services do not expect.
- **Rollout complexity**: switching consumers too quickly before fallback handling is mature could create regressions in SEO or page content.
- **Performance impact**: poorly cached master record loading could slow page generation if not optimized.

## Notes

- The plan is intentionally implementation-agnostic and does not require any code changes at this stage.
- The first migration should prioritize formats already used in the site’s core format pages and converter landing relationships.
- A phased rollout with clear fallback paths will minimize disruption and preserve existing page behavior.
