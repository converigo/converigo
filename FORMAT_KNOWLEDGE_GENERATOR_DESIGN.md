# Programmatic Format Knowledge Generator Design

## Goal

Design a generator that builds format knowledge files in `app/data/format_knowledge/{slug}.json` from canonical format records in `app/data/formats/{slug}.json`.

The generator should produce valid format knowledge payloads for the existing schema and scale to hundreds of formats.

## Output requirements

Each generated format knowledge file must include:
- `slug`
- `name`
- `quick_answer`
- `definition`
- `use_cases`
- `advantages`
- `limitations`
- `comparisons`
- `related_tools`
- `faq`

It must reuse the existing `app/services/knowledge_schema.py` validations.

## Architecture

### Components

1. **FormatMasterSource** (conceptual)
   - Reads canonical format metadata from `app/data/formats/{slug}.json`.
   - Provides access to format fields such as `slug`, `name`, `category`, `description`, `related_formats`, `related_converters`, `primary_keywords`, `secondary_keywords`, and `search_intent`.

2. **FormatKnowledgeGenerator**
   - Converts canonical format records into format knowledge payloads.
   - Applies deterministic templates and heuristics to generate each required knowledge section.
   - Emits JSON to `app/data/format_knowledge/{slug}.json`.

3. **KnowledgeSchemaValidator**
   - Validates generated payloads against the existing `FORMAT_KNOWLEDGE_FIELD_DEFINITIONS`.
   - Ensures generated files are publish-ready and compatible with `FormatKnowledgeService`.

4. **Generation Orchestrator**
   - Iterates over supported format slugs in `app/data/formats/`.
   - Invokes `FormatKnowledgeGenerator` and validator for every format.
   - Writes generated files in a safe, idempotent manner.

### Data flow

`app/data/formats/{slug}.json` -> `FormatKnowledgeGenerator` -> validate -> `app/data/format_knowledge/{slug}.json`

## Generation flow

1. **Discover formats**
   - Enumerate files in `app/data/formats/`.
   - Derive `slug` from each filename.

2. **Load master record**
   - Parse JSON for a format.
   - Validate canonical fields exist (slug, name, description, category, related_formats, related_converters).
   - Normalize values for consistent generation.

3. **Generate knowledge sections**
   - `quick_answer`
     - One concise sentence explaining the format and its most important use case.
     - Base text on `name`, `category`, and `description`.

   - `definition`
     - A short paragraph describing what the format is, its intent, and a key distinguishing trait.
     - Include format name, category, and major tradeoff.

   - `use_cases`
     - Build 4–6 use case entries from category signals and related content.
     - Use known format types: image, document, audio, video, archive.
     - Map category-specific use cases to the format semantics.

   - `advantages`
     - Generate 3–5 advantage statements from category strengths and format properties.
     - Reuse canonical `description` and generic format benefits.

   - `limitations`
     - Generate 2–4 limitation statements covering file size, compatibility, quality, or workflow constraints.
     - Use category and format-specific tradeoffs where available.

   - `comparisons`
     - Generate 2–3 comparison items to related formats from `related_formats`.
     - For each item, include a title like `"PDF vs DOCX"` and a short contrast.

   - `related_tools`
     - Use `related_converters` to create converter entries.
     - For each converter slug, derive `title` and `href` in the expected shape.
     - If converter reference metadata is available from the converter registry, include `description` from the contract.
     - Fallback to a generated description when metadata is missing.

   - `faq`
     - Generate 5–8 FAQ items covering: what the format is, when to use it, how it compares, compatibility, and conversions.
     - Include at least one localization-aware or generic question if schema examples suggest multi-language support.

4. **Validate generated payload**
   - Run the existing schema validator from `app/services/knowledge_schema.py`.
   - Confirm required sections and item keys are present.
   - Record validation errors with file-specific context.

5. **Write output**
   - Write the generated JSON to `app/data/format_knowledge/{slug}.json`.
   - Support a dry-run mode that validates but does not write files.

## Validation

### Schema reuse

- Use `app/services/knowledge_schema.py` to validate generated knowledge payloads.
- Ensure generated objects comply with:
  - `quick_answer`: non-empty string
  - `definition`: non-empty string
  - `use_cases`: non-empty array of objects with `title` and `text`
  - `advantages`: non-empty array of objects with `title` and `text`
  - `limitations`: non-empty array of objects with `title` and `text`
  - `comparisons`: non-empty array of objects with `title` and `text`
  - `related_tools`: non-empty array of objects with `slug`, `title`, `description`, `href`
  - `faq`: non-empty array of objects with `question` and `answer`

### Runtime validation

- Verify `slug` in generated payload matches source record.
- Confirm `related_tools` slugs correspond to known converter slugs when possible.
- Confirm `related_formats` references in comparisons are valid format slugs.
- Flag any missing or empty strings.

### Scalability validation

- Support batch generation over hundreds of formats with a streaming or incremental approach.
- Use a deterministic production mode that can be rerun safely.
- Provide summary output showing success/failure counts.

## Extensibility

### Template-driven generation

- Use a small set of reusable template patterns for sentences and bullets.
- Example generator helper methods:
  - `generate_quick_answer(record)`
  - `generate_definition(record)`
  - `generate_use_cases(record)`
  - `generate_advantages(record)`
  - `generate_limitations(record)`
  - `generate_comparisons(record, related_formats)`
  - `generate_related_tools(record, converter_registry)`
  - `generate_faq(record)`

- Keep templates data-driven so new categories and formats can be added without changing generator code.

### Plug-in extensions

- Allow optional hooks or override methods for custom format families.
- Example: registered generator extensions for `image`, `video`, `audio`, `archive`, `document`.

### Enrichment augmentation

- Support adding external reference data later, such as:
  - converter contract descriptions
  - SEO keyword mappings
  - format usage analytics

- The generator should produce core knowledge first and allow secondary enrichment passes.

### Output customization

- Allow optional fields such as `title`, `metadata`, or additional `faq` variants.
- Keep the core schema stable while enabling future output expansion.

## Architecture summary

- `app/data/formats/` is the single canonical source for format metadata.
- The generator is a separate write-only process that materializes knowledge JSON in `app/data/format_knowledge/`.
- Validation is centralized through the existing schema module.
- The architecture supports hundreds of formats through batch iteration, deterministic output, and category-driven templates.

## Design goals

- Reuse existing schema and service-compatible format knowledge structure.
- Preserve backward compatibility by generating files that match current payload expectations.
- Provide a clean path for future code integration once the generator is implemented.
- Keep the design scalable, extensible, and safe for large-format catalogs.
