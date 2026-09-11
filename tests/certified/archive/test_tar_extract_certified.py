"""
PROJECT: CONVERIGO
TEST SUITE: Certified TAR Extract Converter (VAR-33 / Batch 6, Gate 1)
STATUS: CERTIFIED (Batch 6 evidence run — pending PC merge-gate approval)

Certified-level coverage for the TAR extract converter (TARExtractPlugin
delegating to ArchiveEngine, with the Batch 6 Gate 1 fix that mirrors the
Batch 5 zip-extract pattern: the extracted directory is repackaged into a
single downloadable TAR file — stdlib tarfile, clean POSIX member names —
so POST /convert (201) is followed by a working GET /download (200)).

Verification: real-file sample (tests/sample.tar), plugin-level round-trip,
HTTP upload -> convert -> download pipeline, output is a valid TAR with an
identical member set and byte-identical member content, single output file,
honest error for non-tar input, security tests remain in place
(tests/certified/archive/test_tar_security.py).
"""

from __future__ import annotations

import asyncio
import io
import tarfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.settings import settings
from app.main import app
from app.plugins.registry import registry

SAMPLE_TAR = Path("tests/sample.tar")
OUTPUT_DIR = settings.OUTPUT_DIR


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def _tar_members(path: Path) -> dict[str, bytes]:
    with tarfile.open(path, "r") as tf:
        return {
            m.name: tf.extractfile(m).read()
            for m in tf.getmembers()
            if m.isfile()
        }


def _add_bytes(tf: tarfile.TarFile, name: str, data: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    tf.addfile(info, io.BytesIO(data))


def _make_real_tar(tmp_path: Path, nested: bool = False) -> Path:
    tar_path = tmp_path / "batch6_sample.tar"
    with tarfile.open(tar_path, "w") as tf:
        _add_bytes(tf, "alpha/one.txt", b"batch6 one\n")
        _add_bytes(tf, "beta/two.txt", b"batch6 two\n")
        if nested:
            _add_bytes(tf, "alpha/deep/three.txt", b"batch6 three\n")
    return tar_path


def _convert(client):
    assert SAMPLE_TAR.exists(), f"Sample file is missing: {SAMPLE_TAR}"
    with SAMPLE_TAR.open("rb") as handle:
        return client.post(
            "/convert",
            files={"file": ("sample.tar", handle, "application/x-tar")},
            data={"target_format": "tar", "operation": "tar-extract"},
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.certified
def test_tar_extract_plugin_discovered():
    """TEST 001: Plugin is properly registered and not a placeholder."""
    plugin = registry.get_plugin("tar", "tar", slug="tar-extract")
    assert plugin is not None
    assert plugin.slug == "tar-extract"
    assert plugin.engine == "archive"
    assert "tar" in plugin.source_formats
    assert "tar" in plugin.target_formats


@pytest.mark.certified
def test_tar_extract_plugin_returns_tar_file_not_directory(tmp_path: Path) -> None:
    """TEST 002 (Batch 6 fix): plugin returns a downloadable TAR file, not a directory."""
    plugin = registry.get_plugin("tar", "tar", slug="tar-extract")
    src = _make_real_tar(tmp_path)
    output = asyncio.run(
        plugin.convert(src, "tar", output_dir=tmp_path / "out", temp_dir=tmp_path / "tmp")
    )
    assert output.is_file() and not output.is_dir()
    assert tarfile.is_tarfile(output)
    expected = _tar_members(src)
    actual = _tar_members(output)
    assert set(actual) == set(expected), (
        f"Member set mismatch: {sorted(actual)} != {sorted(expected)}"
    )
    for name, content in expected.items():
        assert actual[name] == content, f"Member content mismatch: {name}"


@pytest.mark.certified
def test_tar_extract_convert_returns_201_and_publishes_file():
    """TEST 003: POST /convert answers 201 and the published output is a FILE."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text
    output_path = _resolve_public_output_path(response)
    try:
        assert output_path.is_file() and not output_path.is_dir()
        assert tarfile.is_tarfile(output_path), "Published output is not a valid TAR"
    finally:
        output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_tar_extract_output_members_byte_identical():
    """TEST 004: Extracted-and-repackaged members are byte-identical to the input."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text
    output_path = _resolve_public_output_path(response)
    try:
        expected = _tar_members(SAMPLE_TAR)
        actual = _tar_members(output_path)
        assert set(actual) == set(expected), (
            f"Member set mismatch: {sorted(actual)} != {sorted(expected)}"
        )
        for name, content in expected.items():
            assert actual[name] == content, f"Member content mismatch: {name}"
    finally:
        output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_tar_extract_download_served():
    """TEST 005: The repackaged TAR is downloadable through /download (200)."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text

    download_path = response.json()["download_path"]
    download_resp = client.get(download_path)
    assert download_resp.status_code == 200, download_resp.text
    assert download_resp.content, "Downloaded content is empty"
    assert tarfile.is_tarfile(io.BytesIO(download_resp.content)), (
        "Downloaded payload is not a valid TAR"
    )
    assert "attachment" in download_resp.headers.get("content-disposition", "")

    _resolve_public_output_path(response).unlink(missing_ok=True)


@pytest.mark.certified
def test_tar_extract_single_output_file():
    """TEST 006: Exactly one TAR output file is produced per conversion."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text
    conversion_id = Path(
        response.json()["download_path"].removeprefix("/download/")
    ).parts[0]
    files = list((OUTPUT_DIR / conversion_id).glob("*.tar"))
    assert len(files) == 1, f"Expected exactly one TAR output, got: {files}"
    for f in files:
        f.unlink(missing_ok=True)


@pytest.mark.certified
@pytest.mark.parametrize("nested", [False, True])
def test_tar_extract_real_file_preserves_structure(tmp_path: Path, nested: bool) -> None:
    """TEST 007: Real-file parametrized — folder structure survives the round-trip."""
    plugin = registry.get_plugin("tar", "tar", slug="tar-extract")
    src = _make_real_tar(tmp_path, nested=nested)
    output = asyncio.run(
        plugin.convert(src, "tar", output_dir=tmp_path / "out", temp_dir=tmp_path / "tmp")
    )
    assert output.is_file() and tarfile.is_tarfile(output)
    actual = _tar_members(output)
    expected_names = {
        "alpha/one.txt",
        "beta/two.txt",
        *( ["alpha/deep/three.txt"] if nested else [] ),
    }
    assert expected_names <= set(actual), (
        f"Structure lost: {sorted(expected_names)} not in {sorted(actual)}"
    )
    assert actual["alpha/one.txt"] == b"batch6 one\n"


@pytest.mark.certified
def test_tar_extract_rejects_non_tar_input():
    """TEST 008: Non-tar input is rejected (honest error, not fake output)."""
    client = TestClient(app)
    with open("tests/sample.txt", "rb") as handle:
        response = client.post(
            "/convert",
            files={"file": ("sample.txt", handle, "text/plain")},
            data={"target_format": "tar", "operation": "tar-extract"},
        )
    assert response.status_code == 422, response.text
    body = response.json()
    assert body.get("code") == "UNSUPPORTED_CONVERSION", body
