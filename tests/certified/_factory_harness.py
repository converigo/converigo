"""
PROJECT: CONVERIGO
TEST SUITE: Certified Factory Harness (Jalur 2 / F0)

Shared uniform-assertion harness for factory-built converter clusters.
One assertion vocabulary for every batch so each cluster gate answers the
same questions, per the Factory Batch Plan (F0 deliverable 3):

    plugin discovered -> POST /convert 201 -> GET /download 200 ->
    content valid -> honest error class (422 / UNSUPPORTED_CONVERSION)

Usage (per-cluster file, e.g. tests/certified/<cluster>/test_<cluster>_factory_certified.py):

    from tests.certified._factory_harness import (
        assert_honest_unsupported,
        assert_slug_discovered,
        post_convert,
        resolve_output_path,
        run_happy_path,
    )
"""

from __future__ import annotations

from pathlib import Path

from fastapi import Response
from fastapi.testclient import TestClient

from app.core.settings import settings
from app.main import app
from app.plugins.registry import registry

OUTPUT_DIR = settings.OUTPUT_DIR

MIME_BY_SUFFIX = {
    "csv": "text/csv",
    "tsv": "text/tab-separated-values",
    "json": "application/json",
    "txt": "text/plain",
    "html": "text/html",
    "xml": "application/xml",
    "yaml": "application/yaml",
    "yml": "application/yaml",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xls": "application/vnd.ms-excel",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "tiff": "image/tiff",
    "svg": "image/svg+xml",
    "zip": "application/zip",
    "tar": "application/x-tar",
    "gz": "application/gzip",
}


def mime_for(path: Path) -> str:
    return MIME_BY_SUFFIX.get(path.suffix.lstrip(".").lower(), "application/octet-stream")


# ---------------------------------------------------------------------------
# Assertions
# ---------------------------------------------------------------------------

def assert_slug_discovered(slug: str, source: str | None = None, target: str | None = None) -> None:
    """The plugin is registered under its slug (and optional pair)."""
    assert registry.has_slug(slug), f"Plugin '{slug}' is not registered"
    plugin = registry.by_slug[slug]
    assert plugin.slug == slug, f"slug mismatch for {slug}"
    if source is not None and target is not None:
        assert plugin.supports(source, target), (
            f"{slug} fails supports() for {source} -> {target}"
        )


def assert_honest_unsupported(response: Response) -> None:
    """422 + UNSUPPORTED_CONVERSION: no fabricated output for bad input."""
    assert response.status_code == 422, response.text
    body = response.json()
    assert body.get("code") == "UNSUPPORTED_CONVERSION", body


def resolve_output_path(response: Response) -> Path:
    """Resolve the /download payload to its real file under OUTPUT_DIR."""
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


# ---------------------------------------------------------------------------
# Pipeline steps
# ---------------------------------------------------------------------------

def post_convert(
    source_path: Path,
    target_format: str,
    operation: str,
    mime: str | None = None,
    filename: str | None = None,
) -> Response:
    """POST /convert exactly the way production clients do."""
    client = TestClient(app)
    with source_path.open("rb") as handle:
        return client.post(
            "/convert",
            files={"file": (filename or source_path.name, handle, mime or mime_for(source_path))},
            data={"target_format": target_format, "operation": operation},
        )


def run_happy_path(
    source_path: Path,
    target_format: str,
    operation: str,
    mime: str | None = None,
) -> Path:
    """Full discovery -> 201 -> download 200 pipeline; returns the local output.

    Asserts the uniform factory contract; the caller verifies content and
    cleans the returned file up (cleanup_output).
    """
    assert_slug_discovered(operation)
    response = post_convert(source_path, target_format, operation, mime=mime)
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload.get("status") == "success", payload

    download_path = payload["download_path"]
    client = TestClient(app)
    download = client.get(download_path)
    assert download.status_code == 200, download.text
    assert download.content, "Downloaded content is empty"
    assert "attachment" in download.headers.get("content-disposition", ""), (
        "Download is not served as an attachment"
    )
    return resolve_output_path(response)


def cleanup_output(output_path: Path) -> None:
    output_path.unlink(missing_ok=True)
