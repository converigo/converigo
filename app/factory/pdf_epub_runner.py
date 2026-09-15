"""
Project : Converigo
Version : 1.0.0

PDF -> EPUB runner (text-only MVP).

Everything blocking lives here: reading the input, extracting text with MuPDF,
assembling an EPUB 3 container with zipfile and validating it before it is
served.  The plugin (app/plugins/document/pdf_to_epub.py) owns none of that - it
only offloads this module to a worker thread and translates failures - so nothing
in here may ever touch asyncio.

Why each rule below exists (all of them were measured on real inputs during the
B1-B4 preparation phase; the ceilings are the supervisor-approved values):

* MuPDF (PyMuPDF) is the *only* text extractor.  pypdf is used solely as the
  dictionary-level encryption detector, because MuPDF's own ``needs_pass`` /
  ``is_encrypted`` flags can both read ``False`` for an owner-restricted file
  that still carries an /Encrypt dictionary (see _extract_document).
* Every ceiling is enforced before or during extraction, never after the EPUB has
  been built.  A 1,973-byte PDF with overlapping text runs produced 81,199
  characters (41x amplification), so the per-page ceiling is load-bearing and an
  output-size ceiling alone would not have stopped it.
* The container is validated before it is served: mimetype first and STORED,
  required parts present, every XML part well-formed, CRC clean, entry names from
  a closed set, and the result re-opened with MuPDF.  A refusal deletes the
  partial file.
* Nothing that reaches a client is built from exception text, a filesystem path,
  a class name or a PDF string.  Client-facing wording is a static literal (or a
  limit echoed from configuration as an int); the diagnosis stays in ``detail``
  for the server-side log record only.

Dependencies: PyMuPDF, pypdf, lxml, stdlib - all already required.
"""

from __future__ import annotations

import hashlib
import io
import logging
import re
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import fitz
from lxml import etree
from pypdf import PdfReader

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Container constants.
#
# These are literals, never derived from the uploaded filename, from PDF metadata
# or from any other input.  That is what makes "entry names are safe" provable
# instead of probable.
# ---------------------------------------------------------------------------
EPUB_MIME_TYPE = "application/epub+zip"
#: Required first member of the archive; its name and bytes are fixed by the spec.
MIMETYPE_ENTRY_NAME = "mimetype"
CONTAINER_FILE_NAME = "META-INF/container.xml"
PACKAGE_DIR = "EPUB"
PACKAGE_FILE_NAME = PACKAGE_DIR + "/content.opf"
NCX_FILE_NAME = PACKAGE_DIR + "/toc.ncx"
NAV_FILE_NAME = PACKAGE_DIR + "/nav.xhtml"
CSS_FILE_NAME = PACKAGE_DIR + "/style.css"
CHAPTER_PREFIX = PACKAGE_DIR + "/chapter-"
CHAPTER_SUFFIX = ".xhtml"
#: container.xml points at the package document with this exact name.
CONTAINER_ROOTFILE_PATH = PACKAGE_FILE_NAME

OPF_NAMESPACE = "http://www.idpf.org/2007/opf"
DC_NAMESPACE = "http://purl.org/dc/elements/1.1/"
XHTML_NAMESPACE = "http://www.w3.org/1999/xhtml"
NCX_NAMESPACE = "http://www.daisy.org/z3986/2005/ncx/"
CONTAINER_NAMESPACE = "urn:oasis:names:tc:opendocument:xmlns:container"
EPUB_TYPE_NAMESPACE = "http://www.idpf.org/2007/ops"
XML_LANGUAGE_ATTRIBUTE = "{http://www.w3.org/XML/1998/namespace}lang"

#: Fixed CSS: no remote fonts, no images, nothing that can fetch or leak.
STYLE_SHEET = "\n".join(
    (
        "body{margin:1em;line-height:1.5}",
        "h1,h2{font-weight:bold;margin:1em 0 0.5em}",
        "p{margin:0 0 0.5em}",
        ".converigo-page{margin-top:2em}",
        "",
    )
)


# ---------------------------------------------------------------------------
# Refusal kinds.  The kind is internal (log record + plugin routing); only
# CLIENT_MESSAGES is allowed to reach a user.
# ---------------------------------------------------------------------------
REFUSE_MALFORMED = "malformed_pdf"
REFUSE_ENCRYPTED = "encrypted_or_restricted"
REFUSE_REPAIRED = "repaired_input"
REFUSE_NO_PAGES = "no_pages"
REFUSE_NO_TEXT = "no_text"
REFUSE_PAGE_LIMIT = "page_limit"
REFUSE_PAGE_CHARS_LIMIT = "page_chars_limit"
REFUSE_TOTAL_CHARS_LIMIT = "total_chars_limit"
REFUSE_CHAPTER_LIMIT = "chapter_limit"
REFUSE_PACKAGE_LIMIT = "package_limit"
REFUSE_TIME_BUDGET = "time_budget"
REFUSE_IO = "io_failure"
REFUSE_INTERNAL_VALIDATION = "internal_validation"

#: Input-side refusals answer the honest 422 UNSUPPORTED_CONVERSION (the caller
#: can act on them).  Everything else is a safe generic failure at the boundary.
INPUT_REFUSALS = frozenset(
    {
        REFUSE_MALFORMED,
        REFUSE_ENCRYPTED,
        REFUSE_REPAIRED,
        REFUSE_NO_PAGES,
        REFUSE_NO_TEXT,
        REFUSE_PAGE_LIMIT,
        REFUSE_PAGE_CHARS_LIMIT,
        REFUSE_TOTAL_CHARS_LIMIT,
        REFUSE_CHAPTER_LIMIT,
        REFUSE_PACKAGE_LIMIT,
    }
)

#: The sentence used whenever the server itself could not finish.  It matches
#: GENERIC_CONVERSION_FAILURE_MESSAGE in app/services/conversion_service.py in
#: shape so a client can never learn which internal stage gave up.
PLAIN_MESSAGE = "Conversion failed. Please try again."

#: Client-facing wording.  Every entry is a module literal; the only dynamic part
#: permitted is ``{limit}``, filled from a configuration **int** - never from
#: exception text, a path, a page's content or any PDF string.
CLIENT_MESSAGES = {
    REFUSE_MALFORMED: (
        "The file could not be read as a PDF. It may be corrupt or not a PDF."
    ),
    REFUSE_ENCRYPTED: (
        "This PDF is encrypted or access-restricted, so its text cannot be read "
        "safely. Converigo does not convert protected PDFs."
    ),
    REFUSE_REPAIRED: (
        "This PDF needed repair before it could be opened, so Converigo stopped "
        "instead of returning partial text."
    ),
    REFUSE_NO_PAGES: "This PDF has no pages to convert.",
    REFUSE_NO_TEXT: (
        "No selectable text was found in this PDF. Scanned pages need OCR, which "
        "this converter does not do."
    ),
    REFUSE_PAGE_LIMIT: (
        "This PDF has more pages than the converter allows (limit: {limit})."
    ),
    REFUSE_PAGE_CHARS_LIMIT: (
        "One page of this PDF holds more text than the converter allows "
        "(limit: {limit} characters per page)."
    ),
    REFUSE_TOTAL_CHARS_LIMIT: (
        "This PDF holds more text than the converter allows (limit: {limit} "
        "characters)."
    ),
    REFUSE_CHAPTER_LIMIT: (
        "This PDF cannot be divided into the chapters the converter allows "
        "(limit: {limit})."
    ),
    REFUSE_PACKAGE_LIMIT: (
        "The generated EPUB is larger than the converter allows "
        "(limit: {limit} bytes)."
    ),
    REFUSE_TIME_BUDGET: PLAIN_MESSAGE,
    REFUSE_IO: PLAIN_MESSAGE,
    REFUSE_INTERNAL_VALIDATION: PLAIN_MESSAGE,
}

#: A metadata field is attacker-controlled text.  It may only ever become escaped
#: XML *content*: control characters are removed, the value is collapsed to a
#: single line and truncated.  It never becomes a path or an identifier.
METADATA_FIELD_LIMIT = 200

_LANG_TOKEN_RE = re.compile(r"^[A-Za-z]{1,3}(?:-[A-Za-z0-9]{1,8})*$")
_CONTROL_CHARS_RE = re.compile("[\\x00-\\x1f\\x7f\\u2028\\u2029]")
_WHITESPACE_RE = re.compile(r"\s+")


class PdfToEpubError(Exception):
    """A conversion that will not be served.

    ``client_message`` is the only sentence allowed to leave the process.
    ``detail`` is server-side (it may name byte counts, page numbers or the
    library's own error text) and is logged, never rendered.
    """

    def __init__(self, kind: str, client_message: str, detail: str = "") -> None:
        self.kind = kind
        self.client_message = client_message or PLAIN_MESSAGE
        self.detail = detail
        super().__init__(f"{kind}: {detail or client_message}")

    @property
    def is_input_refusal(self) -> bool:
        """True when the *input* is at fault, i.e. an honest 422."""
        return self.kind in INPUT_REFUSALS


def _refusal(kind: str, detail: str = "", limit: int | None = None) -> PdfToEpubError:
    """Build a refusal whose client text is a literal plus an optional int."""
    template = CLIENT_MESSAGES.get(kind, PLAIN_MESSAGE)
    message = template.format(limit=limit) if limit is not None else template
    return PdfToEpubError(kind, message, detail)


@dataclass(frozen=True)
class EpubLimits:
    """The enforced ceilings for one conversion."""

    max_pages: int
    max_chars: int
    max_page_chars: int
    max_package_bytes: int
    max_chapters: int
    time_budget_seconds: float


@dataclass(frozen=True)
class EpubBuildReport:
    """Facts about a successful build, for the server-side log line only."""

    pages: int
    chapters: int
    chars: int
    package_bytes: int
    elapsed_ms: int


def _limits_from_settings() -> EpubLimits:
    from app.core.settings import settings

    return EpubLimits(
        max_pages=settings.PDF_EPUB_MAX_PAGES,
        max_chars=settings.PDF_EPUB_MAX_CHARS,
        max_page_chars=settings.PDF_EPUB_MAX_PAGE_CHARS,
        max_package_bytes=settings.PDF_EPUB_MAX_PACKAGE_BYTES,
        max_chapters=settings.PDF_EPUB_MAX_CHAPTERS,
        time_budget_seconds=settings.PDF_EPUB_TIME_BUDGET_SECONDS,
    )



# ---------------------------------------------------------------------------
# Input guards
# ---------------------------------------------------------------------------
def _read_input(source_path: Path) -> bytes:
    """Read the document once.  MuPDF then works from the bytes, never the path.

    One read also means the encryption probe and the extractor necessarily see
    the same bytes, so there is no window in which a check describes a different
    file than the one that gets converted.
    """
    try:
        raw = source_path.read_bytes()
    except OSError as exc:
        # The path stays in `detail` (server-side); the client only learns that
        # the input could not be read.
        raise _refusal(REFUSE_MALFORMED, detail=f"read {type(exc).__name__}") from exc
    if not raw:
        raise _refusal(REFUSE_MALFORMED, detail="empty input")
    return raw


def _has_encrypt_dictionary(raw: bytes) -> bool:
    """Crude last-resort probe for an /Encrypt key in the raw bytes.

    Only consulted when pypdf could not parse the file at all.  In that branch a
    false positive costs one refused upload while a false negative would hand a
    protected document to the extractor, so the scan is deliberately over-eager:
    any ``/Encrypt`` token anywhere in the file refuses.
    """
    return b"/Encrypt" in raw


def _encryption_refusal_kind(source_path: Path, raw: bytes) -> str | None:
    """Return a refusal kind when the input carries an encryption dictionary.

    pypdf is the authority here on purpose.  MuPDF reports both ``needs_pass``
    and ``is_encrypted`` as False for an owner-restricted PDF that nevertheless
    contains /Encrypt - the blind spot measured in the preparation phase - and
    the approved policy is to refuse *any* PDF with an encryption dictionary,
    whether or not a password is needed to open it.
    """
    try:
        reader = PdfReader(io.BytesIO(raw))
    except Exception as exc:
        if _has_encrypt_dictionary(raw):
            return REFUSE_ENCRYPTED
        logger.info(
            "pdf-to-epub: pypdf could not parse %s (%s); raw /Encrypt scan was clean",
            source_path.name,
            type(exc).__name__,
        )
        return None
    return REFUSE_ENCRYPTED if getattr(reader, "is_encrypted", False) else None


def _open_clean_document(raw: bytes):
    """Open with MuPDF, refusing anything the extractor cannot be trusted on.

    The encryption dictionary check has already run on the raw bytes, so what is
    left here is (a) a document MuPDF itself flags as password-protected or
    encrypted, which must never reach the text loop, and (b) a document MuPDF
    had to *repair* to open at all.  A repaired read is a partial read: some
    objects survive and some do not, so the honest answer is a refusal rather
    than a book that silently drops pages.
    """
    try:
        doc = fitz.open(stream=raw, filetype="pdf")
    except Exception as exc:
        raise _refusal(REFUSE_MALFORMED, detail=f"{type(exc).__name__}") from exc

    try:
        needs_pass = bool(doc.needs_pass)
        encrypted = bool(doc.is_encrypted)
        repaired = bool(doc.is_repaired)
    except Exception as exc:  # pragma: no cover - defensive
        doc.close()
        raise _refusal(
            REFUSE_MALFORMED, detail=f"flags {type(exc).__name__}"
        ) from exc

    if needs_pass or encrypted:
        doc.close()
        raise _refusal(
            REFUSE_ENCRYPTED,
            detail=f"mupdf needs_pass={needs_pass} encrypted={encrypted}",
        )
    if repaired:
        doc.close()
        raise _refusal(REFUSE_REPAIRED, detail="mupdf is_repaired=True")
    return doc


# ---------------------------------------------------------------------------
# Extraction (the only place MuPDF reads text)
# ---------------------------------------------------------------------------
def _extract_pages(doc, limits: EpubLimits, deadline: float) -> list[str]:
    """Extract one text block per page under every text-related ceiling.

    The ceilings are enforced *while* walking the pages, because the cost of a
    pathological page is paid during extraction, not during packaging.  The time
    budget is re-checked per page for the same reason: a single unbounded loop
    would otherwise ignore it completely.
    """
    pages_text: list[str] = []
    total_chars = 0
    page_count = doc.page_count

    for index in range(page_count):
        if time.monotonic() > deadline:
            raise _refusal(
                REFUSE_TIME_BUDGET, detail=f"after {index} of {page_count} pages"
            )
        try:
            text = doc[index].get_text() or ""
        except Exception as exc:
            raise _refusal(
                REFUSE_MALFORMED, detail=f"page {index + 1} {type(exc).__name__}"
            ) from exc

        if len(text) > limits.max_page_chars:
            raise _refusal(
                REFUSE_PAGE_CHARS_LIMIT,
                detail=f"page {index + 1} chars={len(text)}",
                limit=limits.max_page_chars,
            )
        total_chars += len(text)
        if total_chars > limits.max_chars:
            raise _refusal(
                REFUSE_TOTAL_CHARS_LIMIT,
                detail=f"chars={total_chars} at page {index + 1}",
                limit=limits.max_chars,
            )
        pages_text.append(text)

    if not any(_WHITESPACE_RE.sub("", text) for text in pages_text):
        # Zero-text: every page came back empty or whitespace only.  Shipping an
        # empty book would be a fabricated output, so refuse honestly instead.
        raise _refusal(REFUSE_NO_TEXT, detail=f"pages={page_count}")
    return pages_text



# ---------------------------------------------------------------------------
# Page -> chapter pagination
# ---------------------------------------------------------------------------
def _chapter_plan(page_count: int, max_chapters: int) -> tuple[int, int]:
    """Group pages into chapters: return ``(pages_per_chapter, chapter_count)``.

    The rule is derived from the approved ceiling instead of checked after the
    fact: with ``pages_per_chapter = ceil(pages / max_chapters)`` the identity
    ``ceil(pages / pages_per_chapter) <= max_chapters`` holds by construction, so
    a 500-page document becomes 100 chapters of 5 pages while 40 pages stay 40
    single-page chapters.  The explicit comparison below is the defensive branch
    for a misconfigured ceiling (``max_chapters < 1``): that must refuse rather
    than emit a book whose limits the settings do not describe.
    """
    if max_chapters < 1:
        raise _refusal(
            REFUSE_CHAPTER_LIMIT,
            detail=f"max_chapters={max_chapters}",
            limit=max_chapters,
        )
    pages_per_chapter = -(-page_count // max_chapters)
    chapter_count = -(-page_count // pages_per_chapter)
    if chapter_count > max_chapters:
        raise _refusal(
            REFUSE_CHAPTER_LIMIT,
            detail=f"chapters={chapter_count} pages={page_count}",
            limit=max_chapters,
        )
    return pages_per_chapter, chapter_count


def _chapter_file_name(position: int) -> str:
    """Constant, index-derived entry name.  Never built from input text."""
    return f"{CHAPTER_PREFIX}{position:03d}{CHAPTER_SUFFIX}"


def _chapter_label(position: int, first_page: int, last_page: int) -> str:
    if first_page == last_page:
        return f"Chapter {position} (Page {first_page})"
    return f"Chapter {position} (Pages {first_page}-{last_page})"


# ---------------------------------------------------------------------------
# Metadata (attacker-controlled: content only, never structure)
# ---------------------------------------------------------------------------
def _clean_text_field(value: object, limit: int = METADATA_FIELD_LIMIT) -> str:
    """Normalise a PDF metadata value into inert single-line text."""
    if not isinstance(value, str):
        return ""
    text = _CONTROL_CHARS_RE.sub(" ", value)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text[:limit]


def _document_metadata(doc) -> dict[str, str]:
    """Read the two PDF metadata fields the package will show as XML text."""
    try:
        raw_meta = doc.metadata or {}
    except Exception:  # pragma: no cover - defensive
        raw_meta = {}
    if not isinstance(raw_meta, dict):
        raw_meta = {}
    return {
        "title": _clean_text_field(raw_meta.get("title")),
        "author": _clean_text_field(raw_meta.get("author")),
    }


def _document_language(doc) -> str:
    """A BCP-47 token for dc:language, or ``und`` (undetermined).

    dc:language is required, but guessing "en" for a CJK document would be a
    false claim, so the fallback is the explicit "undetermined" subtag.  The
    token is shape-checked before use because it comes from the input.
    """
    try:
        token = str(doc.language() or "").strip()
    except Exception:  # pragma: no cover - defensive
        token = ""
    token = token.replace(" ", "-")
    if token and _LANG_TOKEN_RE.match(token):
        return token
    return "und"


# ---------------------------------------------------------------------------
# XML part builders
#
# lxml builds every part.  That is a security property, not a stylistic choice:
# text assigned through ``element.text`` is escaped by the serializer, so a PDF
# carrying "<script>" or "../../../../etc/passwd" in its title can only ever
# become inert character data in the generated package.
# ---------------------------------------------------------------------------
def _serialize(root, doctype: str | None = None) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", doctype=doctype)


def _xml_root(tag: str, namespace: str, **extra_ns: str):
    nsmap = {None: namespace}
    nsmap.update(extra_ns)
    return etree.Element(tag, nsmap=nsmap)


def _relative_href(file_name: str) -> str:
    """href inside the package: the basename only, never a caller-supplied path."""
    return PurePosixPath(file_name).name


def _build_container_xml() -> bytes:
    root = _xml_root("container", CONTAINER_NAMESPACE)
    root.set("version", "1.0")
    rootfiles = etree.SubElement(root, "rootfiles")
    rootfile = etree.SubElement(rootfiles, "rootfile")
    rootfile.set("full-path", CONTAINER_ROOTFILE_PATH)
    rootfile.set("media-type", "application/oebps-package+xml")
    return _serialize(root)


def _xhtml_skeleton(title: str, language: str):
    """Common <html>/<head>/<body> shared by every XHTML part of the book."""
    root = _xml_root(
        f"{{{XHTML_NAMESPACE}}}html", XHTML_NAMESPACE, epub=EPUB_TYPE_NAMESPACE
    )
    root.set(XML_LANGUAGE_ATTRIBUTE, language or "und")
    root.set("lang", language or "und")
    head = etree.SubElement(root, f"{{{XHTML_NAMESPACE}}}head")
    etree.SubElement(head, f"{{{XHTML_NAMESPACE}}}title").text = title
    sheet = etree.SubElement(head, f"{{{XHTML_NAMESPACE}}}link")
    sheet.set("rel", "stylesheet")
    sheet.set("type", "text/css")
    sheet.set("href", _relative_href(CSS_FILE_NAME))
    body = etree.SubElement(root, f"{{{XHTML_NAMESPACE}}}body")
    return root, body



def _build_package_xml(
    *,
    title: str,
    author: str,
    language: str,
    identifier: str,
    modified: str,
    chapter_files: list[str],
) -> bytes:
    root = _xml_root(f"{{{OPF_NAMESPACE}}}package", OPF_NAMESPACE, dc=DC_NAMESPACE)
    root.set("version", "3.0")
    root.set("unique-identifier", "pub-id")

    metadata = etree.SubElement(root, f"{{{OPF_NAMESPACE}}}metadata")
    identifier_el = etree.SubElement(metadata, f"{{{DC_NAMESPACE}}}identifier")
    identifier_el.set("id", "pub-id")
    identifier_el.text = identifier
    etree.SubElement(metadata, f"{{{DC_NAMESPACE}}}title").text = title
    if author:
        etree.SubElement(metadata, f"{{{DC_NAMESPACE}}}creator").text = author
    etree.SubElement(metadata, f"{{{DC_NAMESPACE}}}language").text = language
    modified_el = etree.SubElement(metadata, f"{{{OPF_NAMESPACE}}}meta")
    modified_el.set("property", "dcterms:modified")
    modified_el.text = modified

    manifest = etree.SubElement(root, f"{{{OPF_NAMESPACE}}}manifest")

    def item(item_id: str, href: str, media_type: str, properties: str = "") -> None:
        node = etree.SubElement(manifest, f"{{{OPF_NAMESPACE}}}item")
        node.set("id", item_id)
        node.set("href", href)
        node.set("media-type", media_type)
        if properties:
            node.set("properties", properties)

    item("nav", _relative_href(NAV_FILE_NAME), "application/xhtml+xml", "nav")
    item("ncx", _relative_href(NCX_FILE_NAME), "application/x-dtbncx+xml")
    item("css", _relative_href(CSS_FILE_NAME), "text/css")
    for position, file_name in enumerate(chapter_files, start=1):
        item(f"ch{position}", _relative_href(file_name), "application/xhtml+xml")

    spine = etree.SubElement(root, f"{{{OPF_NAMESPACE}}}spine")
    spine.set("toc", "ncx")
    for position in range(1, len(chapter_files) + 1):
        etree.SubElement(spine, f"{{{OPF_NAMESPACE}}}itemref").set("idref", f"ch{position}")
    return _serialize(root)


def _build_ncx_xml(
    *, title: str, identifier: str, chapter_labels: list[str]
) -> bytes:
    root = _xml_root(f"{{{NCX_NAMESPACE}}}ncx", NCX_NAMESPACE)
    root.set("version", "2005-1")
    head = etree.SubElement(root, f"{{{NCX_NAMESPACE}}}head")
    for name, content in (("dtb:uid", identifier), ("dtb:depth", "1")):
        meta = etree.SubElement(head, f"{{{NCX_NAMESPACE}}}meta")
        meta.set("name", name)
        meta.set("content", content)
    doc_title = etree.SubElement(root, f"{{{NCX_NAMESPACE}}}docTitle")
    etree.SubElement(doc_title, f"{{{NCX_NAMESPACE}}}text").text = title
    nav_map = etree.SubElement(root, f"{{{NCX_NAMESPACE}}}navMap")
    for position, label in enumerate(chapter_labels, start=1):
        point = etree.SubElement(nav_map, f"{{{NCX_NAMESPACE}}}navPoint")
        point.set("id", f"np{position}")
        point.set("playOrder", str(position))
        label_el = etree.SubElement(point, f"{{{NCX_NAMESPACE}}}navLabel")
        etree.SubElement(label_el, f"{{{NCX_NAMESPACE}}}text").text = label
        etree.SubElement(point, f"{{{NCX_NAMESPACE}}}content").set(
            "src", _relative_href(_chapter_file_name(position))
        )
    return _serialize(root)


def _build_nav_xml(
    *, title: str, language: str, chapter_labels: list[str]
) -> bytes:
    root, body = _xhtml_skeleton(title, language=language)
    nav = etree.SubElement(body, f"{{{XHTML_NAMESPACE}}}nav")
    nav.set(f"{{{EPUB_TYPE_NAMESPACE}}}type", "toc")
    etree.SubElement(nav, f"{{{XHTML_NAMESPACE}}}h1").text = title
    listing = etree.SubElement(nav, f"{{{XHTML_NAMESPACE}}}ol")
    for position, label in enumerate(chapter_labels, start=1):
        item = etree.SubElement(listing, f"{{{XHTML_NAMESPACE}}}li")
        anchor = etree.SubElement(item, f"{{{XHTML_NAMESPACE}}}a")
        anchor.set("href", _relative_href(_chapter_file_name(position)))
        anchor.text = label
    return _serialize(root, doctype="<!DOCTYPE html>")


def _build_chapter_xml(
    *, position: int, language: str, label: str, pages: list[tuple[int, str]]
) -> bytes:
    """One chapter document: a heading plus one block per source page.

    Line structure is preserved by turning each non-empty extracted line into its
    own ``<p>``.  Blank lines carry no content in XHTML and are dropped; nothing
    else is rewritten, reordered or invented, which is what lets the certified
    tests check the extraction page by page and line by line.
    """
    root, body = _xhtml_skeleton(label, language=language)
    etree.SubElement(body, f"{{{XHTML_NAMESPACE}}}h1").text = label
    for page_number, text in pages:
        block = etree.SubElement(body, f"{{{XHTML_NAMESPACE}}}div")
        block.set("class", "converigo-page")
        block.set("id", f"page-{page_number}")
        etree.SubElement(block, f"{{{XHTML_NAMESPACE}}}h2").text = f"Page {page_number}"
        for line in text.splitlines():
            if not line.strip():
                continue
            etree.SubElement(block, f"{{{XHTML_NAMESPACE}}}p").text = line
    return _serialize(root, doctype="<!DOCTYPE html>")



# ---------------------------------------------------------------------------
# Packaging
# ---------------------------------------------------------------------------
def _expected_entry_names(chapter_count: int) -> set[str]:
    """The complete set of entry names a valid package may contain."""
    names = {
        MIMETYPE_ENTRY_NAME,
        CONTAINER_FILE_NAME,
        PACKAGE_FILE_NAME,
        NCX_FILE_NAME,
        NAV_FILE_NAME,
        CSS_FILE_NAME,
    }
    names.update(
        _chapter_file_name(position) for position in range(1, chapter_count + 1)
    )
    return names


def _entry_date_time() -> tuple[int, int, int, int, int, int]:
    """One timestamp for every entry.

    A ZIP stores dates with two-second granularity and cannot express anything
    before 1980, so the value is clamped.  Capturing a single instant keeps the
    entries consistent with each other instead of drifting across a second
    boundary while the archive is written.
    """
    now = time.gmtime()
    return (
        max(now.tm_year, 1980),
        now.tm_mon,
        now.tm_mday,
        now.tm_hour,
        now.tm_min,
        now.tm_sec - (now.tm_sec % 2),
    )


def _new_entry(name: str, date_time: tuple, stored: bool):
    info = zipfile.ZipInfo(name, date_time=date_time)
    # ZIP_DEFLATED everywhere except "mimetype": the OPF/ZIP requirement is that
    # the mimetype member is stored uncompressed, first in the archive, with no
    # extra field.  Readers sniff the format from that entry alone.
    info.compress_type = zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED
    info.extra = b""
    info.external_attr = 0o644 << 16
    return info


def _write_package(
    output_path: Path, parts: list[tuple[str, bytes]], *, date_time: tuple
) -> None:
    try:
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                _new_entry(MIMETYPE_ENTRY_NAME, date_time, stored=True), EPUB_MIME_TYPE
            )
            for name, payload in parts:
                archive.writestr(_new_entry(name, date_time, stored=False), payload)
    except OSError as exc:
        raise _refusal(REFUSE_IO, detail=f"write {type(exc).__name__}") from exc


# ---------------------------------------------------------------------------
# Validation before publish
# ---------------------------------------------------------------------------
def _parse_xml_part(payload: bytes, name: str):
    try:
        return etree.fromstring(payload)
    except etree.XMLSyntaxError as exc:
        raise _refusal(REFUSE_INTERNAL_VALIDATION, detail=f"{name}: {exc}") from exc


def _check_package_references(package, payloads: dict[str, bytes]) -> None:
    """Manifest hrefs must be bare names that resolve to parts that exist."""
    items = package.findall(f".//{{{OPF_NAMESPACE}}}manifest/{{{OPF_NAMESPACE}}}item")
    if not items:
        raise _refusal(REFUSE_INTERNAL_VALIDATION, detail="empty manifest")
    ids = set()
    for item in items:
        item_id = item.get("id") or ""
        href = item.get("href") or ""
        ids.add(item_id)
        if not href or "/" in href or "\\" in href or ".." in href:
            raise _refusal(REFUSE_INTERNAL_VALIDATION, detail=f"href shape {item_id}")
        if f"{PACKAGE_DIR}/{href}" not in payloads:
            raise _refusal(REFUSE_INTERNAL_VALIDATION, detail=f"href target {item_id}")
    spine = package.findall(f".//{{{OPF_NAMESPACE}}}spine/{{{OPF_NAMESPACE}}}itemref")
    for ref in spine:
        if ref.get("idref") not in ids:
            raise _refusal(REFUSE_INTERNAL_VALIDATION, detail="dangling idref")


def _validate_zip_shape(archive: zipfile.ZipFile, chapter_count: int) -> dict:
    """Container-level guarantees: mimetype placement, CRC, closed name set."""
    entries = archive.infolist()
    names = [entry.filename for entry in entries]

    if not entries or names[0] != MIMETYPE_ENTRY_NAME:
        raise _refusal(REFUSE_INTERNAL_VALIDATION, detail=f"first={names[:1]}")
    if entries[0].compress_type != zipfile.ZIP_STORED:
        raise _refusal(REFUSE_INTERNAL_VALIDATION, detail="mimetype compressed")
    if entries[0].extra:
        raise _refusal(REFUSE_INTERNAL_VALIDATION, detail="mimetype extra field")
    if archive.read(MIMETYPE_ENTRY_NAME) != EPUB_MIME_TYPE.encode("ascii"):
        raise _refusal(REFUSE_INTERNAL_VALIDATION, detail="mimetype value")

    corrupt = archive.testzip()
    if corrupt is not None:
        raise _refusal(REFUSE_INTERNAL_VALIDATION, detail=f"CRC failure in {corrupt}")

    # Closed-set check: a name is legal only because the writer is allowed to
    # produce it.  That is the path-traversal guarantee, and unlike a blocklist
    # of "bad" substrings it cannot be stepped around with an unexpected character.
    expected = _expected_entry_names(chapter_count)
    unexpected = sorted(set(names) - expected)
    missing = sorted(expected - set(names))
    if unexpected or missing:
        raise _refusal(
            REFUSE_INTERNAL_VALIDATION,
            detail=f"unexpected={unexpected[:2]} missing={missing[:2]}",
        )
    for name in names:
        member = PurePosixPath(name)
        if member.is_absolute() or ".." in member.parts or "\\" in name:
            raise _refusal(REFUSE_INTERNAL_VALIDATION, detail=f"unsafe name {name}")

    return {name: archive.read(name) for name in names}



def _validate_package(
    output_path: Path, *, chapter_count: int, limits: EpubLimits
) -> int:
    """Prove the finished package is a servable EPUB.  Returns its byte size.

    A failure here is a fault in our own writer (an unusable input was refused
    long before this point), so the client receives the safe generic failure and
    the diagnosis stays in the log record.
    """
    try:
        package_bytes = output_path.stat().st_size
    except OSError as exc:
        raise _refusal(REFUSE_IO, detail=f"stat {type(exc).__name__}") from exc

    if package_bytes > limits.max_package_bytes:
        raise _refusal(
            REFUSE_PACKAGE_LIMIT,
            detail=f"bytes={package_bytes}",
            limit=limits.max_package_bytes,
        )

    try:
        with zipfile.ZipFile(output_path) as archive:
            payloads = _validate_zip_shape(archive, chapter_count)
    except PdfToEpubError:
        raise
    except zipfile.BadZipFile as exc:
        raise _refusal(
            REFUSE_INTERNAL_VALIDATION, detail=f"badzip {type(exc).__name__}"
        ) from exc
    except OSError as exc:
        raise _refusal(REFUSE_IO, detail=f"read {type(exc).__name__}") from exc

    container = _parse_xml_part(payloads[CONTAINER_FILE_NAME], CONTAINER_FILE_NAME)
    rootfiles = container.findall(
        f"{{{CONTAINER_NAMESPACE}}}rootfiles/{{{CONTAINER_NAMESPACE}}}rootfile"
    )
    if len(rootfiles) != 1 or rootfiles[0].get("full-path") != CONTAINER_ROOTFILE_PATH:
        raise _refusal(REFUSE_INTERNAL_VALIDATION, detail="rootfile")
    if CONTAINER_ROOTFILE_PATH not in payloads:
        raise _refusal(REFUSE_INTERNAL_VALIDATION, detail="rootfile target missing")

    package = _parse_xml_part(payloads[PACKAGE_FILE_NAME], PACKAGE_FILE_NAME)
    _check_package_references(package, payloads)

    ncx = _parse_xml_part(payloads[NCX_FILE_NAME], NCX_FILE_NAME)
    if len(ncx.findall(f".//{{{NCX_NAMESPACE}}}navPoint")) != chapter_count:
        raise _refusal(REFUSE_INTERNAL_VALIDATION, detail="navPoint count")
    _parse_xml_part(payloads[NAV_FILE_NAME], NAV_FILE_NAME)
    for position in range(1, chapter_count + 1):
        _parse_xml_part(payloads[_chapter_file_name(position)], "chapter")

    # Round-trip: MuPDF is an independent EPUB reader, so re-opening the book
    # proves the container parses in a real engine and its outline survived.
    try:
        book = fitz.open(str(output_path))
    except Exception as exc:
        raise _refusal(
            REFUSE_INTERNAL_VALIDATION, detail=f"roundtrip {type(exc).__name__}"
        ) from exc
    try:
        if book.page_count < 1:
            raise _refusal(REFUSE_INTERNAL_VALIDATION, detail="roundtrip no pages")
        round_trip = "".join(
            book[index].get_text() for index in range(book.page_count)
        )
        if not round_trip.strip():
            raise _refusal(REFUSE_INTERNAL_VALIDATION, detail="roundtrip empty text")
        if len(book.get_toc()) != chapter_count:
            raise _refusal(
                REFUSE_INTERNAL_VALIDATION,
                detail=f"roundtrip toc={len(book.get_toc())} want={chapter_count}",
            )
    finally:
        book.close()
    return package_bytes


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
#: Used when the PDF carries no usable /Title.  Never built from input.
DEFAULT_PACKAGE_TITLE = "Converted PDF"


def _extract_document(
    source_path: Path, limits: EpubLimits, started: float
) -> tuple[bytes, list[str], dict[str, str], str]:
    """Guard, open, extract.  Returns (raw, per-page text, metadata, language)."""
    raw = _read_input(source_path)

    # The encryption dictionary is probed on the raw bytes before MuPDF is asked
    # to open anything: an owner-restricted PDF can present itself to MuPDF as an
    # ordinary file, and the approved policy is to refuse any PDF carrying
    # /Encrypt at all.
    encrypted = _encryption_refusal_kind(source_path, raw)
    if encrypted:
        raise _refusal(encrypted, detail="encryption dictionary present")

    doc = _open_clean_document(raw)
    try:
        page_count = doc.page_count
        if page_count == 0:
            raise _refusal(REFUSE_NO_PAGES, detail="page_count=0")
        if page_count > limits.max_pages:
            raise _refusal(
                REFUSE_PAGE_LIMIT, detail=f"pages={page_count}", limit=limits.max_pages
            )
        pages_text = _extract_pages(doc, limits, started + limits.time_budget_seconds)
        metadata = _document_metadata(doc)
        language = _document_language(doc)
    finally:
        doc.close()
    return raw, pages_text, metadata, language


def _discard(output_path: Path) -> None:
    """Remove a refused package so nothing partial can ever be served."""
    try:
        output_path.unlink(missing_ok=True)
    except OSError:  # pragma: no cover - the temp tree is cleaned anyway
        logger.warning("pdf-to-epub: could not remove refused output")



def convert_pdf_to_epub(
    source_path: Path,
    output_path: Path,
    limits: EpubLimits | None = None,
) -> EpubBuildReport:
    """Convert a PDF into a validated EPUB written to ``output_path``.

    Blocking by design: the plugin runs this in a worker thread so the event loop
    keeps serving other requests while MuPDF walks pages.  Raises
    :class:`PdfToEpubError` and leaves no file behind on failure.
    """
    source_path = Path(source_path)
    output_path = Path(output_path)
    resolved_limits = limits or _limits_from_settings()
    started = time.monotonic()

    if output_path.exists() and output_path.resolve() == source_path.resolve():
        raise _refusal(REFUSE_IO, detail="output path equals source")

    try:
        raw, pages_text, metadata, language = _extract_document(
            source_path, resolved_limits, started
        )
        pages_per_chapter, chapter_count = _chapter_plan(
            len(pages_text), resolved_limits.max_chapters
        )
        title = metadata["title"] or DEFAULT_PACKAGE_TITLE
        author = metadata["author"]
        # Derived from the input bytes, not from the clock or the filename, so the
        # same PDF always yields the same identifier.
        identifier = "urn:converigo:" + hashlib.sha256(raw).hexdigest()[:32]
        modified = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        chapter_files = [
            _chapter_file_name(position) for position in range(1, chapter_count + 1)
        ]
        labels = [
            _chapter_label(
                position,
                (position - 1) * pages_per_chapter + 1,
                min(position * pages_per_chapter, len(pages_text)),
            )
            for position in range(1, chapter_count + 1)
        ]

        deadline = started + resolved_limits.time_budget_seconds
        parts: list[tuple[str, bytes]] = [
            (CONTAINER_FILE_NAME, _build_container_xml()),
            (
                PACKAGE_FILE_NAME,
                _build_package_xml(
                    title=title,
                    author=author,
                    language=language,
                    identifier=identifier,
                    modified=modified,
                    chapter_files=chapter_files,
                ),
            ),
            (
                NCX_FILE_NAME,
                _build_ncx_xml(
                    title=title, identifier=identifier, chapter_labels=labels
                ),
            ),
            (
                NAV_FILE_NAME,
                _build_nav_xml(title=title, language=language, chapter_labels=labels),
            ),
            (CSS_FILE_NAME, STYLE_SHEET.encode("utf-8")),
        ]

        for position, chapter_file in enumerate(chapter_files, start=1):
            if time.monotonic() > deadline:
                raise _refusal(REFUSE_TIME_BUDGET, detail=f"packaging {position}")
            start = (position - 1) * pages_per_chapter
            chunk = pages_text[start : start + pages_per_chapter]
            parts.append(
                (
                    chapter_file,
                    _build_chapter_xml(
                        position=position,
                        language=language,
                        label=labels[position - 1],
                        pages=[
                            (start + offset + 1, text)
                            for offset, text in enumerate(chunk)
                        ],
                    ),
                )
            )

        _write_package(output_path, parts, date_time=_entry_date_time())
        package_bytes = _validate_package(
            output_path, chapter_count=chapter_count, limits=resolved_limits
        )
    except PdfToEpubError as exc:
        _discard(output_path)
        logger.info("pdf-to-epub refused kind=%s detail=%s", exc.kind, exc.detail)
        raise

    report = EpubBuildReport(
        pages=len(pages_text),
        chapters=chapter_count,
        chars=sum(len(text) for text in pages_text),
        package_bytes=package_bytes,
        elapsed_ms=int((time.monotonic() - started) * 1000),
    )
    logger.info(
        "pdf-to-epub built pages=%s chapters=%s chars=%s bytes=%s ms=%s",
        report.pages,
        report.chapters,
        report.chars,
        report.package_bytes,
        report.elapsed_ms,
    )
    return report

