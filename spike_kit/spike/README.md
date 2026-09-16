# LibreOffice XLS→XLSX spike kit (Phase 2, throwaway)

This kit answers the operational questions the Implementation Gate needs before
any `xls → xlsx` converter code is written. It imports **no application code**
and writes **nothing** into the repository.

## Files
| File | Purpose |
|---|---|
| `lo_spike.py` | the whole spike: T1–T8, stdlib only, Linux + Windows capable |
| `Dockerfile.spike` | `python:3.11-slim` + the same LibreOffice apt line as the production `Dockerfile` |
| `run_in_docker.sh` | build + run + copy the report out |
| `spike_report.json` / `.md` | produced by a run (empty/error stub until soffice exists) |

## How to run it (recommended: container identical to production)

```bash
# from this directory, on any Docker-capable host (Linux or Docker Desktop)
bash run_in_docker.sh
# extra flags pass through, e.g. heavier concurrency + tighter stress timeout
bash run_in_docker.sh --conc 4,8,16 --stress-timeout 10
```

Equivalent manual commands:

```bash
docker build -f Dockerfile.spike -t converigo-lo-spike ..
docker run --rm -v "$PWD:/out" converigo-lo-spike \
    python3 /spike/lo_spike.py --conc 4,8 --out /out
```

To spike the **real** Railway/production image instead of an identical one:

```bash
docker build -t converigo-prod .            # repo Dockerfile
docker run --rm --entrypoint sh converigo-prod -c \
  'mkdir -p /spike && echo ready'           # app image already contains soffice
docker cp fixtures/. convergo:/spike/fixtures   # copy fixtures into the container
docker run --rm -v "$PWD:/out" --entrypoint python3 converigo-prod \
  /spike/lo_spike.py --conc 4,8 --out /out
```

## What each test proves

| Test | Question answered | Gate |
|---|---|---|
| T1 single ×5 | does a genuine BIFF8 `.xls` become a valid OOXML `.xlsx`; cold vs warm cost | G1 must be 5/5 valid |
| T2 repeated ×20 | stability + drift across many invocations | G2 ≥19/20, no upward drift |
| T3 concurrent (unique profiles) | does LibreOffice scale at 4 and 8, cost per file, peak RSS | G3 all succeed, no cross-talk |
| T4 concurrent (one shared profile) | the hazard the runner design must avoid | documents lock behaviour |
| T5 bulk stress (21.8 MB / 1,000,020 cells) | worst-case time + RSS for sizing timeout and memory | G6 recorded vs the app's timeout policy |
| T6 timeout + kill | does the timeout fire, does the process group die, orphans/zombies, partial output | G4 killed=True, orphans=0, zombies=0 |
| T7 corrupt / truncated / masquerade | honest failure, exit codes, whether garbage in produces a file | G5 no valid output from corrupt input |
| T8 residue | profiles/temp/lock cleanup after the run | residue = 0 |

Fixtures consumed (see `../fixtures/PROVENANCE.md`): `sample_legacy_biff8.xls`
(34 KB, 4 sheets, formulas/dates/formats/merged), `stress_biff8_120kc.xls`
(2.7 MB, 120 k cells, 20 k formulas), `stress_biff8_bulk1m.xls` (21.8 MB,
1 M cells), `corrupt_truncated_biff8.xls`, `corrupt_garbage_biff8.xls`,
`masquerade_xlsx_named_xls.xls`.

## Running without Docker (any Linux host with LibreOffice)

```bash
sudo apt-get install -y --no-install-recommends libreoffice libreoffice-calc
cd .tmp/xls_prep/spike && ./run_native_linux.sh
```

Numbers stay host-specific (no cgroup limits), but conversion correctness,
profile isolation, timeout/kill and corrupt-input behaviour are all valid.


## Measurement notes and limits
- Peak RSS is read from `/proc/<pid>/status` `VmRSS` for every live
  `soffice`/`libreoffice` process at 40 Hz, summed → it includes the
  `soffice.bin` child, which is where the real memory lives on Linux.
- On Windows the same poll falls back to `tasklist` process counting; **no RSS**
  is available there, so a Windows run yields conversion/lock/timeout evidence
  only and must be labelled as non-equivalent to the production runtime.
- Zombies are counted from `/proc` `State: Z` (Linux-only concept).
- The spike never installs anything and never edits `requirements.txt`.

## Exit codes
- `0` spike completed, report written
- `3` `soffice` not found → report written with an `error` field (no evidence)
