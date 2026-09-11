"""
PROJECT: CONVERIGO
TEST SUITE: Certified RAR Extract Converter (VAR-34 / Batch 6, Gate 2)
STATUS: CERTIFIED (Batch 6 evidence run — pending PC merge-gate approval)

Certified-level coverage for the RAR extract converter (RARExtractPlugin
delegating to ArchiveEngine after the VAR-34 migration from subprocess
``unrar`` to in-process ``libarchive-c`` RAR4/RAR5 readers).

The plugin mirrors the Batch 6 Gate 1 pattern: the /convert download
route serves a single FILE, so multi-member archives are repackaged into
one TAR (clean POSIX member names) and single-member archives are
returned as the extracted file itself.

Verification: real RAR4 and RAR5 fixtures (from the libarchive project
test corpus, vendored under tests/fixtures/rar), plugin-level round-trip,
HTTP upload -> convert -> download pipeline, byte-identical member
content, honest typed errors (422 UNSUPPORTED_CONVERSION, never a
generic 500) for password-protected, multi-volume and corrupt input.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import struct
import tarfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.settings import settings
from app.main import app
from app.plugins.registry import registry

FIXTURE_DIR = Path("tests/fixtures/rar")
OUTPUT_DIR = settings.OUTPUT_DIR

RAR4_MEMBERS = FIXTURE_DIR / "rar4_members.rar"
RAR5_MEMBERS = FIXTURE_DIR / "rar5_members.rar"
RAR5_SINGLE = FIXTURE_DIR / "rar5_single.rar"
RAR4_PASSWORD = FIXTURE_DIR / "rar4_password.rar"
RAR5_PASSWORD = FIXTURE_DIR / "rar5_password.rar"
RAR4_MULTIVOLUME = FIXTURE_DIR / "rar4_multivolume_part1.rar"
RAR5_MULTIVOLUME = FIXTURE_DIR / "rar5_multivolume_part1.rar"


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


def _rar_members(path: Path) -> dict[str, bytes]:
    """Reference read of a RAR fixture via libarchive-c (name -> bytes)."""
    import libarchive

    members: dict[str, bytes] = {}
    with libarchive.file_reader(str(path)) as archive:
        for entry in archive:
            if entry.isfile:
                members[entry.pathname] = b"".join(entry.get_blocks())
    return members


def _tar_members(path: Path) -> dict[str, bytes]:
    with tarfile.open(path, "r") as tf:
        return {
            m.name: tf.extractfile(m).read()
            for m in tf.getmembers()
            if m.isfile()
        }


def _convert(client: TestClient, fixture: Path):
    assert fixture.exists(), f"Fixture is missing: {fixture}"
    with fixture.open("rb") as handle:
        return client.post(
            "/convert",
            files={"file": (fixture.name, handle, "application/x-rar-compressed")},
            data={"target_format": "rar", "operation": "rar-extract"},
        )


def _assert_unsupported(response, *message_fragments: str) -> None:
    assert response.status_code == 422, response.text
    body = response.json()
    assert body.get("code") == "UNSUPPORTED_CONVERSION", body
    message = str(body.get("message") or "")
    for fragment in message_fragments:
        assert fragment.lower() in message.lower(), (fragment, message)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.certified
def test_rar_extract_plugin_discovered():
    """TEST 001: Plugin is properly registered and not a placeholder."""
    plugin = registry.get_plugin("rar", "rar", slug="rar-extract")
    assert plugin is not None
    assert plugin.slug == "rar-extract"
    assert plugin.source_formats == ["rar"]
    assert plugin.target_formats == ["rar"]


@pytest.mark.certified
def test_rar4_extract_e2e_members_byte_identical():
    """TEST 002: RAR4 success E2E — 201 -> download 200 -> valid TAR,
    member set and content byte-identical to the source archive."""
    client = TestClient(app)
    response = _convert(client, RAR4_MEMBERS)
    assert response.status_code == 201, response.text

    output_path = _resolve_public_output_path(response)
    try:
        download = client.get(response.json()["download_path"])
        assert download.status_code == 200, download.text
        assert tarfile.is_tarfile(io.BytesIO(download.content))

        expected = _rar_members(RAR4_MEMBERS)
        actual = _tar_members(output_path)
        assert set(actual) == set(expected), (
            f"Member set mismatch: {sorted(actual)} != {sorted(expected)}"
        )
        for name, content in expected.items():
            assert actual[name] == content, f"Member content mismatch: {name}"
    finally:
        output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_rar5_extract_e2e_members_byte_identical():
    """TEST 003: RAR5 success E2E — 201 -> download 200 -> valid TAR,
    member set and content byte-identical to the source archive."""
    client = TestClient(app)
    response = _convert(client, RAR5_MEMBERS)
    assert response.status_code == 201, response.text

    output_path = _resolve_public_output_path(response)
    try:
        download = client.get(response.json()["download_path"])
        assert download.status_code == 200, download.text
        assert tarfile.is_tarfile(io.BytesIO(download.content))

        expected = _rar_members(RAR5_MEMBERS)
        actual = _tar_members(output_path)
        assert set(actual) == set(expected)
        for name, content in expected.items():
            assert actual[name] == content, f"Member content mismatch: {name}"
    finally:
        output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_rar5_single_member_returns_file_directly():
    """TEST 004: Single-member RAR returns the extracted file itself,
    byte-exact, with no TAR packaging."""
    client = TestClient(app)
    response = _convert(client, RAR5_SINGLE)
    assert response.status_code == 201, response.text

    download_path = response.json()["download_path"]
    assert download_path.endswith(".txt"), download_path

    download = client.get(download_path)
    assert download.status_code == 200, download.text

    expected = _rar_members(RAR5_SINGLE)
    assert set(expected) == {"helloworld.txt"}
    assert download.content == expected["helloworld.txt"]


@pytest.mark.certified
def test_rar_extract_single_output_file():
    """TEST 005: Exactly one output file is produced per conversion."""
    client = TestClient(app)
    response = _convert(client, RAR5_MEMBERS)
    assert response.status_code == 201, response.text

    conversion_id = Path(
        response.json()["download_path"].removeprefix("/download/")
    ).parts[0]
    files = [f for f in (OUTPUT_DIR / conversion_id).glob("*") if f.is_file()]
    assert len(files) == 1, f"Expected exactly one output file, got: {files}"
    for f in files:
        f.unlink(missing_ok=True)


@pytest.mark.certified
def test_rar4_password_protected_honest_error():
    """TEST 006: RAR4 password-protected -> 422 UNSUPPORTED_CONVERSION
    (no silent failure, no generic 500).

    Category-only assert: the encrypted-error classification comes from
    the engine's version-independent structural header pre-scan, so the
    test must not pin any native error message wording."""
    client = TestClient(app)
    response = _convert(client, RAR4_PASSWORD)
    _assert_unsupported(response)


@pytest.mark.certified
def test_rar5_password_protected_honest_error():
    """TEST 007: RAR5 password-protected -> 422 UNSUPPORTED_CONVERSION.

    Category-only assert: same version-independence rationale as TEST 006
    (libarchive 3.6.2 fails RAR5 header decryption with a message that
    never mentions passphrase/password/encrypted)."""
    client = TestClient(app)
    response = _convert(client, RAR5_PASSWORD)
    _assert_unsupported(response)


@pytest.mark.certified
def test_rar4_multivolume_honest_error():
    """TEST 008: RAR4 multi-volume first part -> 422 UNSUPPORTED_CONVERSION."""
    client = TestClient(app)
    response = _convert(client, RAR4_MULTIVOLUME)
    _assert_unsupported(response, "multi-volume")


@pytest.mark.certified
def test_rar5_multivolume_honest_error():
    """TEST 009: RAR5 multi-volume first part -> 422 UNSUPPORTED_CONVERSION.
    Guards the silent-empty-output failure mode of continuation volumes."""
    client = TestClient(app)
    response = _convert(client, RAR5_MULTIVOLUME)
    _assert_unsupported(response, "multi-volume")


@pytest.mark.certified
def test_rar_corrupt_body_honest_error(tmp_path: Path):
    """TEST 010: RAR signature with corrupt body -> 422 UNSUPPORTED_CONVERSION
    (honest unsupported-content error, not a 500)."""
    client = TestClient(app)
    corrupt = tmp_path / "corrupt.rar"
    corrupt.write_bytes(b"Rar!\x1a\x07\x00" + struct.pack("<HHH", 0, 0, 6) + b"\x00" * 32)
    response = _convert(client, corrupt)
    _assert_unsupported(response, "rar")


@pytest.mark.certified
def test_rar_extract_rejects_non_rar_input():
    """TEST 011: Non-RAR upload on the rar-extract operation is rejected
    upstream with the standard unsupported-conversion contract."""
    client = TestClient(app)
    with open("tests/sample.txt", "rb") as handle:
        response = client.post(
            "/convert",
            files={"file": ("sample.txt", handle, "text/plain")},
            data={"target_format": "rar", "operation": "rar-extract"},
        )
    assert response.status_code == 422, response.text
    body = response.json()
    detail = body.get("detail") or body
    assert detail.get("code") == "UNSUPPORTED_CONVERSION", body


@pytest.mark.certified
def test_rar_extract_plugin_level_round_trip(tmp_path: Path):
    """TEST 012: Plugin-level round-trip on a real RAR5 fixture mirrors the
    HTTP behavior (single servable file, byte-identical members)."""
    plugin = registry.get_plugin("rar", "rar", slug="rar-extract")
    output = asyncio.run(
        plugin.convert(
            RAR5_MEMBERS,
            "rar",
            output_dir=tmp_path / "out",
            temp_dir=tmp_path / "tmp",
        )
    )
    assert output.is_file()
    assert tarfile.is_tarfile(output)
    expected = _rar_members(RAR5_MEMBERS)
    actual = _tar_members(output)
    assert set(actual) == set(expected)
    for name in sorted(expected):
        assert actual[name] == expected[name], name
    hashlib.sha256(b"".join(actual.values())).hexdigest()  # deterministic touch


