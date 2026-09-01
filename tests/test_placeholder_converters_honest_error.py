"""
PR-0 stopgap regression tests — the placeholder office converters must NOT
serve a fake .txt file disguised as a successful conversion. Instead they must
return an honest "not available yet" response (HTTP 422 + code
UNSUPPORTED_CONVERSION + clear message).

PR-A2 finalises docx-to-jpg and ppt-to-jpg as real converters with first-page
rasterization (python-docx/python-pptx -> reportlab PDF -> PyMuPDF -> JPG).
Their placeholder entries have been removed; the two remaining placeholders
(XLSX-to-PNG? ODT-to-APNG?) will land in future PRs.

All placeholder converters have been delivered — this file is kept as a
regression placeholder to guard against future regressions. When new
placeholder converters are added, re-register them in PLACEHOLDER_CASES.
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
# PR-1a: ppt-to-docx & xlsx-to-docx removed (now real native converters).
# PR-1b: docx-to-xlsx & ppt-to-xlsx removed (now real native converters).
# PR-1c: docx-to-ppt & xlsx-to-ppt removed (now real native converters).
# PR-A2: docx-to-jpg & ppt-to-jpg removed (now real raster converters).
# No placeholder converters remain; re-register future placeholders here.
PLACEHOLDER_CASES: list[tuple[str, str, str]] = []


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
