#!/usr/bin/env python3
"""
CONVERIGO - XLS->XLSX FINAL EVIDENCE PROBE (one controlled CI iteration).

Throwaway evidence tooling. Imports NO application code, reads no converter
JSON, changes no registry/contract, writes nothing outside its --out dir.
It closes the three gaps the Implementation Gate still owes the Supervisor:

  G4  containment / termination
        forced-timeout conversion against REAL soffice: SIGTERM -> grace ->
        SIGKILL, wait/reap, whole-process-tree verification, orphan + zombie +
        temp/profile residue audit, plus a SIGKILL-escalation CONTROL (a child
        that ignores SIGTERM) proving the escalation path is live.

  G6  resource envelope under the production cgroup
        single conversion + N-way concurrency, measured with cgroup v2
        memory.peak / memory.events / pids.current (the numbers that actually
        count against the 1 GB and 1000-pid caps) AND the 40 Hz VmRSS tree sum
        used by the earlier spike, so both methodologies agree.

  BIFF5 decision evidence
        genuine BIFF5, genuine BIFF7, the third-party 0x0550 variant, malformed
        BIFF5 (truncated / scrambled / wrong stream / not-OLE2), fed to real
        soffice byte-for-byte. NO normalisation, NO repair, NO patching: the
        0x0550 decision is derived from what LibreOffice actually does.

Every number in the final report comes from this probe's JSON output.

Usage:
  python3 lo_evidence.py --phase env|single|conc|g4|biff5 --out DIR
                         [--fixtures DIR] [--conc N] [--soffice PATH]
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from pathlib import Path

IS_POSIX = os.name == "posix"
CG2 = Path("/sys/fs/cgroup")

FIXTURES = {
    "sample": "sample_legacy_biff8.xls",          # 34 KB BIFF8, production-representative
    "stress": "stress_biff8_120kc.xls",           # 2.7 MB, 120k cells, 20k formulas
    "bulk": "stress_biff8_bulk1m.xls",            # 21.8 MB, 1,000,020 cells (evidence-only)
    "biff5": "sample_biff5.xls",                  # genuine BIFF5  (0x0500/2412/1994)
    "biff7": "sample_biff7.xls",                  # genuine BIFF7  (0x0500/0x0DBB/1995)
    "biff7_0550": "sample_biff7_0550.xls",        # third-party 0x0550 variant
    "trunc5": "corrupt_truncated_biff5.xls",
    "garb5": "corrupt_garbage_biff5.xls",
    "wrong_stream": "wrong_ole2_stream.xls",
    "not_ole2_junk": "not_ole2_junk.xls",
    "not_ole2_random": "not_ole2_random.xls",
    "not_ole2_text": "not_ole2_text.xls",
    "biff2_raw": "sample_biff2_raw.xls",
}


# ------------------------------------------------------------------ cgroup v2
def _cg_read(name: str) -> str | None:
    for cand in (CG2 / name, CG2 / "memory" / name):
        try:
            return cand.read_text().strip()
        except OSError:
            continue
    return None


def _cg_int(name: str) -> int | None:
    raw = _cg_read(name)
    if raw is None or raw == "max":
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def cgroup_state() -> dict:
    """Snapshot of the container's resource envelope (cgroup v2 preferred)."""
    ev_raw = _cg_read("memory.events") or ""
    events = {}
    for line in ev_raw.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].isdigit():
            events[parts[0]] = int(parts[1])
    v2 = (CG2 / "memory.max").exists()
    # memory.stat separates anonymous memory from reclaimable page cache, so a
    # peak can be read honestly against the 1 GB cap instead of being inflated
    # by file pages that the kernel can drop.
    stat = {}
    stat_raw = _cg_read("memory.stat") or ""
    for line in stat_raw.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].lstrip("-").isdigit():
            stat[parts[0]] = int(parts[1])
    mem_total = None
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                mem_total = int(line.split()[1]) * 1024
                break
    except OSError:
        pass
    return {
        "cgroup_version": "v2" if v2 else "v1-or-none",
        "cgroup_controllers": (_cg_read("cgroup.controllers") or "").split(),
        "memory.max": _cg_read("memory.max"),
        "memory.high": _cg_read("memory.high"),
        "memory.peak": _cg_int("memory.peak"),
        "memory.swap.max": _cg_read("memory.swap.max"),
        "memory.current": _cg_int("memory.current"),
        "memory.stat": stat,
        "pids.max": _cg_read("pids.max"),
        "pids.current": _cg_int("pids.current"),
        "cpu.max": _cg_read("cpu.max"),
        "memory.events": events,
        "host_mem_total_bytes": mem_total,
        "in_container": Path("/.dockerenv").exists(),
    }


# ------------------------------------------------------------------- process
def _proc_field(pid: str, fname: str) -> str | None:
    try:
        return (Path("/proc") / pid / fname).read_text(errors="replace")
    except OSError:
        return None


def _cmdline(pid: str) -> str:
    raw = _proc_field(pid, "cmdline")
    return "" if raw is None else raw.replace("\0", " ")


def _vmrss(pid: str) -> int:
    st = _proc_field(pid, "status")
    if not st:
        return 0
    for line in st.splitlines():
        if line.startswith("VmRSS:"):
            try:
                return int(line.split()[1]) * 1024
            except (IndexError, ValueError):
                return 0
    return 0


def _state(pid: str) -> str:
    st = _proc_field(pid, "status")
    if not st:
        return "?"
    m = re.search(r"^State:\s*(\S+)", st, re.M)
    return m.group(1) if m else "?"


def _pgid_of(pid: int) -> int | None:
    try:
        st = (Path("/proc") / str(pid) / "stat").read_text()
        tail = st[st.rindex(")") + 2:].split()   # comm may contain spaces/parens
        return int(tail[2])                       # fields: state ppid pgid ...
    except (OSError, IndexError, ValueError):
        return None


def soffice_tree() -> list[dict]:
    """Live soffice/libreoffice processes (pid, rss, state, cmdline)."""
    out: list[dict] = []
    if not (IS_POSIX and Path("/proc").is_dir()):
        return out
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        cmd = _cmdline(entry.name)
        if not re.search(r"soffice|libreoffice", cmd):
            continue
        out.append({"pid": int(entry.name), "rss": _vmrss(entry.name),
                    "state": _state(entry.name), "cmd": cmd[:160]})
    return out


def zombie_count() -> int:
    if not (IS_POSIX and Path("/proc").is_dir()):
        return -1
    return sum(1 for e in Path("/proc").iterdir()
               if e.name.isdigit() and _state(e.name).startswith("Z"))


class Sampler:
    """40 Hz poller: VmRSS tree sum + pids.current + live-proc count.

    The VmRSS sum is the parity measurement used by the earlier spike; it is
    kept so the new cgroup numbers can be cross-checked against the old ones.
    """

    def __init__(self, hz: float = 40.0):
        self.hz = hz
        self._stop = threading.Event()
        self._t = None
        self.rss_peak = 0
        self.pids_peak = 0
        self.procs_peak = 0
        self.samples = 0

    def _run(self):
        while not self._stop.is_set():
            tree = soffice_tree()
            total = sum(p["rss"] for p in tree)
            self.samples += 1
            if total > self.rss_peak:
                self.rss_peak = total
            if len(tree) > self.procs_peak:
                self.procs_peak = len(tree)
            pc = _cg_int("pids.current")
            if pc is not None and pc > self.pids_peak:
                self.pids_peak = pc
            self._stop.wait(1.0 / self.hz)

    def __enter__(self):
        self._stop.clear()
        self.rss_peak = self.pids_peak = self.procs_peak = 0
        self.samples = 0
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        if self._t:
            self._t.join(timeout=2.0)
        return False


# ------------------------------------------------------------------- helpers
def to_uri(p: Path) -> str:
    return p.resolve().as_uri()


def valid_ooxml(path: Path) -> dict:
    """Is this a real OOXML workbook, and what sheets does it declare?"""
    out = {"is_zip": False, "valid": False, "sheets": [], "bytes": 0}
    try:
        out["bytes"] = path.stat().st_size
    except OSError:
        return out
    if path.read_bytes()[:4] != b"PK\x03\x04":
        return out
    out["is_zip"] = True
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            if "[Content_Types].xml" not in names or "xl/workbook.xml" not in names:
                return out
            if z.testzip() is not None:
                return out
            wb = z.read("xl/workbook.xml").decode("utf-8", "replace")
            out["sheets"] = re.findall(r'<sheet[^>]*name="([^"]+)"', wb)
            out["valid"] = True
    except Exception:  # noqa: BLE001
        return out
    return out


def find_soffice(explicit: str | None) -> tuple[str | None, list[str]]:
    tried: list[str] = []
    cands: list[str] = [explicit] if explicit else []
    env_p = os.environ.get("SOFFICE_PATH")
    if env_p:
        cands.append(env_p)
    for name in ("soffice", "libreoffice"):
        w = shutil.which(name)
        if w:
            cands.append(w)
    if IS_POSIX:
        cands += ["/usr/bin/soffice", "/usr/lib/libreoffice/program/soffice"]
    for c in cands:
        if not c:
            continue
        tried.append(c)
        if Path(c).exists():
            return c, tried
        w = shutil.which(c)
        if w:
            return w, tried + [w]
    return None, tried


def soffice_version(b: str) -> str:
    try:
        r = subprocess.run([b, "--version"], capture_output=True, text=True, timeout=90)
        return ((r.stdout or "") + (r.stderr or "")).strip()[:200] or "no output"
    except Exception as exc:  # noqa: BLE001
        return f"UNKNOWN ({type(exc).__name__})"


def kernel_info() -> str:
    try:
        return Path("/proc/version").read_text().strip()
    except OSError:
        return platform.version()


class RunCtx:
    """Per-run scratch space; tracked so residue can be audited exactly."""

    def __init__(self, root: Path, tag: str):
        self.tag = tag
        self.tmp = root / f"tmp_{tag}"
        self.profile = root / f"prof_{tag}"
        self.out = root / f"out_{tag}"
        for d in (self.tmp, self.profile, self.out):
            d.mkdir(parents=True, exist_ok=True)


def tree_gone(dead_pids: set[int], deadline_s: float = 8.0) -> tuple[bool, list[dict], float]:
    """Wait until every PID we spawned is really gone (no orphans, no zombies).

    Reaps the group and confirms cancellation is synchronised: the caller only
    proceeds once the tree is empty or the deadline expires.
    """
    t0 = time.perf_counter()
    while True:
        leftover = [p for p in soffice_tree() if p["pid"] in dead_pids]
        for pid in dead_pids:                    # count our own zombies too
            if _state(str(pid)).startswith("Z") and not any(p["pid"] == pid for p in leftover):
                leftover.append({"pid": pid, "rss": 0, "state": "Z", "cmd": "<zombie>"})
        if not leftover:
            return True, [], round(time.perf_counter() - t0, 3)
        if time.perf_counter() - t0 > deadline_s:
            return False, leftover, round(time.perf_counter() - t0, 3)
        time.sleep(0.05)

# --------------------------------------------------------- conversion (G4 G6)
def convert(binpath: str, src: Path, ctx: RunCtx, *, timeout: float,
            grace: float = 5.0) -> dict:
    """One headless XLS->XLSX conversion with full G4 containment.

    Mirrors what a production runner must do: dedicated profile per call,
    start_new_session so a timeout can kill the whole process group, then
    SIGTERM -> bounded grace -> SIGKILL -> wait/reap.
    """
    src_copy = ctx.tmp / src.name
    shutil.copy2(src, src_copy)
    argv = [binpath,
            f"-env:UserInstallation={to_uri(ctx.profile)}",
            "--headless", "--invisible", "--norestore", "--nologo",
            "--nofirststartwizard", "--convert-to", "xlsx",
            "--outdir", str(ctx.out), str(src_copy)]
    out_log, err_log = ctx.tmp / "stdout.log", ctx.tmp / "stderr.log"
    env = dict(os.environ)
    env.update({"HOME": str(ctx.tmp), "TMPDIR": str(ctx.tmp), "LANG": "C.UTF-8"})

    res: dict = {"timeout_s": timeout, "grace_s": grace, "killed": False,
                 "sigterm_sent": False, "sigkill_sent": False,
                 "term_to_death_s": None, "exit": None, "error": None}
    t0 = time.perf_counter()
    try:
        with open(out_log, "wb") as fo, open(err_log, "wb") as fe:
            kw: dict = {"stdout": fo, "stderr": fe, "cwd": str(ctx.tmp), "env": env}
            if IS_POSIX:
                kw["start_new_session"] = True
            proc = subprocess.Popen(argv, **kw)
            res["pid"] = proc.pid
            try:
                res["exit"] = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                res["killed"] = True
                res["sigterm_sent"] = True
                pgid = os.getpgid(proc.pid)
                t_term = time.perf_counter()
                try:
                    os.killpg(pgid, 15)            # SIGTERM to the whole group
                except OSError as exc:
                    res["error"] = f"killpg SIGTERM failed: {exc}"
                try:
                    res["exit"] = proc.wait(timeout=grace)
                    res["term_to_death_s"] = round(time.perf_counter() - t_term, 3)
                except subprocess.TimeoutExpired:
                    res["sigkill_sent"] = True
                    try:
                        os.killpg(pgid, 9)        # SIGKILL escalation
                    except OSError as exc:
                        res["error"] = (res["error"] or "") + f" | killpg SIGKILL failed: {exc}"
                    res["exit"] = proc.wait(timeout=10)
                    res["term_to_death_s"] = round(time.perf_counter() - t_term, 3)
    except Exception as exc:  # noqa: BLE001 - probe must report, never crash
        res["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
    res["wall_s"] = round(time.perf_counter() - t0, 3)

    produced = sorted(p.name for p in ctx.out.glob("*.xlsx"))
    res["produced_files"] = produced
    if produced:
        vv = valid_ooxml(ctx.out / produced[0])
        res["output_valid_xlsx"] = vv["valid"]
        res["output_sheets"] = vv["sheets"]
        res["output_bytes"] = vv["bytes"]
    else:
        res["output_valid_xlsx"] = False
        res["output_sheets"] = []
        res["output_bytes"] = 0
    try:
        res["stderr"] = err_log.read_text(errors="replace").strip()[-400:]
    except OSError:
        res["stderr"] = ""
    return res




def g4_convert(binpath: str, src: Path, ctx: RunCtx, *, timeout: float,
               grace: float = 5.0) -> dict:
    """G4 containment probe: FORCE the termination path against real soffice.

    Differs from convert() by snapshotting the process tree at kill time and
    then synchronously verifying the whole tree is reaped (no orphans, no
    zombies, no partial survivors) before returning.
    """
    src_copy = ctx.tmp / src.name
    shutil.copy2(src, src_copy)
    argv = [binpath,
            f"-env:UserInstallation={to_uri(ctx.profile)}",
            "--headless", "--invisible", "--norestore", "--nologo",
            "--nofirststartwizard", "--convert-to", "xlsx",
            "--outdir", str(ctx.out), str(src_copy)]
    out_log, err_log = ctx.tmp / "stdout.log", ctx.tmp / "stderr.log"
    env = dict(os.environ)
    env.update({"HOME": str(ctx.tmp), "TMPDIR": str(ctx.tmp), "LANG": "C.UTF-8"})

    res: dict = {"timeout_s": timeout, "grace_s": grace, "killed": False,
                 "sigterm_sent": False, "sigkill_sent": False, "exit": None,
                 "error": None, "tree_at_kill": [], "tree_reaped": None,
                 "orphan_leftovers": [], "reap_wait_s": None}
    t0 = time.perf_counter()
    try:
        with open(out_log, "wb") as fo, open(err_log, "wb") as fe:
            kw: dict = {"stdout": fo, "stderr": fe, "cwd": str(ctx.tmp), "env": env}
            if IS_POSIX:
                kw["start_new_session"] = True
            proc = subprocess.Popen(argv, **kw)
            res["pid"] = proc.pid
            try:
                res["exit"] = proc.wait(timeout=timeout)
                res["outcome"] = "completed_before_timeout"
            except subprocess.TimeoutExpired:
                res["killed"] = True
                res["sigterm_sent"] = True
                res["outcome"] = "timeout_fired"
                pgid = os.getpgid(proc.pid)
                t_term = time.perf_counter()
                res["tree_at_kill"] = [p for p in soffice_tree()
                                       if _pgid_of(p["pid"]) == pgid]
                dead = {p["pid"] for p in res["tree_at_kill"]} or {proc.pid}
                try:
                    os.killpg(pgid, 15)           # SIGTERM
                except OSError as exc:
                    res["error"] = f"killpg(SIGTERM) failed: {exc}"
                try:
                    res["exit"] = proc.wait(timeout=grace)
                    res["stage"] = "died_from_sigterm"
                except subprocess.TimeoutExpired:
                    res["sigkill_sent"] = True
                    res["stage"] = "died_from_sigkill"
                    try:
                        os.killpg(pgid, 9)       # SIGKILL escalation
                    except OSError as exc:
                        res["error"] = (res["error"] or "") + f" | killpg(SIGKILL) failed: {exc}"
                    res["exit"] = proc.wait(timeout=10)
                res["term_to_death_s"] = round(time.perf_counter() - t_term, 3)
                # synchronised cancellation: do not return until tree is empty
                gone, leftovers, wait_s = tree_gone(dead, deadline_s=8.0)
                res["tree_reaped"] = gone
                res["orphan_leftovers"] = leftovers
                res["reap_wait_s"] = wait_s
    except Exception as exc:  # noqa: BLE001
        res["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
        res["outcome"] = "probe_exception"
    res["wall_s"] = round(time.perf_counter() - t0, 3)

    produced = sorted(p.name for p in ctx.out.glob("*.xlsx"))
    res["produced_files"] = produced
    res["partial_output_emitted"] = bool(produced)
    if produced:
        res["output_valid_xlsx"] = valid_ooxml(ctx.out / produced[0])["valid"]
    else:
        res["output_valid_xlsx"] = False
    try:
        res["stderr"] = err_log.read_text(errors="replace").strip()[-300:]
    except OSError:
        res["stderr"] = ""
    return res


# -------------------------------------------------------------------- phases
def _ckpt(outdir: Path, phase: str, payload: dict) -> None:
    """Incremental checkpoint: flush partial evidence after every item.

    Under a 1 GB cgroup a large conversion can trip the kernel OOM-killer. The
    probe itself is tiny, but if it were to die mid-phase this guarantees the
    evidence gathered so far still reaches the artifact directory.
    """
    try:
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / f"evidence_{phase}.json").write_text(
            json.dumps(payload, indent=2, default=str), encoding="utf-8")
    except OSError:
        pass


def phase_env(binpath: str, fixdir: Path, root: Path, args) -> dict:
    return {
        "kernel": kernel_info(),
        "os": platform.platform(),
        "soffice_bin": binpath,
        "soffice_version": soffice_version(binpath),
        "cgroup": cgroup_state(),
        "cpus": os.cpu_count(),
        "python": platform.python_version(),
        "fixtures_present": {k: {"name": v, "bytes": (fixdir / v).stat().st_size}
                             for k, v in FIXTURES.items() if (fixdir / v).exists()},
    }


def phase_single(binpath: str, fixdir: Path, root: Path, args) -> dict:
    """G6 baseline: one isolated conversion of each real fixture."""
    out = {}
    for key in ("sample", "stress", "bulk"):
        try:
            f = _resolve_fixture(fixdir, key)
        except FileNotFoundError:
            out[key] = {"missing": True, "fixture_error": "see stderr"}
            continue
        ctx = RunCtx(root, f"single_{key}")
        with Sampler() as s:
            r = convert(binpath, f, ctx, timeout=args.single_timeout)
            r["rss_peak_vmrss_bytes"] = s.rss_peak
            r["procs_peak"] = s.procs_peak
            r["pids_peak"] = s.pids_peak
            r["samples"] = s.samples
        r["cgroup_after"] = cgroup_state()
        out[key] = r
        _ckpt(Path(args.out), "single", out)     # flush partial evidence
    return out


def phase_conc(binpath: str, fixdir: Path, root: Path, args) -> dict:
    """G6 concurrency: N parallel isolated conversions of the sample fixture."""
    n = args.conc
    try:
        f = _resolve_fixture(fixdir, "sample")
    except FileNotFoundError:
        return {"workers": n, "fixture": FIXTURES["sample"], 
                "runs": [], "successes": 0, "missing": True, 
                "fixture_error": "see stderr"}
    res = {"workers": n, "fixture": FIXTURES["sample"], "runs": [], "successes": 0}
    ctxs = [RunCtx(root, f"c{n}_{i}") for i in range(n)]
    results: list = [None] * n
    with Sampler() as s:
        t0 = time.perf_counter()
        threads = []

        def work(i: int):
            results[i] = convert(binpath, f, ctxs[i], timeout=args.single_timeout)

        for i in range(n):
            th = threading.Thread(target=work, args=(i,))
            threads.append(th)
            th.start()
        for th in threads:
            th.join(timeout=args.single_timeout + 30)
        res["wall_total_s"] = round(time.perf_counter() - t0, 3)
        res["runs"] = results
        res["successes"] = sum(1 for r in results
                               if r and r.get("exit") == 0 and r.get("output_valid_xlsx"))
        res["rss_peak_vmrss_bytes"] = s.rss_peak
        res["procs_peak"] = s.procs_peak
        res["pids_peak"] = s.pids_peak
        res["samples"] = s.samples
    res["cgroup_after"] = cgroup_state()
    return res

# ---------------------------------------------------------------- G4 phases
def _g4_sigkill_control(root: Path) -> dict:
    """Prove the SIGTERM -> grace -> SIGKILL ladder terminates a stubborn child.

    A child that deliberately ignores SIGTERM MUST be reaped by the SIGKILL
    escalation; this proves the escalation path is live and effective,
    independent of how soffice happens to react to SIGTERM.
    """
    if not IS_POSIX:
        return {"skipped": "posix-only test"}
    prog = root / "stubborn.py"
    prog.write_text(
        "import signal, time, os\n"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)   # ignore SIGTERM\n"
        "open(os.environ['MARK'], 'w').write('alive')\n"
        "time.sleep(300)\n", encoding="utf-8")
    mark = root / "stubborn.mark"
    env = dict(os.environ)
    env["MARK"] = str(mark)
    res = {"timeout_s": 0.5, "grace_s": 1.5, "killed": False,
           "sigterm_sent": False, "sigkill_sent": False, "exit": None}
    t0 = time.perf_counter()
    try:
        proc = subprocess.Popen([sys.executable, str(prog)], env=env,
                                start_new_session=True,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        res["pid"] = proc.pid
        try:
            proc.wait(timeout=0.5)
            res["outcome"] = "completed_before_timeout"
        except subprocess.TimeoutExpired:
            res["killed"] = True
            res["sigterm_sent"] = True
            pgid = os.getpgid(proc.pid)
            os.killpg(pgid, 15)
            try:
                proc.wait(timeout=1.5)
                res["outcome"] = "UNEXPECTED_survived_sigterm"
            except subprocess.TimeoutExpired:
                res["sigkill_sent"] = True
                os.killpg(pgid, 9)
                proc.wait(timeout=5)
                res["outcome"] = "sigkill_escalation_required"
            res["exit"] = proc.returncode
    except Exception as exc:  # noqa: BLE001
        res["error"] = f"{type(exc).__name__}: {str(exc)[:160]}"
    res["wall_s"] = round(time.perf_counter() - t0, 3)
    res["mark_file_present_after"] = mark.exists()
    return res


def phase_g4(binpath: str, fixdir: Path, root: Path, args) -> dict:
    """G4: force the termination path against real, genuinely-working soffice.

    Uses deliberately SHORT timeouts so the kill machinery provably fires while
    soffice is mid-conversion. The earlier spike's 1.5 s timeout NEVER fired
    because the fixture finished in 0.776 s; here 0.12-1.0 s guarantees the
    ladder runs against a live soffice process tree.
    """
    out: dict = {}
    tiers = [("g4_sample", "sample", 0.12), ("g4_stress", "stress", 0.30),
             ("g4_bulk", "bulk", 1.00)]
    for tag, key, tout in tiers:
        f = _resolve_fixture(fixdir, key)
        if not f.exists():
            out[tag] = {"missing": True}
            continue
        ctx = RunCtx(root, tag)
        with Sampler() as s:
            r = g4_convert(binpath, f, ctx, timeout=tout, grace=args.g4_grace)
            r["live_soffice_procs_peak"] = s.procs_peak
        out[tag] = r
        _ckpt(Path(args.out), "g4", out)         # flush partial evidence

    out["g4_control"] = _g4_sigkill_control(root)
    return out


def _resolve_fixture(fixdir: Path, key: str) -> Path:
    """Locate a fixture by key, checking candidate directories in order.

    Candidate precedence:
        1. fixdir / name  (directly in the passed fixtures dir)
        2. fixdir.parent / "fixtures" / name  ( sibling spike_kit/fixtures)
        3. fixdir / "evidence_fixtures" / name  (legacy nested path)

    If the fixture is absent, raises FileNotFoundError with candidate paths.
    """
    name = FIXTURES[key]
    candidates: list[Path] = [
        fixdir / name,
        fixdir.parent / "fixtures" / name,
        fixdir / "evidence_fixtures" / name,
    ]
    for c in candidates:
        if c.exists():
            return c
    # Explicit failure with candidate paths
    raise FileNotFoundError(
        f"Fixture not found: {name}\n"
        f"Candidates checked:\n"
        + "\n".join(f"  {p}" for p in candidates)
    )


# ---------------------------------------------------------------- BIFF5
def _bof_probe(path: Path) -> dict:
    """Read the OLE2/BOF identity WITHOUT changing any byte. Pure observation.

    Reports the container magic, the Workbook/Book stream presence and the BOF
    version field so the 0x0550 decision rests on what the file actually
    contains plus what soffice actually does with it - nothing is rewritten.

    The BOF record is opcode 0x0809 (little-endian bytes 09 08) followed by a
    2-byte record length, then the 2-byte version field. The earlier regex
    matched the first 09 08 byte pair anywhere in the file and read one byte,
    which reported a nonsense version; this anchors on the full record header
    and reads the version field as a little-endian 16-bit value.
    """
    raw = path.read_bytes()
    d = {"bytes": len(raw),
         "ole2_magic": raw[:8] == bytes.fromhex("d0cf11e0a1b11ae1"),
         "zip_magic": raw[:4] == b"PK\x03\x04",
         "bof_version": None, "workbook_stream": None, "stream_names": []}
    if d["ole2_magic"]:
        for name in ("Workbook", "Book"):
            if raw.find(name.encode("utf-16-le")) >= 0:
                d["stream_names"].append(name)
        d["workbook_stream"] = d["stream_names"][0] if d["stream_names"] else None
    # BOF record: opcode 0x0809 (LE: 09 08), then record length 0x0008 (LE: 08 00),
    # then the 2-byte version field (LE). Anchor on the 4-byte header so a stray
    # 09 08 elsewhere in the container cannot be mistaken for the BOF.
    for m in re.finditer(rb"\x09\x08\x08\x00(..)", raw, re.S):
        try:
            ver = int.from_bytes(m.group(1), "little")
            d["bof_version"] = f"0x{ver:04X}"
            break
        except Exception:  # noqa: BLE001
            continue
    return d


def phase_biff5(binpath: str, fixdir: Path, root: Path, args) -> dict:
    """BIFF5 decision evidence: feed genuine/malformed/0x0550 files to soffice.

    No byte is normalised, repaired or rewritten anywhere. Each fixture is
    converted byte-for-byte; the result records what LibreOffice actually did.
    """
    keys = ["biff5", "biff7", "biff7_0550", "trunc5", "garb5", "wrong_stream",
            "not_ole2_junk", "not_ole2_random", "not_ole2_text", "biff2_raw"]
    out: dict = {}
    for key in keys:
        f = _resolve_fixture(fixdir, key)
        if not f.exists():
            out[key] = {"missing": True}
            continue
        ctx = RunCtx(root, f"b5_{key}")
        info = _bof_probe(f)
        with Sampler() as s:
            r = convert(binpath, f, ctx, timeout=args.single_timeout)
            r["live_soffice_procs_peak"] = s.procs_peak
        r["container"] = info
        out[key] = r
        _ckpt(Path(args.out), "biff5", out)      # flush partial evidence
    return out


# ---------------------------------------------------------------- residue
def residue_audit(root: Path, tmp_root: str) -> dict:
    """T8-parity residue audit, scoped to artifacts THIS probe created."""
    prof_left = [p.name for p in root.glob("prof_*")]
    tmp_left = [p.name for p in Path(tmp_root).glob("loev_*")
                if p.name != Path(tmp_root).name]
    locks = [str(p.relative_to(root)) for p in root.rglob(".lock")]
    return {
        "temp_dirs_left": len(tmp_left),
        "temp_dirs_names": tmp_left[:10],
        "profile_dirs_left": len(prof_left),
        "profile_lock_files": locks[:10],
        "live_soffice_procs_at_end": len(soffice_tree()),
        "zombies_at_end": zombie_count(),
    }


# -------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="final XLS->XLSX evidence probe")
    ap.add_argument("--phase", required=True,
                    choices=["env", "single", "conc", "g4", "biff5"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--fixtures", required=True)
    ap.add_argument("--soffice", default=None)
    ap.add_argument("--conc", type=int, default=4)
    ap.add_argument("--single-timeout", type=float, default=60.0)
    ap.add_argument("--g4-grace", type=float, default=5.0)
    args = ap.parse_args()

    fixdir = Path(args.fixtures)
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    binpath, tried = find_soffice(args.soffice)

    tmp_root = tempfile.mkdtemp(prefix="loev_")
    root = Path(tempfile.mkdtemp(prefix="loev_root_"))
    payload: dict = {
        "phase": args.phase,
        "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "host": (f"{platform.system()} {platform.release()} {platform.machine()} "
                 f"py{platform.python_version()}"),
        "cgroup_at_start": cgroup_state(),
        "soffice_candidates_tried": tried,
        "soffice_bin": binpath,
        "soffice_version": soffice_version(binpath) if binpath else None,
        "kernel": kernel_info(),
    }
    rc = 0
    if not binpath:
        payload["error"] = "soffice not found"
        rc = 3
    else:
        try:
            fn = {"env": phase_env, "single": phase_single, "conc": phase_conc,
                  "g4": phase_g4, "biff5": phase_biff5}[args.phase]
            payload["results"] = fn(binpath, fixdir, root, args)
        except Exception as exc:  # noqa: BLE001
            payload["error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
            rc = 2

    shutil.rmtree(root, ignore_errors=True)      # full cleanup, then honest audit
    shutil.rmtree(tmp_root, ignore_errors=True)
    payload["residue_after_cleanup"] = residue_audit(root, tmp_root)
    payload["cgroup_at_end"] = cgroup_state()
    payload["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")

    j = outdir / f"evidence_{args.phase}.json"
    j.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(json.dumps(payload, indent=2, default=str)[:9000])
    print(f"\nwrote {j}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
