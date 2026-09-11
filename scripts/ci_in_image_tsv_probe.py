"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / F1)
Version : 1.0.0

In-image probe for Factory Batch F1 (cluster G-A: TSV <-> CSV).

Executed INSIDE the production image by docker-runtime-verify step [4/5]:

    python scripts/ci_in_image_tsv_probe.py tests/sample.tsv tests/sample.csv

For each fixture the matching factory plugin is resolved through the real
registry, the conversion runs against a temp working dir, and the output is
parsed and compared against the source rows.  Exit code 0 = PASS.

The RAR probe (scripts/ci_in_image_rar_probe.py) remains the default for
archive batches; this probe is selected via the probe_script dispatch input.
"""
from __future__ import annotations

import csv as csv_mod
import io
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.plugins.registry import registry  # noqa: E402


def _read_rows(payload: bytes, delimiter: str) -> list[dict]:
    return list(csv_mod.DictReader(
        io.StringIO(payload.decode("utf-8")), delimiter=delimiter))


def _run(slug: str, fixture: Path, target_format: str,
         src_delim: str, out_delim: str) -> None:
    assert registry.has_slug(slug), f"{slug} not registered"
    plugin = registry.by_slug[slug]
    source_rows = _read_rows(fixture.read_bytes(), src_delim)
    import asyncio

    with tempfile.TemporaryDirectory(prefix="f1_probe_") as tmp:
        output = asyncio.run(plugin.convert(fixture, target_format))
        assert output.is_file(), f"{slug}: no output file {output}"
        out_rows = _read_rows(output.read_bytes(), out_delim)
        assert out_rows == source_rows, f"{slug}: content mismatch"
        print(f"PROBE {slug}: {fixture.name} -> {output.name} "
              f"({len(out_rows)} rows) OK")


def _ensure_fixture(path_hint: str | None, kind: str, tmp: str) -> Path:
    """Use the hinted fixture when present; otherwise generate one.

    The docker image is built from the git checkout, so gitignored sample
    files (tests/sample.csv is intentionally ignored) are absent in-image;
    the probe therefore generates its own fixtures when needed.
    """
    if path_hint:
        candidate = Path(path_hint)
        if candidate.is_file():
            return candidate
    rows = [
        {"id": "1", "name": "alpha", "score": "95.5", "active": "True"},
        {"id": "2", "name": "beta", "score": "87.25", "active": "False"},
        {"id": "3", "name": "gamma", "score": "42.0", "active": "True"},
    ]
    header = ["id", "name", "score", "active"]
    generated = Path(tmp) / f"probe_fixture.{kind}"
    with generated.open("w", encoding="utf-8", newline="") as handle:
        writer = csv_mod.DictWriter(
            handle, fieldnames=header,
            delimiter="\t" if kind == "tsv" else ",")
        writer.writeheader()
        writer.writerows(rows)
    return generated


def main(argv: list[str]) -> int:
    with tempfile.TemporaryDirectory(prefix="f1_probe_") as tmp:
        tsv_hint = next((a for a in argv if a.lower().endswith(".tsv")), None)
        csv_hint = next((a for a in argv if a.lower().endswith(".csv")), None)
        tsv = _ensure_fixture(tsv_hint, "tsv", tmp)
        csv_f = _ensure_fixture(csv_hint, "csv", tmp)
        _run("tsv-to-csv", tsv, "csv", "\t", ",")
        _run("csv-to-tsv", csv_f, "tsv", ",", "\t")
    print("F1 IN-IMAGE PROBE PASS: tsv-to-csv + csv-to-tsv round-trips OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))