#!/usr/bin/env python3
"""
CONVERIGO - XLS->XLSX PREPARATION (Phase 2): LibreOffice headless spike.

Throwaway tooling ONLY. It never imports application code and never touches the
repository. It answers exactly the questions the Implementation Gate needs about
`soffice --headless --convert-to xlsx` for genuine legacy BIFF8 .xls input:

  T1 single conversion            x5 warm/cold timings, exit codes, output validity
  T2 repeated conversions         20x sequential, same fixture, fresh profile each run
  T3 concurrent conversions       N workers, UNIQUE -env:UserInstallation profiles
  T4 shared-profile control       N workers, ONE profile (documents the lock hazard)
  T5 stress fixture               large BIFF8 workbook: time, peak RSS, output size
  T6 timeout behaviour            short timeout, then kill process group; orphans/zombies
  T7 malformed inputs             corrupt/truncated/masquerade fixtures -> honest failure
  T8 profile isolation + cleanup  residue check: profiles, .lock files, temp dirs

Output: spike_report.json + spike_report.md next to this script (plus stdout).

Usage:
  python3 lo_spike.py [--soffice PATH] [--fixtures DIR] [--conc 4,8,12]
                      [--stress-timeout 8] [--skip t3,t5]
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import platform
import random
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import uuid
import zipfile
from pathlib import Path

IS_POSIX = os.name == "posix"
ZIP_MAGIC = b"PK\x03\x04"
REPORT_DIR = Path(__file__).resolve().parent

FIXTURES = {
    "sample": "sample_legacy_biff8.xls",
    "stress": "stress_biff8_120kc.xls",
    "bulk": "stress_biff8_bulk1m.xls",
    "corrupt_truncated": "corrupt_truncated_biff8.xls",
    "corrupt_garbage": "corrupt_garbage_biff8.xls",
    "masquerade": "masquerade_xlsx_named_xls.xls",
}


# --------------------------------------------------------------- environment
def find_soffice(explicit: str | None) -> tuple[str | None, list[str]]:
    tried: list[str] = []
    cands: list[str] = []
    if explicit:
        cands.append(explicit)
        if os.path.isabs(explicit) or os.sep in explicit:
            p = Path(explicit)
            if p.exists():
                return str(p), tried + [explicit]
    env = os.environ.get("SOFFICE_PATH")
    if env:
        cands.append(env)
    for name in ("soffice", "libreoffice"):
        w = shutil.which(name)
        if w:
            cands.append(w)
    if IS_POSIX:
        cands += ["/usr/bin/soffice", "/usr/lib/libreoffice/program/soffice",
                  "/usr/bin/libreoffice"]
    else:
        base = Path("C:/Program Files")
        for exe in (base / "LibreOffice/program/soffice.exe",):
            cands.append(str(exe))
    for c in cands:
        tried.append(c)
        if c and Path(c).exists():
            return c, tried
        w = shutil.which(c) if c else None
        if w:
            return w, tried
    return None, tried


def soffice_version(binpath: str) -> str:
    """`--version` exits immediately, so it needs no dedicated profile."""
    try:
        r = subprocess.run([binpath, "--version"], capture_output=True, text=True,
                           timeout=90)
        return ((r.stdout or "") + (r.stderr or "")).strip()[:200] or "no output"
    except Exception as exc:  # noqa: BLE001
        return f"UNKNOWN ({type(exc).__name__}: {str(exc)[:80]})"


# ------------------------------------------------------------------ sampling


# --------------------------------------------------------------- conversion
class RssSampler:
    """Background poller of total soffice RSS across the host (Linux /proc)."""

    def __init__(self, hz: float = 40.0):
        self.hz = hz
        self._stop = __import__("threading").Event()
        self._thread = None
        self.peak = 0
        self.samples: list[int] = []

    def _run(self):
        import threading  # noqa: F401
        while not self._stop.is_set():
            total = sum(rss for _, rss in _soffice_procs())
            self.samples.append(total)
            if total > self.peak:
                self.peak = total
            self._stop.wait(1.0 / self.hz)

    def __enter__(self):
        import threading
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._stop.clear()
        self.peak = 0
        self.samples = []
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        return False


def to_uri(path: Path) -> str:
    return path.resolve().as_uri()


def convert(binpath: str, src: Path, outdir: Path, profile: Path, *,
            timeout: float = 60.0, reuse_profile: bool = False) -> dict:
    """Run one headless XLS->XLSX conversion in a fully isolated process group.

    Mirrors the constraints a production runner must honour:
      - argv list, shell=False (no string interpolation into a shell)
      - dedicated -env:UserInstallation per invocation
      - start_new_session=True so a timeout can kill the whole group
      - stdout/stderr captured to files, not inherited pipes
      - bounded wall clock, then SIGTERM -> grace -> SIGKILL
    """
    outdir.mkdir(parents=True, exist_ok=True)
    if not reuse_profile:
        shutil.rmtree(profile, ignore_errors=True)
    profile.mkdir(parents=True, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="lospike_")
    src_copy = Path(tmp) / src.name
    shutil.copy2(src, src_copy)

    argv = [
        binpath,
        f"-env:UserInstallation={to_uri(profile)}",
        "--headless", "--invisible", "--norestore", "--nologo", "--nofirststartwizard",
        "--convert-to", "xlsx",
        "--outdir", str(outdir),
        str(src_copy),
    ]
    out_log = Path(tmp) / "stdout.log"
    err_log = Path(tmp) / "stderr.log"
    env = dict(os.environ)
    env.update({"HOME": tmp, "TMPDIR": tmp, "LANG": "C.UTF-8"})

    t0 = time.perf_counter()
    res: dict = {"argv_tail": argv[-3:], "timeout": timeout, "killed": False,
                 "exit": None, "error": None}
    try:
        with open(out_log, "wb") as fo, open(err_log, "wb") as fe:
            popen_kw: dict = {"stdout": fo, "stderr": fe, "cwd": tmp, "env": env}
            if IS_POSIX:
                popen_kw["start_new_session"] = True
            proc = subprocess.Popen(argv, **popen_kw)
            try:
                res["exit"] = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                res["killed"] = True
                try:
                    if IS_POSIX:
                        os.killpg(os.getpgid(proc.pid), 15)
                    else:
                        proc.terminate()
                except Exception:  # noqa: BLE001
                    pass
                try:
                    proc.wait(timeout=5)
                except Exception:  # noqa: BLE001
                    try:
                        if IS_POSIX:
                            os.killpg(os.getpgid(proc.pid), 9)
                        else:
                            proc.kill()
                    except Exception:  # noqa: BLE001
                        pass
                    try:
                        proc.wait(timeout=5)
                    except Exception:  # noqa: BLE001
                        res["error"] = "process survived SIGKILL"
    except Exception as exc:  # noqa: BLE001
        res["error"] = f"{type(exc).__name__}: {exc}"

    dur = time.perf_counter() - t0
    produced = sorted(outdir.glob("*.xlsx"), key=lambda p: p.stat().st_mtime)
    target = produced[-1] if produced else None
    res.update(
        duration=round(dur, 3),
        stdout=_read(out_log), stderr=_read(err_log),
        output=str(target.name) if target else None,
        output_bytes=target.stat().st_size if target and target.exists() else 0,
        output_valid_xlsx=is_valid_xlsx(target) if target else False,
    )
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(profile, ignore_errors=True)
    return res


def _read(path: Path, limit: int = 600) -> str:
    try:
        return path.read_text(errors="replace").strip()[-limit:]
    except OSError:
        return ""


def is_valid_xlsx(path: Path) -> bool:
    """Output must be a real OOXML package, not just a renamed file."""
    try:
        if path is None or not path.exists():
            return False
        if path.read_bytes()[:4] != ZIP_MAGIC:
            return False
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            if "xl/workbook.xml" not in names:
                return False
            z.read("xl/workbook.xml")
            return z.testzip() is None
    except Exception:  # noqa: BLE001
        return False

def _soffice_procs() -> list[tuple[int, int]]:
    """Return [(pid, rss_bytes)] for live soffice/libreoffice processes."""
    out: list[tuple[int, int]] = []
    if IS_POSIX and Path("/proc").is_dir():
        for entry in Path("/proc").iterdir():
            if not entry.name.isdigit():
                continue
            try:
                cmd = entry.joinpath("cmdline").read_bytes().replace(b"\0", b" ").decode(
                    "utf-8", "replace")
            except OSError:
                continue
            if not re.search(r"soffice|libreoffice", cmd):
                continue
            rss = 0
            try:
                for line in entry.joinpath("status").read_text().splitlines():
                    if line.startswith("VmRSS:"):
                        rss = int(line.split()[1]) * 1024
                        break
            except OSError:
                pass
            out.append((int(entry.name), rss))
        return out
    try:  # Windows fallback: no /proc, use tasklist (Working Set is unavailable there)
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq soffice.bin", "/FO", "CSV",
                            "/NH"], capture_output=True, text=True, timeout=20)
        n = sum(1 for ln in r.stdout.splitlines() if "soffice" in ln.lower())
        r2 = subprocess.run(["tasklist", "/FI", "IMAGENAME eq soffice.exe", "/FO", "CSV",
                             "/NH"], capture_output=True, text=True, timeout=20)
        n += sum(1 for ln in r2.stdout.splitlines() if "soffice" in ln.lower())
        for _ in range(n):
            out.append((-1, 0))
    except Exception:  # noqa: BLE001
        pass
    return out


def zombie_count() -> int:
    """Processes stuck in Z state (Linux only meaningful)."""
    if not (IS_POSIX and Path("/proc").is_dir()):
        return -1
    z = 0
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            st = entry.joinpath("status").read_text()
        except OSError:
            continue
        if re.search(r"^State:\s*Z", st, re.M):
            z += 1
    return z


def container_envelope() -> dict:
    """cgroup limits + CPU count, so RSS numbers can be read against the real cap."""
    env: dict = {"cpus": os.cpu_count()}
    for label, path in (
        ("memory.max", "/sys/fs/cgroup/memory.max"),                      # cgroup v2
        ("memory.limit_in_bytes", "/sys/fs/cgroup/memory/memory.limit_in_bytes"),  # v1
    ):
        p = Path(path)
        if p.exists():
            raw = p.read_text().strip()
            env[label] = raw if raw == "max" else _as_int(raw)
    for label, path in (("cpu.max", "/sys/fs/cgroup/cpu.max"),
                        ("cpu.cfs_quota_us", "/sys/fs/cgroup/cpu/cpu.cfs_quota_us")):
        p = Path(path)
        if p.exists():
            env[label] = p.read_text().strip()
    if "memory.max" not in env and "memory.limit_in_bytes" not in env:
        mp = Path("/proc/meminfo")
        if mp.exists():
            for line in mp.read_text().splitlines():
                if line.startswith("MemTotal:"):
                    env["host_mem_total_kb"] = line.split()[1]
                    break
    return env


def _as_int(text: str):
    try:
        return int(text)
    except ValueError:
        return text


def wall(fn, *a, **kw):
    t0 = time.perf_counter()
    out = fn(*a, **kw)
    return out, round(time.perf_counter() - t0, 3)


def run_all(binpath: str, fixdir: Path, root: Path, conc_levels: list[int],
            stress_timeout: float) -> dict:
    results: dict = {}
    sample = fixdir / FIXTURES["sample"]
    stress = fixdir / FIXTURES["bulk"]
    if not stress.exists():  # degrade to the mid tier if the bulk probe is absent
        stress = fixdir / FIXTURES["stress"]

    def slot(name):
        d = root / name
        d.mkdir(parents=True, exist_ok=True)
        return d

    # ---- T1 single (first run cold, then warm) -------------------------
    rows = []
    for i in range(5):
        d, w = wall(convert, binpath, sample, slot(f"t1_out_{i}"),
                    root / f"t1_prof_{i}", timeout=90)
        rows.append({"run": i, "wall": w, "exit": d["exit"],
                     "valid_xlsx": d["output_valid_xlsx"], "out_bytes": d["output_bytes"],
                     "stderr": d["stderr"][:200]})
    ok = [r for r in rows if r["valid_xlsx"]]
    results["T1_single"] = {
        "runs": rows, "successes": len(ok),
        "durations_s": [r["wall"] for r in rows],
        "first_run_s": rows[0]["wall"],
        "median_rest_s": statistics.median([r["wall"] for r in rows[1:]]) if len(rows) > 1 else None,
    }

    # ---- T2 repeated 20x ----------------------------------------------
    reps = []
    for i in range(20):
        d, w = wall(convert, binpath, sample, slot("t2_out"), root / f"t2_prof_{i}", timeout=90)
        reps.append({"i": i, "wall": w, "valid": d["output_valid_xlsx"], "exit": d["exit"]})
    good = [r["wall"] for r in reps if r["valid"]]
    results["T2_repeated"] = {
        "runs": len(reps), "successes": len(good),
        "min_s": min(good) if good else None, "max_s": max(good) if good else None,
        "mean_s": round(statistics.mean(good), 3) if good else None,
        "drift_last_minus_first_s": round(reps[-1]["wall"] - reps[0]["wall"], 3),
    }

    # ---- T3 concurrent with UNIQUE profiles ---------------------------
    conc_report = {}
    for n in conc_levels:
        def one(k, n=n):
            d, w = wall(convert, binpath, sample, slot(f"t3_{n}_out"),
                        root / f"t3_{n}_prof_{k}", timeout=180)
            return {"k": k, "wall": w, "valid": d["output_valid_xlsx"],
                    "exit": d["exit"], "stderr": d["stderr"][:160]}

        with RssSampler() as s:
            t0 = time.perf_counter()
            with cf.ThreadPoolExecutor(max_workers=n) as ex:
                out = list(ex.map(one, range(n)))
            span = round(time.perf_counter() - t0, 3)
        succ = [o for o in out if o["valid"]]
        conc_report[n] = {
            "workers": n, "successes": len(succ), "wall_total_s": span,
            "per_run_s": [o["wall"] for o in out],
            "slowest_s": max(o["wall"] for o in out),
            "peak_rss_bytes": s.peak,
            "throughput_files_per_min": round(len(succ) / span * 60, 2) if span else None,
            "failures": [o for o in out if not o["valid"]][:3],
        }
    results["T3_concurrent_unique_profiles"] = conc_report

    # ---- T4 concurrent SHARING one profile (hazard control) ------------
    n = conc_levels[-1] if conc_levels else 4
    shared = root / "t4_shared_profile"
    shared.mkdir(parents=True, exist_ok=True)

    def one_shared(k):
        d, w = wall(convert, binpath, sample, slot(f"t4_out_{k}"), shared,
                    timeout=180, reuse_profile=True)
        return {"k": k, "wall": w, "valid": d["output_valid_xlsx"], "exit": d["exit"],
                "stderr": d["stderr"][:200], "stdout": d["stdout"][:200]}

    with cf.ThreadPoolExecutor(max_workers=n) as ex:
        sh_out = list(ex.map(one_shared, range(n)))
    pat = re.compile(r"in use|lock|installation", re.I)
    lock_msgs = [o for o in sh_out if pat.search(o["stderr"] + o["stdout"])]
    results["T4_shared_profile_control"] = {
        "workers": n, "successes": sum(1 for o in sh_out if o["valid"]),
        "lock_or_profile_messages": len(lock_msgs),
        "sample_message": ((lock_msgs[0]["stderr"] or lock_msgs[0]["stdout"])[:220]
                           if lock_msgs else None),
        "note": "reuse_profile=True keeps the shared profile alive across runs",
    }
    shutil.rmtree(shared, ignore_errors=True)

    # ---- T5 stress fixture (with RSS sampling) -------------------------
    with RssSampler() as s5:
        d5, w5 = wall(convert, binpath, stress, slot("t5_out"), root / "t5_prof",
                      timeout=stress_timeout * 4)
    results["T5_stress"] = {
        "fixture_bytes": stress.stat().st_size, "wall_s": w5, "exit": d5["exit"],
        "valid_xlsx": d5["output_valid_xlsx"], "out_bytes": d5["output_bytes"],
        "peak_rss_bytes": s5.peak, "stderr": d5["stderr"][:250],
    }

    # ---- T6 timeout + process-group kill -------------------------------
    procs_before = len(_soffice_procs())
    d6, w6 = wall(convert, binpath, stress, slot("t6_out"), root / "t6_prof", timeout=1.5)
    time.sleep(3)
    procs_after = len(_soffice_procs())
    results["T6_timeout_kill"] = {
        "timeout_s": 1.5, "wall_s": w6, "killed": d6["killed"],
        "post_kill_error": d6["error"], "exit": d6["exit"],
        "soffice_procs_before": procs_before, "soffice_procs_after": procs_after,
        "orphans_left": max(0, procs_after - procs_before),
        "zombies": zombie_count(), "partial_output_emitted": bool(d6["output"]),
    }

    # ---- T7 malformed / adversarial inputs -----------------------------
    mal = {}
    for key in ("corrupt_truncated", "corrupt_garbage", "masquerade"):
        src = fixdir / FIXTURES[key]
        if not src.exists():
            mal[key] = {"skipped": "fixture missing"}
            continue
        d, w = wall(convert, binpath, src, slot(f"t7_{key}"), root / f"t7_prof_{key}",
                    timeout=90)
        mal[key] = {"fixture_bytes": src.stat().st_size, "wall_s": w, "exit": d["exit"],
                    "killed": d["killed"], "produced_output": bool(d["output"]),
                    "output_valid_xlsx": d["output_valid_xlsx"],
                    "stderr": d["stderr"][:300], "stdout": d["stdout"][:200]}
    results["T7_malformed"] = mal

    # ---- T8 residue / isolation ----------------------------------------
    tmp_root = Path(tempfile.gettempdir())
    leftovers = [p.name for p in tmp_root.glob("lospike_*") if p.name != tmp_root.name]
    prof_left = [p.name for p in root.glob("*prof*")] if root.exists() else []
    locks = [str(p.relative_to(root)) for p in root.rglob(".lock")]
    results["T8_cleanup_residue"] = {
        "temp_dirs_left": len(leftovers),
        "profile_dirs_still_present": len(prof_left),
        "profile_lock_files_found": locks[:10],
        "live_soffice_procs_at_end": len(_soffice_procs()),
        "zombies_at_end": zombie_count(),
    }
    return results


def write_report(payload: dict, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    j = outdir / "spike_report.json"
    j.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    lines = [
        "# LibreOffice XLS->XLSX spike report", "",
        f"- host: {payload['host']}",
        f"- soffice bin: `{payload['soffice_bin']}`",
        f"- soffice version: {payload['soffice_version']}",
        f"- started: {payload['started']}", "",
    ]
    for key, val in (payload.get("results") or {}).items():
        lines += [f"## {key}", "```json",
                  json.dumps(val, indent=2, default=str)[:2800], "```", ""]
    md = outdir / "spike_report.md"
    md.write_text("\n".join(lines), encoding="utf-8")
    return j, md


def main() -> int:
    ap = argparse.ArgumentParser(description="throwaway LibreOffice XLS->XLSX spike")
    ap.add_argument("--soffice", default=None)
    ap.add_argument("--fixtures",
                    default=str(Path(__file__).resolve().parents[1] / "fixtures"))
    ap.add_argument("--conc", default="4,8")
    ap.add_argument("--stress-timeout", type=float, default=15.0)
    ap.add_argument("--out", default=str(REPORT_DIR))
    args = ap.parse_args()

    binpath, tried = find_soffice(args.soffice)
    fixdir = Path(args.fixtures)
    payload = {
        "host": (f"{platform.system()} {platform.release()} {platform.machine()} "
                 f"py{platform.python_version()} in_container="
                 f"{os.path.exists('/.dockerenv')}"),
        "soffice_candidates_tried": tried,
        "soffice_bin": binpath,
        "soffice_version": None,
        "fixtures": {k: {"path": str(fixdir / v), "bytes": (fixdir / v).stat().st_size}
                     for k, v in FIXTURES.items() if (fixdir / v).exists()},
        "container_envelope": container_envelope(),
        "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "results": {},
    }
    if not binpath:
        payload["error"] = ("soffice/libreoffice not found - spike did not run. "
                            "Execute inside the production image (see README.md).")
        j, md = write_report(payload, Path(args.out))
        print("ERROR:", payload["error"])
        print(f"wrote {j}\nwrote {md}")
        return 3

    payload["soffice_version"] = soffice_version(binpath)
    print(f"soffice  = {binpath}\nversion  = {payload['soffice_version']}\n")
    root = Path(tempfile.mkdtemp(prefix="lospike_root_"))
    try:
        conc = [int(x) for x in re.split(r"[,\s]+", args.conc) if x.strip()]
        payload["results"] = run_all(binpath, fixdir, root, conc, args.stress_timeout)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    j, md = write_report(payload, Path(args.out))
    print(json.dumps(payload["results"], indent=2, default=str)[:7000])
    print(f"\nwrote {j}\nwrote {md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
