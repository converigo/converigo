# Converigo Landing Automation Engine

## Architecture

The Converigo Landing Automation Engine is a content-generation and page-assembly system for producing converter landing pages from structured converter metadata. Its purpose is to make every converter page consistent, SEO-ready, and easy to publish while preserving a clear human review step.

### 1. Overall Architecture

The engine operates in a simple pipeline:

Converter Metadata
  -> Page Assembly
  -> SEO Content Generation
  -> Schema and Link Generation
  -> Review and Publish

The system should treat each converter as a structured object with known metadata and then assemble the landing page from reusable templates and rules.

### 2. Input

The engine should accept the following input objects:

- Converter
  - converter id
  - converter name
  - source format
  - target format
  - category
  - intent
  - description

- Category
  - video
  - audio
  - image
  - document
  - pdf
  - ocr
  - archive
  - ai

- Supported Formats
  - source formats
  - target formats
  - related formats
  - compatibility notes

- Metadata
  - title prefix
  - short description
  - use cases
  - benefits
  - FAQ items
  - related converters
  - canonical target
  - sitemap priority

### 3. Output

The engine should produce the following output components:

- Landing Page
  - hero section
  - upload CTA
  - benefits section
  - supported formats block
  - how-to-use section
  - FAQ section
  - related converters

- FAQ
  - short, useful answers for common user questions

- Meta Title
  - concise and keyword-aware
  - aligned with the converter intent

- Meta Description
  - one clear summary of the conversion benefit

- Open Graph
  - title
  - description
  - image fallback
  - URL

- JSON-LD Schema
  - WebPage or SoftwareApplication schema
  - FAQPage schema when FAQ content exists
  - BreadcrumbList schema

- Breadcrumb
  - category and tool hierarchy

- Internal Links
  - related tools in the same cluster
  - supporting blog links
  - adjacent category links

- Related Converters
  - same intent
  - same source or target format
  - same conversion journey

- Canonical Rules
  - one canonical URL per converter page
  - no duplicate routing variants

- Sitemap Entry
  - include the published page in the sitemap

### 4. Content Rules

Generated content should follow these rules:
- Focus on one primary converter intent.
- Avoid generic filler.
- Use plain, useful language.
- Show the user what the tool does in one clear paragraph.
- Keep the CTA obvious and immediate.
- Include a benefit-driven explanation rather than just a feature list.

### 5. SEO Rules

The engine should enforce these SEO rules:
- One clear primary keyword phrase per page
- One clear converter intent per page
- Unique title and description for each converter
- Canonical URL always present
- Structured data always present where appropriate
- Internal links built from related converters and topics
- No thin or duplicate pages

### 6. Quality Checklist

Before publishing, the generated page should pass this checklist:
- unique title
- unique meta description
- working internal links
- valid FAQ content
- correct schema markup
- correct breadcrumb path
- non-duplicate canonical URL
- clear CTA present
- page fits the converter category template

### 7. Duplicate Content Prevention

Duplicate content should be prevented by:
- generating unique titles and descriptions per converter
- using converter-specific metadata and examples
- preventing two pages from targeting the same canonical intent
- limiting auto-generated content to a shared structure and inserting unique facts
- requiring human review for near-duplicate pages

### 8. Future AI Integration

The engine should later support AI-assisted enhancements such as:
- automatic FAQ generation
- richer use-case summaries
- dynamic comparison sections
- variant-specific meta descriptions
- topic-cluster recommendations

AI should assist content creation, but the final page should still pass the review gate and remain human-verified.

### 9. Publishing Workflow

The publishing workflow should be:

Draft
  -> Metadata Review
  -> Content Assembly
  -> SEO Review
  -> Human Review
  -> Publish
  -> Index and Monitor

### 10. Human Review Gate

A human review gate is required before launch. The reviewer should verify:
- the converter is actually supported
- the content is accurate
- the page is useful to a real user
- the metadata is not misleading
- the internal links are appropriate
- the schema is valid

### 11. Versioning Strategy

Each generated landing page should be versioned with:
- page template version
- metadata version
- content rule version
- review status
- publish timestamp

This allows rollback and comparison when templates or rules change.

### 12. Rollback Strategy

Rollback should be simple and safe:
- keep the previous published version of the page
- preserve the last approved metadata snapshot
- revert to the previous template if quality drops
- remove or replace the page if duplicate-content or logic issues are found

## Workflow

Converter Metadata
  -> Template Assembly
  -> SEO Generation
  -> Schema and Link Build
  -> Human Review
  -> Publish

## Recommendation

Converigo should implement the landing automation engine as a metadata-driven content pipeline with a strong human review gate. This will allow the product to scale new converter pages quickly while keeping the quality, SEO structure, and internal linking system consistent.
