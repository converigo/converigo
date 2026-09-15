"""
PROJECT: CONVERIGO
TEST SUITE: Certified PDF -> EPUB converter (text-only MVP)

Certified-level coverage for app/plugins/document/pdf_to_epub.py and its runner
app/factory/pdf_epub_runner.py.

Why the tests are shaped like this:

* The fixtures under tests/fixtures/pdf_to_epub are the preparation-phase
  evidence, promoted and re-measured here: test_fixtures_manifest_is_still_true
  reads the committed manifest and re-derives every property from the file bytes,
  so no test can quietly pass against a fixture that stopped being true.
* Extraction truth is checked line by line against MuPDF itself, not against a
  hand-written expectation, which is the only assertion that can catch a
  converter that invents, drops or reorders text.
* Ceilings are proved at the approved production value with a fixture that really
  exceeds it (501 pages, 81,200 characters on one page), and at a lowered value
  for the ceilings no committable file can reach (cumulative characters, package
  bytes).  A lowered ceiling still exercises the real guard code.
* Refusals are asserted twice: the exact internal refusal kind from the runner,
  and the HTTP status, public code and non-leaking message at the API boundary.
"""

from __future__ import annotations

import asyncio
import json
import threading
import zipfile
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient
from lxml import etree
from pypdf import PdfReader

from app.core.settings import settings
from app.factory.pdf_epub_runner import (
    EPUB_MIME_TYPE,
    INPUT_REFUSALS,
    PLAIN_MESSAGE,
    REFUSE_CHAPTER_LIMIT,
    REFUSE_ENCRYPTED,
    REFUSE_MALFORMED,
    REFUSE_NO_PAGES,
    REFUSE_NO_TEXT,
    REFUSE_PAGE_CHARS_LIMIT,
    REFUSE_PAGE_LIMIT,
    REFUSE_PACKAGE_LIMIT,
    REFUSE_REPAIRED,
    REFUSE_TIME_BUDGET,
    REFUSE_TOTAL_CHARS_LIMIT,
    EpubLimits,
    PdfToEpubError,
    convert_pdf_to_epub,
)
from app.main import app
from app.plugins.registry import registry
from app.services.converter_data_service import ConverterDataService
from app.services.target_capability import build_capability

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "pdf_to_epub"
REPO_ROOT = Path(__file__).resolve().parents[3]
CONVERTERS_DIR = REPO_ROOT / "app" / "data" / "converters"
MANIFEST = json.loads(
    (FIXTURE_DIR / "fixtures_manifest.json").read_text(encoding="utf-8")
)["fixtures"]
OUTPUT_DIR = settings.OUTPUT_DIR

XHTML_NS = "http://www.w3.org/1999/xhtml"
OPF_NS = "http://www.idpf.org/2007/opf"
NCX_NS = "http://www.daisy.org/z3986/2005/ncx/"
CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"

POSITIVE = sorted(n for n, m in MANIFEST.items() if m["kind"] == "positive")
REFUSALS = sorted(n for n, m in MANIFEST.items() if m["kind"] == "refusal")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def fixture_path(name: str) -> Path:
    path = FIXTURE_DIR / name
    assert path.exists(), f"committed fixture is missing: {name}"
    return path


def limits_with(**overrides) -> EpubLimits:
    """The approved production ceilings, with one named override per test."""
    values = {
        "max_pages": settings.PDF_EPUB_MAX_PAGES,
        "max_chars": settings.PDF_EPUB_MAX_CHARS,
        "max_page_chars": settings.PDF_EPUB_MAX_PAGE_CHARS,
        "max_package_bytes": settings.PDF_EPUB_MAX_PACKAGE_BYTES,
        "max_chapters": settings.PDF_EPUB_MAX_CHAPTERS,
        "time_budget_seconds": settings.PDF_EPUB_TIME_BUDGET_SECONDS,
    }
    values.update(overrides)
    return EpubLimits(**values)


def build(tmp_path: Path, name: str, **ceilings):
    """Run the runner on a committed fixture, writing into tmp_path."""
    output = tmp_path / "out.epub"
    report = convert_pdf_to_epub(fixture_path(name), output, limits_with(**ceilings))
    return output, report


def read_part(package: Path, entry: str) -> bytes:
    with zipfile.ZipFile(package) as archive:
        return archive.read(entry)


def package_entries(package: Path) -> list[str]:
    with zipfile.ZipFile(package) as archive:
        return [info.filename for info in archive.infolist()]


def chapter_lines(package: Path, position: int) -> list[str]:
    """Every non-empty paragraph of one chapter document, in document order."""
    root = etree.fromstring(read_part(package, f"EPUB/chapter-{position:03d}.xhtml"))
    return [
        (node.text or "").strip()
        for node in root.iter(f"{{{XHTML_NS}}}p")
        if (node.text or "").strip()
    ]


def expected_page_lines(name: str, page_index: int) -> list[str]:
    """The lines MuPDF extracts from one page of the fixture, verbatim."""
    with fitz.open(str(fixture_path(name))) as doc:
        return [
            line.strip()
            for line in (doc[page_index].get_text() or "").splitlines()
            if line.strip()
        ]


def upload(client: TestClient, name: str, target: str = "epub", operation: str = "pdf-to-epub"):
    return client.post(
        "/convert",
        files=[
            (
                "file",
                (Path(name).name, fixture_path(name).read_bytes(), "application/pdf"),
            )
        ],
        data={"target_format": target, "operation": operation},
    )


def published_output(response) -> Path:
    download_path = response.json()["download_path"]
    assert download_path.startswith("/download/")
    parts = Path(download_path.removeprefix("/download/")).parts
    path = OUTPUT_DIR.joinpath(*parts)
    assert path.exists(), f"expected published output: {download_path}"
    return path


# ---------------------------------------------------------------------------
# Fixture integrity
# ---------------------------------------------------------------------------
@pytest.mark.certified
@pytest.mark.parametrize("name", sorted(MANIFEST))
def test_fixtures_manifest_is_still_true(name: str) -> None:
    """Re-derive every manifest claim from the committed bytes."""
    declared = MANIFEST[name]
    path = fixture_path(name)
    raw = path.read_bytes()

    try:
        reader = PdfReader(str(path))
        assert bool(reader.is_encrypted) is declared["encrypted"], (
            f"{name}: encryption state drifted"
        )
    except Exception as exc:  # noqa: BLE001 - unparseable is itself the claim
        assert declared["encrypted"] is False, f"{name}: {type(exc).__name__}"

    try:
        doc = fitz.open(stream=raw, filetype="pdf")
    except Exception:  # a fixture that cannot be opened proves the malformed case
        assert declared["refusal"] == REFUSE_MALFORMED, name
        return
    with doc:
        assert bool(doc.needs_pass) is bool(declared.get("mupdf_needs_pass", False))
        assert bool(doc.is_repaired) is bool(declared.get("mupdf_is_repaired", False))
        if "pages" in declared:
            assert doc.page_count == declared["pages"], f"{name}: page count drifted"
        if "chars" in declared:
            total = sum(len(doc[i].get_text() or "") for i in range(doc.page_count))
            assert total == declared["chars"], f"{name}: extracted chars drifted"
        if "max_page_chars" in declared:
            longest = max(len(doc[i].get_text() or "") for i in range(doc.page_count))
            assert longest <= declared["max_page_chars"], f"{name}: page got denser"
        for marker in declared.get("markers", []):
            body = "".join(doc[i].get_text() or "" for i in range(doc.page_count))
            assert marker in body, f"{name}: marker {marker!r} no longer extractable"


def test_refusal_fixtures_are_disjoint_from_positive_ones() -> None:
    """No fixture can be used to prove both acceptance and refusal."""
    assert set(POSITIVE).isdisjoint(REFUSALS)
    for name in REFUSALS:
        assert MANIFEST[name]["refusal"] in INPUT_REFUSALS


# ---------------------------------------------------------------------------
# 1-2. Happy path and multi-page
# ---------------------------------------------------------------------------
@pytest.mark.certified
def test_happy_path_single_page_pdf_becomes_a_valid_epub() -> None:
    client = TestClient(app)
    response = upload(client, "epub_text_1p_minimal.pdf")
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["target_format"] == "epub"
    assert payload["filename"].endswith(".epub")

    package = published_output(response)
    try:
        assert package.read_bytes()[:2] == b"PK"
        assert "EPUB/chapter-001.xhtml" in package_entries(package)
        assert chapter_lines(package, 1) == expected_page_lines(
            "epub_text_1p_minimal.pdf", 0
        )
    finally:
        package.unlink(missing_ok=True)


@pytest.mark.certified
def test_multi_page_pdf_produces_one_chapter_per_page(tmp_path: Path) -> None:
    package, report = build(tmp_path, "epub_text_3p.pdf")
    assert (report.pages, report.chapters) == (3, 3)
    entries = package_entries(package)
    assert [e for e in entries if e.startswith("EPUB/chapter-")] == [
        "EPUB/chapter-001.xhtml",
        "EPUB/chapter-002.xhtml",
        "EPUB/chapter-003.xhtml",
    ]
    for position in range(1, 4):
        assert chapter_lines(package, position) == expected_page_lines(
            "epub_text_3p.pdf", position - 1
        )
    # The spine order is the page order, not an arbitrary manifest order.
    spine = etree.fromstring(read_part(package, "EPUB/content.opf")).findall(
        f".//{{{OPF_NS}}}spine/{{{OPF_NS}}}itemref"
    )
    assert [node.get("idref") for node in spine] == ["ch1", "ch2", "ch3"]


@pytest.mark.certified
def test_mixed_text_and_image_pages_keep_their_text(tmp_path: Path) -> None:
    """The image-only middle page yields an empty page block, never filler text."""
    package, report = build(tmp_path, "epub_mixed_text_image.pdf")
    assert (report.pages, report.chapters) == (3, 3)
    assert chapter_lines(package, 1) == expected_page_lines("epub_mixed_text_image.pdf", 0)
    assert chapter_lines(package, 2) == [], "invented text for a page with no text layer"
    assert chapter_lines(package, 3) == expected_page_lines("epub_mixed_text_image.pdf", 2)
    assert "MIXED PAGE 1 MARKER-1" in chapter_lines(package, 1)[0]



# ---------------------------------------------------------------------------
# 3-4. Content truth across every positive fixture
# ---------------------------------------------------------------------------
@pytest.mark.certified
@pytest.mark.parametrize("name", POSITIVE)
def test_extracted_text_is_truthful_line_by_line(tmp_path: Path, name: str) -> None:
    package, report = build(tmp_path, name)
    pages_per_chapter = -(-report.pages // report.chapters)
    for position in range(1, report.chapters + 1):
        produced: list[str] = []
        for offset in range(pages_per_chapter):
            page_index = (position - 1) * pages_per_chapter + offset
            if page_index >= report.pages:
                break
            produced.extend(expected_page_lines(name, page_index))
        assert chapter_lines(package, position) == produced, (
            f"{name}: chapter {position} does not match the MuPDF extraction"
        )


@pytest.mark.certified
def test_unicode_survives_the_conversion(tmp_path: Path) -> None:
    package, _ = build(tmp_path, "epub_utf8_cjk.pdf")
    document = read_part(package, "EPUB/chapter-001.xhtml").decode("utf-8")
    assert chapter_lines(package, 1)[0] == "CJK MARKER-777"
    assert "\u65e5\u672c\u8a9e" in document  # Japanese
    assert "\u4e2d\u6587" in document  # Chinese
    assert "\u05e9\u05dc\u05d5\u05dd" in document  # Hebrew


@pytest.mark.certified
def test_latin1_era_characters_are_preserved_not_mojibake(tmp_path: Path) -> None:
    package, _ = build(tmp_path, "epub_text_3p.pdf")
    joined = "\n".join(chapter_lines(package, 1))
    assert "CP1252: \u00dcnicode na\u00efve r\u00e9sum\u00e9" in joined, repr(joined)
    assert "\u201equotes\u201c" in joined, repr(joined)


@pytest.mark.certified
def test_every_page_marker_survives_a_24_page_book(tmp_path: Path) -> None:
    package, report = build(tmp_path, "epub_multipage_24p.pdf")
    assert (report.pages, report.chapters) == (24, 24)
    blob = "".join(
        read_part(package, entry).decode("utf-8")
        for entry in package_entries(package)
        if entry.endswith(".xhtml")
    )
    for page in range(1, 25):
        assert f"PAGE {page} MARKER-{page:04d}" in blob, f"page {page} text was lost"


# ---------------------------------------------------------------------------
# 5-7. Container structure, mimetype member, round-trip
# ---------------------------------------------------------------------------
@pytest.mark.certified
def test_package_is_a_clean_zip_with_the_required_parts(tmp_path: Path) -> None:
    package, report = build(tmp_path, "epub_text_3p.pdf")
    with zipfile.ZipFile(package) as archive:
        assert archive.testzip() is None
        names = [info.filename for info in archive.infolist()]
    assert names == [
        "mimetype",
        "META-INF/container.xml",
        "EPUB/content.opf",
        "EPUB/toc.ncx",
        "EPUB/nav.xhtml",
        "EPUB/style.css",
        "EPUB/chapter-001.xhtml",
        "EPUB/chapter-002.xhtml",
        "EPUB/chapter-003.xhtml",
    ]
    assert report.chapters == 3


@pytest.mark.certified
def test_mimetype_entry_is_first_stored_uncompressed_and_exact(tmp_path: Path) -> None:
    package, _ = build(tmp_path, "epub_text_1p_minimal.pdf")
    with zipfile.ZipFile(package) as archive:
        first = archive.infolist()[0]
        assert first.filename == "mimetype"
        assert first.compress_type == zipfile.ZIP_STORED
        assert first.extra == b""
        assert archive.read("mimetype") == EPUB_MIME_TYPE.encode("ascii")
    # Raw check: the 30-byte local header plus the 8-byte name put the stored
    # payload at a fixed offset, uncompressed, at the very start of the archive.
    assert package.read_bytes()[38:58] == EPUB_MIME_TYPE.encode("ascii")


@pytest.mark.certified
def test_epub_round_trips_through_mupdf(tmp_path: Path) -> None:
    """Re-open the book with the same engine family and check text + outline."""
    package, report = build(tmp_path, "epub_dense_8p_chars.pdf")
    with fitz.open(str(package)) as book:
        assert book.page_count >= 1
        text = "".join(book[i].get_text() for i in range(book.page_count))
        assert "DENSE PAGE 1 MARKER" in text
        assert "DENSE PAGE 8 MARKER" in text
        toc = book.get_toc()
        assert len(toc) == report.chapters == 8
        assert toc[0][1] == "Chapter 1 (Page 1)"


@pytest.mark.certified
def test_package_document_is_well_formed_and_self_consistent(tmp_path: Path) -> None:
    package, report = build(tmp_path, "epub_multipage_24p.pdf")
    entries = set(package_entries(package))
    container = etree.fromstring(read_part(package, "META-INF/container.xml"))
    rootfile = container.findall(
        f"{{{CONTAINER_NS}}}rootfiles/{{{CONTAINER_NS}}}rootfile"
    )
    assert len(rootfile) == 1
    assert rootfile[0].get("full-path") == "EPUB/content.opf"
    assert rootfile[0].get("media-type") == "application/oebps-package+xml"

    opf = etree.fromstring(read_part(package, "EPUB/content.opf"))
    items = opf.findall(f".//{{{OPF_NS}}}manifest/{{{OPF_NS}}}item")
    hrefs = {item.get("href") for item in items}
    assert {f"chapter-{i:03d}.xhtml" for i in range(1, report.chapters + 1)} <= hrefs
    for href in hrefs:
        assert f"EPUB/{href}" in entries, f"dangling manifest href {href}"
    ncx = etree.fromstring(read_part(package, "EPUB/toc.ncx"))
    assert len(ncx.findall(f".//{{{NCX_NS}}}navPoint")) == report.chapters


@pytest.mark.certified
def test_output_extension_is_epub_and_download_declares_the_media_type() -> None:
    client = TestClient(app)
    response = upload(client, "epub_text_1p_minimal.pdf")
    assert response.status_code == 201, response.text
    download_path = response.json()["download_path"]
    assert download_path.endswith(".epub")

    served = client.get(download_path)
    assert served.status_code == 200
    assert served.headers["content-type"].startswith(EPUB_MIME_TYPE)
    assert "attachment" in served.headers.get("content-disposition", "")
    assert served.content[:2] == b"PK"
    published_output(response).unlink(missing_ok=True)



# ---------------------------------------------------------------------------
# 9-11. Honest refusals at the API boundary
# ---------------------------------------------------------------------------
def assert_refused(client: TestClient, name: str) -> dict:
    response = upload(client, name)
    assert response.status_code == 422, f"{name}: {response.status_code} {response.text}"
    body = response.json()
    assert body["code"] == "UNSUPPORTED_CONVERSION", body
    assert isinstance(body["message"], str) and body["message"]
    return body


@pytest.mark.certified
@pytest.mark.parametrize(
    "name", [n for n, m in MANIFEST.items() if m.get("refusal") == REFUSE_ENCRYPTED]
)
def test_encrypted_pdf_is_refused_with_an_honest_422(name: str) -> None:
    """Every /Encrypt PDF is refused - including the owner-only MuPDF cannot see."""
    with pytest.raises(PdfToEpubError) as raised:
        convert_pdf_to_epub(fixture_path(name), Path("must-not-be-created.epub"))
    assert raised.value.kind == REFUSE_ENCRYPTED
    assert raised.value.is_input_refusal
    body = assert_refused(TestClient(app), name)
    assert "encrypt" in body["message"].lower() or "restricted" in body["message"].lower()


def test_owner_only_fixture_would_have_slipped_past_mupdf_alone() -> None:
    """Prove the pypdf guard is load-bearing rather than decorative.

    If MuPDF ever starts reporting this file, the guard stays correct but the
    premise of the test changes, and that must be a conscious decision rather
    than a silent pass - so the contradiction is asserted explicitly.
    """
    name = "epub_encrypted_owner_only.pdf"
    raw = fixture_path(name).read_bytes()
    with fitz.open(stream=raw, filetype="pdf") as doc:
        assert doc.needs_pass == 0
        assert doc.is_encrypted is False
    assert PdfReader(str(fixture_path(name))).is_encrypted is True
    assert b"/Encrypt" in raw


@pytest.mark.certified
@pytest.mark.parametrize(
    "name", [n for n, m in MANIFEST.items() if m.get("refusal") == REFUSE_MALFORMED]
)
def test_malformed_pdf_is_refused_with_an_honest_422(name: str) -> None:
    with pytest.raises(PdfToEpubError) as raised:
        convert_pdf_to_epub(fixture_path(name), Path("must-not-be-created.epub"))
    assert raised.value.kind == REFUSE_MALFORMED
    if fixture_path(name).read_bytes()[:5] == b"%PDF-":
        assert_refused(TestClient(app), name)


@pytest.mark.certified
def test_repaired_pdf_is_refused_because_partial_text_is_not_truth() -> None:
    with pytest.raises(PdfToEpubError) as raised:
        convert_pdf_to_epub(
            fixture_path("epub_truncated.pdf"),
            Path("must-not-be-created.epub"),
            limits_with(),
        )
    assert raised.value.kind == REFUSE_REPAIRED
    assert_refused(TestClient(app), "epub_truncated.pdf")


@pytest.mark.certified
def test_zero_text_pdf_is_refused_and_no_empty_book_is_shipped(tmp_path: Path) -> None:
    with pytest.raises(PdfToEpubError) as raised:
        build(tmp_path, "epub_image_only.pdf")
    assert raised.value.kind == REFUSE_NO_TEXT
    assert not (tmp_path / "out.epub").exists(), "refusal left a file behind"
    assert_refused(TestClient(app), "epub_image_only.pdf")


@pytest.mark.certified
def test_pageless_pdf_is_refused(tmp_path: Path) -> None:
    with pytest.raises(PdfToEpubError) as raised:
        build(tmp_path, "epub_zero_page.pdf")
    assert raised.value.kind == REFUSE_NO_PAGES
    assert not (tmp_path / "out.epub").exists()



# ---------------------------------------------------------------------------
# 12-16. Mandatory ceilings
# ---------------------------------------------------------------------------
@pytest.mark.certified
def test_page_ceiling_at_the_approved_value(tmp_path: Path) -> None:
    """501 real pages against the production limit of 500."""
    assert settings.PDF_EPUB_MAX_PAGES == 500
    assert MANIFEST["epub_over_500pages.pdf"]["pages"] == 501
    with pytest.raises(PdfToEpubError) as raised:
        build(tmp_path, "epub_over_500pages.pdf")
    assert raised.value.kind == REFUSE_PAGE_LIMIT
    assert not (tmp_path / "out.epub").exists()
    assert_refused(TestClient(app), "epub_over_500pages.pdf")


@pytest.mark.certified
def test_per_page_character_ceiling_at_the_approved_value(tmp_path: Path) -> None:
    """1,973 bytes that amplify to 81,200 characters if allowed to run."""
    assert settings.PDF_EPUB_MAX_PAGE_CHARS == 10_000
    assert MANIFEST["epub_over_page_chars.pdf"]["chars"] == 81_200
    with pytest.raises(PdfToEpubError) as raised:
        build(tmp_path, "epub_over_page_chars.pdf")
    assert raised.value.kind == REFUSE_PAGE_CHARS_LIMIT
    assert "10000" in raised.value.client_message
    assert not (tmp_path / "out.epub").exists()


@pytest.mark.certified
def test_cumulative_character_ceiling_is_enforced(tmp_path: Path) -> None:
    assert settings.PDF_EPUB_MAX_CHARS == 2_000_000
    # The production value is unreachable with a committable fixture, so the
    # same guard runs against a dense multi-page file at a lowered value, while
    # the assertion above pins the wired-up production number.
    total = MANIFEST["epub_dense_8p_chars.pdf"]["chars"]
    with pytest.raises(PdfToEpubError) as raised:
        build(tmp_path, "epub_dense_8p_chars.pdf", max_chars=total - 1)
    assert raised.value.kind == REFUSE_TOTAL_CHARS_LIMIT
    assert not (tmp_path / "out.epub").exists()
    # One character more and the same document converts: what stopped the run
    # was the ceiling, not a blanket refusal of this fixture.
    package, report = build(tmp_path, "epub_dense_8p_chars.pdf", max_chars=total)
    assert report.chars == total
    assert package.exists()


@pytest.mark.certified
def test_package_size_ceiling_is_enforced(tmp_path: Path) -> None:
    assert settings.PDF_EPUB_MAX_PACKAGE_BYTES == 5_000_000
    with pytest.raises(PdfToEpubError) as raised:
        build(tmp_path, "epub_multipage_24p.pdf", max_package_bytes=2_000)
    assert raised.value.kind == REFUSE_PACKAGE_LIMIT
    assert not (tmp_path / "out.epub").exists(), "oversized package was left on disk"


@pytest.mark.certified
def test_chapter_ceiling_holds_by_the_pagination_rule() -> None:
    assert settings.PDF_EPUB_MAX_CHAPTERS == 120
    from app.factory.pdf_epub_runner import _chapter_plan

    for pages in (1, 2, 119, 120, 121, 240, 499, 500):
        per_chapter, chapters = _chapter_plan(pages, 120)
        assert chapters <= 120
        assert chapters * per_chapter >= pages
        assert (chapters - 1) * per_chapter < pages
    assert _chapter_plan(500, 120) == (5, 100)
    assert _chapter_plan(24, 120) == (1, 24)
    # A misconfigured ceiling refuses instead of producing an unbounded book.
    with pytest.raises(PdfToEpubError) as raised:
        _chapter_plan(10, 0)
    assert raised.value.kind == REFUSE_CHAPTER_LIMIT


@pytest.mark.certified
def test_time_budget_is_enforced_inside_the_loop_without_output(tmp_path: Path) -> None:
    """A spent budget stops the run and leaves nothing servable."""
    assert settings.PDF_EPUB_TIME_BUDGET_SECONDS == 45
    output = tmp_path / "out.epub"
    with pytest.raises(PdfToEpubError) as raised:
        convert_pdf_to_epub(
            fixture_path("epub_multipage_24p.pdf"),
            output,
            limits_with(time_budget_seconds=0),
        )
    assert raised.value.kind == REFUSE_TIME_BUDGET
    assert not raised.value.is_input_refusal, "a timeout must not masquerade as a 422"
    assert raised.value.client_message == PLAIN_MESSAGE
    assert not output.exists()


@pytest.mark.certified
def test_settings_defaults_are_the_approved_limits() -> None:
    assert settings.PDF_EPUB_MAX_PAGES == 500
    assert settings.PDF_EPUB_MAX_CHARS == 2_000_000
    assert settings.PDF_EPUB_MAX_PAGE_CHARS == 10_000
    assert settings.PDF_EPUB_MAX_PACKAGE_BYTES == 5_000_000
    assert settings.PDF_EPUB_MAX_CHAPTERS == 120
    assert settings.PDF_EPUB_TIME_BUDGET_SECONDS == 45



# ---------------------------------------------------------------------------
# 18. No internal leakage
# ---------------------------------------------------------------------------
LEAK_MARKERS = (
    "Traceback",
    "app/plugins",
    "app/factory",
    "pdf_epub_runner",
    "PDFToEPUBPlugin",
    "UnsupportedConversionError",
    "PdfToEpubError",
    "fitz",
    "MuPDF",
    "pypdf",
    "PyMuPDF",
    "RuntimeError",
    ".py",
)


@pytest.mark.certified
def test_refusal_messages_do_not_leak_internals() -> None:
    """Static client wording: no class names, modules, engines or paths."""
    for name in REFUSALS:
        with pytest.raises(PdfToEpubError) as raised:
            convert_pdf_to_epub(
                fixture_path(name), Path("must-not-be-created.epub"), limits_with()
            )
        message = raised.value.client_message
        assert message, name
        for marker in LEAK_MARKERS:
            assert marker not in message, f"{name}: leaked {marker!r} in {message!r}"
        assert "\\" not in message and "C:" not in message, f"{name}: path-like text"
        # The refusal kind is internal vocabulary and must not surface either.
        assert raised.value.kind not in message


@pytest.mark.certified
def test_http_refusal_body_carries_no_paths_or_exception_text() -> None:
    client = TestClient(app)
    for name in (
        "epub_encrypted_owner_only.pdf",
        "epub_image_only.pdf",
        "epub_truncated.pdf",
    ):
        body = assert_refused(client, name)
        text = json.dumps(body)
        for marker in ("C:\\", "app/", ".py", "Traceback", "fitz", "pypdf", "MuPDF"):
            assert marker not in text, f"{name}: {marker!r} reached the client"
        assert str(settings.TEMP_DIR) not in text
        assert str(settings.OUTPUT_DIR) not in text


# ---------------------------------------------------------------------------
# 19. Content safety: metadata cannot reach structure
# ---------------------------------------------------------------------------
ALLOWED_ENTRIES = {
    "mimetype",
    "META-INF/container.xml",
    "EPUB/content.opf",
    "EPUB/toc.ncx",
    "EPUB/nav.xhtml",
    "EPUB/style.css",
    "EPUB/chapter-001.xhtml",
}


@pytest.mark.certified
def test_evil_metadata_cannot_become_a_path_or_live_markup(tmp_path: Path) -> None:
    package, _ = build(tmp_path, "epub_evil_metadata.pdf")
    entries = package_entries(package)
    assert set(entries) == ALLOWED_ENTRIES, "an entry name was derived from the input"
    for entry in entries:
        assert ".." not in entry and "\\" not in entry and not entry.startswith("/")

    opf = read_part(package, "EPUB/content.opf").decode("utf-8")
    ncx = read_part(package, "EPUB/toc.ncx").decode("utf-8")
    nav = read_part(package, "EPUB/nav.xhtml").decode("utf-8")
    blob = opf + ncx + nav
    # The script tag survives only in escaped form; the traversal string only as
    # inert text inside one element.  Nothing executable came through.
    assert "&lt;script&gt;" in blob
    assert "<script>" not in blob
    assert "onerror=" not in blob
    for payload in (opf, ncx, nav):
        etree.fromstring(payload.encode("utf-8"))


@pytest.mark.certified
def test_xml_specials_in_body_text_are_escaped_not_executed(tmp_path: Path) -> None:
    package, _ = build(tmp_path, "epub_text_3p.pdf")
    document = read_part(package, "EPUB/chapter-001.xhtml").decode("utf-8")
    assert "&lt;tag&gt;" in document and "<tag>" not in document
    assert "&amp;amp;" in document  # the page literally contains "&amp;"
    lines = chapter_lines(package, 1)
    assert any("XML specials: <tag> &amp;" in line for line in lines), lines



# ---------------------------------------------------------------------------
# Async safety: the blocking engine must never run on the event loop
# ---------------------------------------------------------------------------
@pytest.mark.certified
def test_conversion_runs_off_the_event_loop(monkeypatch, tmp_path: Path) -> None:
    from app.factory.pdf_epub_runner import EpubBuildReport
    from app.plugins.document import pdf_to_epub as plugin_module

    seen: dict[str, str] = {}

    def fake_runner(source_path, output_path, limits=None):
        seen["worker"] = threading.current_thread().name
        Path(output_path).write_bytes(b"PK\x03\x04stub")
        return EpubBuildReport(1, 1, 1, 8, 1)

    monkeypatch.setattr(plugin_module, "convert_pdf_to_epub", fake_runner)
    plugin = plugin_module.PDFToEPUBPlugin()

    async def drive():
        loop_thread = threading.current_thread().name
        produced = await plugin.convert(
            fixture_path("epub_text_1p_minimal.pdf"), "epub", output_dir=tmp_path
        )
        return loop_thread, produced

    loop_thread, produced = asyncio.run(drive())
    assert produced.exists()
    assert seen["worker"] != loop_thread, "MuPDF ran on the event loop thread"


@pytest.mark.certified
def test_input_refusal_becomes_the_typed_422_error(monkeypatch, tmp_path: Path) -> None:
    from app.plugins.document import pdf_to_epub as plugin_module
    from app.services.conversion_service import UnsupportedConversionError

    def refuse(source_path, output_path, limits=None):
        raise PdfToEpubError(REFUSE_ENCRYPTED, "static refusal", detail="internal only")

    monkeypatch.setattr(plugin_module, "convert_pdf_to_epub", refuse)
    plugin = plugin_module.PDFToEPUBPlugin()

    async def drive():
        with pytest.raises(UnsupportedConversionError) as raised:
            await plugin.convert(
                fixture_path("epub_text_1p_minimal.pdf"), "epub", output_dir=tmp_path
            )
        return str(raised.value)

    assert asyncio.run(drive()) == "static refusal"


@pytest.mark.certified
def test_resource_failure_becomes_a_generic_error_not_a_422(
    monkeypatch, tmp_path: Path
) -> None:
    """A spent budget must not be dressed up as an honest input refusal."""
    from app.plugins.document import pdf_to_epub as plugin_module
    from app.services.conversion_service import UnsupportedConversionError

    def exhaust(source_path, output_path, limits=None):
        raise PdfToEpubError(REFUSE_TIME_BUDGET, PLAIN_MESSAGE, detail="budget spent")

    monkeypatch.setattr(plugin_module, "convert_pdf_to_epub", exhaust)
    plugin = plugin_module.PDFToEPUBPlugin()

    async def drive():
        try:
            await plugin.convert(
                fixture_path("epub_text_1p_minimal.pdf"), "epub", output_dir=tmp_path
            )
        except UnsupportedConversionError:  # pragma: no cover - the failure mode
            return "unsupported"
        except RuntimeError as exc:
            return str(exc)
        return "no-error"  # pragma: no cover

    assert asyncio.run(drive()) == PLAIN_MESSAGE



# ---------------------------------------------------------------------------
# 20-21. Target authority, dispatchability and discovery
# ---------------------------------------------------------------------------
@pytest.mark.certified
def test_plugin_is_discovered_and_registered() -> None:
    assert "pdf-to-epub" in registry.discovery_summary["loaded_plugins"]
    skipped = [item["plugin"] for item in registry.discovery_summary["skipped_plugins"]]
    assert not [name for name in skipped if "pdf_to_epub" in name]

    pair_plugin = registry.get_plugin("pdf", "epub")
    assert pair_plugin.slug == "pdf-to-epub"
    assert registry.get_plugin("pdf", "epub", slug="pdf-to-epub") is pair_plugin
    assert pair_plugin.registration_pairs() == [("pdf", "epub")]
    assert pair_plugin.advertisable is True


@pytest.mark.certified
def test_target_authority_offers_pdf_to_epub_only_because_it_dispatches() -> None:
    """D5 parity: what is offered is exactly what the registry can dispatch."""
    view = build_capability(registry=registry)
    assert "epub" in view.map.get("pdf", [])
    assert not [item for item in view.rejections if item.startswith("pdf->epub")]

    # Every offered target for every source must still resolve to a plugin, so a
    # new pair cannot be advertised without being dispatchable.
    for source, targets in view.map.items():
        for target in targets:
            plugin = registry.get_plugin(source, target)
            assert (source, target) in plugin.registration_pairs()


def test_epub_input_is_not_a_capability() -> None:
    """EPUB is an output only: no fabricated input side was created."""
    with pytest.raises(ValueError):
        registry.get_plugin("epub", "pdf")
    with pytest.raises(ValueError):
        registry.get_plugin("epub", "txt")
    assert "epub" not in build_capability(registry=registry).map


@pytest.mark.certified
def test_converter_json_contract_and_plugin_are_atomic() -> None:
    """No phantom tool: JSON, contract and a dispatchable plugin arrive together."""
    from app.services.converter_data_service import ConverterDataService
    from app.services.converter_registry_service import ConverterRegistryService

    data_dir = CONVERTERS_DIR
    contract = ConverterRegistryService(data_dir).get_by_slug("pdf-to-epub")
    assert contract is not None, "converter JSON shipped without a contract"
    assert contract["input_formats"] == ["pdf"]
    assert contract["output_formats"] == ["epub"]
    assert contract["accepted_mime_types"] == ["application/pdf"]
    sample = REPO_ROOT / contract["regression_sample"]
    assert sample.exists(), f"declared regression sample is missing: {sample}"

    data_service = ConverterDataService(data_dir)
    tool = data_service.load_converter_by_slug("pdf-to-epub")
    assert tool["source"] == "pdf" and tool["target"] == "epub"
    assert tool in data_service.list_public_converters()
    # The reason it is public is that the pair really dispatches.
    assert registry.get_plugin("pdf", "epub").slug == "pdf-to-epub"


@pytest.mark.certified
def test_existing_pdf_targets_still_resolve() -> None:
    """Adding a target must not steal or break an established pair.

    The expected slug per pair is the measured baseline fact: the (pdf, docx)
    pair is owned by pdf-to-word and (pdf, xlsx) by pdf-to-excel, so the names
    below are what has to keep working after pdf-to-epub registers.
    """
    for target, slug in (
        ("txt", "pdf-to-txt"),
        ("odt", "pdf-to-odt"),
        ("docx", "pdf-to-word"),
        ("html", "pdf-to-html"),
        ("md", "pdf-to-md"),
        ("xlsx", "pdf-to-excel"),
        ("jpg", "pdf-to-jpg"),
        ("epub", "pdf-to-epub"),
    ):
        assert registry.get_plugin("pdf", target).slug == slug
    # The recommendation ranking for pdf is untouched: this MVP converter sits
    # below the mature workhorses on purpose.
    assert registry.get_best_plugin("pdf").slug != "pdf-to-epub"


@pytest.mark.certified
def test_download_mime_is_declared_without_the_system_mime_database(monkeypatch) -> None:
    """The response type is declared by Converigo, not guessed from the host."""
    import mimetypes

    from app.main import EXPLICIT_DOWNLOAD_MEDIA_TYPES

    monkeypatch.setattr(mimetypes, "guess_type", lambda name: (None, None))
    assert EXPLICIT_DOWNLOAD_MEDIA_TYPES[".epub"] == EPUB_MIME_TYPE



# ---------------------------------------------------------------------------
# Phantom-tool protection
#
# The audit found that the universal tool page can be driven by converter JSON
# before the pair is dispatchable.  These tests pin the opposite direction: the
# capability must follow the registry, so removing the dispatchability removes
# the offer even while the JSON stays on disk.
# ---------------------------------------------------------------------------
class _RegistryWithoutPairs:
    """A registry view with the given pairs deleted."""

    def __init__(self, source_registry, dropped) -> None:
        self.plugins = {
            key: plugin
            for key, plugin in source_registry.plugins.items()
            if key not in dropped
        }
        self.by_slug = dict(source_registry.by_slug)
        self.slug_winner_pairs = dict(source_registry.slug_winner_pairs)


@pytest.mark.certified
def test_epub_target_disappears_when_the_pair_stops_dispatching() -> None:
    """The offer is derived from dispatchability, not from the JSON on disk."""
    assert "epub" in build_capability(registry=registry).map.get("pdf", [])

    stripped = _RegistryWithoutPairs(registry, {("pdf", "epub")})
    view = build_capability(registry=stripped)
    assert "epub" not in view.map.get("pdf", [])
    assert "epub" in build_capability(registry=registry).map.get("pdf", [])


@pytest.mark.certified
def test_tool_page_is_live_and_matches_a_dispatchable_pair() -> None:
    """A /tools/<slug> page exists only because the converter really converts."""
    response = TestClient(app).get("/tools/pdf-to-epub")
    assert response.status_code == 200, response.status_code
    plugin = registry.get_plugin("pdf", "epub", slug="pdf-to-epub")
    assert plugin.supports(".pdf", "epub")

    entries = ConverterDataService(CONVERTERS_DIR).sitemap_entries("https://converigo.com")
    locs = {entry["loc"] for entry in entries}
    assert "https://converigo.com/tools/pdf-to-epub" in locs
    assert len(locs) == len(entries), "the sitemap emitted a duplicate URL"

