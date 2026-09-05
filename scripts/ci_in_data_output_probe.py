"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / F5)
Version : 1.0.0

In-image probe for Factory Batch F5 (cluster G-E: Excel/HTML data output).

Executed INSIDE the production image by docker-runtime-verify step [4/5]
(dispatch with probe_script=scripts/ci_in_data_output_probe.py):

    python scripts/ci_in_data_output_probe.py

All fixtures are generated in-image (openpyxl/csv modules), so the probe
is self-sufficient exactly like the F1-F4 probes.  The two F5 net-new
plugins are resolved through the real registry and executed through their
public async convert(); the three D9 wire-up slugs are conversion-smoked
and the page/contract artifact policy is asserted.  Exit code 0 = PASS.
"""
from __future__ import annotations

import asyncio
import csv as csv_mod
import json
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.plugins.registry import registry  # noqa: E402

ROWS = [
    {"id": "1", "name": "alpha", "score": "95.5", "active": "True"},
    {"id": "2", "name": "beta", "score": "87.25", "active": "False"},
    {"id": "3", "name": "gamma", "score": "42.0", "active": "True"},
]
HEADER = ["id", "name", "score", "active"]

NET_NEW = ["xlsx-to-tsv", "csv-to-html"]
WIRE_UP = ["json-to-xlsx", "xlsx-to-json", "xlsx-to-html"]
CONTRACTS = ["csv-to-html", "xlsx-to-tsv", "xlsx-to-json", "xlsx-to-html"]
PAGE_ONLY = ["json-to-xlsx"]


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        if tag in ("td", "th"):
            self._cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._row is not None and self._cell is not None:
            self._row.append("".join(self._cell))
            self._cell = None
        if tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def _build_csv(path: Path) -> Path:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv_mod.DictWriter(handle, fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(ROWS)
    return path


def _build_xlsx(path: Path) -> Path:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "data"
    sheet.append(HEADER)
    for row in ROWS:
        sheet.append([row[col] for col in HEADER])
    workbook.save(str(path))
    return path


def _build_json(path: Path) -> Path:
    path.write_text(json.dumps(ROWS), encoding="utf-8")
    return path


def _verify_tsv(payload: Path) -> None:
    with payload.open("r", encoding="utf-8", newline="") as handle:
        out_rows = list(csv_mod.DictReader(handle, delimiter="\t"))
    assert len(out_rows) == len(ROWS), f"tsv row count {len(out_rows)}"
    for got, want in zip(out_rows, ROWS):
        assert got["id"] == want["id"] and got["name"] == want["name"], got


def _verify_html(payload: Path) -> None:
    parser = _TableParser()
    parser.feed(payload.read_text(encoding="utf-8"))
    assert len(parser.rows) == 1 + len(ROWS), f"html row count {len(parser.rows)}"
    assert parser.rows[0] == HEADER, parser.rows[0]


def _verify_xlsx(payload: Path) -> None:
    import pandas as pd

    frame = pd.read_excel(payload)
    assert len(frame) == len(ROWS), f"xlsx row count {len(frame)}"
    assert list(frame.columns) == HEADER, list(frame.columns)


def _verify_json(payload: Path) -> None:
    data = json.loads(payload.read_text(encoding="utf-8"))
    assert len(data) == len(ROWS), data


async def _convert(slug: str, source: Path, target: str, working: Path) -> Path:
    plugin = registry.by_slug[slug]
    return await plugin.convert(source, target, output_dir=working)


def main() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="f5_probe_") as tmp:
        root = Path(tmp)
        csv_fixture = _build_csv(root / "probe_fixture.csv")
        xlsx_fixture = _build_xlsx(root / "probe_fixture.xlsx")
        json_fixture = _build_json(root / "probe_fixture.json")

        plan = [
            ("xlsx-to-tsv", xlsx_fixture, "tsv", _verify_tsv),
            ("csv-to-html", csv_fixture, "html", _verify_html),
            ("json-to-xlsx", json_fixture, "xlsx", _verify_xlsx),
            ("xlsx-to-json", xlsx_fixture, "json", _verify_json),
            ("xlsx-to-html", xlsx_fixture, "html", _verify_html),
        ]
        for slug, fixture, target, verifier in plan:
            try:
                assert registry.has_slug(slug), f"{slug} not registered"
                output_path = asyncio.run(_convert(
                    slug, fixture, target, root / f"out_{slug.replace('-', '_')}"
                ))
                assert output_path.is_file() and output_path.stat().st_size > 0
                verifier(output_path)
                print(f"F5 PROBE OK: {slug} ({fixture.suffix} -> {target})")
            except Exception as exc:  # noqa: BLE001 - probe reports all
                failures.append(f"{slug}: {type(exc).__name__}: {exc}")

        converters_dir = (
            Path(__file__).resolve().parent.parent / "app" / "data" / "converters"
        )
        for slug in NET_NEW + WIRE_UP:
            page = converters_dir / f"{slug}.json"
            if page.exists():
                print(f"F5 PROBE OK: D9 page artifact {page.name}")
            else:
                failures.append(f"D9 page artifact missing: {page.name}")
        for slug in CONTRACTS:
            contract = converters_dir / f"{slug}.contract.json"
            if contract.exists():
                print(f"F5 PROBE OK: contract artifact {contract.name}")
            else:
                failures.append(f"contract artifact missing: {contract.name}")
        for slug in PAGE_ONLY:
            contract = converters_dir / f"{slug}.contract.json"
            if contract.exists():
                failures.append(f"unexpected contract artifact (page-only policy): {contract.name}")

    if failures:
        print("F5 PROBE: FAIL")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("F5 PROBE: PASS (5/5 data-output converters verified in-image)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
