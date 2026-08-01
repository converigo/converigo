# Release Process

This document describes the release process for Converigo, from tagging to deployment verification.

## Release sources
- Releases are created from the `main` branch only.

## Release steps (summary)
1. Ensure all PRs merged into `main` have passing CI and reviewer approval.
2. Run the pre-release checklist locally (see `docs/WORKFLOW.md` and `docs/DEVELOPMENT_POLICY.md`).
3. Update changelog and bump version.
4. Create an annotated git tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"` and push tags.
5. Trigger the release pipeline (CI/CD) which builds artifacts, runs integration tests, and deploys to staging.
6. Run post-deploy checks: route checks, smoke UI tests, and sample conversions.
7. After staging verification, promote to production following deployment runbook.

## Post-release verification
- Confirm production endpoints serve expected static assets (logo, CDN content).
- Run a small QA smoke suite against production read-only endpoints.

## Rollback
- Use documented rollback procedures in the deployment runbook. Prioritize safety: if a release causes failures, rollback promptly and open an incident.
