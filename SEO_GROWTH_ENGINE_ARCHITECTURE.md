# SEO Growth Engine Architecture

## Purpose

Design a unified, programmatic SEO growth engine that expands the Learning Center and format ecosystem without introducing a new framework, a new database, or implementation changes.

The architecture reuses the existing Converigo systems already in place:
- Format Master Database
- Format Knowledge Generator
- ArticleService
- Article Schema
- SeoService
- InternalLinkService

## Design Principles

1. Reuse existing architecture
   - Keep the current JSON-first content model.
   - Reuse the existing services and validation layers instead of introducing a new persistence layer.

2. No new framework
   - Stay within the current FastAPI + Jinja2 + JSON content pattern.
   - Use existing routers and templates as consumers of generated content.

3. No database
   - Treat JSON files in the existing data folders as the content source of truth.
   - Use the current app/data structure as the canonical content layer.

4. Deterministic generation
   - Each generator should produce stable output from existing source data.
   - The same input should yield the same output.

5. Validation-first output
   - Generate content only when it passes the existing schema and quality checks.

---

## High-Level Architecture

The SEO growth engine is organized into four layers:

### 1. Source Layer
This layer provides canonical content signals from the existing app data model.

Sources include:
- Format Master Database records
- Format Knowledge Generator output
- Learning Center article JSON files
- Converter metadata and related format/converter mappings
- Existing SEO metadata builders and internal-link heuristics

### 2. Generation Layer
This layer contains the programmatic generators that turn source signals into SEO-ready content assets.

Planned generators:
- Topic Cluster Generator
- Comparison Page Generator
- Guide Page Generator
- Format Encyclopedia Generator
- FAQ Generator

### 3. Validation Layer
This layer ensures generated output fits the existing schema and quality expectations.

Validation uses:
- ArticleSchemaValidator for Learning Center article content
- Existing knowledge validation patterns for format knowledge payloads
- Consistency checks for slugs, links, metadata, and structured data fields

### 4. Publishing Layer
This layer turns validated content into pages and metadata that the existing site can render.

Publishing reuses:
- SeoService for titles, descriptions, canonical URLs, robots, and structured data
- InternalLinkService for cross-linking across articles, formats, comparisons, and converters
- Existing routers and templates for rendering

---

## Core Components

### Format Master Database
The Format Master Database remains the canonical source for format metadata.

Its role is to provide authoritative source data for:
- format identity and taxonomy
- related formats
- related converters
- SEO intent
- primary and secondary keywords
- comparison candidates
- encyclopedia structure

This should remain JSON-based and file-driven, consistent with the existing data layout.

### Format Knowledge Generator
The Format Knowledge Generator continues to materialize richer format knowledge from the master records.

It provides reusable content blocks for:
- quick answers
- definitions
- use cases
- advantages
- limitations
- comparisons
- FAQs

These generated knowledge blocks feed into encyclopedia and guide generation.

### ArticleService
ArticleService remains the canonical content access layer for Learning Center articles.

It should be used to:
- discover learning articles
- load article content by slug
- list articles by category or topic
- support topic cluster and FAQ generation from the existing article corpus

### Article Schema
The article schema continues to define the structure for all Learning Center content.

It should be used to validate:
- titles and descriptions
- section structure
- FAQ shape
- related articles, formats, converters, and tools
- breadcrumb and CTA metadata where applicable

### SeoService
SeoService remains the shared SEO renderer for metadata and structured data.

It should be extended conceptually to support:
- page title and description generation for each generated asset
- canonical URL generation
- robots metadata
- JSON-LD for articles, guides, comparisons, and encyclopedia pages
- breadcrumb schema generation

### InternalLinkService
InternalLinkService remains the cross-linking engine.

It should be reused to connect generated pages with:
- related converter pages
- related format pages
- related comparison pages
- related knowledge pages
- related Learning Center articles

---

## Generator Design

### 1. Topic Cluster Generator
Purpose: build topical content hubs around high-value search intents.

Inputs:
- format master records
- article topics and categories
- related converters and formats
- existing article metadata

Outputs:
- cluster landing pages
- article groupings by topic
- topic-level internal-link recommendations
- cluster metadata and breadcrumb structure

Why it fits the current architecture:
- It can reuse ArticleService to gather article content and InternalLinkService to connect the cluster to related assets.

### 2. Comparison Page Generator
Purpose: generate comparison pages for format pairs and conversion scenarios.

Inputs:
- format master records
- related format relationships
- converter metadata
- knowledge blocks for each format

Outputs:
- comparison page content structure
- SEO metadata
- FAQ blocks
- related converter and format links
- comparison-specific breadcrumb and schema data

Why it fits the current architecture:
- It naturally uses the Format Master Database and SeoService, and it can feed InternalLinkService with comparison relationships.

### 3. Guide Page Generator
Purpose: generate practical how-to and workflow pages for conversions, workflow choices, and format handling.

Inputs:
- converter mappings
- format knowledge blocks
- article content and topics
- common user intent patterns

Outputs:
- guide page content structure
- title and description variants
- step-based sections
- FAQ sections
- internal-link recommendations to converters, formats, and articles

Why it fits the current architecture:
- It aligns well with ArticleService and ArticleSchema because guides can be modeled as a specialized article type with a consistent shape.

### 4. Format Encyclopedia Generator
Purpose: build or enrich encyclopedia-style format pages.

Inputs:
- format master records
- format knowledge generator output
- related converters and formats
- related comparison candidates

Outputs:
- format encyclopedia page structure
- metadata and canonical targets
- related links
- FAQ sections
- comparison links and converter links

Why it fits the current architecture:
- It is the clearest reuse point for the Format Master Database and Format Knowledge Generator.

### 5. FAQ Generator
Purpose: produce question-and-answer content that supports both article pages and SEO landing pages.

Inputs:
- format knowledge blocks
- article sections and FAQ content
- topic cluster themes
- comparison page intent data

Outputs:
- FAQ arrays for articles, guides, comparisons, and encyclopedia pages
- search-intent-driven question variants
- schema-ready FAQ structures

Why it fits the current architecture:
- It can be shared across all generated page types and validated with the existing article schema and SEO output pipeline.

---

## Unified Generation Workflow

The full flow should be sequential and deterministic:

1. Collect canonical inputs
   - Load format master records
   - Load existing article content
   - Load converter and format relationship data

2. Generate content blocks
   - Use the Format Knowledge Generator to produce reusable knowledge sections
   - Use the FAQ Generator to create FAQ content per topic or format

3. Generate page payloads
   - Create topic cluster content
   - Create comparison page content
   - Create guide page content
   - Create encyclopedia page content

4. Validate generated payloads
   - Validate articles and generated article-like content with ArticleSchemaValidator
   - Validate knowledge-bearing payloads with the existing knowledge schema pattern
   - Ensure slugs, links, metadata, and FAQ structures are consistent

5. Enrich with SEO metadata
   - Use SeoService to add titles, descriptions, canonical URLs, robots, breadcrumbs, and JSON-LD

6. Add internal links
   - Use InternalLinkService to connect generated pages to related pages across the site

7. Publish through existing rendering layer
   - Render via the current routers and templates without introducing a new frontend framework

---

## Content Output Strategy

The engine should produce content in a form that fits the existing repository conventions:

- Learning Center and guide content under the existing article JSON structure
- encyclopedia and knowledge content through the existing format knowledge pattern
- metadata and SEO fields through SeoService
- link relationships through InternalLinkService

This keeps the architecture simple and compatible with the current app.

---

## Benefits of This Architecture

- Reuses the existing services and content shape instead of creating parallel systems
- Keeps content file-based and reviewable
- Supports topic clusters, comparisons, guides, and encyclopedia pages from one unified pipeline
- Makes SEO generation extensible without introducing new infrastructure
- Preserves compatibility with the current templates, routers, and validation patterns

---

## Recommended Governance Model

To keep the system maintainable:
- Treat the Format Master Database as the canonical source for format-level facts
- Treat ArticleService and ArticleSchema as the canonical source for Learning Center content
- Treat SeoService as the canonical metadata and schema renderer
- Treat InternalLinkService as the canonical internal-link engine
- Keep each generator focused on one page family and one intent type

This creates a clean, scalable architecture that fits the existing Converigo system rather than replacing it.
