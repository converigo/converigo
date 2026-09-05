"""
PROJECT: CONVERIGO
TEST SUITE: Certified PDF Ops Cluster - Factory Batch F3 (Jalur 2)

Factory Batch Plan F3 (cluster G-C net-new): six PDF-operation converters
built on the F0 factory base (app/factory/plugin_base.py):

    pdf-rotate, pdf-unlock, pdf-watermark, pdf-metadata,
    pdf-to-html, pdf-to-md

ONE parametric test file for the whole F3 batch, using the shared factory
harness uniform contract:

    plugin discovered -> POST /convert 201 -> GET /download 200 ->
    output content verified -> honest 422 UNSUPPORTED_CONVERSION

Governance notes:
- Supervisor D5a: pdf-protect is DEFERRED to a future options-channel
  batch (no honest password source without an options channel), so it is
  deliberately NOT part of this suite.
- Supervisor D5b: pdf-to-html / pdf-to-md are MVP fixed-semantics TEXT
  EXTRACTION converters.  This suite contains explicit limitation tests:
  text-dominant PDFs convert and carry the extracted text; image-only
  (scanned) PDFs get the honest 422 UNSUPPORTED_CONVERSION class instead
  of a fabricated empty file.
- All four (pdf, pdf) operations are slug-aware (pdf-compress precedent):
  they resolve through their unique slugs and never overwrite each other.
Fixtures are generated in-memory with reportlab + pypdf (both already
required), so the suite adds zero binary assets.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas

from tests.certified._factory_harness import (
    assert_honest_unsupported,
    assert_slug_discovered,
    cleanup_output,
    post_convert,
    run_happy_path,
)

FIXTURE_TEXT_1 = "Converigo certified fixture page one"
FIXTURE_TEXT_2 = "Converigo certified fixture page two"
PRODUCER = "Converigo (https://converigo.com)"


# ---------------------------------------------------------------------------
# Fixture builders (real PDFs, deterministic content, in-memory reportlab)
# ---------------------------------------------------------------------------

def _make_text_pdf(path: Path) -> Path:
    """Text-dominant 2-page PDF - the happy-path input for the cluster."""
    canvas = Canvas(str(path), pagesize=(612, 792))
    for text in (FIXTURE_TEXT_1, FIXTURE_TEXT_2):
        canvas.setFont("Helvetica", 14)
        canvas.drawString(72, 720, text)
        canvas.showPage()
    canvas.save()
    return path


def _make_single_page_text_pdf(path: Path, text: str) -> Path:
    """Single-page text PDF used as the base of encrypted fixtures."""
    canvas = Canvas(str(path), pagesize=(612, 792))
    canvas.setFont("Helvetica", 14)
    canvas.drawString(72, 720, text)
    canvas.showPage()
    canvas.save()
    return path


def _make_owner_encrypted_pdf(path: Path) -> Path:
    """Owner-restricted PDF: opens without a password (empty user password).

    This is the input pdf-unlock is honestly allowed to handle.
    """
    base = path.with_name(f"{path.stem}_base.pdf")
    _make_single_page_text_pdf(base, FIXTURE_TEXT_1)
    reader = PdfReader(str(base))
    writer = PdfWriter()
    writer.append(reader)
    writer.encrypt(user_password="", owner_password="converigo-owner")
    with path.open("wb") as handle:
        writer.write(handle)
    sanity = PdfReader(str(path))
    assert sanity.is_encrypted, "fixture must be encrypted"
    assert sanity.decrypt("") is not None, "empty user password must open"
    base.unlink(missing_ok=True)
    return path


def _make_user_encrypted_pdf(path: Path) -> Path:
    """User-password PDF: opens ONLY with a real password -> honest 422."""
    base = path.with_name(f"{path.stem}_base.pdf")
    _make_single_page_text_pdf(base, FIXTURE_TEXT_1)
    reader = PdfReader(str(base))
    writer = PdfWriter()
    writer.append(reader)
    writer.encrypt(user_password="secret-user", owner_password="converigo-owner")
    with path.open("wb") as handle:
        writer.write(handle)
    base.unlink(missing_ok=True)
    return path


def _make_image_only_pdf(path: Path) -> Path:
    """Scanned-style PDF: graphics only, zero extractable text."""
    canvas = Canvas(str(path), pagesize=(612, 792))
    canvas.setFillColorRGB(0.2, 0.4, 0.8)
    canvas.rect(100, 400, 300, 200, fill=1, stroke=0)
    canvas.setStrokeColorRGB(0.9, 0.3, 0.3)
    canvas.setLineWidth(6)
    canvas.line(80, 200, 520, 340)
    canvas.showPage()
    canvas.save()
    assert not (PdfReader(str(path)).pages[0].extract_text() or "").strip(), (
        "image-only fixture must have no extractable text"
    )
    return path


def _make_corrupt_pdf(path: Path) -> Path:
    """Truncated garbage with a PDF name: never produces fabricated output."""
    path.write_bytes(b"%PDF-1.7 truncated garbage - no xref, no objects")
    return path


# ---------------------------------------------------------------------------
# Content verifiers per converter
# ---------------------------------------------------------------------------

def _verify_pdf_readable(path: Path) -> PdfReader:
    reader = PdfReader(str(path))
    assert len(reader.pages) >= 1, "output PDF has no pages"
    return reader


def _verify_rotate(path: Path) -> None:
    reader = _verify_pdf_readable(path)
    assert len(reader.pages) == 2, len(reader.pages)
    # 90 degrees clockwise is expressed via the /Rotate page attribute
    # (MediaBox stays portrait; renderers apply the rotation).
    for page in reader.pages:
        assert (page.get("/Rotate") or 0) == 90, page.get("/Rotate")


def _verify_unlock(path: Path) -> None:
    reader = _verify_pdf_readable(path)
    assert not reader.is_encrypted, "unlock output must open without a password"
    assert FIXTURE_TEXT_1 in (reader.pages[0].extract_text() or "")


def _verify_metadata(path: Path) -> None:
    reader = _verify_pdf_readable(path)
    assert reader.metadata.producer == PRODUCER, reader.metadata
    assert reader.metadata.creator == PRODUCER, reader.metadata


def _verify_watermark(path: Path) -> None:
    reader = _verify_pdf_readable(path)
    assert len(reader.pages) == 2, len(reader.pages)
    found = False
    for page in reader.pages:
        contents = page.get_contents()
        if contents is None:
            continue
        stream = contents.get_data().decode("latin-1", "ignore")
        if "CONVERIGO" in stream:
            found = True
    assert found, "watermark stamp text missing from page content streams"


def _verify_html(path: Path) -> None:
    body = path.read_text(encoding="utf-8")
    assert body.lstrip().lower().startswith("<!doctype html>")
    assert FIXTURE_TEXT_1 in body and FIXTURE_TEXT_2 in body
    # D5b honesty note must survive into the artifact itself.
    assert "NOT a layout-preserving conversion" in body


def _verify_md(path: Path) -> None:
    body = path.read_text(encoding="utf-8")
    assert "## Page 1" in body and "## Page 2" in body
    assert FIXTURE_TEXT_1 in body and FIXTURE_TEXT_2 in body


# ---------------------------------------------------------------------------
# Uniform factory contract: one parametrized pipeline for the whole cluster
# ---------------------------------------------------------------------------

CASES = [
    ("pdf-rotate", "pdf", _make_text_pdf, "application/pdf", _verify_rotate),
    (
        "pdf-unlock",
        "pdf",
        _make_owner_encrypted_pdf,
        "application/pdf",
        _verify_unlock,
    ),
    ("pdf-watermark", "pdf", _make_text_pdf, "application/pdf", _verify_watermark),
    ("pdf-metadata", "pdf", _make_text_pdf, "application/pdf", _verify_metadata),
    ("pdf-to-html", "html", _make_text_pdf, "application/pdf", _verify_html),
    ("pdf-to-md", "md", _make_text_pdf, "application/pdf", _verify_md),
]


@pytest.mark.certified
@pytest.mark.parametrize(
    "slug,target_format,builder,mime,verifier",
    [pytest.param(*case, id=case[0]) for case in CASES],
)
def test_factory_happy_path_uniform_contract(
    slug: str,
    target_format: str,
    builder,
    mime: str,
    verifier,
    tmp_path: Path,
) -> None:
    """Uniform pipeline: 201 -> download 200 -> content verified per case."""
    fixture = builder(tmp_path / f"fixture_{slug}.pdf")
    assert fixture.is_file(), f"fixture builder produced no file: {fixture}"
    output = run_happy_path(fixture, target_format, slug, mime=mime)
    try:
        verifier(output)
    finally:
        cleanup_output(output)


@pytest.mark.certified
@pytest.mark.parametrize(
    "slug,target_format",
    [(case[0], case[1]) for case in CASES],
)
def test_factory_honest_error_for_wrong_input_type(
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


# ---------------------------------------------------------------------------
# F3-specific: encryption honesty, corrupt input, MVP limitations
# ---------------------------------------------------------------------------

USER_PASSWORD_CASES = [
    ("pdf-unlock", "pdf", _make_user_encrypted_pdf),
    ("pdf-rotate", "pdf", _make_user_encrypted_pdf),
    ("pdf-to-md", "md", _make_user_encrypted_pdf),
]


@pytest.mark.certified
@pytest.mark.parametrize(
    "slug,target_format,builder",
    [pytest.param(s, t, b, id=f"{s}-user-password") for s, t, b in USER_PASSWORD_CASES],
)
def test_user_password_pdfs_get_honest_422(
    slug: str,
    target_format: str,
    builder,
    tmp_path: Path,
) -> None:
    """PDFs protected with a real user password are honestly unsupported
    (no silent partial output, no 500) - 422 UNSUPPORTED_CONVERSION."""
    fixture = builder(tmp_path / "user_locked.pdf")
    response = post_convert(fixture, target_format, slug)
    assert_honest_unsupported(response)


@pytest.mark.certified
@pytest.mark.parametrize(
    "slug,target_format",
    [(case[0], case[1]) for case in CASES],
)
def test_corrupt_pdf_gets_honest_422(
    slug: str,
    target_format: str,
    tmp_path: Path,
) -> None:
    """Undecodable PDF input never produces fabricated output."""
    fixture = _make_corrupt_pdf(tmp_path / "corrupt.pdf")
    response = post_convert(fixture, target_format, slug)
    assert_honest_unsupported(response)


@pytest.mark.certified
@pytest.mark.parametrize(
    "slug,target_format",
    [("pdf-to-html", "html"), ("pdf-to-md", "md")],
)
def test_mvp_text_extraction_honest_on_image_only_pdf(
    slug: str,
    target_format: str,
    tmp_path: Path,
) -> None:
    """D5b MVP limitation made explicit: image-only (scanned) PDFs have no
    extractable text, so the MVP converters answer with the honest 422
    error class instead of returning an empty fabricated file."""
    fixture = _make_image_only_pdf(tmp_path / "scan.pdf")
    response = post_convert(fixture, target_format, slug)
    assert_honest_unsupported(response)


@pytest.mark.certified
def test_unlock_accepts_unencrypted_pdf(tmp_path: Path) -> None:
    """pdf-unlock is idempotent on already-unrestricted files (201 + valid output)."""
    from tests.certified._factory_harness import resolve_output_path

    fixture = _make_text_pdf(tmp_path / "plain.pdf")
    response = post_convert(fixture, "pdf", "pdf-unlock")
    assert response.status_code == 201, response.text
    output = resolve_output_path(response)
    try:
        _verify_unlock(output)
    finally:
        cleanup_output(output)


# ---------------------------------------------------------------------------
# F3-specific: slug-aware self-pair resolution (pdf-compress precedent, D4)
# ---------------------------------------------------------------------------

SELF_PAIR_OPS = [
    "pdf-rotate",
    "pdf-unlock",
    "pdf-watermark",
    "pdf-metadata",
]


@pytest.mark.certified
def test_self_pair_operations_resolve_to_distinct_plugins() -> None:
    """Every (pdf, pdf) operation is reachable via its own slug and the four
    operations never overwrite each other at the slug level (the same
    slug-aware pattern as pdf-compress / pdf-split)."""
    from app.plugins.registry import registry

    resolved = []
    for slug in SELF_PAIR_OPS:
        assert registry.has_slug(slug), slug
        plugin = registry.get_plugin("pdf", "pdf", slug=slug)
        assert plugin.slug == slug
        resolved.append(type(plugin).__name__)

    assert len(set(resolved)) == len(SELF_PAIR_OPS), resolved


@pytest.mark.certified
def test_self_pair_legacy_pair_index_still_resolves() -> None:
    """The shared (pdf, pdf) legacy pair index still holds exactly one
    deterministic plugin (sorted module discovery -> last registered wins)."""
    from app.plugins.registry import registry

    legacy = registry.get_plugin("pdf", "pdf")
    assert legacy is not None
    assert legacy.slug == "pdf-split"
    assert registry.get_plugin("pdf", "pdf") is legacy


@pytest.mark.certified
def test_cross_format_targets_and_dropdown_map() -> None:
    """The two cross-format converters extend the pdf target set with html
    and md only; self-pair operations never leak into the derived map, and
    html/md stay download-only formats (never sources)."""
    from app.plugins.registry import registry

    for slug in ("pdf-to-html", "pdf-to-md"):
        assert registry.has_slug(slug), slug

    pdf_targets = {
        tgt
        for (src, tgt) in registry.plugins
        if src == "pdf" and tgt != "pdf"
    }
    assert pdf_targets == {
        "doc", "docx", "html", "jpeg", "jpg", "md", "odt",
        "ppt", "pptx", "txt", "word", "xls", "xlsx",
    }
    assert ("pdf", "pdf") in registry.plugins  # ops live here, off the map

    sources = {src for (src, _tgt) in registry.plugins}
    assert "html" not in sources and "md" not in sources
