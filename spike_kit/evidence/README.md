# XLS→XLSX final evidence kit (one controlled CI iteration)

Throwaway evidence tooling for the **final evidence run** approved by the
Supervisor. It closes the three remaining gaps of the XLS→XLSX Implementation
Gate with real numbers measured on real Linux + real LibreOffice + cgroup v2:

| Gap | What is measured | Where |
|---|---|---|
| **G4** containment | forced timeout → SIGTERM → grace → SIGKILL against a *live* soffice tree; whole-tree reap verification; orphan/zombie/temp/profile residue audit; SIGKILL-escalation control | `phase_g4`, `g4_convert`, `_g4_sigkill_control` |
| **G6** resource envelope | single + N-concurrent conversion under the production cgroup, read from `memory.peak` / `memory.current` / `memory.stat` / `pids.current` / `memory.events` plus the 40 Hz VmRSS tree sum for parity with the earlier spike | `phase_single`, `phase_conc`, `cgroup_state`, `Sampler` |
| **BIFF5** decision | genuine BIFF5, genuine BIFF7, the third-party `0x0550` variant and malformed BIFF5 fed to real soffice byte-for-byte | `phase_biff5`, `_bof_probe` |

## Scope firewall (what this kit never touches)

Allowed by the Supervisor for this iteration: **CI/evidence harness, spike
scripts, evidence fixtures, report/artifact.** This kit is all four and only
those four. It does **not** import or modify any application source, plugin,
contract, registry, `ALLOWED_EXTENSIONS`, `ACCEPTED_BOF_VERSIONS`, converter
JSON, Railway configuration or Railway deployment, and it enables nothing.
The 21.8 MB bulk fixture is CI evidence only and never enters the application
runtime or the repo's `tests/assets`.

`lo_evidence.py` is Python-stdlib-only: it adds no dependency to the repo and
does not touch `requirements.txt`.

## How it runs (production-equivalent, capped)

`run_final_evidence.sh` builds the **production image** from the repo
`Dockerfile` (so the LibreOffice under test is the one the app actually ships,
not a spike-only substitute) and runs the probe inside it under the exact
Railway production envelope:

```
docker run --rm --memory 1000000000 --pids-limit 1000 \
  --entrypoint python3 converigo-evidence:prod \
  /app/spike_kit/evidence/lo_evidence.py --phase <env|single|conc|g4|biff5> \
                                         --out /out --fixtures /app/spike_kit/evidence_fixtures
```

* `--memory 1000000000` = the Railway memory limit (1,000,000,000 B)
* `--pids-limit 1000` = the Railway `pidLimit`
* `ubuntu-latest` runner → Linux + cgroup v2 + genuine LibreOffice

Each phase is a separate container, so a crash/OOM in one phase cannot destroy
another phase's evidence, and `_ckpt()` flushes partial JSON after every item.

## G4: why the termination path now actually fires

The earlier spike (`spike_kit/spike`) reported `killed=false` for its T6 probe:
the 1.5 s timeout was longer than the fixture's 0.776 s conversion, so the
SIGTERM→SIGKILL ladder never ran against a live soffice. This kit deliberately
uses **short** timeouts (0.12 s / 0.30 s / 1.00 s across the 34 KB / 2.7 MB /
21.8 MB fixtures) so the ladder provably fires while soffice is mid-work, then
it snapshots the process tree at kill time and synchronously verifies the whole
tree is reaped before returning. The `g4_control` tier runs a child that
**ignores SIGTERM** to prove the SIGKILL escalation is live and effective.

## BIFF5 / 0x0550: no normalisation, ever

`_bof_probe()` is read-only: it reports the OLE2 magic, the Workbook/Book
stream and the BOF version field. No fixture byte is rewritten, repaired or
normalised anywhere in this kit. The `0x0550` decision is derived purely from
what LibreOffice actually does with the byte-exact file.

## Output

`spike_kit/evidence/out/evidence_<phase>.json` per phase, uploaded as the
**final-evidence** artifact by `.github/workflows/xls-final-evidence.yml`
(dispatch-only; it never runs automatically and never on `main` directly).
Every number in `XLS_XLSX_FINAL_REMEDIATION_EVIDENCE_REPORT.md` is traceable to
these JSON files.
