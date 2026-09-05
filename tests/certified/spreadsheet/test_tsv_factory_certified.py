"""
PROJECT: CONVERIGO
TEST SUITE: Certified TSV Data Cluster - Factory Batch F1 (Jalur 2)

Factory Batch Plan F1 (cluster G-A net-new): the two TSV converters
(SPR-14 tsv-to-csv, SPR-15 csv-to-tsv) built on the F0 factory base
(app/factory/plugin_base.py).  ONE parametric test file for the whole F1
batch, using the shared factory harness uniform contract:

    plugin discovered -> POST /convert 201 -> GET /download 200 ->
    output content verified -> honest 422 UNSUPPORTED_CONVERSION

Governance note: the four remaining G-A candidates (SPR-01 xlsx-to-csv,
SPR-02 csv-to-xlsx, SPR-05 csv-to-json, SPR-06 json-to-csv) were already
installed and certified before F1; they are covered by the F0 pilot
(test_spreadsheet_factory_certified.py).
"""

from __future__ import annotations

import csv as csv_mod
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
    _write_csv,
)


def _write_tsv(path: Path) -> Path:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv_mod.DictWriter(handle, fieldnames=list(ROWS[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(ROWS)
    return path


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


def _verify_csv_rows(path: Path) -> None:
    _assert_rows_equivalent(_read_rows_from_csv(path), ROWS)


def _verify_tsv_rows(path: Path) -> None:
    _assert_rows_equivalent(_read_rows_from_tsv(path), ROWS)


# ---------------------------------------------------------------------------
# Case table: (slug, target_format, fixture_builder, content_verifier)
# ---------------------------------------------------------------------------

CASES = [
    ("tsv-to-csv", "csv", _write_tsv, _verify_csv_rows),
    ("csv-to-tsv", "tsv", _write_csv, _verify_tsv_rows),
]

MIMES = {
    "tsv": "text/tab-separated-values",
    "csv": "text/csv",
}


@pytest.mark.certified
@pytest.mark.parametrize(
    "slug,target_format,expected_source",
    [(slug, target, slug.split("-to-")[0]) for slug, target, _, _ in CASES],
)
def test_factory_plugin_discovered(slug: str, target_format: str, expected_source: str) -> None:
    """Each F1 slug is registered with its (source, target) pair."""
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