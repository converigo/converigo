"""
PROJECT: CONVERIGO
TEST SUITE: Certified ZIP Extract Converter (VAR-33 / Batch 5)
STATUS: CERTIFIED (Batch 5 evidence run — pending PC merge-gate approval)

Certified-level coverage for the ZIP extract converter (ZIPExtractPlugin
delegating to ArchiveEngine, with the Batch 5 fix that packages the
extracted directory into a downloadable ZIP via stdlib shutil.make_archive).

Verification: real-file sample (tests/sample.zip), plugin-level extraction
and repackaging, HTTP upload -> convert -> download pipeline, output is a
valid ZIP with identical member set and byte-identical member content,
single output file, honest error for non-zip input, security tests remain
in place (tests/certified/archive/test_zip_security.py).
"""

from __future__ import annotations

import asyncio
import io
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.settings import settings
from app.main import app
from app.plugins.registry import registry

SAMPLE_ZIP = Path("tests/sample.zip")
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


def _zip_members(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path, "r") as zf:
        return {
            name: zf.read(name)
            for name in zf.namelist()
            if not name.endswith("/")
        }


def _make_real_zip(tmp_path: Path, nested: bool = False) -> Path:
    zip_path = tmp_path / "batch5_sample.zip"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("alpha/one.txt", "batch5 one\n")
        zf.writestr("beta/two.txt", "batch5 two\n")
        if nested:
            zf.writestr("alpha/deep/three.txt", "batch5 three\n")
    zip_path.write_bytes(buffer.getvalue())
    return zip_path


def _convert(client, filename: str = "sample.zip"):
    assert SAMPLE_ZIP.exists(), f"Sample file is missing: {SAMPLE_ZIP}"
    with SAMPLE_ZIP.open("rb") as handle:
        return client.post(
            "/convert",
            files={"file": (filename, handle, "application/zip")},
            data={"target_format": "zip", "operation": "zip-extract"},
        )


@pytest.mark.certified
def test_zip_extract_plugin_discovered():
    """TEST 001: Plugin is properly registered and not a placeholder."""
    plugin = registry.get_plugin("zip", "zip", slug="zip-extract")
    assert plugin is not None
    assert plugin.slug == "zip-extract"
    assert plugin.engine == "archive"
    assert "zip" in plugin.source_formats
    assert "zip" in plugin.target_formats


@pytest.mark.certified
def test_zip_extract_plugin_returns_zip_file_not_directory(tmp_path: Path) -> None:
    """TEST 002 (Batch 5 fix): plugin returns a downloadable ZIP file, not a directory."""
    plugin = registry.get_plugin("zip", "zip", slug="zip-extract")
    src = _make_real_zip(tmp_path)
    output = asyncio.run(
        plugin.convert(src, "zip", output_dir=tmp_path / "out", temp_dir=tmp_path / "tmp")
    )
    assert isinstance(output, Path), "Plugin must return a Path"
    assert output.is_file(), (
        f"VAR-33 defect regressed: plugin returned a directory again ({output})"
    )
    assert output.suffix.lower() == ".zip"
    assert output.stat().st_size > 0
    assert zipfile.is_zipfile(output), "Repackaged output is not a valid ZIP"


@pytest.mark.certified
def test_zip_extract_conversion_success():
    """TEST 003: HTTP extraction succeeds and returns a download path."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload.get("status") == "success"
    assert payload.get("download_path"), payload


@pytest.mark.certified
def test_zip_extract_output_is_valid_zip_with_identical_members():
    """TEST 004: Output is a valid ZIP whose members match the sample byte-for-byte."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text
    output_path = _resolve_public_output_path(response)
    try:
        assert zipfile.is_zipfile(output_path), "Output is not a valid ZIP file"
        expected = _zip_members(SAMPLE_ZIP)
        actual = _zip_members(output_path)
        assert set(actual) == set(expected), (
            f"Member set mismatch: {sorted(actual)} != {sorted(expected)}"
        )
        for name, content in expected.items():
            assert actual[name] == content, f"Member content mismatch: {name}"
    finally:
        output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_zip_extract_download_served():
    """TEST 005: The repackaged ZIP is downloadable through /download."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text

    download_path = response.json()["download_path"]
    download_resp = client.get(download_path)
    assert download_resp.status_code == 200, download_resp.text
    assert download_resp.content, "Downloaded content is empty"
    assert zipfile.is_zipfile(io.BytesIO(download_resp.content)), (
        "Downloaded payload is not a valid ZIP"
    )
    assert "attachment" in download_resp.headers.get("content-disposition", "")

    _resolve_public_output_path(response).unlink(missing_ok=True)


@pytest.mark.certified
def test_zip_extract_single_output_file():
    """TEST 006: Exactly one ZIP output file is produced per conversion."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text
    conversion_id = Path(
        response.json()["download_path"].removeprefix("/download/")
    ).parts[0]
    files = list((OUTPUT_DIR / conversion_id).glob("*.zip"))
    assert len(files) == 1, f"Expected exactly one ZIP output, got: {files}"
    for f in files:
        f.unlink(missing_ok=True)


@pytest.mark.certified
@pytest.mark.parametrize("nested", [False, True])
def test_zip_extract_real_file_preserves_structure(tmp_path: Path, nested: bool) -> None:
    """TEST 007: Real-file parametrized — folder structure survives the round-trip."""
    plugin = registry.get_plugin("zip", "zip", slug="zip-extract")
    src = _make_real_zip(tmp_path, nested=nested)
    output = asyncio.run(
        plugin.convert(src, "zip", output_dir=tmp_path / "out", temp_dir=tmp_path / "tmp")
    )
    assert output.is_file() and zipfile.is_zipfile(output)
    actual = _zip_members(output)
    expected_names = {
        "alpha/one.txt",
        "beta/two.txt",
        *( ["alpha/deep/three.txt"] if nested else [] ),
    }
    assert expected_names <= set(actual), (
        f"Structure lost: {sorted(expected_names)} not in {sorted(actual)}"
    )
    assert actual["alpha/one.txt"] == b"batch5 one\n"


@pytest.mark.certified
def test_zip_extract_rejects_non_zip_input():
    """TEST 008: Non-zip input is rejected (honest error, not fake output)."""
    client = TestClient(app)
    with open("tests/sample.txt", "rb") as handle:
        response = client.post(
            "/convert",
            files={"file": ("sample.txt", handle, "text/plain")},
            data={"target_format": "zip", "operation": "zip-extract"},
        )
    assert response.status_code == 422, response.text
    body = response.json()
    assert body.get("code") == "UNSUPPORTED_CONVERSION", body

