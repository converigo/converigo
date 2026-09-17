# XLS → XLSX — LINUX ENVIRONMENT ACQUISITION REPORT

**Status:** Implementation Gate **remains CLOSED**. Evidence/discovery only.
**Scope:** read-only audit of existing environments. No dispatch, no PR, no Railway
write, no app/contract/registry change, no production stress test.

---

## 0. Executive summary

The runtime the previous gap-closure report named as the single blocker — *"a Linux
host with cgroup v2 and LibreOffice"* — **already exists in this repository's own CI
and has already executed successfully once**, producing measured, Linux-native
LibreOffice evidence for G1–G6.

| Question | Answer |
|---|---|
| Does a Linux + cgroup-v2 + LibreOffice path exist today? | **YES** — GitHub Actions `ubuntu-latest` + `spike_kit` LibreOffice image |
| Has it actually run? | **YES** — run `35095551296`, `success`, 2026-09-16, 1m10s |
| Did it produce real G6 numbers? | **YES** — peak RSS at n=1/4/8 measured against real `soffice` |
| Is the G4 kill path closed by that run? | **NO** — T6 `killed=false`; the fixture converted in 0.776 s, under the 1.5 s timeout, so SIGTERM→SIGKILL never fired against real `soffice` |
| Was any production stress test run? | **NO** — Railway was queried read-only only (limits re-verified) |
| Is anything new installed or created? | **NO** — no Docker/WSL/LibreOffice install, no staging service, no repo change |

**Correction to the prior report.** `XLS_XLSX_REMEDIATION_GAP_CLOSURE_REPORT.md` §A.1/§D
records that *no container exists and standing one up would be an implementation
action*. That was accurate **for the local Windows host**, and it remains accurate
there. But it is no longer the whole picture: PR #112 (commit `8893972`, merged
2026-09-16T12:22Z, *"CI/kit-only XLS→XLSX LibreOffice spike. No application
enablement."*) added a disposable spike kit **and a dispatch-only verify workflow on
`main`**. That path postdates the working branch (`fix/pr1-ole2-honest-disable` @
`f1f9e62`) and the stale local `origin/main` ref (`dbd543f`), which is why it was not
visible in the previous audit. Blockers **D1 and D2 are now substantially
addressable** through infrastructure that already exists; D3 (spec fetch) is
unaffected.

---

## A. Discovered environments

Discovery was exhaustive and read-only: local host scan, `gh` (authenticated as
`converigo`, scopes `repo`+`workflow` — **list/view/download only, zero dispatch**),
and Railway CLI (authenticated as `jevi thos`) read-only GraphQL.

| # | Environment | Linux | LibreOffice | cgroup v2 | Status | Evidence |
|---|---|---|---|---|---|---|
| **E1** | **GitHub Actions `ubuntu-latest` via `lo-spike-verify`** (`.github/workflows/lo-spike-verify.yml`, on `main`) | ✅ kernel 6.17.0-1022-azure x86_64 | ✅ LO 25.2.3.2 | ✅ readable | **ACTIVE, 1 successful run** | workflow ID `359618112`; run `35095551296`, `success`, `workflow_dispatch`, 2026-09-16T12:23:37Z, 1m10s |
| **E2** | **GitHub Actions `ubuntu-latest` via `docker-runtime-verify`** (`.github/workflows/docker-verify.yml`) | ✅ same runner | ✅ (production image installs `libreoffice`, `Dockerfile:9`) | ✅ | **ACTIVE, healthy CI** (5/5 recent runs success) | workflow ID `350723934`; triggers `pull_request`/`push`/`workflow_dispatch` |
| **E3** | Railway **production** (service `converigo`, id `34e98712-762c-47b6-b87e-1acfbce6fca8`, region `iad`, ● Online) | ✅ | ✅ (image has `libreoffice`) | ✅ | **EXISTS — explicitly NOT a test target** | only environment that exists on Railway |
| **E4** | Local Windows host | ❌ (Cygwin 3.6.9 emulation only) | ❌ absent | ❌ | unchanged | prior report §A.1 |

**Negative findings (unchanged, re-verified):** no `soffice`/`libreoffice` locally;
no Docker/podman/nerdctl/containerd, `act`, colima, lima, or qemu on the host; WSL
`wsl.exe` present but no distro installed; no reachable remote box; no other CI
systems (no Jenkinsfile, `.gitlab-ci.yml`, `.circleci`).

**Railway has no non-production environment.** `railway environment list` returns
exactly one environment: `production (linked)`. There is no staging/preview
environment to reuse, and creating one is explicitly disallowed.


---

## B. Exact environment capabilities

### B.1 E1 — `lo-spike-verify` (the recommended path)

Proven by its own completed run. Exact, measured capability:

| Capability | Value (from the actual run, not assumed) |
|---|---|
| Kernel / arch | `Linux 6.17.0-1022-azure x86_64`, `in_container=True` |
| Python | 3.11.16 |
| `soffice` binary | `/usr/bin/soffice` (found on first candidate) |
| LibreOffice version | `25.2.3.2 520(Build:2)` |
| Image base | `python:3.11-slim` + `libreoffice libreoffice-calc libreoffice-writer libreoffice-impress` (`Dockerfile.spike`), the **same apt line as the production `Dockerfile` at baseline `a932341`** — version, profile layout and process model match production |
| Build guard | `RUN soffice --version` — the image build **fails** if LibreOffice is absent |
| CPUs visible in container | 4 |
| `memory.max` | `"max"` — **cgroup v2 present and readable, but NO cap applied** |
| `cpu.max` | `"max 100000"` — unconstrained |
| Cold-start wall | full spike (image build + T1–T8) completed in **1m10s** |
| Permissions | `contents: read` only |
| Trigger | `workflow_dispatch` **only** — never runs automatically; inputs `conc` (default `4,8`) and `stress_timeout` (default `15`) |
| Artifact | `spike-report` (`spike_report.json` 5,853 B · `spike_report.md` 4,568 B · `summary.md` 992 B) — **already retrieved read-only** to `.tmp/xls_prep/spike_artifact/` |
| Design intent (quoted from the workflow) | *"It executes no application code, needs no secrets … this workflow never enables anything by itself."* |

What the instruments measure (`spike_kit/spike/lo_spike.py`, stdlib-only, 557 lines):

- **RSS** — 40 Hz poll of `/proc/<pid>/status` `VmRSS` summed across **every** live
  `soffice`/`libreoffice` process, so it includes `soffice.bin` (where the real
  memory lives on Linux). This is the same whole-tree `/proc` discipline the prior
  report's C.3 accounting proof demanded.
- **Containment** — `start_new_session=True`, then on timeout `os.killpg(getpgid, 15)`
  → 5 s grace → `os.killpg(getpgid, 9)` → reap: the exact setsid→SIGTERM→grace→SIGKILL
  sequence already proven in `g4_probe_posix.pl`, here against **real `soffice`**.
- **Residue** — temp dirs, profile dirs, `.lock` files, live `soffice` procs, and
  `/proc` `State: Z` zombies.
- **cgroup** — reads `/sys/fs/cgroup/memory.max` + `cpu.max` (v2) with v1 fallback.

### B.2 E2 — `docker-runtime-verify`

Builds the **real production image** from the branch `Dockerfile` and runs a
parameterised probe inside it (`probe_script` / `certified_suite` dispatch inputs,
defaulting to the RAR suite). Since the production image already contains
`libreoffice`, E2 can execute LibreOffice probes *in the production image* without
touching production itself. 5/5 recent runs green (2026-09-15 → 2026-09-16).

### B.3 Measured evidence already in hand (from run `35095551296`)

| Gate | Probe | Measured (Linux-native, real `soffice`) |
|---|---|---|
| G1 | T1 ×5 / T2 ×20 | **5/5** and **20/20** valid XLSX; drift last−first = **0.001 s**; mean 0.452 s |
| G3 | T3 unique profiles | n=4: **4/4**; n=8: **8/8**; no cross-talk |
| G3 | T4 shared profile | **5/8** valid, 0 lock messages — the shared-profile hazard is real |
| G4 | T6 timeout kill | `killed=false`, orphans 0, zombies 0 — **kill path NOT exercised** (see C.4) |
| G4 | T8 residue | `temp_dirs_left=1`, `profile_dirs_left=0`, `live_soffice=0`, **`zombies_at_end=5`** |
| G5 | T7 malformed | **all three** corrupt/truncated/masquerade inputs were "repaired" into *valid* XLSX — garbage-in does NOT mean garbage-out with `soffice` |
| G6 | T5 / T3 peak RSS | see C.5 |


---

## C. Linux / cgroup-v2 availability

### C.1 Linux kernel — YES
`Linux 6.17.0-1022-azure x86_64` on the GitHub-hosted `ubuntu-latest` runner, inside
the spike container (`in_container=True`). This is a real Linux kernel, not an
emulation layer — a category upgrade over the Cygwin 3.6.9 evidence in the prior
report.

### C.2 cgroup v2 — YES, present and readable
The run's `container_envelope` successfully read `/sys/fs/cgroup/memory.max` and
`/sys/fs/cgroup/cpu.max` — **cgroup-v2 unified-hierarchy files** — so v2 is mounted
and readable in the runner container (v1 would have fallen through to
`memory/memory.limit_in_bytes`, which did not happen).

### C.3 …but NOT pinned to the Railway budget
`memory.max = "max"` and `cpu.max = "max 100000"`: the spike container ran
**unconstrained**. So the RSS figures below are `soffice`'s *appetite*, not its
behaviour **under** Railway's 1 GB cap (where the n=8 case would be OOM-killed).
`run_in_docker.sh` passes no `--memory`/`--pids-limit`. A Railway-faithful G6
measurement needs the cap applied — see §G.

### C.4 G4 status — the existing run does NOT close it
T6 used the committed stress fixture `stress_biff8_120kc.xls` (2,680,320 B) with a
**hardcoded 1.5 s** timeout. That fixture converted in **0.776 s**, so the timeout
never expired, `killed=false`, and the SIGTERM→grace→SIGKILL escalation has **still
never fired against real `soffice` on Linux**. The dispatch input `stress_timeout`
feeds T5 (`timeout = stress_timeout * 4`) only — **T6's 1.5 s is not tunable from the
workflow UI.** This is the precise remaining G4 gap.

### C.5 G6 status — real numbers now exist (unconstrained)

| Scenario | Peak RSS | vs Railway 1,000,000,000 B budget |
|---|---|---|
| T5 single (120 k cells) | **222,130,176 B** (211.8 MiB) | 22.2% — 77.8% headroom |
| T3 concurrency n=4 | **882,679,808 B** (841.8 MiB) | **88.3%** — only 11.7% headroom |
| T3 concurrency n=8 | **1,385,431,040 B** (1,321.2 MiB) | **138.5% — EXCEEDS BUDGET** |

Marginal cost per additional worker (n=4→8): 125,687,808 B ≈ 119.9 MiB (shared pages
amortise the ~211.8 MiB single-conversion cost).

This is the first real, Linux-native, `soffice`-measured input for the G6 guard —
the exact input the prior report recorded as missing (`guard.status =
NOT_DERIVABLE`). It is now *derivable in principle*, but two honest caveats hold:
**(i)** the container was uncapped, so these are demand figures, not capped
behaviour; **(ii)** RSS is 40 Hz-sampled `VmRSS`, not the kernel-maintained
`memory.peak` the `g6_measure.py` design calls for, so transient peaks can be
missed. A conservative reading already says: **n=4 leaves only 11.7% headroom and n=8
is over budget** — any safe guard is well below 8.

---

## D. LibreOffice availability

| Location | LibreOffice | Detail |
|---|---|---|
| E1 spike image | ✅ **25.2.3.2** | `Dockerfile.spike`: `python:3.11-slim` + `libreoffice`/`-calc`/`-writer`/`-impress`; `RUN soffice --version` guards the build |
| E2 / E3 production image | ✅ | `Dockerfile:9` installs `libreoffice` (same apt line as the spike image at baseline `a932341`) — production already ships it |
| Local Windows host | ❌ | absent; not to be installed here |

Version match matters: the spike image deliberately mirrors production's LibreOffice
line, so process model (`soffice` → `oosplash` → `soffice.bin`), profile layout and
`-env:UserInstallation` behaviour are production-representative.

---

## E. Recommended evidence path

**E1 — `lo-spike-verify` on `main`.** Rationale, ranked:

1. **It already exists and already works** — no new infrastructure, no install, no
   Railway change, no app code. Zero acquisition cost.
2. **It is production-faithful** — same LibreOffice apt line and base image as
   production; runs inside a container on a real Linux kernel.
3. **It is disposable and isolated** — an ephemeral CI job in an ephemeral container.
   It touches no Railway resource, needs no secrets (`permissions: contents: read`
   only), and "never enables anything by itself."
4. **It is parameterised** — `conc` and `stress_timeout` dispatch inputs, plus an
   artifact upload, so follow-up evidence runs are re-dispatches, not new code.
5. It is the only path that satisfies **all** requirements (Linux + cgroup v2 +
   LibreOffice) *without* the forbidden actions.

E2 (`docker-runtime-verify`) is the fallback if evidence must run inside the exact
production image; it is heavier (full production build) and its default probe is the
RAR suite.

Railway production is **not** a recommended path — it is the protected target, and no
staging environment exists to substitute for it.

---

## F. What can be executed immediately

**Already done this task (all read-only, all verified):**

- Retrieved the existing `spike-report` artifact (run `35095551296`) — real G1/G3/G5
  results and the first real G6 peak-RSS numbers.
- Re-verified Railway limits fresh via read-only GraphQL:
  `cpu=2`, `memoryBytes=1,000,000,000`, `pidLimit=1000`, `limitOverride=null`,
  latest deployment `64f57561` **SUCCESS** @ 2026-09-16T12:22:06Z on commit `8893972`.
- Confirmed `docker-runtime-verify` CI is green (5/5) and that only `production`
  exists on Railway.

**Ready to execute, no repo/Railway change, no production impact — but NOT auto-run
per instruction ("jangan otomatis … menjalankan stress test"):**

```bash
# re-dispatch of the EXISTING workflow on main; nothing is created or modified
gh workflow run lo-spike-verify.yml \
  --ref main -f conc=2,3,4,8 -f stress_timeout=15
```

This alone would yield per-N peak RSS at 2 and 3 (the values a conservative guard
actually needs, currently unmeasured) and confirm reproducibility. It does **not**
close G4 — T6's timeout is hardcoded and its fixture is too fast (§C.4).

**Explicitly NOT executed:** any workflow dispatch, any stress test, any Railway
mutation, any app/contract/registry edit, any PR.

---

## G. Remaining prerequisites requiring Supervisor approval

Every item below needs an approval decision because each is either a repository
change or a CI run — none is a local action.

| # | Prerequisite | Why it needs approval | Exact gap it closes |
|---|---|---|---|
| **G1** | Permission to **dispatch `lo-spike-verify`** (a disposable CI stress run) | Instruction says do not auto-run stress tests | First cgroup-visible G6 numbers at N=2/3; G1/G3/G5 reproducibility |
| **G2** | **Commit `stress_biff8_bulk1m.xls` (21,836,800 B, 1 M cells / 20 k formulas) to `spike_kit/fixtures/` on `main`** — it exists locally under `.tmp/xls_prep/fixtures/` but is **not** on `main`, so T5/T6 silently degrade to the 120 k-cell mid tier (`lo_spike.py` fallback) | Repo change (adds a binary fixture) | **G4**: a fixture slow enough to exceed T6's 1.5 s timeout finally forces SIGTERM→SIGKILL against real `soffice`; G6 worst-case RSS |
| **G3** | **Pin the container to the Railway budget** — add `--memory=1000000000 --pids-limit=1000` to `spike_kit/spike/run_in_docker.sh` | Repo change (CI/kit only, not app source) | **G6**: Railway-faithful capped measurement — observe the real OOM boundary instead of unconstrained demand |
| **G4** | **Make T6's timeout tunable** (currently hardcoded 1.5 s; `stress_timeout` only feeds T5) | Repo change (kit) | **G4**: lets a dispatch force the kill path without a bigger fixture |
| **G5** | **B.7 runtime treatment of `0x0550`** — run `soffice --convert-to xlsx` on the `0x0550` fixture. The fixture and its controlled two-byte patch pair exist under `.tmp/xls_prep/biff5/` but are not on `main` | Repo change (fixture + probe) | **B.7**: decides whether the two-byte normalisation path in the prior report's B.8 is ever needed |
| **G6** | *(optional)* Port `g4_probe_posix.pl` / `g6_measure.py` onto `main` if the Supervisor prefers those specific instruments (they currently live only in the git-ignored `.tmp/xls_prep/`) over `lo_spike.py`'s equivalents — the latter already read `memory.max`/`cpu.max` and implement the same kill sequence | Repo change | G4/G6 instrument parity |

**Not blocked, and deliberately left alone:** no Railway staging environment is
proposed (none exists; creating one is disallowed), and production is untouched —
Task C compliance: only read-only `serviceInstanceLimits`/`deployments` queries were
executed, **no mutation**.

---

## H. Scope integrity

- **Implementation Gate: CLOSED.** No converter code, no `ALLOWED_EXTENSIONS`, no
  `ACCEPTED_BOF_VERSIONS`, no registry/contract change, no PR.
- All discovery was read-only: `gh workflow list/view`, `gh run list/view/download`
  (existing artifact), `gh api` `contents`/`commits`, `git` inspection, and Railway
  GraphQL **queries** only.
- Nothing was installed. No Docker, WSL, or LibreOffice on the Windows host; no
  Railway resource created or reconfigured; no workflow dispatched.
- New on-disk artefacts live under the git-ignored `.tmp/xls_prep/` (`.gitignore:87`
  matches `*.tmp`): `spike_artifact/` (retrieved evidence), `spike_kit_main/` (fetched
  `main` sources for analysis), and scratch helpers.
- Only new tracked file: this report.

**Bottom line:** the environment is no longer the blocker — it exists, it is
proven, and it has already produced real G6 numbers. What remains is a set of
small, clearly-scoped repo/CI changes (§G) plus one dispatch decision, all of which
sit squarely with the Supervisor.

**Explicitly NOT executed:** any workflow dispatch, any stress test, any Railway
mutation, any app/contract/registry edit, any PR.

