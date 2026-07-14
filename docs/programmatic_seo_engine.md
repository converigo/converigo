# Programmatic SEO Engine

## Architecture

- The SEO engine reads converter contracts from the existing converter registry contract files.
- Each active contract produces a deterministic SEO payload with:
  - SEO title
  - meta description
  - intro copy
  - FAQ entries
  - CTA copy
  - related keywords
  - breadcrumb data
  - JSON-LD payload
- Template substitution supports simple placeholders such as {name}, {source}, and {target}.
- The output is deterministic and stable across repeated runs for the same contract set.
