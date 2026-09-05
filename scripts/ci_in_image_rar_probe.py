#!/usr/bin/env python3
"""
CI infrastructure (NOT converter code): in-image extraction probe used by
.github/workflows/docker-verify.yml (POINT 4/5 of the Docker runtime
verification checklist).

Opens real RAR fixtures from the libarchive project test corpus (vendored
under tests/fixtures/rar) with the image's own native libarchive via
libarchive-c, and asserts the extraction output is structurally valid:
member names, byte sizes and content sha256 prefixes must match the
known-good reference readings taken when the fixtures were vendored.

Runs INSIDE the production image (python:3.11-slim + libarchive13) to prove
the native runtime can read and extract real RAR4/RAR5 payloads.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import libarchive

# Reference readings per fixture (member name -> (size_bytes, sha256[:16])).
# Sources: tests/fixtures/rar/*, provenance and digests recorded in the
# Gate 2 runtime-verification evidence document (tmp/gate2_runtime_verification.md).
KNOWN_FIXTURES: dict[str, dict[str, tuple[int, str]]] = {
    "rar4_members.rar": {
        "LibarchiveAddingTest.html": (20111, "ee16390e87152d7d"),
        "testdir/test.txt": (20, "5a5f16e01faf8adf"),
        "testdir/LibarchiveAddingTest.html": (20111, "ee16390e87152d7d"),
    },
    "rar5_members.rar": {
        "test1.bin": (4096, "7d89f86f9f69d744"),
        "test2.bin": (4096, "f81e6fceeeab3663"),
        "test3.bin": (4096, "5e621f2b6ce8fed7"),
        "test4.bin": (4096, "2627f40180217252"),
    },
    "rar5_single.rar": {
        "helloworld.txt": (29, "fef9ad8cf601b43f"),
    },
}


def _fail(message: str) -> None:
    print(f"PROBE_FAIL: {message}")
    raise SystemExit(1)


def probe(fixture_arg: str) -> None:
    fixture = Path(fixture_arg)
    if not fixture.exists():
        _fail(f"fixture not found inside the image: {fixture}")

    expected = KNOWN_FIXTURES.get(fixture.name)

    files: dict[str, bytes] = {}
    non_files: list[str] = []
    with libarchive.file_reader(str(fixture)) as archive:
        for entry in archive:
            if entry.isfile:
                files[entry.pathname] = b"".join(entry.get_blocks())
            else:
                non_files.append(entry.pathname)

    print(f"== {fixture}: {len(files)} file member(s), "
          f"{len(non_files)} non-file member(s) {non_files or ''}")

    if not files:
        _fail(f"no file members extracted from {fixture}")

    if expected is not None:
        if set(files) != set(expected):
            _fail(
                f"member set mismatch for {fixture.name}: "
                f"actual={sorted(files)} expected={sorted(expected)}"
            )
        for name, (size, sha16) in expected.items():
            data = files[name]
            if len(data) != size:
                _fail(f"{fixture.name}:{name} size mismatch: "
                      f"actual={len(data)} expected={size}")
            digest16 = hashlib.sha256(data).hexdigest()[:16]
            if digest16 != sha16:
                _fail(f"{fixture.name}:{name} content mismatch: "
                      f"actual={digest16} expected={sha16}")
            print(f"   OK {name}: {len(data)} bytes sha256[:16]={digest16}")
    else:
        print("   OK (unknown fixture: >=1 file member required and present)")

    print(f"EXTRACT_OK {fixture.name}")


def main() -> None:
    fixtures = sys.argv[1:]
    if not fixtures:
        _fail("usage: ci_in_image_rar_probe.py <fixture.rar> [...]")
    for fixture_arg in fixtures:
        probe(fixture_arg)
    print("IN_IMAGE_RAR_PROBE_PASS")


if __name__ == "__main__":
    main()
