# Converigo Project State

## Vision

Converigo is a modern online file conversion platform designed to be the easiest, fastest, and cleanest way to convert files.

The focus is on building a trusted conversion experience with polished UX, strong SEO, and a clear product foundation.

## Current Phase

- **Phase:** Product Foundation
- **Current focus:** Legacy template cleanup and release readiness
- **Checkpoint:** C3.3.1
- **Milestone:** Legacy Cleanup

## Current Milestone

- **Universal Tool Page**
- Completed migration of landing rendering to a JSON-driven universal tool page for converter routes.
- Legacy public URLs remain active while sharing the same renderer and structured data pipeline.
- Ensured universal sections for hero, upload, benefits, features, formats, how-to-use, FAQ, related tools, use cases, about formats, CTA, and structured data are rendered from converter JSON.

## Packages in Scope

- `IMG-001 PNG→WEBP`
  - Landing page
  - Converter metadata
  - Route and SEO support
  - Tests

- `IMG-002 WEBP→PNG`
  - Landing page
  - Converter metadata
  - Route and SEO support
  - Tests

## Roadmap Summary

1. Complete the Image Foundation milestone.
2. Validate category landing pages, metadata, and internal linking.
3. Secure release readiness through QA and repository audit.
4. Prepare the first checkpoint for GitHub Push.
5. Preserve legacy public URLs while introducing a shared universal converter route.

## Development Workflow

- Work from `main` or a release branch.
- Keep feature scope limited to the current checkpoint.
- Do not modify unrelated application code during release preparation.
- Use `brain/` docs as the single source of truth for release status.

## Checkpoint Health

- Checkpoint C1 is focused on the image category.
- The project is in a release gate phase: audit, cleanup, and prepare for push.
- Only intended files for C1 are staged in git.
