# Converigo Decision Log

## Decision Record

### D001 — Checkpoint-first release process
- **Decision:** Use named checkpoints to manage release scope and audit readiness.
- **Rationale:** Checkpoints keep the project focused and prevent unrelated changes from leaking into release candidate builds.
- **Outcome:** Checkpoint C1 is the official release gate for Image Foundation.

### D002 — Image Foundation milestone
- **Decision:** Treat the image category as the first formal milestone after project initialization.
- **Rationale:** Image conversions are a core product offering and provide clear value for release.
- **Outcome:** C1 delivers `IMG-001` PNG→WEBP and `IMG-002` WEBP→PNG as the first production packages.

### D003 — No code change in documentation
- **Decision:** Brain and release docs are separate from application code.
- **Rationale:** Documentation files should not alter runtime behavior or feature scope.
- **Outcome:** All `brain/` and `docs/` files are content-only and do not modify application code.

### D004 — Release blockers only
- **Decision:** For C1 final push, only unresolved release blockers may be addressed.
- **Rationale:** Avoid scope creep and preserve checkpoint integrity.
- **Outcome:** The final audit and fix cycle was limited to accessibility and repository cleanliness.

### D005 — Git readiness validation
- **Decision:** Only checkpoint-related files are staged for the C1 commit.
- **Rationale:** Ensures a clean release commit with no accidental changes.
- **Outcome:** C1 readiness was verified for the intended files only.

### D006 — Universal route compatibility
- **Decision:** Introduce a shared universal converter route without removing or changing existing public URLs.
- **Rationale:** Route compatibility is required for SEO stability, legacy links, and gradual migration to JSON-driven landing rendering.
- **Outcome:** Existing landing URLs remain functional while the shared route uses the same converter data service and tool template.

### D007 — JSON-driven tool page sections
- **Decision:** Render all universal tool page sections from converter JSON data and keep router logic minimal.
- **Rationale:** This reduces hardcoded landing logic and ensures consistent migration across tools.
- **Outcome:** Hero, upload, benefits, features, supported formats, how-to-use, FAQ, related tools, use cases, about formats, CTA, and structured data are now derived from JSON-driven context.

### D008 — Legacy template containment
- **Decision:** Move legacy landing templates into a dedicated legacy folder without changing routes, URLs, SEO, or runtime behavior.
- **Rationale:** This cleans up template structure while preserving compatibility and avoiding regressions.
- **Outcome:** Legacy landing templates are preserved under the legacy folder and the active landing experience remains centered on the universal tool page.

### D009 — SEO Audit Engine as read-only service
- **Decision:** Create a standalone, read-only SEO audit engine (`SeoAuditEngine`) that inspects converter pages without modifying any existing architecture.
- **Rationale:** A separate audit layer provides deterministic SEO health metrics without risk of altering routing, converters, or plugins.
- **Outcome:** All 46 converter pages are audited with 15 check types each. Average score 84.2/100 (GOOD). No architecture changes required.

### D010 — SEO Content Enhancement via JSON data files
- **Decision:** Enhance converter landing pages by modifying only the JSON data files (`app/data/converters/*.json`) without changing any templates, routes, or backend logic.
- **Rationale:** JSON data files are the single source of truth for page content. Enhancing them is data-only, requires no code changes, and the SEO Audit Engine automatically reflects improvements.
- **Outcome:** Average SEO score improved from 84.2 → 98.9/100. All 46 pages now EXCELLENT (90-100). Dashboard updated with SEO Audit section. No architecture changes.

### D011 — Search Console Readiness as separate read-only audit service
- **Decision:** Create a separate `SearchConsoleReadinessService` dedicated to validating Search Console requirements (sitemap, robots, indexability, structured data, canonical, core SEO) without modifying the existing SEO Audit Engine.
- **Rationale:** Search Console readiness is a distinct concern from SEO scoring. A separate service keeps concerns separated, uses a weighted scoring model (100 points across 6 categories), and provides actionable recommendations specific to Search Console verification.
- **Outcome:** 24 tests PASS. 61 pages audited with 736 checks. Readiness Score: 41.2/100 (CRITICAL) — baseline established. API endpoint and dashboard integration complete. No architecture changes.

Decision Record: FASE 16 — CLOSED (2026-08-18)

Context
- Baseline run: two E2E tests failed during Phase 16 verification:
  - `tests/e2e/test_convert_flow.py::test_jpg_conversion_flow`
  - `tests/e2e/test_convert_flow.py::test_png_conversion_flow`
- Failure symptom: Playwright `TimeoutError` waiting for `.format-chip` to appear in the served UI.

Summary baseline
- Two E2E tests failed as listed above; root cause surfaced as a frontend runtime mismatch where `.format-chip` is never rendered during the tested flow.

Root cause
- Two parallel upload implementations exist in the codebase:
  - Legacy inline flow: `addFiles()` (inline in `converigo_main.html`) — active in the served page during tests.
  - Modular flow: `UploadManager` / `RecommendationManager` (static JS modules) — present on disk and served, but not effective for the upload path exercised by the tests.
- Result: the modular `RecommendationManager` flow (which would render `.format-chip`) is not invoked in the runtime path used by the failing tests; the legacy inline path does not call the recommendation render, producing no `.format-chip` and causing the Playwright timeout.

Classification
- A — Application bug. Record as dev backlog item; not a Phase-16 blocking regression for release gating.

Investigation pointer
- Relevant commit for follow-up: `28d40ec` (message: "consolidate production mainpage and remove legacy homepage") — inspect how legacy vs modular flows were merged and which template remains active in production.

Clarification about "hang"
- Not a true hang: isolated re-runs of the E2E tests exit normally after the configured Playwright timeout (~3 minutes), consistent with observed TimeoutError behavior.

Production / Safety
- No application source code was changed or committed during the investigation. All temporary experiment files and scripts created for runtime checks were removed or reverted before this entry.

Decision
- FASE 16: CLOSED. Proceed to FASE 17. Track this frontend bug as a separate backlog ticket for the dev team to reconcile legacy vs modular upload/recommendation flows.

Recorded: 2026-08-18
Recorder: GitHub Copilot (agent-assisted)
