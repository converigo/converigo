# XLS → XLSX Implementation Plan (Bounded, Evidence-Anchored)

**Status:** DRAFT — awaiting Supervisor review. **No code is changed by this document.**
**Gate:** Implementation Gate = OPEN (CONDITIONAL) per Supervisor decision.
**Scope:** `xls → xlsx` ONLY. Everything else is explicitly out of scope (§11).

**Evidence base (authoritative, do not paraphrase from memory):**
CI run `35178439497`, branch `fix/pr1-ole2-honest-disable` @ `0065a04`, artifacts
`evidence_{env,g4,single,conc_{1,2,4,8},biff5}.json`, summarized in
`XLS_XLSX_FINAL_REMEDIATION_EVIDENCE_REPORT.md` (§C–§I). Every number quoted below
is from that run.

---

## §0. Measured baseline (verified live in this session, not assumed)

The current behaviour of the four relevant pairs was exercised end-to-end against a
genuine OLE2/BIFF5 file (`spike_kit/evidence_fixtures/sample_biff5.xls`) posted to
`POST /convert` on this branch. This is the **regression oracle** the implementation
must not disturb:

| Upload | Target | Today | Response body (truncated) |
|---|---|---|---|
| `.doc` | `pdf` | **HTTP 500** | `RuntimeError: Legacy .doc format (OLE2 compound document) is not supported…` |
| `.ppt` | `pdf` | **HTTP 500** | `PackageNotFoundError: Package not found at 'uploads\…\.ppt'` |
| `.ppt` | `xlsx` | **HTTP 500** | `Legacy .ppt format (OLE2 compound document) is not supported…` |
| `.xls` | `pdf` | **HTTP 500** | `InvalidFileException: openpyxl does not support the old .xls file format…` |
| `.xls` | `xlsx` | **HTTP 422** | `{"code":"UNSUPPORTED_CONVERSION","message":"Converter xls -> xlsx tidak tersedia."}` |

Derived facts (all verified, not inferred):

1. **`('xls','xlsx')` is NOT registered** in `PluginRegistry.plugins` — the pair is the
   *only* unregistered Office pair, and its absence is the single reason `xls→xlsx`
   422s today.
2. **`.xls` upload is already enabled at the gate.** `xls` ∈ `ALLOWED_EXTENSIONS`
   (`app/utils/file_validator.py`), has an OLE2 magic signature entry and an expected
   MIME (`application/vnd.ms-excel`). **The firewall item "do not enable xls upload
   yet" is therefore already satisfied; `ALLOWED_EXTENSIONS` needs NO change.**
   Enablement = registering the *conversion pair*, not opening the upload gate.
3. **`ACCEPTED_BOF_VERSIONS` does not exist yet** (verified by `git grep` across the
   whole repo). It is a NEW constant introduced by this plan.
4. **`soffice` is already in the production image.** The Dockerfile installs
   `libreoffice`; `railway.json`/`railway.toml` set `builder = "dockerfile"`, so
   Railway builds the Dockerfile path. **No `requirements.txt` change, no runtime
   `xlrd`, no Railway service change is required.** (`nixpacks.toml` does not list
   libreoffice but is **inert** for this Railway service; a consistency edit is
   optional and listed in §7 as hygiene only.)
5. **Honest-disable is per-plugin and content-based**, not a central allow-list:
   `_guard_ooxml_container()` (`document_factory.py`) and `_detect_container()`
   (`word_to_pdf.py`) sniff `PK`/`D0CF11E0` magic and reject legacy OLE2 inputs.
6. **The frontend advertises `xls:['DOC','DOCX','PDF','POWERPOINT','PPT','PPTX','WORD']`
   with no `XLSX`** in `STATIC_TARGET_MAP` (`tool_result_widget_v2.js` and
   `app/templates/main/converigo_main.html`).

> **⚠ Discrepancy to resolve before implementation.** The Supervisor's brief states
> "DOC remains 415 / PPT remains 415". The live code returns **HTTP 500** for those
> pairs today (leaked library text in `detail`), not 415 and not 422. This plan
> therefore defines "unchanged" as **byte-identical to the measured §0 baseline** and
> proves it by regression test (§6, §8). If the Supervisor's intent is that DOC/PPT
> should return an honest 415/422, that is a **separate PR-1 follow-up**, explicitly
> out of scope here (§11) — because fixing it would itself change DOC/PPT behaviour.

---

## §1. Architecture

### 1.1 Pair-scoped enablement, minimal blast radius

The registry keys plugins by `(source, target)` (`app/plugins/registry.py`).
A plugin declaring exactly `source_formats=["xls"]`, `target_formats=["xlsx"]`
registers **one** key, `('xls','xlsx')`, plus `by_slug["xls-to-xlsx"]`. No other key,
plugin, converter JSON, contract or engine method is altered. DOC/PPT code paths are
provably untouched (§6).

```
app/plugins/document/xls_to_xlsx.py     NEW   XLSToXLSXPlugin  (pair-scoped, slug "xls-to-xlsx")
app/utils/ole2_preflight.py             NEW   magic + BOF preflight  (ACCEPTED_BOF_VERSIONS)
app/utils/soffice_runner.py             NEW   containment + profile isolation + kill ladder
app/core/settings.py                    MOD   6 env-backed knobs (§3)
app/services/conversion_service.py      MOD   1 line: add "xls" to the document timeout family
app/static/js/widgets/tool_result_widget_v2.js   MOD   STATIC_TARGET_MAP xls row += 'XLSX'
app/templates/main/converigo_main.html           MOD   same map (second copy)
tests/…                                 NEW   certified suite + tracked fixtures (§8)
```

`XLSToXLSXPlugin` follows the `excel_to_pdf.py` precedent (a thin `ConverterPlugin`
that delegates to a helper), **not** the pandas `SpreadsheetConverterPlugin` base —
pandas/openpyxl cannot read BIFF, and the firewall forbids runtime `xlrd`. All parsing
is done by `soffice`; Python only orchestrates and validates.

### 1.2 Exact invocation (the evidence-proven command line)

`soffice_runner.py` reproduces the exact `argv`/`env` that G4/G6/BIFF5 evidence
verified (`spike_kit/evidence/lo_evidence.py::convert()`), because that is the only
invocation whose containment and resource numbers we actually hold:

```
soffice \
  -env:UserInstallation=file://<per-request profile dir> \
  --headless --invisible --norestore --nologo --nofirststartwizard \
  --convert-to xlsx --outdir <out dir> <source copy>
```

- **argv is fixed and passed as a list** (no `shell=True`); target is the literal
  string `xlsx`. No user-controlled substring reaches the command line.
- **`HOME`, `TMPDIR`** are set to the per-request scratch dir; **`LANG=C.UTF-8`**.
- The source is **copied** into the scratch dir first; the original uploaded file is
  never passed to `soffice` (so output lands in a directory we control and the upload
  dir is never an outdir).

### 1.3 Per-request profile isolation

Every request gets, **under `temp_dir`** (which `ConversionService` already creates at
`settings.TEMP_DIR/<conversion_id>` and already cleans up on every exit path):

```
<temp_dir>/profile/     unique -env:UserInstallation target  (NEVER ~/.config, NEVER shared)
<temp_dir>/scratch/     HOME + TMPDIR + the copied source + stdout.log/stderr.log
<temp_dir>/out/         --outdir; the produced .xlsx appears here
```

Rationale (evidence §I.3): profiles must never be shared between concurrent
instances. Placing the profile **under `temp_dir`** is what made the residue audit
report `profile_dirs_left: 0` — the service's existing `_cleanup_temp_artifacts()`
reaps it. A profile written to `~/.config` would survive cleanup and is forbidden.


### 1.4 Process-tree containment

POSIX path (production is Linux, cgroup v2, per `evidence_env.json`):

- `start_new_session=True` → the child becomes a process-group leader.
- Timeout/cancel → `os.killpg(pgid, SIGTERM)` → bounded grace
  (`XLS_GRACE_SECONDS`, default 5, evidence-proven) → `os.killpg(pgid, SIGKILL)`
  if still alive → `proc.wait()` with a hard reap deadline → assert tree empty.
- This is the ladder G4 proved: SIGTERM alone terminated all three real tiers
  (`tree_reaped=True`, `orphans=0`); SIGKILL was only needed by the deliberately
  stubborn control child. The escalation path is therefore **known-live**, not
  theoretical.
- **The kill ladder runs in a `finally`**, so it also fires when the *outer*
  `ConversionService` timeout cancels this coroutine. A service-level `wait_for`
  cancellation must not orphan a `soffice` tree — this is the whole reason the
  runner owns its own reaping.
- Non-POSIX (Windows dev host): `start_new_session` is unavailable; fall back to
  `proc.terminate()`/`kill()` on the root only. Containment tests are POSIX-only
  (marked like the evidence probe's `IS_POSIX` guards); production is unaffected.

### 1.5 Timeout / cancellation behaviour

| Layer | Value | Source |
|---|---|---|
| Plugin hard ceiling | `XLS_CONVERSION_TIMEOUT_SECONDS` (default **120**) | new setting; bulk 21.8 MB measured 3.574 s, so 120 s is ~33× headroom |
| Kill grace | `XLS_GRACE_SECONDS` (default **5**) | evidence G4 |
| Service-level | `DOCUMENT_CONVERSION_TIMEOUT_SECONDS` (existing) | `conversion_service._get_timeout_seconds` gains `"xls"` (1 line) |
| Queue wait | `XLS_QUEUE_TIMEOUT_SECONDS` (default **120**) | §3 |

`asyncio.wait_for(runner(), XLS_CONVERSION_TIMEOUT_SECONDS)`; on `TimeoutError` **or**
`CancelledError` the `finally` performs §1.4 and then raises an honest
`ConversionError("Conversion timed out…")` (→ 500, §4).

### 1.6 Output validation

`soffice_runner.validate_output()` (mirrors `valid_ooxml()` from the evidence probe):

1. Exactly **one** `.xlsx` in the out dir (deterministic single-servable-file policy,
   same as `FactoryConversionPlugin`); else honest 422.
2. Magic `PK\x03\x04`; `zipfile.ZipFile.testzip() is None`; `xl/workbook.xml` present.
3. Sheet names parsed from `workbook.xml`; **≥ 1 sheet**, else honest 422 (rejects
   empty workbooks — never ship a content-less file).
4. **Reopen** the result read-only with `openpyxl` to prove it is a real readable
   workbook, not a syntactically-valid-but-unreadable zip.
5. Output extension/MIME is `xlsx` / `application/vnd.openxmlformats-officedocument
   .spreadsheetml.sheet`; the existing `/download` route serves it as an attachment
   (harness already asserts `attachment` in `content-disposition`).

### 1.7 Round-trip validation — and its honest limit

**Claimed:** the shipped file is a genuine, reopenable OOXML workbook produced by
LibreOffice from the user's bytes, with the source's sheets preserved.

**NOT claimed:** cell-level or byte-level fidelity parity.

Reason, stated plainly: proving cell parity requires a BIFF reader in the runtime
(`xlrd`), which the firewall forbids and which evidence §I.5 says is unnecessary for
the acceptance decision anyway. So round-trip validation is: structural validity
(§1.6) + reopenability + sheet presence, and the **tracked fixtures carry pinned
expected sheet names** (§8) so fidelity is asserted where we can know it. This
limitation must also be disclosed on the tool page FAQ (the F7 precedent discloses its
own text-only render limit the same way).


---

## §2. Legacy OLE2 Policy

- **`xls → xlsx` is the ONLY newly allowed OLE2 path.** Enablement is the single
  registry key `('xls','xlsx')` plus one plugin. No other OLE2-consuming pair is
  registered, advertised or modified.
- **`.doc` / `.ppt` remain disabled exactly as today** (§0 baseline: HTTP 500 with the
  existing OLE2/`PackageNotFoundError` messages). Their plugins, guards and
  advertisement maps are untouched.
- **No broad OLE2 exception.** The preflight gate (§4) is a *pair-scoped* check inside
  `XLSToXLSXPlugin` only. It is not added to `file_validator.py`, not to the registry,
  not to any shared base class — so it cannot leak into DOC/PPT behaviour.
- **Unsupported BOF `0x0550` remains rejected**, as an explicit policy decision:
  `ACCEPTED_BOF_VERSIONS = {"0x0500", "0x0600"}`.
  - `0x0500` — genuine BIFF5 **and** BIFF7 (evidence §F: both report `0x0500`).
  - `0x0600` — BIFF8, the production-representative tier: the G6 `sample`/`stress`/
    `bulk` fixtures are all BIFF8 and all returned `exit=0`, `valid=True`.
  - `0x0550` — third-party variant; **rejected by policy even though LibreOffice
    converts it successfully** (evidence §F: `biff7_0550` → `exit=0`, `valid=True`).
    This is deliberate provenance hygiene and directly implements evidence §I.5:
    *"Base acceptance on the BOF version field, not conversion success."*
- Acceptance order is: **OLE2 magic → Workbook/Book stream present → BOF version ∈
  accepted set**. A file failing any step is rejected preflight, **before** any process
  is spawned (so a rejected file costs zero PIDs and zero memory).

---

## §3. Resource Guard

**Initial active-conversion limit = 1** (`XLS_MAX_ACTIVE_CONVERSIONS`, default `1`,
env-overridable).

**This is a conservative implementation policy choice, not a safety proof.** The
evidence does **not** prove N=2+ is unsafe — on the contrary, N=4 ran 4/4 at 61 % of
the memory cap and N=8 ran 8/8 at 97 % with `oom_kill=0`. The binding constraint is
memory, and the measured per-conversion cost of a *bulk-class* file is 404 MiB (42 % of
the 954 MiB cap), which is why capacity must be memory-gated rather than open-loop.
The limit of 1 exists so that the first shipped version cannot, under any upload mix,
approach the cap. Raising it later is a data-led decision, not a code fix.

**Behaviour when a second XLS conversion arrives while the slot is occupied:**

```
                         ┌─ active slot free? ──► run immediately
   request arrives ──────┤
                         └─ no ──► waiters < XLS_MAX_WAITERS (default 4)?
                                     ├─ yes ──► await semaphore, ≤ XLS_QUEUE_TIMEOUT_SECONDS (120 s)
                                     │           ├─ acquired ──► run
                                     │           └─ timed out ──► HTTP 503 SERVER_BUSY (honest, no process spawned)
                                     └─ no ──► HTTP 503 SERVER_BUSY immediately
```

**Why this cannot accumulate processes or PIDs:** a *waiting* request has spawned
**nothing** — it is an `asyncio` coroutine awaiting a semaphore. Processes exist only
for the single active conversion, which evidence bounds at ~2 `soffice` processes and
~12 PIDs (N=1 row: `procs_peak=2`, `pids_peak=12` of the 1000-PID cap). There is no
unbounded queue, no worker pre-spawn, no process pool. The queue is a bounded set of
in-memory waiters; the ceiling is `1 active × ≤4 waiting = 5 requests` total in flight.

The semaphore is created lazily on first use (binds to the running event loop) and is
module-scoped = **per service instance**, matching the Railway start command
(a single `uvicorn` process per `railway.json`). If horizontal scaling is ever
introduced, this guard becomes per-instance and must be revisited — recorded in §10.

Retry-on-abort (evidence §I.2): exit `134` / `SIGABRT` /
`com::sun::star::lang::WrappedTargetRuntimeException` is treated as **retryable** with a
bounded retry count (`XLS_MAX_RETRIES`, default `2`), each attempt using a **fresh
profile/scratch tree**. This mirrors the engine's existing transient-failure policy and
the single observed N=2 failure (which did not recur at N=4/N=8).


---

## §4. Error Contract

All mappings reuse the existing exception→HTTP plumbing
(`UnsupportedConversionError` → 422 via `unsupported_conversion_exception_handler`;
`ConversionError` → 500). One new exception, `ConversionBusyError` (a `ConversionError`
subclass), carries the 503 path. **Client-facing messages never contain temp paths,
profile paths, PID numbers, or raw `soffice` stderr** — those are logged server-side
only (the evidence stderr contains `failed to launch javaldx`, which must not leak).

| Input / situation | HTTP | code | Message (user-facing, verbatim-owned) | Where decided |
|---|---|---|---|---|
| **Valid XLS** (OLE2 + Workbook/Book + BOF ∈ accepted) | **201** | — | success + `download_path` | §1 |
| **Corrupt / truncated XLS** (magic + BOF pass, `soffice` yields no/invalid/empty output) | **422** | `UNSUPPORTED_CONVERSION` | "The file could not be converted. It may be corrupt, truncated, or use an Excel feature this converter cannot read. Please try a different file." | §1.6 |
| **Garbage OLE2** (OLE2 magic present but no Workbook/Book stream, or BOF field absent) | **422** | `UNSUPPORTED_CONVERSION` | "The file is not a valid Excel workbook (no Workbook stream / unrecognized format)." | §2 preflight |
| **OOXML masquerade** (`PK` magic wearing a `.xls` name — `masquerade_xlsx_named_xls.xls`) | **422** | `UNSUPPORTED_CONVERSION` | "This file is actually an Office Open XML (.xlsx) file, not a legacy .xls file. Please upload it with its correct .xlsx extension." | §2 preflight (magic ≠ OLE2) |
| **Unsupported BIFF** (BOF `0x0550`, or BIFF2/other not in accepted set) | **422** | `UNSUPPORTED_CONVERSION` | "This legacy Excel format is not supported. Please save the file as a modern .xlsx workbook and try again." | §2 preflight |
| **Non-OLE2 junk / random / text named `.xls`** | **422** | `UNSUPPORTED_CONVERSION` | "The uploaded file is not a legacy Excel (.xls) workbook." | §2 preflight |
| **Timeout** (hard ceiling exceeded) | **500** | `CONVERSION_FAILED` | "Conversion timed out. Please try again with a smaller file." | §1.5 (process tree reaped first) |
| **LibreOffice crash** (`SIGABRT`/`WrappedTarget*` exit 134) | retry × `XLS_MAX_RETRIES`; then **500** | `CONVERSION_FAILED` | "The conversion service was temporarily unavailable. Please try again." | §3 retry-on-abort |
| **LibreOffice non-zero exit, other** | **500** | `CONVERSION_FAILED` | same generic message | §1.4 |
| **Invalid output** (produced file fails §1.6) | **422** | `UNSUPPORTED_CONVERSION` | "Conversion did not produce a valid Excel workbook." | §1.6 |
| **Cancellation** (client disconnect / outer timeout cancels coroutine) | **500** | `CONVERSION_FAILED` | process tree is reaped in `finally`, then honest error | §1.4 |
| **Slot occupied & queue full / queue timeout** | **503** | `SERVER_BUSY` | "The service is currently converting another file. Please retry in a moment." | §3 |

**Honesty guarantees:** no path fabricates output; no path returns a fake `.txt`; a 201
is only ever returned when a validated, reopenable `.xlsx` exists under
`OUTPUT_DIR/<conversion_id>/`.

---

## §5. Security

| Concern | Control |
|---|---|
| **Filename / path safety** | The plugin receives `UploadService`'s stored path, which is `<uuid4 hex>.xls` — no user-controlled segments. `validate_filename()` already rejects `..`, `/`, `\`, empty and over-long names. Defense in depth: the runner asserts the source stem contains no path separators before composing output names. Output is written only into the per-request out dir. `ConversionService._publish_output` already enforces output-path root containment. |
| **Temp profile isolation** | Per-request profile under `temp_dir`; `-env:UserInstallation` unique per request; `HOME`/`TMPDIR` redirected. Never `~/.config`, never shared (§1.3). |
| **Cleanup on every exit path** | Success, validation failure, timeout, crash, cancellation and exception all funnel through one `finally` that runs the kill ladder and removes profile/scratch/out. `ConversionService` additionally reaps `temp_root`. Evidence residue audit target: `0 temp dirs, 0 profile dirs, 0 lock files, 0 live soffice procs, 0 zombies` — reproduced by the containment test (§8). |
| **Process-tree kill / reap** | §1.4: process group + SIGTERM→grace→SIGKILL + synchronous reap verification. |
| **Resource ceilings** | Upload size `MAX_UPLOAD_SIZE` (100 MB, existing); wall-clock timeout (§1.5); memory bounded by cgroup (Railway 1 GB) **and** the §3 concurrency guard; PIDs bounded to ~12 per active conversion vs the 1000 cap. |
| **Output extension / MIME / magic** | Output must be `PK`-magic OOXML with `xl/workbook.xml`, reopened successfully (§1.6); served as `xlsx` MIME via the existing attachment download route. |
| **No internal path / process leakage** | Error messages are from a fixed allow-list (§4); `soffice` stderr, temp/profile paths and PIDs go to server logs only. |
| **No shell injection surface** | Fixed `argv` list, no `shell=True`, literal `--convert-to xlsx`. |
| **Document macros** | Headless `--convert-to` does not execute document macros on conversion. Recorded as accepted residual risk (§10). |
| **No new dependencies** | `soffice` is a system binary already in the Docker image; no pip additions, no `xlrd` (firewall). |


---

## §6. Existing PR-1 Compatibility (proof, not assertion)

**Structural proof.** The change adds exactly one registry key (`'xls','xlsx'`) and one
slug. `PluginRegistry.register()` writes only `self.plugins[key]`, `by_slug[slug]`,
`source_cache[source]`, `registered_keys[slug]`. Therefore:

- **DOC remains exactly as §0 measured** — no DOC plugin, guard, pair or advertisement
  map is modified; the code paths `('doc','pdf')`, `('doc','xlsx')`, … are the same
  bytes before and after.
- **PPT remains exactly as §0 measured** — same argument for `('ppt',*)`.
- **`('xls','xlsx')` is pair-scoped** — the plugin declares only that pair, so
  `('xls','pdf')`, `('xls','docx')`, `('xls','ppt')` … keep their current plugins and
  behaviour.
- **No unrelated converter behaviour changes** — `DocumentEngine`, the spreadsheet
  pandas cluster, the factory plugins and every certified pair are untouched; the only
  shared-file edits are the additive settings, the one-line timeout-family entry, and
  the two `STATIC_TARGET_MAP` `xls` rows (which add `XLSX` to `xls` only).

**Behavioural proof (executed as tests, §8).** A new regression suite asserts, against
the §0 oracle, that after the change:

1. `doc→pdf` returns the same status and same `detail` prefix as the §0 baseline.
2. `ppt→pdf` and `ppt→xlsx` likewise.
3. `xls→pdf` likewise (unchanged plugin).
4. `('xls','xlsx')` — and **only** that pair — changes status, from 422 → 201 with a
   validated `.xlsx`.
5. Registry diff assertion: `set(registry.plugins.keys())` after == before ∪
   `{('xls','xlsx')}`; `by_slug` gains only `xls-to-xlsx`.
6. `ALLOWED_EXTENSIONS` and `DISALLOWED_EXTENSIONS` are byte-identical (a test reads
   the module and pins the membership of `doc`/`ppt`/`xls`).

The one intentional advertisement change (`xls` gains `XLSX` in the two
`STATIC_TARGET_MAP` copies) is asserted by an F7-style governance test so the map
cannot silently drift from the registry — the same pattern that already pins the
`docx`/`pptx` rows.

---

## §7. Files to Change (exact, no broad edits)

**New files**
1. `app/utils/ole2_preflight.py` — `ACCEPTED_BOF_VERSIONS = {"0x0500","0x0600"}`,
   magic detection, Workbook/Book stream detection, BOF version read (port of the
   evidence-proven `_bof_probe` regex `\x09\x08\x08\x00(..)`), and a `classify()` that
   returns the honest rejection reason or `ACCEPTED`.
2. `app/utils/soffice_runner.py` — `soffice` discovery, `RunCtx`-style per-request
   trees, the §1.2 invocation, §1.4 kill ladder in `finally`, §1.6 output validation,
   retry-on-abort (§3), and bounded profile/scratch cleanup.
3. `app/plugins/document/xls_to_xlsx.py` — `XLSToXLSXPlugin`: `slug="xls-to-xlsx"`,
   `source_formats=["xls"]`, `target_formats=["xlsx"]`, `category="document"`,
   `engine="document"`, pair-scoped preflight, §3 admission, delegation to the runner.
4. `tests/assets/regression/` fixtures (per `spike_kit/fixtures/PROVENANCE.md`
   intended-destination list): `sample_legacy_biff8.xls`, `corrupt_truncated_biff8.xls`,
   `corrupt_garbage_biff8.xls`, `masquerade_xlsx_named_xls.xls`,
   `stress_biff8_120kc.xls`. **The 21.8 MB bulk tier stays out of the repo**
   (evidence/CI probe only, per PROVENANCE).
5. `tests/certified/document/test_xls_to_xlsx_certified.py` — §8 contract suite.
6. `tests/certified/document/test_xls_containment.py` — POSIX-only containment +
   residue + concurrency guard suite.
7. `tests/test_pr1_ole2_compat_regression.py` — the §6 oracle suite.

**Modified files (additive, minimal)**
8. `app/core/settings.py` — `XLS_MAX_ACTIVE_CONVERSIONS=1`, `XLS_MAX_WAITERS=4`,
   `XLS_CONVERSION_TIMEOUT_SECONDS=120`, `XLS_GRACE_SECONDS=5`, `XLS_QUEUE_TIMEOUT_SECONDS=120`,
   `XLS_MAX_RETRIES=2` (all `os.getenv`-backed, all defaulted to the evidence values).
9. `app/services/conversion_service.py` — one line: add `"xls"` to the
   `{"pdf","docx","doc","txt","md"}` family in `_get_timeout_seconds()`.
10. `app/static/js/widgets/tool_result_widget_v2.js` — `STATIC_TARGET_MAP.xls` gains
    `'XLSX'`.
11. `app/templates/main/converigo_main.html` — the same map's second copy, same edit.

**Conditional (needs Supervisor nod at implementation time — currently firewalled)**
- `app/data/converters/xls-to-xlsx.contract.json` + `xls-to-xlsx.json` landing artifacts
  — required **only** if we follow the office-cluster governance pattern (F7 ships them
  and its certified test asserts their presence). Listed separately because the current
  firewall forbids "add registry/contract yet".
- Optional hygiene: `nixpacks.toml` `nixPkgs += "libreoffice-calc"` for builder-parity
  (inert for this Railway service, which is `builder = "dockerfile"`).

**Explicitly NOT changed**
`ALLOWED_EXTENSIONS` • `DISALLOWED_EXTENSIONS` • `requirements.txt` (no `xlrd`) •
`Dockerfile` (libreoffice already present) • `railway.json` / `railway.toml` •
DOC/PPT plugins and guards • `DocumentEngine` • pandas spreadsheet cluster •
any certified converter JSON • any engine other than via the single timeout line.


---

## §8. Tests

Fixtures: the tracked set from §7 item 4 (real OLE2/BIFF8) plus the BIFF5/BIFF7/0x0550
evidence fixtures referenced from `spike_kit/evidence_fixtures/` via path constants
(not duplicated into the repo where PROVENANCE forbids).

**A. Format contract** (`test_xls_to_xlsx_certified.py`, uses the shared
`tests/certified/_factory_harness.py` vocabulary: discovered → 201 → download 200 →
content verified → honest 422)

| Case | Fixture | Expectation |
|---|---|---|
| Genuine BIFF5 | `sample_biff5.xls` (BOF `0x0500`) | 201, valid reopenable `.xlsx`, sheet names pinned |
| Genuine BIFF7 | `sample_biff7.xls` (BOF `0x0500`) | 201, valid, pinned sheets |
| Genuine BIFF8 (production-representative) | `sample_legacy_biff8.xls` (BOF `0x0600`) | 201, valid, pinned sheets (Ledger/Summary/Formats/Emptyish) |
| Corrupt / truncated | `corrupt_truncated_biff8.xls` | preflight or output-validation rejects → 422, no output file |
| Corrupt / scrambled | `corrupt_garbage_biff8.xls` | 422, no output file |
| **BOF 0x0550** | `sample_biff7_0550.xls` | **422 preflight, despite LibreOffice being able to convert it** — proves policy over capability |
| OOXML masquerade | `masquerade_xlsx_named_xls.xls` (`PK` magic, `.xls` name) | 422 with the masquerade message; never 201 |
| Garbage non-OLE2 | `not_ole2_junk.xls`, `not_ole2_random.xls`, `not_ole2_text.xls` | 422, zero processes spawned |
| Empty / unreadable | 0-byte `.xls` | 422 |

**B. Concurrency / guard** (`test_xls_containment.py`)
- Two simultaneous valid conversions: exactly one runs, the other is queued or returns
  503 — **never** a second `soffice` process (assert live-proc count).
- `XLS_MAX_WAITERS+1` simultaneous requests: the surplus gets immediate 503, no
  process spawned, no PID growth.
- Guard is honoured under the real timeout: oversized input + short timeout does not
  leak a process.

**C. Timeout / kill** (POSIX-only)
- Deliberately short timeout against a real conversion (the G4 method): SIGTERM fires,
  tree reaped, `orphans=0`, no partial output served, honest 500 returned.
- Stubborn-child control (the `_g4_sigkill_control` pattern): a child ignoring SIGTERM
  is reaped by SIGKILL escalation — proves the ladder is live independently of
  `soffice`'s own SIGTERM behaviour.
- Cancellation: abort the client mid-conversion → tree reaped, no orphan.

**D. Cancellation & residue**
- After every case above: `0 temp dirs, 0 profile dirs, 0 lock files, 0 live soffice
  processes, 0 zombies` under the request trees (the evidence residue audit, as a
  repeatable assertion).
- Retry-on-abort: simulate exit-134 once → bounded retry with a fresh profile
  succeeds; retry budget exhausted → honest 500.

**E. Output validity / MIME**
- Downloaded file is `PK`-magic, `xl/workbook.xml` present, ≥1 sheet, reopenable by
  `openpyxl`; served with the correct MIME and `attachment` disposition; filename is
  `<stem>.xlsx`.

**F. DOC/PPT regression** (`test_pr1_ole2_compat_regression.py`)
- Asserts the §0 oracle byte-for-byte for `doc→pdf`, `ppt→pdf`, `ppt→xlsx`,
  `xls→pdf`, and the `('xls','xlsx')` 422→201 transition.
- Asserts the registry key-set delta is exactly `{('xls','xlsx')}` and the slug delta
  is exactly `{"xls-to-xlsx"}`.
- Asserts `ALLOWED_EXTENSIONS` membership for `doc`/`ppt`/`xls` is unchanged.

**G. Advertisement governance**
- F7-style: `STATIC_TARGET_MAP.xls` in both files equals the registry-derived target
  list for `xls` (i.e. the previous list **plus** `XLSX`), so a future drift fails CI.

Certified tests run in CI on Linux (the containment subset is POSIX-gated). The suite
must pass alongside the existing full regression — no existing test is modified to
make the new one pass.

---

## §9. Deployment / Verification

1. **Targeted tests** — the §8 suites green on Linux CI.
2. **Full regression** — the existing suite (incl. all certified clusters and the
   F7 governance tests) unchanged-green; the §6 registry-diff assertion is the
   proof that nothing else moved.
3. **PR** — opened from a feature branch off `fix/pr1-ole2-honest-disable` (or `main`,
   per Supervisor preference), containing only the §7 file list.
4. **Supervisor merge approval** — explicit gate; no merge before.
5. **Railway auto-deploy** — merge to `main` builds via `builder = "dockerfile"`
   (libreoffice already in image). No Railway service change by this plan.
6. **Production smoke** — upload a real `.xls`, expect `201` + a `.xlsx` that Excel /
   LibreOffice opens; verify the sheet content is intact.
7. **Verify DOC/PPT remain disabled** — post the same OLE2 file as `.doc`/`.ppt` and
   confirm the §0 statuses and messages are reproduced exactly.
8. **Verify resource/process cleanup** — after the smoke tests, confirm no residual
   `soffice` processes, no orphaned temp/profile trees under `temp/` or `outputs/`,
   and PID/memory usage back to baseline.
9. **Verify the guard** — issue two concurrent `xls→xlsx` requests; confirm one runs
   and the other queues or 503s, and that only one `soffice` tree exists at any moment.
10. **Evidence re-run (optional, on the PR)** — `xls-final-evidence.yml` may be
    re-dispatched to confirm the production-image envelope still holds after the code
    lands; it changes no application state.


---

## §10. Risk Register

| # | Risk | Status | Mitigation / trigger |
|---|---|---|---|
| R1 | **LibreOffice SIGABRT / `WrappedTargetRuntimeException` (exit 134) under concurrent startup** — observed 1/2 at N=2 with full per-worker profile isolation; did not recur at N=4/N=8 (startup race, not load-driven) | **OPEN — known, unresolved, not hidden** | Bounded retry with fresh profile (§3). Do NOT describe as fixed. If it recurs in production beyond the retry budget, treat as P1 and consider pre-warming or a long-lived worker. |
| R2 | **Memory saturation** — N=8 hit 922 MiB (97 % of the 954 MiB cap, ~32 MiB headroom, `oom_kill=0`); bulk-class conversions cost 404 MiB each | OPEN (sizing constraint) | Guard = 1 active (§3) makes this unreachable at launch. Raising the guard requires memory-aware admission, not a count bump. |
| R3 | **`VmRSS` tree sum double-counts shared pages** (1.43 GiB at N=8 vs 922 MiB cgroup) — monitoring could cry wolf | OPEN (observability) | Cgroup `memory.peak`/`memory.events` is the authoritative metric; document this in the runbook. |
| R4 | **LibreOffice version drift** — the Dockerfile installs whatever Debian ships at build time; evidence is against 25.2.3.2 | OPEN | Pin or record the shipped version in the smoke check; a major LibreOffice upgrade re-opens G4/G6. |
| R5 | **Windows dev-host containment gap** — no process groups; grandchildren may survive a `terminate()` | Accepted, dev-only | Containment tests POSIX-gated; production is Linux. |
| R6 | **Document macro execution during headless conversion** | Accepted residual | `--convert-to` does not auto-run macros; monitor for CVEs in the shipped LibreOffice. |
| R7 | **Per-instance guard ≠ global under horizontal scaling** | Future | Guard is module-scoped; if Railway scales to >1 instance, admission must move to a shared limiter. |
| R8 | **No cell-level round-trip parity proof** (no runtime BIFF reader) | Accepted, disclosed | §1.7 limit + pinned fixture sheet expectations + FAQ disclosure. |
| R9 | **0x0550 rejection may refuse files users consider valid** | Accepted by policy | Supervisor-mandated; message tells users how to proceed. |

---

## §11. Hard Firewall — Acknowledged & Honoured

This plan **modifies nothing**. Until the Supervisor approves this plan AND lifts the
firewall, the following remain untouched, by design:

- ❌ `xls` upload enablement — **already satisfied** (§0.2: `xls` is in the allow-list;
  no change needed or made)
- ❌ registry / contract additions — deferred (§7 "Conditional")
- ❌ `ALLOWED_EXTENSIONS` / `DISALLOWED_EXTENSIONS` — no change (§7)
- ❌ `ACCEPTED_BOF_VERSIONS` — does not exist yet; created only at implementation time
- ❌ runtime `xlrd` — none; `soffice` parses (§1.1)
- ❌ DOC/PPT behaviour — untouched and regression-pinned to the §0 oracle (§6)
- ❌ Railway service / config — no change (§9.5)
- ❌ merge / deploy — none

**Internal consistency check (self-audit):**
§1's invocation/containment ≡ evidence `convert()` (proven) · §2's accepted BOF set ≡
evidence §F + G6 BIFF8 tiers · §3's limits ≡ evidence §G numbers (404 MiB / 922 MiB /
12 PIDs) · §4's mappings ≡ existing exception→HTTP plumbing + one additive 503 ·
§5 ⊆ existing validators + §1/§3/§4 · §6 ⊆ §0 oracle + registry key-set delta ·
§7 file list ⊇ every artifact referenced by §1–§10 · §8 covers every behaviour in
§1–§6 · §9 steps reference §7/§8 artifacts · §10 R1/R2 quote evidence §E verbatim.
No section promises a capability the evidence does not support, and no section hides
the N=2 SIGABRT.

---

## §12. Definition of Done (for the implementation phase, after approval)

1. `('xls','xlsx')` converts a real BIFF5/BIFF7/BIFF8 file end-to-end: 201 →
   validated, reopenable `.xlsx` download.
2. 0x0550, OOXML-masquerade, garbage, corrupt and non-OLE2 inputs all return honest 422
   with the §4 messages, spawning zero processes.
3. Timeout, crash and cancellation leave **zero** orphans, zombies, temp dirs, profile
   dirs or lock files.
4. Concurrency guard holds at 1 active process under concurrent load; surplus requests
   queue bounded or receive 503; PID/memory growth is bounded by evidence.
5. §0 DOC/PPT baseline is byte-identical; registry delta is exactly one key + one slug.
6. Full regression suite green; production smoke + cleanup + guard verification signed off.

---

**Deliverable status:** this document is the complete plan.
**STOP — returned for Supervisor review. No implementation has started.**
