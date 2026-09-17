# XLS→XLSX remediation — evidence-acquisition report

**Evidence only. No implementation.** No converter code, no PR, no merge, no
deploy, no ledger/certification change, and no change to any permanent source
policy was made in this work.

> **Provenance note (honest disclosure).** The original Tasks 1–4 body of this
> file was damaged beyond recovery by a shell redirect error during this
> session (a `Get-Content | Out-File` round-trip on the same path truncated it).
> It was **not** recoverable from git (the file is untracked) or from any
> working-tree copy. Rather than reconstruct numbers from memory, this file now
> points at the artefacts that still exist on disk and at the complete, fresh
> CI evidence report that supersedes it. **The authoritative report is
> [`XLS_XLSX_FINAL_REMEDIATION_EVIDENCE_REPORT.md`](./XLS_XLSX_FINAL_REMEDIATION_EVIDENCE_REPORT.md)**
> (also at `.tmp/xls_prep/final_evidence/`).

| | |
|---|---|
| Date | 2026-09-16 (Tasks 1–4, local) · 2026-09-17 (fresh CI evidence run) |
| Host | Windows (`os.name=nt`, `sys.platform=win32`), Python 3.11.9 |
| Runtime available | **no `soffice`/`libreoffice`, no Docker/podman, no WSL** — hence the CI run |
| Workspace | probes under git-ignored `.tmp/xls_prep/` (`git check-ignore` → `.gitignore:87:*.tmp`) |
| Gate definitions | `docs/PHASE4_ENGINE_POLICY.md` G1–G6 |
| Supervisor tasks | 1 G4 containment · 2 G5 preflight · 3 BIFF5 fixtures · 4 G6 production resources |

---

## Section H — Fresh CI evidence run (2026-09-17)

The local host cannot run LibreOffice, so all gate evidence was captured in CI
on the production image. Four harness defects were found and repaired before
the clean run (details in the FINAL report §H):

| ID | Defect | Fix |
|----|--------|-----|
| D1 | fixture path missed `spike_kit/fixtures/` | `_resolve_fixture()` dual-path |
| D2 | BOF version regex read 1 byte | anchored header, 2-byte field |
| **D3** | **`phase_conc` had no `return` → `results` always `null`** | **added `return res`** |
| D4 | conc loop overwrote one JSON per N | per-N `evidence_conc_${N}.json` |

**Clean run:** `35178439497` · branch `fix/pr1-ole2-honest-disable` @ `0065a04` ·
`workflow_dispatch` with `conc="1 2 4 8"` · **conclusion: success**

| Gate | Result | Key numbers |
|------|--------|-------------|
| **G4 containment** | **PASS** | 3/3 tiers SIGTERM-killed, whole-tree reaped, **0 orphans / 0 zombies / 0 residue**; SIGKILL escalation control verified (exit −9) |
| **G6 single** | **PASS** | sample 0.615 s · stress 1.067 s · bulk 21.8 MB → 3.574 s, **404 MiB** cgroup peak (42 % of the 954 MiB Railway cap) |
| **G6 concurrency** | **PASS, 1 transient** | N=1 1/1 · **N=2 1/2** (worker SIGABRT 134, `WrappedTargetRuntimeException`) · N=4 4/4 · **N=8 8/8** in 2.103 s at **922 MiB = 97 % of cap**, 0 OOM kills |
| **BIFF5 / 0x0550** | **CONFIRMED** | BIFF5/BIFF7 → `0x0500`; third-party variant → **`0x0550`**; malformed/non-OLE2 → `None`; 10/10 converted by real soffice, zero rewriting |

Concurrency metrics are **captured and valid** — the blocker from the previous
run is closed. The N=2 SIGABRT is a genuine LibreOffice 25.2.3.2 startup race
(profiles were already isolated per worker) and is recorded as retryable for the
implementation phase.

---

## Local Tasks 1–4 artefacts (still on disk, git-ignored)

The probes themselves and their machine-readable output are intact even though
the prose body was lost; every number in the FINAL report traces to these:

| Task | Path | Contents |
|------|------|----------|
| 3 — BIFF5 fixtures | `.tmp/xls_prep/biff5/make_biff5.py` | 9 deterministic `.xls` generators + SHA-256 |
| 3 — fixture validation | `.tmp/xls_prep/validate_fixtures.py` | xlrd 2.0.2 cross-check verdicts |
| 2 — G5 preflight | `.tmp/xls_prep/preflight/preflight_validator.py`, `preflight_results.json` | preflight rule engine + results |
| 1 — G4 containment | `.tmp/xls_prep/g4/g4_probe.py`, `g4_results.json` | containment probe (local, POSIX-design) |
| 4 — G6 production resources | `.tmp/xls_prep/g6/railway_query.py`, `g6_deployments.json`, `g6_railway_status.json` | read-only Railway GraphQL envelope query |
| CI evidence run | `evidence_artifacts/fresh-run/final-evidence/` | the five phase JSONs + `summary.md` from run `35178439497` |
| Previous CI run | `.tmp/xls_prep/final_evidence/new-run/` | run `35174757691` artifacts, kept for provenance of the D1–D4 repairs |

**Supervisor decision requested:** whether the G4/G6/BIFF5 evidence in the FINAL
report is sufficient to open the Implementation Gate.
