# F-9 GOVERNANCE CLOSURE + EVIDENCE RECONCILIATION

**Date:** 2026-09-10 · **Authority:** Supervisor · **Role:** Executor · **Mode:** Controlled implementation (documentation/governance only)
**Decision Record:** **D012** — see `brain/DECISIONS.md`
**Canonical production:** `worthy-light / production / converigo`
**Production SHA (baseline):** `d4723f476a50dfa8ab00b7ddc6c41ded8240aff9`

---

## 1. Technical status

| Item | Result |
|---|---|
| F-9 technical verification | **CLOSED / PASS** |
| Merge commit | `47a373b03a3a9c0e7e2153729a4ef3001e1be189` (PR #89, non-squash) |
| Ancestry | **PASS** — `47a373b` is an ancestor of `d4723f4` (topological, `merge-base --is-ancestor` = exit 0) |
| Registry provenance | **PASS** — 5 × `<slug>.json` + 5 × `<slug>.contract.json` present on blob `d4723f4`, introduced by `c9d8849`, untouched between `47a373b` and `d4723f4` |
| Rendering model | **Registry-driven** — no generic fallback; missing registry → `HTTPException(404, "Tool page not found")` |
| Production routes | 5 `/tools/<slug>` = HTTP 200 + real content; sitemap includes the 5 URLs |
| Post-migration production verification | **FULL PASS (21/21)** |

F-9 slugs: `csv-to-xlsx`, `xlsx-to-csv`, `csv-to-json`, `json-to-csv`, `mp4-to-gif`.

## 2. Governance status

- **Ratification:** Supervisor **D012** — F-9 retained; **no rollback**; **no F-9 production code change**.
- **Historical authorization:** **NOT verifiable from the repository.** D012 is a *current* ratification of the existing outcome, not a reconstruction of the 2026-09-07 approval.

## 3. Production

- **Canonical:** `worthy-light / production / converigo`.
- **Baseline SHA:** `d4723f4`.
- **Deployment of PR #89:** `47a373b` was deployed to the canonical production at **`2026-09-07T12:06:18Z`** (GitHub deployment id `6308303831`, final status `success` @ `2026-09-07T12:12:22Z`).
- **Legacy:** `amiable-growth` = offline / legacy (not canonical).

## 4. Final status

**F-9 = CLOSED / PASS.** Governance closed by D012. No rollback. No production code change.

## 5. Erratum

Historical evidence is preserved verbatim. A clearly-marked **ERRATUM** was appended to `F9_POSTMERGE_INCIDENT_REPORT.md` to correct the "PR #89 not in production canonical / production offline" reading. Corrections recorded there:

- `amiable-growth` = legacy / offline production.
- `worthy-light` = canonical production.
- PR #89 / `47a373b` **was** deployed to `worthy-light` @ `2026-09-07T12:06:18Z`.
- Current baseline = `d4723f4`.

## 6. Scope guard

Documentation/governance only. No change to: `pdf-metadata`, F-9 contracts' `canonical_url`, 5 WIP converters, 7Z, 7 regressions, PR-1d, SEO implementation, production, worktrees, or the converter ledger.

## 7. Related evidence

- `F9_EVIDENCE_REPORT.md` (pre-merge, historical)
- `F9_POSTMERGE_INCIDENT_REPORT.md` (+ ERRATUM)
- `F9_POSTMIGRATION_PRODUCTION_VERIFICATION.md` (21/21 PASS)
- `f9_prodver_deployment_status.txt`, `f9_ledger_at_47a373b.json`, `f9_converters_at_47a373b.txt`