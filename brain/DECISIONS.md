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

### D012 — F-9 Ratification: Retain Merged Registry Restore (PR #89) and Correct Production-History Record
- **Decision:** Ratify — for the record and as the current Supervisor decision — the already-merged and already-deployed F-9 registry restore (PR #89, merge commit `47a373b`), and retain it **without rollback**. F-9 technical verification is **CLOSED / PASS**. No production code change is made for F-9.
- **Rationale:** F-9 results are already in the production lineage and are verified. A rollback would remove working, registry-driven pages and create more risk than it removes. The correct governance action is to ratify the existing outcome and record the evidentiary limits honestly.
- **Historical authorization limit (stated honestly):** The historical approval of 2026-09-07 **CANNOT be verified from the repository**. This record is a CURRENT Supervisor ratification of the existing outcome — it is **NOT** a reconstruction or retroactive proof of the original approval.
- **Evidence basis:** merge `47a373b` proven **ancestor** of production baseline `d4723f4` (topological `merge-base --is-ancestor` = exit 0, not timestamp-based); the 5 F-9 registry + contract JSON present on blob `d4723f4` and untouched between `47a373b` and `d4723f4`; the 5 `/tools/<slug>` routes return HTTP 200 served **from the registry** (no generic fallback — `render_universal_tool_page` raises `HTTPException(404, "Tool page not found")` on missing registry); sitemap includes the 5 URLs.
- **Outcome:** F-9 = **CLOSED / PASS**. No rollback. No F-9 production code change. Production canonical = `worthy-light / production / converigo @ d4723f476a50dfa8ab00b7ddc6c41ded8240aff9`. Governance of F-9 is closed by this ratification. Evidence: `f7_evidence/f9/F9_GOVERNANCE_CLOSURE.md`.
- **Known orphan references (recorded for honesty):** `brain/ROADMAP.md` cites "Decision D013" (governance reconciliation) although no D012/D013 record existed prior to this entry. This entry therefore uses the next genuinely free number, **D012**. D013/D014 remain unrecorded.
