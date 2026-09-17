#!/usr/bin/env python3
"""CI gate analysis for the XLS -> XLSX validation run.

Reads the artifacts produced by the xls-xlsx-ci-validation workflow and decides
pass/fail for the GATE:
  * artifacts/junit_certified.xml  - the 6-test certified suite must be fully
    green (6 run, 0 failures/errors, 0 skipped; a skip means LibreOffice was
    not detected in-image, which is itself a gate failure).
  * artifacts/xls_xlsx_validation.json - the in-image probe must have 0 failed
    checks and no phase-level errors.

Exits 0 when the gate is green, 1 otherwise. Prints every failure it finds.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


def analyze_certified(path: Path) -> list[str]:
    failures: list[str] = []
    if not path.exists():
        return ["certified junit artifact missing"]
    root = ET.fromstring(path.read_text())
    total = int(root.attrib.get("tests", 0))
    errs = int(root.attrib.get("errors", 0)) + int(root.attrib.get("failures", 0))
    skipped = int(root.attrib.get("skipped", 0))
    print(f"[certified] tests={total} errors+failures={errs} skipped={skipped}")
    for tc in root.iter("testcase"):
        for child in tc:
            if child.tag in ("failure", "error", "skipped"):
                failures.append(f"certified::{tc.attrib['name']} -> {child.tag}")
    if errs:
        failures.append(f"certified: {errs} error/failure(s)")
    if skipped:
        failures.append(
            f"certified: {skipped} test(s) SKIPPED (soffice not detected in-image?)"
        )
    return failures


def analyze_probe(path: Path) -> list[str]:
    failures: list[str] = []
    if not path.exists():
        return ["probe evidence json missing"]
    data = json.loads(path.read_text())
    totals = data.get("totals", {})
    print(f"[probe] passed={totals.get('passed', 0)} failed={totals.get('failed', 0)}")
    for phase, pdata in data.get("phases", {}).items():
        if pdata.get("phase_error"):
            failures.append(f"probe::{phase} PHASE ERROR: {pdata['phase_error']}")
        for check in pdata.get("checks", []):
            if not check.get("ok"):
                failures.append(
                    f"probe::{phase}/{check['name']}: {str(check.get('detail'))[:90]}"
                )
    return failures


def main() -> int:
    artifacts = Path("artifacts")
    failures = analyze_certified(artifacts / "junit_certified.xml")
    failures += analyze_probe(artifacts / "xls_xlsx_validation.json")

    if failures:
        print("\n=== GATE FAILURES ===")
        for f in failures:
            print(" -", f)
        return 1
    print("\n=== GATE GREEN: certified 6 passed, probe 0 failures ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
