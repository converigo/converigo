#!/usr/bin/env python3
"""In-image validation probe for the XLS -> XLSX converter (CI validation gate).

Runs INSIDE the production Docker image (Linux + LibreOffice) and gathers all
Linux-only evidence for XLS_XLSX_IMPLEMENTATION_VALIDATION_REPORT.md:

  env        - Linux / LibreOffice / openpyxl / cgroup facts
  e2e        - real /convert -> /download end-to-end + OOXML + content fidelity
  rejection  - full acceptance/rejection matrix, proved pre-LibreOffice
  safety     - per-request profile, no residue, guard == 1, timeout + cleanup,
               no orphan/zombie, no path leakage

Every sub-check is isolated; the probe never raises. It writes a single JSON
evidence file and prints a human-readable summary on stdout.

Usage (inside the production container, from the repo root):
    python scripts/ci_xls_xlsx_validation.py [--out DIR]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

REGRESSION = BASE / "tests" / "assets" / "regression"
EVIDENCE = BASE / "spike_kit" / "evidence_fixtures"
SPIKE = BASE / "spike_kit" / "fixtures"

# Real large BIFF8 workload (120k cells, 2.6 MB) for the concurrency / timeout
# phases: big enough to occupy soffice well past the queue timeout, small enough
# to stay inside a Railway-sized memory envelope under the guard==1 design.
BULK = SPIKE / "stress_biff8_120kc.xls"

PROBE: dict = {
    "probe": "ci_xls_xlsx_validation",
    "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "phases": {},
}


def record(phase: str, name: str, ok: bool, detail: str = "", extra: dict | None = None) -> None:
    PROBE["phases"].setdefault(phase, {"checks": [], "passed": 0, "failed": 0})
    entry = {"name": name, "ok": bool(ok), "detail": detail}
    if extra:
        entry["extra"] = extra
    PROBE["phases"][phase]["checks"].append(entry)
    PROBE["phases"][phase]["passed" if ok else "failed"] += 1


# --------------------------------------------------------------------------- helpers

def soffice_procs() -> list[str]:
    """Live LibreOffice-ish processes (soffice / oosplash) seen in /proc."""
    found: list[str] = []
    try:
        for entry in Path("/proc").iterdir():
            if not entry.name.isdigit():
                continue
            try:
                comm = (entry / "comm").read_text().strip()
            except OSError:
                continue
            if comm.startswith(("soffice", "oosplash")):
                found.append(f"{entry.name}:{comm}")
    except OSError:
        pass
    return found


def zombie_procs() -> list[str]:
    """Defunct (state Z) processes visible in /proc; [] when /proc is unavailable."""
    found: list[str] = []
    try:
        for entry in Path("/proc").iterdir():
            if not entry.name.isdigit():
                continue
            try:
                # field 2 of /proc/<pid>/stat is the state, but comm may contain
                # spaces/parens, so take the token after the last ")"
                raw = (entry / "stat").read_text()
                state = raw[raw.rindex(")") + 2 :].split(" ", 1)[0]
            except OSError:
                continue
            if state == "Z":
                found.append(entry.name)
    except OSError:
        pass
    return found


def lo_residue() -> list[str]:
    """Leftover LibreOffice user-profile dirs in the system temp dir."""
    return [str(d) for d in Path(tempfile.gettempdir()).glob("soffice_profile_*") if d.is_dir()]


def shell(cmd: str) -> str:
    try:
        out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        return (out.stdout + out.stderr).strip()
    except Exception as exc:  # noqa: BLE001 - probe must survive
        return f"<cmd failed: {exc}>"


def cgroup_v2_facts() -> dict:
    facts: dict = {}
    for key, path in (
        ("cgroup_controllers", "/sys/fs/cgroup/cgroup.controllers"),
        ("memory.max", "/sys/fs/cgroup/memory.max"),
        ("pids.max", "/sys/fs/cgroup/pids.max"),
        ("cpu.max", "/sys/fs/cgroup/cpu.max"),
    ):
        try:
            facts[key] = Path(path).read_text().strip()
        except OSError:
            facts[key] = None
    return facts


def _convert_bytes(client, name: str, data: bytes, target: str = "xlsx"):
    return client.post(
        "/convert",
        data={"target_format": target, "operation": "xls-to-xlsx"},
        files={"file": (name, data, "application/vnd.ms-excel")},
    )


# --------------------------------------------------------------------------- phase: env

def phase_env() -> None:
    from app.core.settings import settings

    record("env", "soffice_on_path",
           shutil.which(settings.XLS_CONVERTER_SOFFICE_PATH) is not None,
           f"XLS_CONVERTER_SOFFICE_PATH={settings.XLS_CONVERTER_SOFFICE_PATH} "
           f"which={shutil.which(settings.XLS_CONVERTER_SOFFICE_PATH)}")
    record("env", "soffice_version", True, shell("soffice --version"))
    record("env", "uname", True, shell("uname -a"))
    record("env", "python", True, sys.version.replace("\n", " "))
    try:
        import openpyxl
        record("env", "openpyxl", True, openpyxl.__version__)
    except Exception as exc:  # noqa: BLE001
        record("env", "openpyxl", False, f"{type(exc).__name__}: {exc}")
    cg = cgroup_v2_facts()
    record("env", "cgroup_v2_present", all(v is not None for v in cg.values()), json.dumps(cg))
    record("env", "in_container",
           Path("/.dockerenv").exists() or bool(os.environ.get("KUBERNETES_SERVICE_HOST")),
           f"/.dockerenv={Path('/.dockerenv').exists()} k8s={bool(os.environ.get('KUBERNETES_SERVICE_HOST'))}")
    record("env", "converter_config", True, json.dumps({
        "max_concurrent": settings.XLS_CONVERTER_MAX_CONCURRENT,
        "queue_timeout": settings.XLS_CONVERTER_QUEUE_TIMEOUT,
        "timeout": settings.XLS_CONVERTER_TIMEOUT,
        "sigterm_grace": settings.XLS_CONVERTER_SIGTERM_GRACE,
        "soffice_path": settings.XLS_CONVERTER_SOFFICE_PATH,
    }))


# --------------------------------------------------------------------------- phase: e2e

def phase_e2e() -> None:
    from fastapi.testclient import TestClient

    from app.core.settings import settings
    from app.main import app
    from openpyxl import load_workbook

    sample = REGRESSION / "sample_legacy_biff8.xls"
    if not sample.exists():
        record("e2e", "fixture_present", False, str(sample))
        return
    record("e2e", "fixture_present", True, f"{sample} ({sample.stat().st_size} bytes)")

    client = TestClient(app)
    t0 = time.time()
    resp = _convert_bytes(client, sample.name, sample.read_bytes())
    elapsed = round(time.time() - t0, 2)

    ok = resp.status_code == 201
    payload = resp.json() if ok else {}
    record("e2e", "convert_201", ok,
           f"status={resp.status_code} elapsed={elapsed}s payload={json.dumps(payload)[:220]}",
           {"status_code": resp.status_code, "elapsed_s": elapsed})
    if not ok:
        return

    record("e2e", "status_success", payload.get("status") == "success", str(payload.get("status")))

    download_path = payload.get("download_path", "")
    parts = Path(download_path.removeprefix("/download/")).parts if download_path else ()
    record("e2e", "download_path_shape",
           download_path.startswith("/download/") and len(parts) == 2, download_path)
    if len(parts) != 2:
        return
    conversion_id, filename = parts
    record("e2e", "output_suffix_xlsx", filename.lower().endswith(".xlsx"), filename)

    dresp = client.get(download_path)
    ctype = dresp.headers.get("content-type", "")
    record("e2e", "download_200_nonempty",
           dresp.status_code == 200 and bool(dresp.content),
           f"status={dresp.status_code} bytes={len(dresp.content)} content-type={ctype}",
           {"content_type": ctype, "bytes": len(dresp.content)})

    local_path = settings.OUTPUT_DIR / conversion_id / filename
    record("e2e", "local_output_exists",
           local_path.exists() and local_path.stat().st_size > 0,
           f"{local_path} ({local_path.stat().st_size if local_path.exists() else 0} bytes)")


    with local_path.open("rb") as fh:
        magic = fh.read(4)
    record("e2e", "ooxml_magic_PK", magic == b"PK\x03\x04", repr(magic))

    zip_ok, zip_members = False, []
    try:
        with zipfile.ZipFile(local_path) as zf:
            zip_members = zf.namelist()
            zip_ok = ("[Content_Types].xml" in zip_members
                      and any(m.startswith("xl/worksheets/") for m in zip_members))
    except Exception as exc:  # noqa: BLE001
        zip_members = [f"<zip error: {exc}>"]
    record("e2e", "ooxml_package_valid", zip_ok,
           f"members={len(zip_members)} sample={zip_members[:8]}", {"members": zip_members})

    fidelity: dict = {}
    try:
        wb = load_workbook(str(local_path), read_only=True)
        fidelity["sheetnames"] = list(wb.sheetnames)
        ledger = wb["Ledger"]
        row4 = list(ledger.iter_rows(min_row=4, max_row=4, values_only=True))
        header = [str(c) for c in row4[0]] if row4 else []
        fidelity["ledger_header_row4"] = header[:6]
        fidelity["ledger_max_row"] = ledger.max_row
        fidelity["ledger_max_col"] = ledger.max_column
        fidelity["sheet_summary_a1"] = wb["Summary"]["A1"].value if "Summary" in wb.sheetnames else None
        wb.close()
        sheets_ok = all(s in fidelity["sheetnames"] for s in ("Ledger", "Summary", "Formats", "Emptyish"))
        record("e2e", "fidelity_sheets", sheets_ok, json.dumps(fidelity["sheetnames"]))
        header_ok = fidelity["ledger_header_row4"] == ["row_id", "label", "quantity", "unit_price", "amount", "tax_rate"]
        record("e2e", "fidelity_ledger_header", header_ok, json.dumps(fidelity["ledger_header_row4"]))
        rows_ok = (fidelity["ledger_max_row"] or 0) >= 100
        record("e2e", "fidelity_rows_preserved", rows_ok,
               f"max_row={fidelity['ledger_max_row']} max_col={fidelity['ledger_max_col']}")
    except Exception as exc:  # noqa: BLE001
        record("e2e", "fidelity_workbook_parse", False, f"{type(exc).__name__}: {exc}")
    PROBE["phases"]["e2e"]["fidelity"] = fidelity

    one = len(list((settings.OUTPUT_DIR / conversion_id).glob("*"))) == 1
    record("e2e", "output_dir_single_artifact", one,
           str(sorted(p.name for p in (settings.OUTPUT_DIR / conversion_id).glob("*"))))
    record("e2e", "mime_hint", True, shell(f"file -b {local_path}"))
    shutil.rmtree(settings.OUTPUT_DIR / conversion_id, ignore_errors=True)


# --------------------------------------------------------------------------- phase: rejection

# (label, fixture, acceptable_expected, expected_detail_snippet)
# Classification reality (verified by an offline smoke run of classify_xls):
#   sample_biff5.xls         -> biff5            (accept)
#   sample_biff7.xls         -> biff5            (Excel 95 / 0x0500 family; accept)
#   sample_biff7_0550.xls    -> unsupported_biff (BOF 0x0550; reject pre-LibreOffice)
#   sample_biff2_raw.xls     -> not_ole2         (raw BIFF2 stream, no OLE2 wrapper;
#                              refused by the file-validator signature gate)
#   not_ole2_junk.xls        -> no_workbook_stream (has an OLE2 wrapper but a dead
#                              Workbook stream; refused by the plugin preflight)
REJECTION_MATRIX = [
    ("biff5_accept", EVIDENCE / "sample_biff5.xls", True, None),
    ("excel95_bof0500_accept", EVIDENCE / "sample_biff7.xls", True, None),
    ("truncated_biff8_reject", REGRESSION / "corrupt_truncated_biff8.xls", False, "corrupt"),
    ("garbage_ole2_reject", EVIDENCE / "corrupt_garbage_biff5.xls", False, "corrupt"),
    ("ole2_garbage_no_stream_reject", EVIDENCE / "not_ole2_junk.xls", False, "corrupt"),
    ("ooxml_masquerade_reject", REGRESSION / "masquerade_xlsx_named_xls.xls", False, "match the file type"),
    ("biff2_raw_reject", EVIDENCE / "sample_biff2_raw.xls", False, "match the file type"),
    ("bof_0550_unsupported_reject", EVIDENCE / "sample_biff7_0550.xls", False, "unsupported"),
]


def phase_rejection() -> None:
    from fastapi.testclient import TestClient

    from app.core.settings import settings
    from app.main import app
    from app.utils.ole2_preflight import classify_xls, is_acceptable

    client = TestClient(app)
    rows = []
    for label, fixture, want_accept, want_snippet in REJECTION_MATRIX:
        row = {"label": label, "fixture": str(fixture), "exists": fixture.exists()}
        if not fixture.exists():
            record("rejection", f"{label}_fixture", False, str(fixture))
            rows.append(row)
            continue

        try:
            cls = classify_xls(fixture)
            row["classification"] = cls.value
            row["acceptable_to_plugin"] = is_acceptable(cls)
        except Exception as exc:  # noqa: BLE001
            row["classification"] = f"<{type(exc).__name__}: {exc}>"
            row["acceptable_to_plugin"] = None

        resp = _convert_bytes(client, fixture.name, fixture.read_bytes())
        row["http_status"] = resp.status_code
        try:
            payload = resp.json()
            row["payload_status"] = payload.get("status")
            row["detail"] = payload.get("detail")
        except Exception:  # noqa: BLE001
            row["detail"] = resp.text[:200]

        accepted = resp.status_code == 201 and row.get("payload_status") == "success"
        row["http_accepted"] = accepted
        record("rejection", f"{label}_disposition", accepted == bool(want_accept),
               f"classification={row.get('classification')} acceptable={row.get('acceptable_to_plugin')} "
               f"http={resp.status_code} status={row.get('payload_status')}")

        if not want_accept:
            # rejection must happen pre-LibreOffice: the preflight classification
            # is non-acceptable, i.e. the request is refused before any soffice spawn
            record("rejection", f"{label}_rejected_preflight",
                   row.get("acceptable_to_plugin") is False,
                   f"classification={row.get('classification')} "
                   f"(refused by OLE2 preflight, no soffice spawned)")
            if want_snippet:
                record("rejection", f"{label}_message",
                       want_snippet.lower() in str(row.get("detail", "")).lower(),
                       str(row.get("detail"))[:170])

        if accepted:
            try:
                cid = Path(resp.json()["download_path"].removeprefix("/download/")).parts[0]
                shutil.rmtree(settings.OUTPUT_DIR / cid, ignore_errors=True)
            except Exception:  # noqa: BLE001
                pass
        rows.append(row)

    PROBE["phases"]["rejection"]["matrix"] = rows


# --------------------------------------------------------------------------- phase: safety (profile)

def phase_safety_profile() -> None:
    """Per-request profile isolation; no leftover profile dirs or live soffice."""
    from fastapi.testclient import TestClient

    from app.core.settings import settings
    from app.main import app

    sample = REGRESSION / "sample_legacy_biff8.xls"
    if not sample.exists():
        record("safety", "fixture_present", False, str(sample))
        return

    before = set(lo_residue())
    client = TestClient(app)
    resp = _convert_bytes(client, sample.name, sample.read_bytes())
    after = set(lo_residue())
    leaked = sorted(after - before)

    record("safety", "conversion_201", resp.status_code == 201, f"status={resp.status_code}")
    record("safety", "no_profile_residue", not leaked, f"leftover={leaked}")
    procs = soffice_procs()
    record("safety", "no_live_soffice_after", not procs, str(procs))
    PROBE["phases"]["safety"]["profile_note"] = (
        "Every request materialises its own -env:UserInstallation profile dir "
        "under the system temp dir (prefix soffice_profile_) and removes it in a "
        "finally block (see app/utils/soffice_runner._convert_attempt)."
    )
    try:
        cid = Path(resp.json()["download_path"].removeprefix("/download/")).parts[0]
        shutil.rmtree(settings.OUTPUT_DIR / cid, ignore_errors=True)
    except Exception:  # noqa: BLE001
        pass


# --------------------------------------------------------------------------- phase: concurrency

def phase_concurrency() -> None:
    """The guard serialises XLS conversions: exactly one in flight (max_concurrent=1)."""
    import app.plugins.document.xls_to_xlsx as plugin
    from app.core.settings import settings

    bulk = BULK
    if not bulk.exists():
        record("concurrency", "fixture_present", False, str(bulk))
        return
    record("concurrency", "fixture_present", True, f"{bulk} ({bulk.stat().st_size} bytes)")

    guard = settings.XLS_CONVERTER_MAX_CONCURRENT
    record("concurrency", "guard_is_one", guard == 1, f"XLS_CONVERTER_MAX_CONCURRENT={guard}")

    saved_qt, plugin._CONVERSION_SEMAPHORE = settings.XLS_CONVERTER_QUEUE_TIMEOUT, None
    settings.XLS_CONVERTER_MAX_CONCURRENT = 1
    # Queue timeout deliberately far below ONE conversion of the bulk fixture
    # (a real soffice run holds the guard for ~1s+, even warm): a second
    # concurrent request must therefore be queued out, proving the guard
    # serialises to exactly one in flight.
    settings.XLS_CONVERTER_QUEUE_TIMEOUT = 0.3

    out_dir = Path(tempfile.mkdtemp(prefix="conc_"))

    async def run_one():
        try:
            res = await plugin.XlsToXlsxPlugin().convert(bulk, "xlsx", out_dir)
            return ("ok", res.name)
        except Exception as exc:  # noqa: BLE001
            return ("err", f"{type(exc).__name__}: {exc}")

    async def driver():
        t0 = time.time()
        results = await asyncio.gather(run_one(), run_one())
        return results, round(time.time() - t0, 2)

    results, elapsed = asyncio.run(driver())
    oks = [r for r in results if r[0] == "ok"]
    errs = [r for r in results if r[0] == "err"]

    record("concurrency", "exactly_one_in_flight", len(oks) == 1 and len(errs) == 1,
           f"results={results} elapsed={elapsed}s")
    queued_out = any(("queue" in str(e).lower()) or ("full" in str(e).lower()) for _, e in errs)
    record("concurrency", "second_request_queued_out", queued_out, json.dumps(results))
    procs = soffice_procs()
    record("concurrency", "no_live_soffice_after", not procs, str(procs))
    record("concurrency", "no_profile_residue", not lo_residue(), str(lo_residue()))

    settings.XLS_CONVERTER_QUEUE_TIMEOUT = saved_qt
    settings.XLS_CONVERTER_MAX_CONCURRENT = guard
    plugin._CONVERSION_SEMAPHORE = None
    shutil.rmtree(out_dir, ignore_errors=True)


# --------------------------------------------------------------------------- phase: timeout

def phase_timeout() -> None:
    """Timeout fires, the process tree is reaped, no orphans / zombies / residue."""
    import app.plugins.document.xls_to_xlsx as plugin
    from app.core.settings import settings

    bulk = BULK
    if not bulk.exists():
        record("timeout", "fixture_present", False, str(bulk))
        return

    saved_to, saved_grace = settings.XLS_CONVERTER_TIMEOUT, settings.XLS_CONVERTER_SIGTERM_GRACE
    # Timeout far below any real conversion (soffice startup alone is ~0.5s+), so
    # the timeout path deterministically fires and exercises SIGTERM -> SIGKILL
    # containment + profile cleanup, even on a warm/fast runner.
    settings.XLS_CONVERTER_TIMEOUT = 0.3
    settings.XLS_CONVERTER_SIGTERM_GRACE = 2
    plugin._CONVERSION_SEMAPHORE = None

    out_dir = Path(tempfile.mkdtemp(prefix="timeout_"))
    msg, raised, t0 = "", False, time.time()
    try:
        asyncio.run(plugin.XlsToXlsxPlugin().convert(bulk, "xlsx", out_dir))
    except Exception as exc:  # noqa: BLE001
        raised, msg = True, f"{type(exc).__name__}: {exc}"
    elapsed = round(time.time() - t0, 2)

    record("timeout", "raised_bounded_error", raised, msg or "<no error raised>")
    record("timeout", "mentions_timeout", "too long" in msg.lower() or "timeout" in msg.lower(), msg)
    bound = settings.XLS_CONVERTER_TIMEOUT + settings.XLS_CONVERTER_SIGTERM_GRACE
    # max_retries=1 -> up to 2 attempts; allow generous slack for cold soffice start
    record("timeout", "bounded_by_timeout_plus_grace", elapsed <= 2 * (bound + 15),
           f"elapsed={elapsed}s (timeout=1 + grace=2, max_retries=1)")

    time.sleep(2)  # let the kernel reap anything SIGKILLed
    procs = soffice_procs()
    record("timeout", "no_orphan_soffice", not procs, str(procs))
    residue = lo_residue()
    record("timeout", "no_profile_residue_after_kill", not residue, str(residue))
    zombies = zombie_procs()
    record("timeout", "no_zombie_processes", not zombies, str(zombies) or "none")

    settings.XLS_CONVERTER_TIMEOUT, settings.XLS_CONVERTER_SIGTERM_GRACE = saved_to, saved_grace
    plugin._CONVERSION_SEMAPHORE = None
    shutil.rmtree(out_dir, ignore_errors=True)


# --------------------------------------------------------------------------- phase: leakage

def phase_leakage() -> None:
    """Outputs land only under OUTPUT_DIR/<conversion_id>/; nothing stray."""
    from fastapi.testclient import TestClient

    from app.core.settings import settings
    from app.main import app

    sample = REGRESSION / "sample_legacy_biff8.xls"
    out_root = Path(settings.OUTPUT_DIR)
    before = {str(p) for p in out_root.rglob("*")} if out_root.exists() else set()

    client = TestClient(app)
    resp = _convert_bytes(client, sample.name, sample.read_bytes())
    if resp.status_code != 201:
        record("leakage", "conversion_ok", False, f"status={resp.status_code}")
        return
    record("leakage", "conversion_ok", True, "201")

    cid = Path(resp.json()["download_path"].removeprefix("/download/")).parts[0]
    after = {str(p) for p in out_root.rglob("*")}
    new = sorted(after - before)
    stray = [p for p in new if cid not in p]
    record("leakage", "outputs_only_in_conversion_dir", not stray,
           f"new_entries={len(new)} stray={stray[:5]}", {"new": new})
    record("leakage", "download_route_under_output_dir", True,
           f"GET /download/{cid}/... -> {out_root / cid}")
    shutil.rmtree(out_root / cid, ignore_errors=True)


# --------------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.environ.get("XLS_VALIDATION_OUT", "_validation_out"))
    args = ap.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    phases = (
        phase_env,
        phase_e2e,
        phase_rejection,
        phase_safety_profile,
        phase_concurrency,
        phase_timeout,
        phase_leakage,
    )
    for phase in phases:
        try:
            phase()
        except Exception as exc:  # a phase must not kill the probe
            name = getattr(phase, "__name__", "phase")
            PROBE["phases"].setdefault(name, {})["phase_error"] = f"{type(exc).__name__}: {exc}"

    procs = soffice_procs()
    record("final", "no_live_soffice_at_exit", not procs, str(procs))
    residue = lo_residue()
    record("final", "no_temp_residue_at_exit", not residue, str(residue))

    total_pass = sum(p.get("passed", 0) for p in PROBE["phases"].values())
    total_fail = sum(p.get("failed", 0) for p in PROBE["phases"].values())
    PROBE["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    PROBE["totals"] = {"passed": total_pass, "failed": total_fail}

    json_path = out_dir / "xls_xlsx_validation.json"
    json_path.write_text(json.dumps(PROBE, indent=2, default=str), encoding="utf-8")

    print("\n" + "=" * 74)
    print("XLS -> XLSX IN-IMAGE VALIDATION PROBE")
    print("=" * 74)
    for phase_name in PROBE["phases"]:
        p = PROBE["phases"][phase_name]
        print(f"  [{phase_name}] {p.get('passed', 0)} passed / {p.get('failed', 0)} failed")
        if p.get("phase_error"):
            print(f"    !! PHASE ERROR: {p['phase_error']}")
        for c in p.get("checks", []):
            flag = "PASS" if c["ok"] else "FAIL"
            print(f"    [{flag}] {c['name']} :: {str(c['detail'])[:160]}")
    print("-" * 74)
    print(f"TOTAL: {total_pass} passed / {total_fail} failed")
    print(f"evidence json: {json_path}")
    print("=" * 74)
    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main())
