"""
PROJECT: CONVERIGO
TEST SUITE: Certified Spreadsheet / Data Pipeline Converters (Batch 1)
STATUS: DEVELOPMENT (certification pending evidence review)

Coverage: SPR-01 xlsx-to-csv, SPR-02 csv-to-xlsx, SPR-05 csv-to-json,
SPR-06 json-to-csv, SPR-07 xlsx-to-json, SPR-08 json-to-xlsx, SPR-17 xlsx-to-html.

Pipeline: real files (XLSX via openpyxl, CSV/JSON text) uploaded through the
/convert API -> registry slug resolution -> plugin convert() -> download
artifact, with content verification on every output.

Licensing: pandas (BSD-3-Clause), openpyxl (MIT) - both safe.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.settings import settings
from app.main import app
from app.plugins.registry import registry
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

OUTPUT_DIR = settings.OUTPUT_DIR


def _resolve_public_output_path(response) -> Path:
    payload = response.json()
    download_path = payload.get("download_path")
    assert download_path, payload
    assert download_path.startswith("/download/")
    relative_parts = Path(download_path.removeprefix("/download/")).parts
    assert len(relative_parts) == 2, f"Unexpected download path shape: {download_path}"
    conversion_id, filename = relative_parts
    output_path = OUTPUT_DIR / conversion_id / filename
    assert output_path.exists(), f"Expected output file not found: {output_path}"
    return output_path


def _convert_via_api(source_path: Path, target_format: str, operation: str) -> Path:
    client = TestClient(app)
    mime_types = {
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv",
        "json": "application/json",
    }
    suffix = source_path.suffix.lstrip(".").lower()
    with source_path.open("rb") as handle:
        response = client.post(
            "/convert",
            files={"file": (source_path.name, handle, mime_types[suffix])},
            data={"target_format": target_format, "operation": operation},
        )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload.get("status") == "success", payload
    assert payload.get("download_path"), payload
    return _resolve_public_output_path(response)

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.certified
def test_spreadsheet_plugins_discovered() -> None:
    """All 7 spreadsheet plugins are registered with slug + pair."""
    expected = {
        "xlsx-to-csv": ("xlsx", "csv"),
        "csv-to-xlsx": ("csv", "xlsx"),
        "csv-to-json": ("csv", "json"),
        "json-to-csv": ("json", "csv"),
        "xlsx-to-json": ("xlsx", "json"),
        "json-to-xlsx": ("json", "xlsx"),
        "xlsx-to-html": ("xlsx", "html"),
    }
    for slug, (source, target) in expected.items():
        plugin = registry.get_plugin(source, target, slug=slug)
        assert plugin is not None, f"{slug} not found in registry"
        assert plugin.slug == slug
        assert plugin.supports(source, target), f"{slug} fails supports() for {source}->{target}"


@pytest.mark.certified
def test_xlsx_to_csv_roundtrip(tmp_path: Path) -> None:
    source = _write_xlsx(tmp_path / "input.xlsx")
    output = _convert_via_api(source, "csv", "xlsx-to-csv")
    try:
        assert output.suffix.lower() == ".csv"
        rows = _read_rows_from_csv(output)
        _assert_rows_equivalent(rows, ROWS)
    finally:
        output.unlink(missing_ok=True)


@pytest.mark.certified
def test_csv_to_xlsx_roundtrip(tmp_path: Path) -> None:
    source = _write_csv(tmp_path / "input.csv")
    output = _convert_via_api(source, "xlsx", "csv-to-xlsx")
    try:
        assert output.suffix.lower() == ".xlsx"
        rows = _read_rows_from_xlsx(output)
        _assert_rows_equivalent(rows, ROWS)
    finally:
        output.unlink(missing_ok=True)


@pytest.mark.certified
def test_csv_to_json_roundtrip(tmp_path: Path) -> None:
    source = _write_csv(tmp_path / "input.csv")
    output = _convert_via_api(source, "json", "csv-to-json")
    try:
        assert output.suffix.lower() == ".json"
        rows = _read_rows_from_json(output)
        _assert_rows_equivalent(rows, ROWS)
    finally:
        output.unlink(missing_ok=True)


@pytest.mark.certified
def test_json_to_csv_roundtrip(tmp_path: Path) -> None:
    source = _write_json(tmp_path / "input.json")
    output = _convert_via_api(source, "csv", "json-to-csv")
    try:
        assert output.suffix.lower() == ".csv"
        rows = _read_rows_from_csv(output)
        _assert_rows_equivalent(rows, ROWS)
    finally:
        output.unlink(missing_ok=True)


@pytest.mark.certified
def test_xlsx_to_json_roundtrip(tmp_path: Path) -> None:
    source = _write_xlsx(tmp_path / "input.xlsx")
    output = _convert_via_api(source, "json", "xlsx-to-json")
    try:
        assert output.suffix.lower() == ".json"
        rows = _read_rows_from_json(output)
        _assert_rows_equivalent(rows, ROWS)
    finally:
        output.unlink(missing_ok=True)


@pytest.mark.certified
def test_json_to_xlsx_roundtrip(tmp_path: Path) -> None:
    source = _write_json(tmp_path / "input.json")
    output = _convert_via_api(source, "xlsx", "json-to-xlsx")
    try:
        assert output.suffix.lower() == ".xlsx"
        rows = _read_rows_from_xlsx(output)
        _assert_rows_equivalent(rows, ROWS)
    finally:
        output.unlink(missing_ok=True)


@pytest.mark.certified
def test_xlsx_to_html_roundtrip(tmp_path: Path) -> None:
    source = _write_xlsx(tmp_path / "input.xlsx")
    output = _convert_via_api(source, "html", "xlsx-to-html")
    try:
        assert output.suffix.lower() == ".html"
        html = output.read_text(encoding="utf-8")
        assert "<table" in html, "Output HTML has no <table>"
        for name in ("alpha", "beta", "gamma"):
            assert name in html, f"Missing row value {name} in HTML output"
    finally:
        output.unlink(missing_ok=True)
