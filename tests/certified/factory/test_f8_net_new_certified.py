"""
PROJECT: CONVERIGO
TEST SUITE: Certified F8 Net-New Converters (Jalur 2)

Factory Batch F8: five net-new certified converters in three sub-batches:
  F8-A (zero new deps): docx-to-md (mammoth), image-to-base64 +
        base64-to-image (Pillow + stdlib base64, bit-exact data URI)
  F8-B (+Markdown>=3.10.3): md-to-html (python-markdown core, D5b
        disclosure-only: raw HTML blocks pass through verbatim)
  F8-C (+pinned lxml/beautifulsoup4): html-to-csv via pandas.read_html,
        first table in document order

Harness contract: plugin discovered -> POST /convert 201 -> GET /download 200
-> output content verified -> honest 422 UNSUPPORTED_CONVERSION.

Governance: tracked regression samples exist for docx (tests/sample.docx),
png (tests/sample.png) and txt (tests/sample.txt), so the F8-A slugs ship
contract artifacts per the F4-validated tracked-sample policy (F7 office
precedent).  No tests/sample.md or tests/sample.html is tracked, so
md-to-html and html-to-csv ship page-only (F6 precedent) - both asserted
below.
"""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path

import pytest
from PIL import Image

from tests.certified._factory_harness import (
    assert_honest_unsupported,
    cleanup_output,
    post_convert,
    run_happy_path,
)

PNG_SAMPLE = Path("tests/sample.png")
JPG_SAMPLE = Path("tests/sample.jpg")
DOCX_SAMPLE = Path("tests/assets/regression/sample.docx")  # real OOXML ZIP
OFFICE_MIME = "application/octet-stream"
CORRUPT_OOXML_JUNK = b"PK\x03\x04" + b"not-a-real-ooxml-container" * 8
OLE2_JUNK = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"legacy-doc-bytes" * 8

CONTRACT_SLUGS = {
    "docx-to-md": ("document", Path("tests/sample.docx")),
    "image-to-base64": ("image", Path("tests/sample.png")),
    "base64-to-image": ("image", Path("tests/sample.txt")),
}
PAGE_ONLY_SLUGS = ("md-to-html", "html-to-csv")
F8_SLUGS = tuple(CONTRACT_SLUGS) + PAGE_ONLY_SLUGS


def _data_uri(path: Path) -> str:
    mime = "image/png" if path.suffix == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


# ---------------------------------------------------------------------------
# F8-A: docx-to-md
# ---------------------------------------------------------------------------


@pytest.mark.certified
def test_docx_to_md_happy_path(tmp_path: Path) -> None:
    output = run_happy_path(DOCX_SAMPLE, "md", "docx-to-md", mime=OFFICE_MIME)
    try:
        assert output.suffix == ".md"
        text = output.read_text(encoding="utf-8")
        assert text.strip(), "Markdown output is empty"
        assert "\x00" not in text, "Binary content leaked into the Markdown output"
    finally:
        cleanup_output(output)


@pytest.mark.certified
def test_docx_to_md_honest_422_for_zip_junk(tmp_path: Path) -> None:
    bad = tmp_path / "bad.docx"
    bad.write_bytes(CORRUPT_OOXML_JUNK)
    response = post_convert(bad, "md", "docx-to-md", mime=OFFICE_MIME)
    # PK junk passes the ZIP signature gate, so the conversion layer must
    # answer the honest UNSUPPORTED_CONVERSION class (never 500/fake file).
    assert_honest_unsupported(response)


@pytest.mark.certified
def test_docx_to_md_plugin_guard_rejects_ole2_directly(tmp_path: Path) -> None:
    """Legacy OLE2 .doc bytes are rejected by the plugin's OOXML guard.

    HTTP-level uploads of OLE2 bytes never reach the plugin (the upload
    signature gate stops them first, currently with a pre-existing 500
    mapping that predates F8 and is tracked as a cross-cutting hygiene
    item); this test pins the plugin-layer honest-422 contract itself.
    """
    import asyncio

    from app.plugins.registry import registry
    from app.services.conversion_service import UnsupportedConversionError

    bad = tmp_path / "legacy.docx"
    bad.write_bytes(OLE2_JUNK)
    plugin = registry.by_slug["docx-to-md"]
    with pytest.raises(UnsupportedConversionError):
        asyncio.run(plugin.convert(bad, "md", output_dir=tmp_path))


# ---------------------------------------------------------------------------
# F8-A: base64 pair (bit-exact encode, verified decode)
# ---------------------------------------------------------------------------


@pytest.mark.certified
@pytest.mark.parametrize(
    ("sample", "expected_mime"), [(PNG_SAMPLE, "image/png"), (JPG_SAMPLE, "image/jpeg")]
)
def test_image_to_base64_bit_exact_data_uri(
    sample: Path, expected_mime: str, tmp_path: Path
) -> None:
    output = run_happy_path(sample, "txt", "image-to-base64")
    try:
        match = re.match(r"^data:([^;]+);base64,(.*)$", output.read_text("utf-8").strip(), re.DOTALL)
        assert match, "Output is not a single data URI"
        assert match.group(1) == expected_mime
        assert base64.b64decode(match.group(2)) == sample.read_bytes(), (
            "Base64 transport is not bit-exact"
        )
    finally:
        cleanup_output(output)


# ---------------------------------------------------------------------------
# F8-B: md-to-html (D5b disclosure-only MVP)
# ---------------------------------------------------------------------------

MD_FIXTURE = (
    "# Alpha heading\n\nSome **bold** body text.\n\n"
    '<p data-probe="raw-html">RAW-HTML-BLOCK-42</p>\n\n'
    "- bullet one\n- bullet two\n"
)


@pytest.mark.certified
def test_md_to_html_happy_path_and_d5b_passthrough(tmp_path: Path) -> None:
    fixture = tmp_path / "probe.md"
    fixture.write_text(MD_FIXTURE, encoding="utf-8")
    output = run_happy_path(fixture, "html", "md-to-html")
    try:
        assert output.suffix == ".html"
        text = output.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in text
        assert "<h1>Alpha heading</h1>" in text
        assert "<strong>bold</strong>" in text
        # D5b pinned passthrough: raw HTML blocks are re-emitted verbatim.
        assert '<p data-probe="raw-html">RAW-HTML-BLOCK-42</p>' in text
    finally:
        cleanup_output(output)


# ---------------------------------------------------------------------------
# F8-C: html-to-csv
# ---------------------------------------------------------------------------

HTML_TABLE_FIXTURE = (
    "<html><body>\n"
    "<table><tr><th>city</th><th>pop</th></tr>"
    "<tr><td>Bandung</td><td>2500000</td></tr>"
    "<tr><td>Medan</td><td>2300000</td></tr></table>\n"
    "<table><tr><th>ignored</th></tr><tr><td>x</td></tr></table>\n"
    "</body></html>"
)


@pytest.mark.certified
def test_html_to_csv_first_table(tmp_path: Path) -> None:
    fixture = tmp_path / "probe.html"
    fixture.write_text(HTML_TABLE_FIXTURE, encoding="utf-8")
    output = run_happy_path(fixture, "csv", "html-to-csv")
    try:
        assert output.suffix == ".csv"
        rows = output.read_text(encoding="utf-8").strip().splitlines()
        assert rows[0] == "city,pop"
        assert "Bandung,2500000" in rows
        assert "Medan,2300000" in rows
        assert all("ignored" not in row for row in rows), "Second table leaked"
    finally:
        cleanup_output(output)


# ---------------------------------------------------------------------------
# Governance: map rows, artifacts, pins, ledger
# ---------------------------------------------------------------------------


def _static_target_map() -> dict[str, list[str]]:
    html_text = Path("app/templates/main/converigo_main.html").read_text(encoding="utf-8")
    block = html_text.split("const STATIC_TARGET_MAP = {", 1)[1].split("};", 1)[0]
    mapping: dict[str, list[str]] = {}
    for key, values in re.findall(r"(['\"a-zA-Z0-9_]+):\[(.*?)\]", block):
        mapping[key.strip("'\"")] = [
            v.strip().strip("'\"") for v in values.split(",") if v.strip()
        ]
    return mapping


@pytest.mark.certified
def test_static_target_map_f8_rows() -> None:
    """The deployed STATIC_TARGET_MAP reflects the F8 delta exactly."""
    mapping = _static_target_map()
    assert mapping.get("md") == ["HTML"], mapping.get("md")
    assert mapping.get("html") == ["CSV"], mapping.get("html")
    assert mapping.get("docx") == [
        "HTML", "JPEG", "JPG", "MD", "PDF", "POWERPOINT", "PPT", "PPTX",
        "SPREADSHEET", "XLS", "XLSX",
    ], mapping.get("docx")
    assert mapping.get("jpg") == ["ICO", "PDF", "PNG", "TIFF", "TXT", "WEBP"], mapping.get("jpg")
    assert mapping.get("png") == [
        "BMP", "ICO", "JPEG", "JPG", "PDF", "TIFF", "TXT", "WEBP",
    ], mapping.get("png")
    assert mapping.get("webp") == ["ICO", "JPEG", "JPG", "PDF", "PNG", "TIFF", "TXT"], mapping.get("webp")
    assert mapping.get("bmp") == ["JPEG", "JPG", "PDF", "PNG", "TXT", "WEBP"], mapping.get("bmp")
    assert mapping.get("tiff") == ["JPEG", "JPG", "PDF", "PNG", "TXT"], mapping.get("tiff")
    assert mapping.get("gif") == ["MP4", "PDF", "TXT"], mapping.get("gif")
    assert mapping.get("txt") == ["BMP", "GIF", "JPG", "PDF", "PNG", "TIFF", "WEBP"], mapping.get("txt")


@pytest.mark.certified
def test_f8_artifacts_shipped() -> None:
    """F8-A slugs ship contract + page artifacts (tracked samples exist);
    md-to-html and html-to-csv ship page-only (F6 precedent)."""
    converters_dir = Path("app/data/converters")
    for slug, (engine, sample) in CONTRACT_SLUGS.items():
        contract_path = converters_dir / f"{slug}.contract.json"
        assert contract_path.is_file(), f"missing contract artifact: {contract_path.name}"
        payload = json.loads(contract_path.read_text(encoding="utf-8"))
        assert payload.get("slug") == slug, payload.get("slug")
        assert payload.get("lifecycle_status") == "certified", payload.get("lifecycle_status")
        assert payload.get("conversion_engine") == engine, payload.get("conversion_engine")
        assert Path(payload["regression_sample"]) == sample, payload["regression_sample"]
        assert sample.is_file(), f"sample missing on disk: {sample}"
        page_path = converters_dir / f"{slug}.json"
        assert page_path.is_file(), f"missing page artifact: {page_path.name}"

    for slug in PAGE_ONLY_SLUGS:
        page_path = converters_dir / f"{slug}.json"
        assert page_path.is_file(), f"missing page artifact: {page_path.name}"
        page = json.loads(page_path.read_text(encoding="utf-8"))
        assert page.get("slug") == slug, page.get("slug")
        assert page.get("lifecycle_status") == "certified", page.get("lifecycle_status")
        assert not (converters_dir / f"{slug}.contract.json").exists(), (
            f"unexpected contract artifact (page-only policy): {slug}"
        )


@pytest.mark.certified
def test_requirements_f8_pins() -> None:
    """F8 Gate 0 hygiene pins are present with security-informed floors."""
    requirements = Path("requirements.txt").read_text(encoding="utf-8")
    assert re.search(r"^Markdown>=3\.10\.3\s*$", requirements, re.MULTILINE), requirements
    assert re.search(r"^lxml>=6\.0\.0\s*$", requirements, re.MULTILINE), requirements
    assert re.search(r"^beautifulsoup4>=4\.12\.0\s*$", requirements, re.MULTILINE), requirements
    assert re.search(r"^PyYAML>=6\.0\.1\s*$", requirements, re.MULTILINE), requirements


@pytest.mark.certified
def test_f8_ledger_locked_entries() -> None:
    """All five F8 slugs are locked certified entries pointing at this file."""
    payload = json.loads(
        Path("app/data/certified_converters.json").read_text(encoding="utf-8")
    )
    entries = {entry["slug"]: entry for entry in payload["certified"]}
    assert len(entries) == len(payload["certified"]), "duplicate ledger slugs"
    for slug in F8_SLUGS:
        entry = entries.get(slug)
        assert entry, f"{slug} missing from certified_converters.json"
        assert entry.get("locked") is True, entry
        assert entry.get("lifecycle_status") == "certified", entry
        expected_test = "tests/certified/factory/test_f8_net_new_certified.py"
        assert expected_test in entry.get("test_files", []), entry


@pytest.mark.certified
def test_html_to_csv_honest_422_without_table(tmp_path: Path) -> None:
    fixture = tmp_path / "no_table.html"
    fixture.write_text("<html><body><p>just text</p></body></html>", encoding="utf-8")
    response = post_convert(fixture, "csv", "html-to-csv")
    assert_honest_unsupported(response)


def _write_data_uri_fixture(tmp_path: Path, sample: Path, mime: str) -> Path:
    fixture = tmp_path / f"payload_{sample.stem}.txt"
    fixture.write_text(_data_uri(sample) + "\n", encoding="ascii")
    return fixture


@pytest.mark.certified
@pytest.mark.parametrize(
    ("sample", "mime", "target"), [(PNG_SAMPLE, "image/png", "png"), (JPG_SAMPLE, "image/jpeg", "jpg")]
)
def test_base64_to_image_roundtrip(
    sample: Path, mime: str, target: str, tmp_path: Path
) -> None:
    fixture = _write_data_uri_fixture(tmp_path, sample, mime)
    output = run_happy_path(fixture, target, "base64-to-image")
    try:
        assert output.suffix == f".{target}"
        with Image.open(sample) as original, Image.open(output) as rebuilt:
            assert rebuilt.format == ("JPEG" if target == "jpg" else "PNG")
            assert rebuilt.size == original.size
            assert rebuilt.convert("RGB").tobytes() == original.convert("RGB").tobytes(), (
                "Re-encoded image is not pixel-identical to the embedded payload"
            )
    finally:
        cleanup_output(output)
