"""
PROJECT: CONVERIGO
TEST SUITE: Certified GZ Extract Converter (VAR-33 / Batch 6, Gate 1)
STATUS: CERTIFIED (Batch 6 evidence run — pending PC merge-gate approval)

Certified-level coverage for the GZ extract converter (GZExtractPlugin
delegating to ArchiveEngine, with the Batch 6 Gate 1 fix that mirrors the
Batch 5 zip-extract pattern: the converter returns a single downloadable
FILE instead of the engine's extraction directory, so POST /convert (201)
is followed by a working GET /download (200)).

Behavior is deterministic per input type:
- standalone .gz (tests/sample.gz): the decompressed file is returned
  directly and its bytes equal gzip.decompress of the input;
- .tar.gz payloads (tests/sample.tar.gz): upload_service stores the file
  as "<uuid>.gz", so the engine decompresses the gzip layer and the
  single returned file IS the decompressed TAR archive (validated here).

Verification: real-file samples, plugin-level round-trips, HTTP upload ->
convert -> download pipeline, content validation (non-corrupt, non-empty,
byte-exact), single output file, honest error for non-gz input, security
tests remain in place (tests/certified/archive/test_tar_security.py).
"""

from __future__ import annotations

import asyncio
import gzip
import io
import tarfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.settings import settings
from app.main import app
from app.plugins.registry import registry

SAMPLE_GZ = Path("tests/sample.gz")
SAMPLE_TAR_GZ = Path("tests/sample.tar.gz")
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


def _tar_members_from_bytes(data: bytes) -> dict[str, bytes]:
    # "r:*" auto-detects compression (raw tar OR gzip layer) — needed for
    # expected-side reads of sample.tar.gz which is still gzipped on disk.
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as tf:
        return {
            m.name: tf.extractfile(m).read()
            for m in tf.getmembers()
            if m.isfile()
        }


def _add_bytes(tf: tarfile.TarFile, name: str, data: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    tf.addfile(info, io.BytesIO(data))


def _make_real_gz(tmp_path: Path) -> Path:
    gz_path = tmp_path / "notes.txt.gz"
    gz_path.write_bytes(gzip.compress(b"gz-extract batch6 payload\n"))
    return gz_path


def _make_real_tar_gz(tmp_path: Path, nested: bool = False) -> Path:
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w") as tf:
        _add_bytes(tf, "alpha/one.txt", b"batch6 one\n")
        _add_bytes(tf, "beta/two.txt", b"batch6 two\n")
        if nested:
            _add_bytes(tf, "alpha/deep/three.txt", b"batch6 three\n")
    tgz_path = tmp_path / "bundle.tar.gz"
    tgz_path.write_bytes(gzip.compress(tar_buffer.getvalue()))
    return tgz_path


def _convert(client, sample: Path, filename: str):
    assert sample.exists(), f"Sample file is missing: {sample}"
    with sample.open("rb") as handle:
        return client.post(
            "/convert",
            files={"file": (filename, handle, "application/gzip")},
            data={"target_format": "gz", "operation": "gz-extract"},
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.certified
def test_gz_extract_plugin_discovered():
    """TEST 001: Plugin is properly registered and not a placeholder."""
    plugin = registry.get_plugin("gz", "gz", slug="gz-extract")
    assert plugin is not None
    assert plugin.slug == "gz-extract"
    assert plugin.engine == "archive"
    assert "gz" in plugin.source_formats
    assert "gz" in plugin.target_formats


@pytest.mark.certified
def test_gz_extract_plugin_returns_decompressed_file_not_directory(tmp_path: Path) -> None:
    """TEST 002 (Batch 6 fix): standalone .gz returns the decompressed file itself."""
    plugin = registry.get_plugin("gz", "gz", slug="gz-extract")
    src = _make_real_gz(tmp_path)
    output = asyncio.run(
        plugin.convert(src, "gz", output_dir=tmp_path / "out", temp_dir=tmp_path / "tmp")
    )
    assert output.is_file() and not output.is_dir()
    assert output.read_bytes() == b"gz-extract batch6 payload\n"


@pytest.mark.certified
def test_gz_extract_targz_plugin_returns_decompressed_tar_file(tmp_path: Path) -> None:
    """TEST 003 (Batch 6 fix): .tar.gz input returns one TAR file with the extracted tree."""
    plugin = registry.get_plugin("gz", "gz", slug="gz-extract")
    src = _make_real_tar_gz(tmp_path, nested=True)
    output = asyncio.run(
        plugin.convert(src, "gz", output_dir=tmp_path / "out", temp_dir=tmp_path / "tmp")
    )
    assert output.is_file() and not output.is_dir()
    assert tarfile.is_tarfile(output)
    actual = _tar_members_from_bytes(output.read_bytes())
    assert set(actual) == {
        "alpha/one.txt",
        "beta/two.txt",
        "alpha/deep/three.txt",
    }, f"Structure lost: {sorted(actual)}"
    assert actual["alpha/one.txt"] == b"batch6 one\n"


@pytest.mark.certified
def test_gz_extract_convert_returns_201_and_publishes_file():
    """TEST 004: POST /convert (real sample.gz) answers 201 with a servable file."""
    client = TestClient(app)
    response = _convert(client, SAMPLE_GZ, "sample.gz")
    assert response.status_code == 201, response.text
    output_path = _resolve_public_output_path(response)
    try:
        assert output_path.is_file() and not output_path.is_dir()
    finally:
        output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_gz_extract_output_content_byte_exact():
    """TEST 005: Decompressed output equals gzip.decompress of the real sample.gz."""
    client = TestClient(app)
    response = _convert(client, SAMPLE_GZ, "sample.gz")
    assert response.status_code == 201, response.text
    output_path = _resolve_public_output_path(response)
    try:
        payload = output_path.read_bytes()
        assert payload, "Decompressed output is empty"
        assert payload == gzip.decompress(SAMPLE_GZ.read_bytes()), (
            "Decompressed content mismatch (corrupt output)"
        )
    finally:
        output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_gz_extract_targz_via_http_returns_decompressed_tar():
    """TEST 006: Real sample.tar.gz -> 201 -> output IS the decompressed TAR archive."""
    client = TestClient(app)
    response = _convert(client, SAMPLE_TAR_GZ, "sample.tar.gz")
    assert response.status_code == 201, response.text
    output_path = _resolve_public_output_path(response)
    try:
        content = output_path.read_bytes()
        assert content, "Decompressed output is empty"
        expected = _tar_members_from_bytes(SAMPLE_TAR_GZ.read_bytes())
        actual = _tar_members_from_bytes(content)
        assert set(actual) == set(expected), (
            f"Member set mismatch: {sorted(actual)} != {sorted(expected)}"
        )
        for name, member_content in expected.items():
            assert actual[name] == member_content, f"Member content mismatch: {name}"
    finally:
        output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_gz_extract_download_served():
    """TEST 007: The decompressed output is downloadable through /download (200)."""
    client = TestClient(app)
    response = _convert(client, SAMPLE_GZ, "sample.gz")
    assert response.status_code == 201, response.text

    download_path = response.json()["download_path"]
    download_resp = client.get(download_path)
    assert download_resp.status_code == 200, download_resp.text
    assert download_resp.content, "Downloaded content is empty"
    assert download_resp.content == gzip.decompress(SAMPLE_GZ.read_bytes()), (
        "Downloaded payload does not match the decompressed sample"
    )
    assert "attachment" in download_resp.headers.get("content-disposition", "")

    _resolve_public_output_path(response).unlink(missing_ok=True)


@pytest.mark.certified
def test_gz_extract_single_output_file():
    """TEST 008: Exactly one output file is produced per conversion."""
    client = TestClient(app)
    response = _convert(client, SAMPLE_GZ, "sample.gz")
    assert response.status_code == 201, response.text
    conversion_id = Path(
        response.json()["download_path"].removeprefix("/download/")
    ).parts[0]
    files = [f for f in (OUTPUT_DIR / conversion_id).iterdir() if f.is_file()]
    assert len(files) == 1, f"Expected exactly one output file, got: {files}"
    for f in files:
        f.unlink(missing_ok=True)


@pytest.mark.certified
def test_gz_extract_rejects_non_gz_input():
    """TEST 009: Non-gz input is rejected (honest error, not fake output)."""
    client = TestClient(app)
    with open("tests/sample.txt", "rb") as handle:
        response = client.post(
            "/convert",
            files={"file": ("sample.txt", handle, "text/plain")},
            data={"target_format": "gz", "operation": "gz-extract"},
        )
    assert response.status_code == 422, response.text
    body = response.json()
    assert body.get("code") == "UNSUPPORTED_CONVERSION", body
