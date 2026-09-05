"""
PROJECT: CONVERIGO
TEST SUITE: Certified Spreadsheet Cluster - Factory Harness Pilot (F0)

Jalur 2 Factory Batch Plan, F0 deliverable 3: ONE parametric test file per
cluster using the shared factory harness (tests/certified/_factory_harness.py).
F0 adds NO new converters - this pilot proves the harness end-to-end on the
seven certified spreadsheet slugs already in production (SPR-01, SPR-02,
SPR-05, SPR-06, SPR-07, SPR-08, SPR-17), with the uniform factory contract:

    plugin discovered -> POST /convert 201 -> GET /download 200 ->
    output content verified -> honest 422 UNSUPPORTED_CONVERSION for
    unsupported input
"""

from __future__ import annotations

import json
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
    ROWS,
    _assert_rows_equivalent,
    _read_rows_from_csv,
    _read_rows_from_json,
    _read_rows_from_xlsx,
    _write_csv,
    _write_json,
    _write_xlsx,
)

# ---------------------------------------------------------------------------
# Case table: (slug, target_format, fixture_builder, content_verifier)
# ---------------------------------------------------------------------------


def _verify_csv_rows(path: Path) -> None:
    _assert_rows_equivalent(_read_rows_from_csv(path), ROWS)


def _verify_xlsx_rows(path: Path) -> None:
    _assert_rows_equivalent(_read_rows_from_xlsx(path), ROWS)


def _verify_json_rows(path: Path) -> None:
    records = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(records, list) and records, records
    _assert_rows_equivalent(records, ROWS)


def _verify_html_table(path: Path) -> None:
    html = path.read_text(encoding="utf-8")
    assert "<table" in html, html[:200]
    assert "alpha" in html and "beta" in html, "row names missing from HTML"
    assert "95.5" in html, "row values missing from HTML"


CASES = [
    ("xlsx-to-csv", "csv", _write_xlsx, _verify_csv_rows),
    ("csv-to-xlsx", "xlsx", _write_csv, _verify_xlsx_rows),
    ("csv-to-json", "json", _write_csv, _verify_json_rows),
    ("json-to-csv", "csv", _write_json, _verify_csv_rows),
    ("xlsx-to-json", "json", _write_xlsx, _verify_json_rows),
    ("json-to-xlsx", "xlsx", _write_json, _verify_xlsx_rows),
    ("xlsx-to-html", "html", _write_xlsx, _verify_html_table),
]

SPREADSHEET_MIMES = {
    "csv": "text/csv",
    "json": "application/json",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def _fixture_for(builder, suffix: str, tmp_path: Path) -> Path:
    fixture = builder(tmp_path / f"factory_fixture.{suffix}")
    assert fixture.is_file(), f"fixture builder produced no file: {fixture}"
    return fixture


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.certified
@pytest.mark.parametrize(
    "slug,target_format,expected_source",
    [(slug, target, slug.split("-to-")[0]) for slug, target, _, _ in CASES],
)
def test_factory_plugin_discovered(slug: str, target_format: str, expected_source: str) -> None:
    """Each factory-cluster slug is registered with its (source, target) pair."""
    assert_slug_discovered(slug, expected_source, target_format)


@pytest.mark.certified
@pytest.mark.parametrize(
    "slug,target_format,builder,verifier",
    [pytest.param(slug, target, builder, verifier, id=slug) for slug, target, builder, verifier in CASES],
)
def test_factory_happy_path_uniform_contract(
    slug: str,
    target_format: str,
    builder,
    verifier,
    tmp_path: Path,
) -> None:
    """Uniform pipeline: 201 -> download 200 -> content verified per case."""
    fixture = _fixture_for(builder, slug.split("-to-")[0], tmp_path)
    output = run_happy_path(
        fixture,
        target_format,
        slug,
        mime=SPREADSHEET_MIMES[slug.split("-to-")[0]],
    )
    try:
        verifier(output)
    finally:
        cleanup_output(output)


@pytest.mark.certified
@pytest.mark.parametrize(
    "slug,target_format",
    [(slug, target) for slug, target, _, _ in CASES],
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
        mime="text/plain",
        filename="sample.txt",
    )
    assert_honest_unsupported(response)
