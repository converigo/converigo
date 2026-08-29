# PR #47 — Phase G Regression Gate Audit Trail

**Date:** 2026-08-29  
**Branch:** `release/phase-g` → `main`  
**Merge commit:** `d08645e5e91523b0aced54bed35afda993a81c6a`

## Context

This directory archives the full pytest regression gate output for **PR #47** ("Phase G: Cluster 4B+4C request-local output_dir/temp_dir contract, race-condition fix, e2e fixture").

The PR delivered three key changes:

| Commit | Description |
|--------|-------------|
| `addfd39` | Phase 26.4 Cluster 4B: migrate archive+image plugins to request-local output_dir/temp_dir signature |
| `ded881e` | Fix (test): resolve race condition in partial failure UI test |
| `f4dfe45` | Feat (conversion): complete Cluster 4C request-local output_dir/temp_dir contract (document/audio/video engines + all 29 plugins) |
| `60ddcfb` | Test (e2e): commit canonical real-test.jpg fixture (8.2KB, valid) so e2e suite is self-contained |

## Regression Gate Results

| Run | File | FAILED | PASSED | Notes |
|-----|------|--------|--------|-------|
| **Baseline** (pre-PR #47) | `pytest_full_baseline.txt` | 15 | 568 | Pre-existing failures (i18n, SEO, globalfmt, etc.) |
| **Live** (post-PR #47) | `pytest_full_live.txt` | 15 | 568 | Identical to baseline — no regressions |
| **Phase A** (Cluster 4B) | `pytest_full_live_phaseA.txt` | 16 | 568 | 1 new failure: `test_normal_conversion_succeeds` (output_dir/temp_dir breakage) |
| **Phase A Fixed** (Cluster 4C) | `pytest_full_live_phaseA_fixed.txt` | 14 | 570 | Cluster 4C + race-condition fix resolved 2 failures; net -1 from baseline |

**Verdict:** 0 new regressions. The 14 remaining failures are pre-existing (i18n, SEO landing pages, office converter hub, sitemap, production audit — all unrelated to Cluster 4B/4C).

## File Contents

| File | Description |
|------|-------------|
| `pytest_full_baseline.txt` | Full pytest output before PR #47 changes (848s) |
| `pytest_full_live.txt` | Full pytest output after PR #47 changes merged (900s) |
| `pytest_full_live_phaseA.txt` | Full pytest output after Cluster 4B migration only (926s) |
| `pytest_full_live_phaseA_fixed.txt` | Full pytest output after Cluster 4C + race-condition fix (727s) |
| `pytest_summary.txt` | Short summary of final live run (15 failed, 568 passed) |

## Relevant Resources

- [PR #47](https://github.com/converigo/converigo/pull/47) — "Phase G: Cluster 4B+4C request-local output_dir/temp_dir contract, race-condition fix, e2e fixture"
- [Merge commit d08645e](https://github.com/converigo/converigo/commit/d08645e5e91523b0aced54bed35afda993a81c6a)