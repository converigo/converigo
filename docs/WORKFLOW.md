# Converigo Workflow

This document describes the typical development workflow used by Converigo engineers. It is intentionally concise — follow `DEVELOPMENT_POLICY.md` for mandatory local rules.

## Branching
- Main branch: `main` (protected)
- Feature branches: `feature/<short-desc>`
- Hotfix branches: `hotfix/<issue-id>`

## Typical task flow
1. Create a feature branch from `main`.
2. Implement changes locally, run unit tests and `python -m compileall .`.
3. Use the canonical dev server (`http://127.0.0.1:8000`) and QA toolkit during development.
4. Capture desktop and mobile screenshots for visual changes and attach them to the PR.
5. Open a pull request with a clear description, test results, and screenshots.
6. Request review and address comments. Run the pre-merge checklist below before merging.

## Pre-merge checklist
- All tests passing locally and in CI.
- `python -m compileall .` exit 0.
- `qa_tools/route_inspector.py` shows expected routes.
- Playwright smoke checks pass (where applicable).
- UI visual diffs reviewed and approved.

## CI/CD
- CI runs the full test matrix, linting, and static checks.
- Releases are created from `main` only (see `RELEASE_PROCESS.md`).

## Where to find more
- Development policy: `docs/DEVELOPMENT_POLICY.md`
- QA toolkit: `docs/QA_TOOLKIT.md`
- Certification process: `docs/CERTIFICATION_PROCESS.md`
