# XLS → XLSX REMEDIATION — GAP CLOSURE REPORT

**Status:** Implementation Gate **remains CLOSED**. No plugin, contract,
registry entry, `ALLOWED_EXTENSIONS` change, converter JSON, application
source change, PR, merge, Railway configuration change or deployment was
made for this work. Every probe lives under the git-ignored
`.tmp/xls_prep/`. The only tracked artefact this phase produces is this
report.

**Scope of this phase — three gaps only:**

| Gap | Question | Outcome of this phase |
|---|---|---|
| **A** | G4 POSIX containment: is the SIGTERM → grace → SIGKILL → reap kill path genuinely executable, with zero orphans and zero residue? | **Executed** — under the MSYS2/Cygwin 3.6.9 POSIX emulation layer, 9 consecutive clean runs, conditional escalation proven, zero residue. Linux-kernel confirmation is the one remaining input. |
| **B** | BIFF5 `0x0550`: is it genuine, what is it, and should it be supported? | **Resolved on the evidence available: not supportable now.** Expected rejection documented, plus the exact minimum change if a real `0x0550` file must later be accepted. |
| **C** | G6 production-resource evidence: how is peak RSS / PID cost measured against the real Railway budget? | **Design complete and its accounting layer proven** against a deterministic stub; the soffice-in-cgroup numbers are the missing input, stated exactly. |

**Evidence discipline (unchanged):** nothing is simulated and labelled as
measured. Where a runtime is unavailable, the artefact is marked
`DEFERRED / NOT EXECUTED` with the exact missing input. No acceptance rule
was tuned to make a test pass.

---

## A. G4 POSIX containment evidence

### A.1 Runtime discovery — what is actually available on this host

The supervisor's instruction was to use the Docker/Linux/CI environment
that *is* available. It was searched for exhaustively; the result is part
of the evidence, not an excuse:

| Runtime | Result |
|---|---|
| `soffice` / `libreoffice` | **ABSENT** (host and the POSIX layer below) |
| `docker`, `podman`, `nerdctl`, `containerd` | **ABSENT** |
| `act` (GitHub Actions local), `colima`, `lima`, `qemu` | **ABSENT** |
| WSL | `wsl.exe` exists but **WSL is not installed** ("The Windows Subsystem for Linux is not installed"); no distro, no `bash.exe` interop. Installing it needs elevation plus a host modification, which the no-install discipline rules out. |
| Remote box (`ssh`) | no `~/.ssh` configuration; no reachable Linux host |
| Railway CLI | `railway shell` / `railway run` operate on a *local* shell with Railway variables — they are **not** a remote container exec — and the live production deployment was not used as a test target (per instruction). |
| **Git for Windows `/usr/bin`** | **PRESENT**: a full MSYS2/Cygwin 3.6.9 POSIX-emulation environment (coreutils, `perl` 5.42.002, `ps`, `/proc`) |

So the POSIX kill path could not be executed against a Linux kernel. It
**was** executed against the Cygwin emulation layer — real syscalls
(`POSIX::setsid`, `kill(SIG, -pgid)`, `waitpid`), a real process tree, real
signals — which is materially stronger than a logic test, and it is
labelled for exactly what it is.

### A.2 The probe — `.tmp/xls_prep/g4/g4_probe_posix.pl`

The probe implements the G4 escalation sequence verbatim, and it *waits for
a heartbeat from a real, running tree before it kills anything*, so the
kill can never be vacuous:

1. the stub converter is forked into its **own session/process group**
   (`POSIX::setsid`), then forks three grandchildren, each leaving the
   residue a real LibreOffice run leaves (profile dir, `.lock`, scratch
   files);
2. **SIGTERM is sent to the whole process group first**
   (`kill('TERM', -$pgid)`), never to the leader alone;
3. a **grace period is polled** by group liveness (`kill(0, -$pgid)`);
4. **SIGKILL escalation fires only if the group survived the grace**;
5. the process the probe is parent of is **reaped with `waitpid`** and its
   exit status inspected;
6. accounting is **scoped**: only PIDs the probe created (recorded lineage,
   `/proc/<pid>/status` PPid relationship, and exact
   `perl g4_probe_posix.pl` argv match) and only files under a unique temp
   prefix. Host-global counts are never used as probe residue;
7. **cancellation synchronisation**: kill + cleanup are guarded so they run
   exactly once, including when the caller cancels mid-flight.

Scenarios: **A** — the deterministic stub *ignores* SIGTERM on purpose (the
supervisor-sanctioned stand-in for a hung converter, since no soffice
exists), so the SIGKILL path is genuinely taken; **B** — a control stub
that *honours* SIGTERM, proving the escalation is conditional rather than
always-kill; **C** — the caller cancels while the converter is running.

### A.3 Measured results (final of 9 consecutive clean runs)

Layer: `MSYS_NT-10.0-26200 … 3.6.9 … Msys` (Cygwin 3.6.9), Perl 5.42.002,
`/proc` available.

**Capability pre-check** (run before any scenario): the process group is
addressable (`group_addressable = 1`); SIGTERM was delivered to a
TERM-ignoring child and **survived** (`term_delivered_ignored = 1`) — i.e.
escalation is genuinely required on this layer.

| Check | A: ignores SIGTERM | B: honours SIGTERM (control) | C: cancelled mid-flight |
|---|---|---|---|
| Tree built / heartbeat received | yes (155.6 ms) | yes (168.5 ms) | yes (163.2 ms) |
| Grandchildren verified in leader's group | 1 | 1 | 1 |
| Parent's group ≠ stub's group (isolation) | 1 | 1 | 1 |
| SIGTERM sent (process group) | yes | yes | yes |
| Grace window | **812 ms, group still alive** | group exited in **61 ms** | 809 ms, still alive |
| **SIGKILL escalation fired** | **yes** | **no — not needed** | **yes** |
| Direct child reaped (`waitpid`) | yes | yes | yes |
| Child exit: killed by signal | **9 (SIGKILL)** | **0 (clean exit on TERM)** | 9 |
| Kill ran exactly once | 1 | 1 | 1 |
| Cleanup ran exactly once | 1 | 1 | 1 |
| Group empty after kill | 1 | 1 | 1 |
| Surviving probe-created PIDs | **0** | **0** | **0** |
| Probe processes still alive | **0** | **0** | **0** |
| Orphans left behind (PPid scan) | **0** | **0** | **0** |
| Stub-created residue files present | **0** | **0** | **0** |
| Probe roots present after cleanup | **0** | **0** | **0** |
| Parent survived / pgid unchanged | 1 / 1 | 1 / 1 | 1 / 1 |
| Cancelled while still running | — | — | 1 |
| Total scenario time | 1950.0 ms | 1243.0 ms | 1529.3 ms |

**Probe-wide post-conditions** after all three scenarios: unique-prefix temp
scan **residue = 0**; cmdline-scoped process scan **alive = 0**. Across
**9 consecutive runs** (3 before and 3 after a portability fix, plus 3 in a
final verification batch — transcript `_leftover_check_final.txt`) every run
exited 0, and the independent leftover check reported
`still_alive_count = 0` with no temp residue.

Scenario **B** is the control that matters most for correctness: because
the stub honoured SIGTERM, the group emptied inside the grace window and
**SIGKILL was never sent** — the escalation is a genuine conditional, not a
blunt always-kill.


### A.4 A real escape, found and fixed (evidence about the layer)

The *first* execution of an earlier revision left **three orphaned `perl`
processes alive with `PPid = 1`** (reparented to the layer's init), still
running minutes after the probe had exited. Root cause: that revision killed
only the process it held a handle to, and the layer — like Windows — does
not cascade a kill to descendants. The escape was detected by the scoped
`perl g4_probe_posix.pl` argv sweep and removed (`still_alive_count = 0`).

Two consequences were carried into the probe and into this report:

1. **Containment verification must be by process identity, not by recorded
   PID.** The recorded grandchild PIDs did not match the survivors; the
   argv- and PPid-based scoped scan did. The probe now verifies with both,
   and a scoped backstop sweep removes anything of the probe's that a group
   kill missed.
2. **This layer is not fully trustworthy for group containment.** The
   escape happened once and never again in six subsequent runs — the
   profile of an emulation-layer quirk, not a design flaw. The production
   kill path targets Linux precisely for this reason, so the Linux-native
   confirmation in A.5 is a genuine gate, not a formality.

### A.5 What remains for G4 (exact missing input)

| Item | Missing input |
|---|---|
| **Linux-native confirmation of the same path** | A Linux kernel runtime: a WSL distro, Docker/podman, or any Linux host. **None is available** (A.1). The probe is portable — it uses no Cygwin-specific API and already normalises the Perl `kill` return-value difference between Linux and this layer — so it can be re-run unchanged on Linux. |
| **Real slow-conversion scenario (G4 scenario B)** | A `soffice` binary on that Linux host. The stub used here is the supervisor-sanctioned stand-in and is labelled as such: it proves the *containment machinery*, never a real conversion. |

The POSIX escalation sequence itself — isolated session, SIGTERM-first,
grace, conditional SIGKILL, reap, scoped zero-residue, cancellation sync —
**has been executed**, and every one of the supervisor's bullets for it has
a measured number above.


---

## B. BIFF5 — closing the `0x0550` gap

Investigation artefact: `.tmp/xls_prep/biff5/investigate_0550.py` →
`investigation_0550.json` (summarised by `summarize_0550.py`). Every number
below is measured on this host.

### B.1 Is the `0x0550` fixture a genuinely valid BIFF/CFBF file?

**Yes, at the container and record-stream level** — measured, not asserted:

| Property | `sample_biff5.xls` | `sample_biff7.xls` | `sample_biff7_0550.xls` |
|---|---|---|---|
| Size | 5632 B | 5632 B | 5632 B |
| Container | OLE2, major version 3, 512-byte sectors | same | same |
| FAT chain / directory | parses cleanly | same | same |
| Workbook stream | `Workbook`, 4096 B | same | same |
| First record | BOF `0x0809`, stream type `0x0005` (workbook globals) | same | same |
| BOF version field | `0x0500` | `0x0500` | **`0x0550`** |
| build / year | 2412 / 1994 | 3515 (0x0DBB) / 1995 | 3515 / 1995 |

Independent corroboration that the container is sound: xlrd 2.0.2 parses the
OLE2 container of the `0x0550` file and locates the workbook stream
successfully — it fails *only* at the version field ("Can't determine file's
BIFF version"). Had the CFBF or stream been malformed, the failure would
have been structural, not versional.

**So the `0x0550` file is a structurally valid OLE2/BIFF workbook whose sole
anomaly is the BOF version-field value.**

### B.2 The correct stream: `Workbook` or `Book`?

**`Book` for BIFF5/BIFF7 (Excel 5.0 / Excel 95); `Workbook` for BIFF8
(Excel 97+).** The OLE2 container shipped with Excel 5.0, and Excel 5/95
name the workbook stream `Book`; `Workbook` is the Excel 97 convention.
Both readers accept either name — preflight (`for cand in ("Workbook",
"Book")`) and xlrd (`for qname in ['Workbook', 'Book']`,
`tools/xlrd/book.py:639`). Verified with a clean `Book`-named variant:
preflight **ACCEPT** (`stream = Book`, label BIFF7) and xlrd
`biff_version = 70`.

(The fixtures ship with the `Workbook` name for both BIFF5 and BIFF7. This
is a deliberate hybrid keeping one variable stable across the fixture family
— both readers accept it — and the real Excel 95 convention was tested
separately as above.)

### B.3 What BIFF version does `0x0550` represent?

`0x0550` is **not a value defined by the BOF record's version field** in any
parser examined. xlrd 2.0.2's own `getbof()` says so explicitly (vendored
source, `tools/xlrd/book.py`, quoted verbatim):

```python
version1 = opcode >> 8
version2, streamtype = unpack('<HH', data[0:4])
if version1 == 0x08:
    build, year = unpack('<HH', data[4:8])
    if version2 == 0x0600: version = 80
    elif version2 == 0x0500:
        if year < 1994 or build in (2412, 3218, 3321): version = 50
        else: version = 70
    else:
        # dodgy one, created by a 3rd-party tool
        version = {0x0000:21, 0x0007:21, 0x0200:21, 0x0300:30,
                   0x0400:40}.get(version2, 0)
```

`0x0550` is absent from that map → `version = 0` →
`XLRDError: Can't determine file's BIFF version`. Note xlrd's classification
of anything outside `{0x0500, 0x0600}` as *"dodgy one, created by a 3rd-party
tool"*, and note that the recognised values are exactly
`0x0007 / 0x0200 / 0x0300 / 0x0500 / 0x0600`.

**Working hypothesis (labelled a hypothesis, not a finding):** `0x0550` is
the Excel **application** version 5.50 (Excel 95) written into the field that
carries the BIFF **format** version, whose correct value is `0x0500`. It fits
the evidence: the fixture pairs `0x0550` with build 3515 / year 1995 — the
real Excel 95 signature — as if a writer had encoded "Excel 95 = Excel 5.5"
instead of the format version.

### B.4 How the current preflight treats it — and the divergence

`preflight_validator.py` declares
`ACCEPTED_BOF_VERSIONS = {0x0500, 0x0550, 0x0600}`, so `0x0550` is
**ACCEPTed** (label `BIFF7_THIRDPARTY_0x0550`). The engine's only available
XLS reader on this host, xlrd 2.0.2, **refuses it outright**. This is a real
policy-vs-parser divergence: a file the gate accepts cannot be read by the
reader the gate exists to protect — which is precisely why `0x0550` was kept
as a fixture rather than silently dropped.


### B.5 The controlled pair: the version field is the *sole* blocker

A byte-diff of the three fixtures shows the `0x0550` variant differs from the
`0x0500` (readable) variant at **exactly two byte offsets — 516 and 582** —
both of which are the low byte of the BOF record's version field (globals
BOF and sheet BOF respectively), `0x50` vs `0x00`. A byte-controlled test was
then run: patching **only** those two bytes from `0x0550` back to `0x0500`
produced a file that

- is still a structurally valid OLE2/CFBF container (same major version,
  same sector size, same stream layout), and
- is read by **xlrd 2.0.2 as BIFF7** (`biff_version = 70`, sheet count 1,
  3851 cells, 1 formula), while preflight continues to ACCEPT it (label
  BIFF7).

Conversely the pristine `0x0550` file is ACCEPTed by preflight but rejected
by xlrd. **The version field, and nothing else, is the divergence.**

### B.6 BIFF5 ≠ BIFF2–4: the structural separation is real

A raw BIFF2 record stream (687 B; BOF record `0x0009`, version `0x0007` —
*not* an OLE2 container) is correctly classified by the preflight as
`NOT_OLE2_CONTAINER` and refused, while xlrd decodes it as BIFF2 (`v21`).
So the CFBF/BIFF5 path and the raw-record BIFF2–4 path are genuinely distinct
classes, and support for one does not imply support for the other. The G6
XL fixture used throughout the earlier remediation remains
`.tmp/xls_prep/fixtures/stress_biff8_bulk1m.xls`.

### B.7 Third-party corroboration (partial — limitations disclosed)

- **LibreOffice** folds Excel 95 into BIFF5: `sc/source/filter/inc/flttypes.hxx`
  defines `enum BiffTyp { Biff2, Biff3, Biff4, Biff5, Biff8 }` — there is **no
  `Biff7` enumerator**. Excel 95 BIFF files are read as Biff5.
- **Apache POI** (`org/apache/poi/hssf/record/BOFRecord.java`) does not
  validate the version field at all: it stores whatever it finds and defaults
  the version to `0x0600` when absent. POI is therefore *lenient* about
  `0x0550` by construction, which is corroboration that the value is
  out-of-spec rather than that xlrd is over-strict.
- **Not obtained (disclosed):** grep.app was rate-limited; the LibreOffice
  git mirror and Bing search were bot-blocked; the Gnumeric parser source was
  too large to fetch; `[MS-XLS]` could not be loaded from this host. **The
  parser-side evidence therefore rests on the local xlrd 2.0.2 source**, with
  the LibreOffice/POI statements above taken from their public source
  listings. LibreOffice's *runtime* treatment of an actual `0x0550` file was
  not determined — no `soffice` on this host (see D).

### B.8 Resolution

**Recommendation: treat `0x0550` as unsupported — do not accept it.**

1. The file is *valid*, so a rejection on container grounds would be wrong.
   The correct refusal reason is a version one: `UNSUPPORTED_BIFF_VERSION`,
   the existing preflight classification for a BIFF variant the engine
   cannot read.
2. The engine's reader on this host **cannot** read it (B.3), so accepting it
   would convert a preflight refusal into a mid-conversion failure — strictly
   worse than refusing up front.
3. No out-of-the-box parser examined recognises `0x0550`; xlrd calls it a
   third-party artifact.
4. **Minimum preflight change, if a real `0x0550` file must later be
   accepted:** remove `0x0550` from `ACCEPTED_BOF_VERSIONS`. If and only if a
   real Excel 95 file carrying `0x0550` is observed *and* a LibreOffice
   runtime is proven to convert it, the minimal supporting change is a
   two-byte normalisation `0x0550` → `0x0500` in the workbook stream before
   the reader sees it — proven sufficient by the controlled pair in B.5.
   That mutates the caller's input, so it needs an explicit supervisor policy
   decision (normalise-and-convert vs. refuse) plus the LibreOffice proof;
   it is **not** implemented here.


---

## C. G6 — production resource evidence

### C.1 Authoritative limits, re-verified fresh (read-only)

The Railway GraphQL schema was corrected this phase:
`serviceInstanceLimits` and `serviceInstanceLimitOverride` are **root
`Query`** fields taking `(environmentId, serviceId)` and returning a JSON
scalar — `Service.serviceInstanceLimits` **does not exist**. A read-only
query (`q_limits2.graphql` → `railway_query.py`) returned:

| Field | Value |
|---|---|
| CPU | **2 vCPU** |
| Memory | **1,000,000,000 B** (≈ 953.7 MiB) |
| PID limit | **1000** |
| Instance limit override | `null` (no override applied) |
| Latest deployment status | **SUCCESS**, `2026-09-16T12:22:06Z` (deployment `64f57561-b148-47cc-a4cb-950aeffed13c`; service instance `5fc6c48d-60ea-43bf-b8d8-76fc4eac4376`) |

Query scope: read-only (`IntrospectionQuery` + limits only). **No mutation
was executed; no Railway configuration was written.** The earlier `railway
up` trial had already expired before this phase, so no deploy path was
available anyway.

### C.2 The measurement design — `g6_measure.py`

The design targets **cgroup v2 on Linux** because that is the only mechanism
that yields a *true peak* without sampling races:

1. **Pin the conversion into a dedicated cgroup** whose `memory.max` and
   `pids.max` are set to the Railway values above (1,000,000,000 B and 1000),
   so any breach fails the measurement rather than the production container.
2. **Read `memory.peak`** (kernel-maintained high-water mark) at the end of
   the conversion — no sampling, so a transient spike cannot be missed.
3. **Account the whole descendant tree**, not just the top-level `soffice`
   process: walk `/proc/<pid>/task/*/children` (and PPid links) to include
   every `oosplash`/`soffice.bin`/helper process, summing RSS per tree.
4. **Sweep concurrency** (1 → N) and record the per-conversion cost as the
   *aggregate* peak divided by N, plus the count of PIDs per conversion.
5. **Baseline**: conversions are capped at the largest fixture,
   `.tmp/xls_prep/fixtures/stress_biff8_bulk1m.xls` (**21,836,800 B** — the
   largest XLS in the work area; the engine's real upload cap is enforced
   elsewhere), so the measurement reflects the largest input available.
6. **Guard derivation**: with a 20 % safety margin and a fixed container
   baseline, the maximum concurrency is
   `min(⌊(0.8·RAM − baseline_RAM) / per_conv_peak⌋, ⌊(1000 − baseline_PIDs) / per_conv_PIDs⌋)`.

### C.3 The accounting layer is proven — against a deterministic stub

The accounting layer above is portable, so it was exercised on this Windows
host via its native analogue (`g6_measure.py`, `mem_stub.py`). The stub
allocates a known amount of RAM, spawns a known number of children, and
**ignores SIGTERM** — the same supervisor-sanctioned stand-in used for G4.
A stub is the right instrument here: its output is deterministic, so it
isolates *whether the accounting is correct*, which is the only question
this host can answer.

| Concurrency | Processes spawned | Tree peak RSS (B) | Measured / requested | Leftover PIDs after cleanup |
|---|---|---|---|---|
| 1 | 4 | 97,030,144 | **4/4** | **0** |
| 2 | 8 | 193,789,952 | **8/8** | **0** |
| 4 | 16 | 387,153,920 | **16/16** | **0** |

Aggregate RSS scales linearly with concurrency (97 → 194 → 387 MB), exactly
as a fixed-cost stub predicts, and per-conversion attribution is stable
(≈ 97 MB, 4 PIDs per conversion). Every process the measurement claims to
account for was confirmed measured (16/16 at N=4) and confirmed gone after
cleanup — an independent leftover sweep reported **0** alive.

Worth recording: the four processes per conversion include the virtualenv's
`python.exe` **launcher shim**, a real descendant that consumes memory and a
PID and that naive single-process accounting would miss entirely. On Linux
the equivalent members are `oosplash`/`soffice.bin` and their helpers; the
lesson transfers directly.

### C.4 The guard is deliberately NOT derived

`g6_measurement.json` records:

```json
"guard": { "status": "NOT_DERIVABLE",
  "per_conversion_peak_rss_bytes": 97030144,
  "per_conversion_pids": 4,
  "ram_budget_bytes": 1000000000, "pid_budget": 1000, "cpu_budget_vcpu": 2,
  "recommended_max_concurrent": 8,
  "reason": "peaks above come from a deterministic memory stub, not from
             real soffice conversions; they prove the accounting layer
             only, never the guard" }
```

The `recommended_max_concurrent` figure is **stub-derived and must not be
read as a production concurrency limit**; it is retained only to demonstrate
that the derivation formula is wired end to end. No guard value is asserted
in this report, and none was applied anywhere in the codebase.


### C.5 What remains for G6 (exact missing input)

| Item | Missing input |
|---|---|
| **Real per-conversion peak RSS and PID cost** | A Linux host with **cgroup v2** and a `soffice` binary — most naturally a throwaway Docker container stood up for the purpose. **None exists yet** (no Docker on this host, and creating one is an implementation action, so it was not done); `g6_measure.py` already carries the cgroup-v2 path and records `runnable: false` here with the reason below. |
| **Production-scale input beyond the largest fixture** | Optional: a production-shaped XLS at or above `.tmp/xls_prep/fixtures/stress_biff8_bulk1m.xls` (21,836,800 B). |

Recorded by the tool on this host:

```json
"cgroup_measurement": { "runnable": false,
  "reason": "requires Linux with cgroup v2 and soffice; this is Windows",
  "missing_input": ["linux host with cgroup v2", "soffice binary"] }
```

Note that C.1's limits and C.3's accounting proof are **host-independent**:
the Railway budget is authoritative regardless of where it is measured, and
the accounting layer is already proven. Only the real-conversion numbers are
outstanding.

---

## D. Remaining blockers

All outstanding items collapse to **one missing runtime**: a Linux host with
cgroup v2 and LibreOffice.

| # | Blocker | Blocks | Exact missing input | Workaround used |
|---|---|---|---|---|
| D1 | No `soffice`/LibreOffice on any available host | G4 real slow-conversion scenario; G6 real peak-RSS/PID numbers; B7 LibreOffice runtime treatment of `0x0550` | `soffice` binary on Linux | Deterministic stubs (labelled as such) |
| D2 | No Linux kernel runtime (WSL not installed; Docker/podman/act/colima/qemu absent) | G4 Linux-native confirmation of the kill path; G6 cgroup-v2 measurement | WSL distro **or** Docker **or** the spike container | Cygwin 3.6.9 emulation layer (G4); native Windows analogue (G6 accounting) |
| D3 | `[MS-XLS]` / LibreOffice `read.cxx` not fetchable from this host | B7 spec-level corroboration of `0x0550` | Fetchable copy of `[MS-XLS]` §2.4.21 (BOF) and LO's `sc/source/filter/lotus/lotus.cxx`/Excel import | Local xlrd 2.0.2 source + LO `flttypes.hxx` enum + POI `BOFRecord` |

Nothing in D is a code defect. Each item is an unexecuted measurement, and
each has a ready, unexecuted instrument on disk waiting for the runtime.

---

## E. Recommendation for the next supervisor gate

**1. Do not open the implementation gate yet.** Every acceptance-relevant
question this phase could answer has an answer; the three that remain all
need the same Linux+LibreOffice runtime and are genuinely un-executable
here. Opening the gate now would mean implementing on unmeasured
assumptions — the exact failure mode the gate exists to prevent.

**2. The single highest-value next action is one runtime, not more probes:**
provide a Linux host with cgroup v2 and LibreOffice (a throwaway Docker
container is the natural route — none exists, and standing one up is an
implementation action that was deliberately not taken). That one action
closes D1 and D2 simultaneously and unlocks three ready-made measurements:

- `perl g4_probe_posix.pl` re-run unchanged on the Linux kernel (G4
  Linux-native confirmation, real slow-conversion scenario);
- `python g6_measure.py` re-run unchanged (real cgroup-v2 peak RSS/PID, and
  the first *derivable* concurrency guard);
- a direct `soffice --convert-to xlsx` on the `0x0550` fixture (B7 runtime
  treatment, which decides whether the normalisation path in B.8 is ever
  needed).

**3. Carry the B.8 decision forward as-is:** `0x0550` is not supportable
today; the expected refusal reason is `UNSUPPORTED_BIFF_VERSION`, and the
two-byte normalisation is documented as the minimum change *if* a real file
appears *and* LibreOffice is proven to convert it. No `ALLOWED_EXTENSIONS`
or `ACCEPTED_BOF_VERSIONS` change is made.

**4. Preserve the accounting-layer lesson:** measure the **whole descendant
tree** and read the **kernel-maintained peak**, never a single process or a
sampled RSS. The stub proof in C.3 shows why — a real descendant (the venv
launcher here; `oosplash`/`soffice.bin` on Linux) is invisible to
single-process accounting.

**5. Gate condition for implementation, restated:** all of A.3 executed
Linux-natively, a G6 guard derived from *real* soffice peaks, and the `0x0550`
refusal class present in the preflight — with `ALLOWED_EXTENSIONS` unchanged
until then.


---

## F. Artefact index and scope integrity

All probes are git-ignored (`.gitignore:87` → `*.tmp` covers `.tmp/`). The
**only** tracked artefact this phase adds is this report.

### F.1 Gap A — POSIX containment

| Artefact | Purpose |
|---|---|
| `.tmp/xls_prep/g4/g4_probe_posix.pl` | The probe (three scenarios, scoped accounting, cancellation sync) |
| `.tmp/xls_prep/g4/stub_hang.py` | The deterministic stub (ignores SIGTERM; leaves profile/lock/scratch residue) |
| `.tmp/xls_prep/g4/_cleanup.sh` | Scoped residue + survivor sweep (argv-matched to the probe only) |
| `.tmp/xls_prep/g4/_run_all.sh` | Batch runner (3 runs per invocation) |
| `.tmp/xls_prep/g4/_leftover_check_final.txt` | Transcript: 3 runs, all exit 0, `still_alive_count=0`, no temp residue |
| `.tmp/xls_prep/g4/g4_results_posix.json` | Probe output (capabilities + all three scenarios) |
| `.tmp/xls_prep/g4/summarize_posix.py` | Findings summary |

### F.2 Gap B — BIFF5 `0x0550`

| Artefact | Purpose |
|---|---|
| `.tmp/xls_prep/biff5/investigate_0550.py` → `investigation_0550.json` | Container validity, stream layout, BOF parsing, controlled pair, `Book` vs `Workbook`, BIFF2 separation |
| `.tmp/xls_prep/biff5/summarize_0550.py` | Findings summary |
| `.tmp/xls_prep/preflight/preflight_validator.py` | Preflight acceptance logic under review (`ACCEPTED_BOF_VERSIONS`) |

### F.3 Gap C — G6 resources

| Artefact | Purpose |
|---|---|
| `.tmp/xls_prep/g6/g6_measure.py` | cgroup-v2 design + portable accounting layer + guard derivation |
| `.tmp/xls_prep/g6/mem_stub.py` | Deterministic stub (known RAM, known children, ignores SIGTERM) |
| `.tmp/xls_prep/g6/g6_measurement.json` | Measurement output incl. `guard` (NOT_DERIVABLE) and `cgroup_measurement.runnable = false` |
| `.tmp/xls_prep/g6/railway_query.py`, `q_limits2.graphql` | Read-only limits query (correct root-`Query` schema) |
| `.tmp/xls_prep/g6/summarize.py` | Findings summary |

### F.4 Scope integrity statement

- **No implementation.** No plugin, contract, registry entry, converter JSON,
  `ALLOWED_EXTENSIONS` entry, or application source was added or modified for
  this work.
- **No `ACCEPTED_BOF_VERSIONS` change.** The set remains `{0x0500, 0x0550,
  0x0600}` in the reviewed preflight; B.8 recommends removing `0x0550` as the
  *next* action, and it is not applied here.
- **No Railway writes.** Only read-only GraphQL queries (introspection +
  limits); no mutation, no deployment, no config change. The `railway up`
  trial had already expired before this phase.
- **No PR, no merge, no deployment.** The implementation gate stays CLOSED.
- **No test was tuned to pass, and no measurement was simulated.** Every
  number in this report was produced by the artefact cited next to it on this
  host; every un-executed item is labelled with the exact missing input.

