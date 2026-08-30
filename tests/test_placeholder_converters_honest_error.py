"""
PR-0 stopgap regression tests — the 8 placeholder office converters must NOT
serve a fake .txt file disguised as a successful conversion. Instead they must
return an honest "not available yet" response (HTTP 422 + code
UNSUPPORTED_CONVERSION + clear message).

Covered slugs:
  docx-to-jpg, docx-to-ppt, docx-to-xlsx,
  ppt-to-docx, ppt-to-jpg, ppt-to-xlsx,
  xlsx-to-docx, xlsx-to-ppt
"""

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.plugins.registry import registry
from app.services.conversion_service import UnsupportedConversionError

REGRESSION_DIR = Path(__file__).parent / "assets" / "regression"

# (slug, sample_filename, target_format)
PLACEHOLDER_CASES = [
    ("docx-to-jpg", "sample.docx", "jpg"),
    ("docx-to-ppt", "sample.docx", "pptx"),
    ("docx-to-xlsx", "sample.docx", "xlsx"),
    ("ppt-to-docx", "sample.pptx", "docx"),
    ("ppt-to-jpg", "sample.pptx", "jpg"),
    ("ppt-to-xlsx", "sample.pptx", "xlsx"),
    ("xlsx-to-docx", "sample.xlsx", "docx"),
    ("xlsx-to-ppt", "sample.xlsx", "pptx"),
]


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def _upload(client, filename: str, target: str, operation: str):
    sample = REGRESSION_DIR / filename
    with sample.open("rb") as handle:
        return client.post(
            "/convert",
            files={"file": (sample.name, handle, "application/octet-stream")},
            data={"target_format": target, "operation": operation},
        )


@pytest.mark.parametrize("slug,filename,target", PLACEHOLDER_CASES)
def test_placeholder_converter_returns_honest_not_available(client, slug, filename, target):
    response = _upload(client, filename, target, slug)

    # Must NOT be a 201 success serving a fake .txt download.
    assert response.status_code == 422, (
        f"{slug}: expected 422 UNSUPPORTED_CONVERSION, got {response.status_code} "
        f"body={response.text[:400]}"
    )

    body = response.json()
    detail = body.get("detail") or body
    assert detail.get("code") == "UNSUPPORTED_CONVERSION", f"{slug}: {detail}"
    message = str(detail.get("message") or "")
    lowered = message.lower()
    assert ("not available" in lowered) or ("belum tersedia" in lowered), f"{slug}: {message}"

    # No download_path should be advertised for a "successful" fake conversion.
    assert "download_path" not in body


@pytest.mark.parametrize("slug,filename,target", PLACEHOLDER_CASES)
def test_placeholder_converter_does_not_write_fake_file(tmp_path, slug, filename, target):
    """The placeholder convert() must not emit any output file at all."""
    source_format = slug.split("-to-")[0]
    plugin = registry.get_plugin(source_format, target, slug=slug)
    sample = REGRESSION_DIR / filename

    with pytest.raises(UnsupportedConversionError) as exc_info:
        asyncio.run(
            plugin.convert(
                source_path=sample,
                target_format=target,
                output_dir=tmp_path,
                temp_dir=tmp_path,
            )
        )

    assert "not available" in str(exc_info.value).lower()
    # No fake output file should exist anywhere in the output/temp dirs.
    assert list(tmp_path.iterdir()) == [], f"{slug}: placeholder wrote output file(s)"


@pytest.mark.parametrize("slug,filename,target", PLACEHOLDER_CASES)
def test_placeholder_converter_route_still_accessible(client, slug, filename, target):
    """The tool page route must remain 200 (normal access), not 404/500."""
    response = client.get(f"/tools/{slug}")
    assert response.status_code == 200, f"{slug}: /tools page returned {response.status_code}"
