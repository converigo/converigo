"""
PROJECT: CONVERIGO
TEST SUITE: Certified Excel/HTML Output Cluster - Factory Batch F5 (Jalur 2)

Factory Batch F5 (cluster G-E): the two net-new data-output converters
(SPR-16 xlsx-to-tsv, SPR-19 csv-to-html) built on the F0 factory base
(app/factory/plugin_base.py), plus the D9 wire-up proof for the three
certified-but-pageless spreadsheet slugs (json-to-xlsx, xlsx-to-json,
xlsx-to-html).  ONE parametric test file for the whole F5 batch, using
the shared factory harness uniform contract:

    plugin discovered -> POST /convert 201 -> GET /download 200 ->
    output content verified -> honest 422 UNSUPPORTED_CONVERSION

Governance note: the wire-up trio was already installed and certified
before F5 (F0 pilot); F5 adds landing pages for all three and contracts
for the slugs whose regression sample is tracked in git (tests/sample.xlsx
- the F4-validated contract policy).  json-to-xlsx stays page-only
(no tests/sample.json exists anywhere in the repo).
"""

from __future__ import annotations

import csv as csv_mod
import json
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest

from tests.certified._factory_harness import (
    assert_honest_unsupported,
    assert_slug_discovered,
    cleanup_output,
    post_convert,
    run_happy_path,
)
from tests.certified.spreadsheet._helpers import (
    CSV_COLUMNS,
    ROWS,
    _assert_rows_equivalent,
    _write_csv,
    _write_xlsx,
)


def _read_rows_from_tsv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv_mod.DictReader(handle, delimiter="\t"))
    return [
        {
            "id": int(r["id"]),
            "name": str(r["name"]),
            "score": float(r["score"]),
            "active": str(r["active"]).strip().lower() in ("true", "1"),
        }
        for r in rows
    ]


def _verify_tsv_rows(path: Path) -> None:
    _assert_rows_equivalent(_read_rows_from_tsv(path), ROWS)


class _TableParser(HTMLParser):
    """Minimal stdlib HTML table extractor (no external deps)."""

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):  # noqa: ANN001 - stdlib signature
        if tag == "tr":
            self._row = []
        if tag in ("td", "th"):
            self._cell = []

    def handle_endtag(self, tag):  # noqa: ANN001 - stdlib signature
        if tag in ("td", "th") and self._row is not None and self._cell is not None:
            self._row.append("".join(self._cell))
            self._cell = None
        if tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):  # noqa: ANN001 - stdlib signature
        if self._cell is not None:
            self._cell.append(data)


def _verify_html_table(path: Path) -> None:
    parser = _TableParser()
    parser.feed(path.read_text(encoding="utf-8"))
    assert len(parser.rows) == 1 + len(ROWS), (
        f"expected header + {len(ROWS)} body rows, got {len(parser.rows)}: {parser.rows}"
    )
    assert parser.rows[0] == CSV_COLUMNS, parser.rows[0]
    for parsed, expected in zip(parser.rows[1:], ROWS):
        assert parsed == [str(expected[col]) for col in CSV_COLUMNS], parsed


# ---------------------------------------------------------------------------
# Case table: (slug, target_format, fixture_builder, content_verifier)
# ---------------------------------------------------------------------------

NET_NEW_CASES = [
    ("xlsx-to-tsv", "tsv", _write_xlsx, _verify_tsv_rows),
    ("csv-to-html", "html", _write_csv, _verify_html_table),
]

WIRE_UP_SLUGS = ["json-to-xlsx", "xlsx-to-json", "xlsx-to-html"]
CONTRACT_SLUGS = ["csv-to-html", "xlsx-to-tsv", "xlsx-to-json", "xlsx-to-html"]
PAGE_ONLY_SLUGS = ["json-to-xlsx"]

MIMES = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv",
    "txt": "text/plain",
}


@pytest.mark.certified
@pytest.mark.parametrize(
    "slug,target_format,expected_source",
    [(slug, target, slug.split("-to-")[0]) for slug, target, _, _ in NET_NEW_CASES],
)
def test_factory_plugin_discovered(slug: str, target_format: str, expected_source: str) -> None:
    """Each F5 net-new slug is registered with its (source, target) pair."""
    assert_slug_discovered(slug, expected_source, target_format)


@pytest.mark.certified
@pytest.mark.parametrize(
    "slug,target_format,builder,verifier",
    [pytest.param(slug, target, builder, verifier, id=slug) for slug, target, builder, verifier in NET_NEW_CASES],
)
def test_factory_happy_path_uniform_contract(
    slug: str,
    target_format: str,
    builder,
    verifier,
    tmp_path: Path,
) -> None:
    """Uniform pipeline: 201 -> download 200 -> content verified per case."""
    fixture = builder(tmp_path / f"factory_fixture.{slug.split('-to-')[0]}")
    assert fixture.is_file(), f"fixture builder produced no file: {fixture}"
    output = run_happy_path(
        fixture,
        target_format,
        slug,
        mime=MIMES[slug.split("-to-")[0]],
    )
    try:
        verifier(output)
    finally:
        cleanup_output(output)


@pytest.mark.certified
@pytest.mark.parametrize(
    "slug,target_format",
    [(slug, target) for slug, target, _, _ in NET_NEW_CASES],
)
def test_factory_honest_error_for_unsupported_input(
    slug: str,
    target_format: str,
) -> None:
    """Wrong-extension input gets the honest 422 error class - never fake output."""
    response = post_convert(
        Path("tests/sample.txt"),
        target_format,
        slug,
        mime=MIMES["txt"],
        filename="sample.txt",
    )
    assert_honest_unsupported(response)


@pytest.mark.certified
def test_factory_honest_error_for_corrupt_xlsx(tmp_path: Path) -> None:
    """A PK-prefixed garbage file that passes the upload signature gate must
    still fail honestly (422 UNSUPPORTED_CONVERSION), never 500/fake output."""
    corrupt = tmp_path / "corrupt.xlsx"
    corrupt.write_bytes(b"PK\x03\x04" + b"this is not a real zip archive" * 8)
    response = post_convert(corrupt, "tsv", "xlsx-to-tsv", mime=MIMES["xlsx"])
    assert_honest_unsupported(response)


@pytest.mark.certified
def test_wireup_slugs_still_registered() -> None:
    """D9 regression smoke: the three certified wire-up slugs stay registered
    with their exact pairs (converter code untouched by F5)."""
    expected = {
        "json-to-xlsx": ("json", "xlsx"),
        "xlsx-to-json": ("xlsx", "json"),
        "xlsx-to-html": ("xlsx", "html"),
    }
    for slug, (source, target) in expected.items():
        assert_slug_discovered(slug, source, target)


@pytest.mark.certified
def test_d9_page_artifacts_shipped() -> None:
    """All five F5 slugs ship landing pages; each is valid certified JSON."""
    converters_dir = Path("app/data/converters")
    for slug in [slug for slug, *_ in NET_NEW_CASES] + WIRE_UP_SLUGS:
        page_path = converters_dir / f"{slug}.json"
        assert page_path.is_file(), f"missing page artifact: {page_path.name}"
        payload = json.loads(page_path.read_text(encoding="utf-8"))
        assert payload.get("slug") == slug, payload.get("slug")
        assert payload.get("lifecycle_status") == "certified", payload.get("lifecycle_status")


@pytest.mark.certified
def test_d9_contract_policy() -> None:
    """Contracts ship exactly for the slugs with a tracked regression sample;
    json-to-xlsx (no tests/sample.json anywhere) stays page-only - the
    F4-validated contract policy."""
    converters_dir = Path("app/data/converters")
    for slug in CONTRACT_SLUGS:
        contract_path = converters_dir / f"{slug}.contract.json"
        assert contract_path.is_file(), f"missing contract artifact: {contract_path.name}"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        assert contract["regression_sample"], contract
        assert Path(contract["regression_sample"]).is_file(), contract["regression_sample"]
    for slug in PAGE_ONLY_SLUGS:
        contract_path = converters_dir / f"{slug}.contract.json"
        assert not contract_path.exists(), f"unexpected contract artifact: {contract_path.name}"


@pytest.mark.certified
def test_static_target_map_f5_rows() -> None:
    """The deployed STATIC_TARGET_MAP rows reflect the F5 delta: xlsx gains
    TSV, csv gains HTML; html stays download-only (target-only)."""
    html_text = Path("app/templates/main/converigo_main.html").read_text(encoding="utf-8")
    block = html_text.split("const STATIC_TARGET_MAP = {", 1)[1].split("};", 1)[0]
    mapping: dict[str, list[str]] = {}
    for key, values in re.findall(r"(['\"a-zA-Z0-9_]+):\[(.*?)\]", block):
        mapping[key.strip("'\"")] = [
            v.strip().strip("'\"") for v in values.split(",") if v.strip()
        ]

    assert "TSV" in mapping.get("xlsx", []), mapping.get("xlsx")
    assert "HTML" in mapping.get("csv", []), mapping.get("csv")
    assert mapping.get("html") == [], "html must stay download-only"
    assert mapping.get("tsv") == ["CSV"], mapping.get("tsv")
