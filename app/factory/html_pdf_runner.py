"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / HTML-PDF)
Version : 1.0.0

Synchronous, process-isolated MuPDF HTML -> PDF runner (html-to-pdf).

Why this module exists
----------------------
MuPDF's HTML engine is native code, and two properties make it unsafe to drive
inside a request: a native hang or segfault cannot be interrupted from Python
(``asyncio.wait_for`` in ConversionService only bounds coroutine suspension
points, and the single-uvicorn-worker event loop is blocked while any sync
engine call runs), and a segfault takes the whole worker - i.e. every
concurrent user - down with it.

So the render happens in a *separate OS process*
(app/factory/html_render_worker.py) that this module spawns with a hard
``subprocess.run(timeout=...)`` and can therefore kill.  This follows the
established F4 precedent in app/factory/ffmpeg_runner.py (sync, subprocess,
timeout-bounded, honest-error translation) instead of inventing a new
mechanism, and - like ffmpeg_runner.py - this file deliberately lives in
app/factory/ so plugin discovery rglob cannot mistake it for a converter.

The synchronous shape here is intentional: the html-to-pdf plugin calls it
through ``asyncio.to_thread`` so the event loop stays free while the child
runs.  A bare sync call from ``async def convert()`` would re-introduce the
freeze this design removes.

Error policy
------------
Every refusal is a typed ``HtmlRenderError`` subclass carrying a static,
client-safe ``client_message`` plus a server-side-only ``detail``.  Raw exit
codes, signal numbers, tracebacks, temp paths and library names never leave
this module: the plugin maps these types to ``UnsupportedConversionError``
(the lazy-import precedent used by app/plugins/data/html_table_factory.py) so
the API answers an honest 422 instead of a 500 or a fabricated PDF.
"""
from __future__ import annotations

import codecs
import json
import logging
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

#: app/factory/html_pdf_runner.py -> app/factory -> app -> repository root.
REPO_ROOT = Path(__file__).resolve().parents[2]

#: The child is executed by path (never ``-m``) so it does not have to import
#: the application package and cannot fail on its import side effects.
RENDER_WORKER_PATH = Path(__file__).resolve().with_name("html_render_worker.py")

#: Prefix of the single machine-readable stdout line the child emits.
RESULT_MARKER = "CONVERIGO_HTML_RENDER_RESULT"

# ---------------------------------------------------------------------------
# Production ceilings (design review 4 - all enforced for real in this file)
# ---------------------------------------------------------------------------

#: Maximum accepted HTML source size in bytes.  Enforced here, NOT via the
#: ``max_upload_size`` field of a converter contract (which is schema-only).
MAX_HTML_INPUT_BYTES = 500 * 1024

#: Maximum element nesting depth.  The audit's crash amplifier (50,000 nested
#: ``<b>``) is ~100x this value and is refused before MuPDF ever sees it;
#: ordinary documents nest to a depth of tens.
MAX_ELEMENT_DEPTH = 500

#: Maximum length of a single unbroken text token: MuPDF's shaping cost grows
#: super-linearly with a word it cannot break.
MAX_TOKEN_LENGTH = 1000

#: Hard cap on rendered pages *and* on pagination-loop iterations (the child
#: enforces the same number independently as a second safety net).
MAX_RENDER_PAGES = 500

#: Wall-clock budget for one child render.  Measured cost basis: ~0.29 s to
#: start a Python child that imports MuPDF, and ~0.12 s for MuPDF to lay out
#: 1,000 pages, so a document at the 500 KB / 500-page ceilings finishes in
#: well under a second.  20 s is >10x headroom for slow storage and inline
#: data-URI images, and 15x below the 300 s service default that applies to an
#: .html source (ConversionService._get_timeout_seconds has no html bucket).
RENDER_TIMEOUT_SECONDS = 20

#: Minimum accepted output size in bytes (a zero-byte file is never served).
MIN_OUTPUT_BYTES = 1

#: Raster resolution for the visible-content check.  36 dpi is a quarter of
#: the PDF point grid: enough to prove "there is ink on this page" while
#: costing ~125k samples per A4 page.
INK_SAMPLE_DPI = 36

#: Grayscale values at or above this are treated as paper (255 = pure white;
#: the band from 251 absorbs antialiasing halos and export ringing).
INK_NEAR_WHITE_FLOOR = 251

#: Total non-near-white pixels required across the WHOLE document.
#:
#: Set from the measurements in tests/fixtures/html_to_pdf/CALIBRATION.md,
#: which the pipeline regenerates: all seven visually-empty fixtures (blank,
#: whitespace-only, &nbsp;-only, display:none, script-only body,
#: white-on-white, 0.01px font) land on exactly 0 ink, while the least inky
#: legitimate document ("one_dot.html", a single period) measures 3 and
#: ordinary reports measure 246 to 6.3 million.  A floor of 1 therefore
#: separates the two classes with no overlap; a higher floor starts refusing
#: legitimate minimal pages, which is the false-positive failure mode the
#: design review flagged (review 6b/6d).
#:
#: The check is a document total, not a per-page rule: page_break_blank_tail
#: .html measures 8,134 ink across its 2 pages with its least-inked page at 0,
#: so a per-page floor would wrongly refuse a validly paginated document.
MIN_TOTAL_INK_PIXELS = 1

#: Bytes of PDF tail scanned for the %%EOF marker.
_TRAILER_SCAN_BYTES = 1024

#: MuPDF's stand-in for an <img> it cannot resolve.  Kept as documentation of
#: what the output contains: it is deliberately NOT matched anywhere, because a
#: rejection rule built on it would also fire on legitimate prose (design
#: review 6d).  The observability signal is count_unresolved_image_tags().
IMAGE_PLACEHOLDER_TOKEN = "[image]"


# ---------------------------------------------------------------------------
# Typed, honest errors
# ---------------------------------------------------------------------------


class HtmlRenderError(Exception):
    """Base class for every html-to-pdf refusal.

    ``str(exc)`` is always the static, client-safe ``client_message``; the
    diagnostic ``detail`` (byte counts, exit codes, exception type names) is a
    separate attribute meant for server-side logging only.
    """

    client_message = "HTML to PDF conversion failed."

    def __init__(self, detail: str = "") -> None:
        self.detail = detail
        super().__init__(self.client_message)


class HtmlInputRejected(HtmlRenderError):
    """The source document is refused before any render process is spawned."""

    client_message = "HTML to PDF conversion refused this document before rendering."


class HtmlInputTooLarge(HtmlInputRejected):
    client_message = (
        "This HTML file is too large to convert safely. Please upload a smaller file."
    )


class HtmlEncodingUnsupported(HtmlInputRejected):
    client_message = (
        "The file encoding was not recognized. Please save the HTML as UTF-8 and try again."
    )


class HtmlStructureRejected(HtmlInputRejected):
    client_message = (
        "This HTML document is structured too deeply or contains a text run that is "
        "too long to render safely."
    )


class HtmlInputEmpty(HtmlInputRejected):
    client_message = "The HTML file is empty, so there is nothing to convert."


class HtmlRenderTimeout(HtmlRenderError):
    client_message = (
        "Rendering this HTML document took too long and was stopped. Please try a "
        "simpler document."
    )


class HtmlRenderCrashed(HtmlRenderError):
    client_message = (
        "The HTML renderer stopped unexpectedly while processing this document. "
        "Please try a simpler document."
    )


class HtmlRenderFailed(HtmlRenderError):
    client_message = "This HTML document could not be rendered to PDF."


class HtmlPageLimitExceeded(HtmlRenderError):
    client_message = (
        "This HTML document would produce too many PDF pages. Please split it or "
        "reduce its content."
    )


class HtmlOutputInvalid(HtmlRenderError):
    client_message = "The generated PDF failed validation, so it was not delivered."


class HtmlOutputVisuallyEmpty(HtmlRenderError):
    client_message = (
        "The document produced no visible content, so no PDF was delivered. This "
        "usually means the page relies on external images, unsupported CSS layout, "
        "or scripts."
    )


# ---------------------------------------------------------------------------
# Structured results
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HtmlRenderOutcome:
    """What the child process reported about a successful render."""

    pid: int
    pages: int
    output_bytes: int
    elapsed_ms: float
    unresolved_images: int = 0


@dataclass(frozen=True)
class HtmlOutputReport:
    """What validation of the produced PDF established."""

    pages: int
    ink_pixels: int
    pages_checked: int
    early_exit: bool


# ---------------------------------------------------------------------------
# Stage 1 - cheap structural guards (pure Python, run before any spawn)
# ---------------------------------------------------------------------------

#: Elements that never open a nesting level in HTML.
_VOID_ELEMENT_NAMES = frozenset(
    {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }
)

_TAG_HEAD_RE = re.compile(r"^\s*/?\s*([A-Za-z][A-Za-z0-9:-]*)")
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_STYLE_OR_SCRIPT_RE = re.compile(
    r"<(style|script)\b.*?</\1\s*>", re.DOTALL | re.IGNORECASE
)
_TAG_RE = re.compile(r"<[^>]*>")
_IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_IMG_SRC_RE = re.compile(r"""src\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""", re.IGNORECASE)


def measure_nesting_depth(html_text: str) -> int:
    """Peak element nesting depth (void and self-closing elements excluded).

    A deliberately small hand-written scanner instead of an HTML parser: it has
    to run before anything expensive and must not itself be attackable by the
    input.  Unbalanced close tags clamp at zero and unclosed open tags count as
    depth - the conservative direction for a guard whose purpose is to bound
    how much work MuPDF is handed.
    """
    depth = 0
    peak = 0
    index = 0
    length = len(html_text)

    while index < length:
        opened = html_text.find("<", index)
        if opened < 0:
            break

        if html_text.startswith("<!--", opened):
            closed = html_text.find("-->", opened + 4)
            index = length if closed < 0 else closed + 3
            continue

        if html_text.startswith("<!", opened) or html_text.startswith("<?", opened):
            closed = html_text.find(">", opened + 2)
            index = length if closed < 0 else closed + 1
            continue

        closed = html_text.find(">", opened + 1)
        if closed < 0:
            break

        raw = html_text[opened + 1:closed]
        index = closed + 1

        match = _TAG_HEAD_RE.match(raw)
        if match is None:
            continue

        if raw.lstrip().startswith("/"):
            depth = max(0, depth - 1)
            continue

        name = match.group(1).lower()
        stripped = raw.rstrip()
        if stripped.endswith(("/", "!")) or name in _VOID_ELEMENT_NAMES:
            continue

        depth += 1
        peak = max(peak, depth)

    return peak


def longest_text_token_length(html_text: str) -> int:
    """Longest unbroken whitespace-delimited run of *rendered* text.

    Markup, comments and <style>/<script> bodies are removed first: the guard
    bounds the length of a word MuPDF must shape, not the size of the source.
    """
    visible = _COMMENT_RE.sub(" ", html_text)
    visible = _STYLE_OR_SCRIPT_RE.sub(" ", visible)
    visible = _TAG_RE.sub(" ", visible)

    longest = 0
    for token in visible.split():
        longest = max(longest, len(token))
    return longest


def count_unresolved_image_tags(html_text: str) -> int:
    """Count <img> tags whose src cannot be resolved offline.

    This is the observability signal for the documented limitation "images only
    via data-URI embedding": MuPDF fetches nothing over the network, so every
    non-data src becomes its ``[image]`` placeholder.  The count never drives a
    decision - the string itself would be worse, since it is also legitimate
    prose (design review 6d).
    """
    unresolved = 0
    for tag in _IMG_TAG_RE.findall(html_text):
        match = _IMG_SRC_RE.search(tag)
        src = (match.group(2) if match else "").strip().lower()
        if not src.startswith("data:"):
            unresolved += 1
    return unresolved


def guard_html_structure(html_text: str) -> None:
    """Raise a typed honest error when the document exceeds a structural cap."""
    depth = measure_nesting_depth(html_text)
    if depth > MAX_ELEMENT_DEPTH:
        raise HtmlStructureRejected(
            f"nesting depth {depth} exceeds the {MAX_ELEMENT_DEPTH} limit"
        )


    token = longest_text_token_length(html_text)
    if token > MAX_TOKEN_LENGTH:
        raise HtmlStructureRejected(
            f"longest unbroken text run is {token} characters "
            f"(limit {MAX_TOKEN_LENGTH})"
        )


# ---------------------------------------------------------------------------
# Stage 1 - source intake: size, encoding, structure
# ---------------------------------------------------------------------------


def decode_html_bytes(raw: bytes) -> str:
    """Strict intake decode: UTF-8 first, UTF-16 BOM as the only fallback.

    ``<meta charset>`` is deliberately NOT consulted (MuPDF ignores it too): a
    cp1252 file that announces its own charset is still refused rather than
    silently mojibake'd.  No lossy fallback (latin-1) is ever used, because it
    accepts every byte sequence and would hand MuPDF text that is wrong in a
    way no validator can see.
    """
    if not raw:
        raise HtmlInputEmpty("zero-byte source")

    if raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        try:
            return raw.decode("utf-16")
        except UnicodeDecodeError as exc:
            raise HtmlEncodingUnsupported(
                f"utf-16 bom decode failed: {type(exc).__name__}"
            ) from exc

    try:
        # utf-8-sig also tolerates a leading UTF-8 BOM, which browsers strip.
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HtmlEncodingUnsupported(
            f"strict utf-8 decode failed at byte {exc.start}"
        ) from exc


def prepare_html_source(source_path: Path) -> str:
    """Validate and load the source; the only gate allowed before the spawn."""
    source_path = Path(source_path)

    try:
        size = source_path.stat().st_size
    except OSError as exc:
        raise HtmlInputRejected(
            f"source file is not readable: {type(exc).__name__}"
        ) from exc

    if size > MAX_HTML_INPUT_BYTES:
        raise HtmlInputTooLarge(
            f"source is {size} bytes, ceiling is {MAX_HTML_INPUT_BYTES}"
        )

    try:
        raw = source_path.read_bytes()
    except OSError as exc:
        raise HtmlInputRejected(f"source read failed: {type(exc).__name__}") from exc

    html_text = decode_html_bytes(raw)
    guard_html_structure(html_text)
    return html_text


# ---------------------------------------------------------------------------
# Stage 2 - the isolated render (blocking; call it via asyncio.to_thread)
# ---------------------------------------------------------------------------

#: Child statuses mapped to the honest error type they mean.  "engine_missing"
#: is deliberately absent: a server without MuPDF is an operator problem, so it
#: stays a RuntimeError -> 500 (F4 runner precedent), while bad input -> 422.
_CHILD_STATUS_TO_ERROR: dict[str, type[HtmlRenderError]] = {
    "input_rejected": HtmlInputRejected,
    "render_failed": HtmlRenderFailed,
    "page_limit": HtmlPageLimitExceeded,
    "output_rejected": HtmlOutputInvalid,
}


def _child_environment() -> dict[str, str]:
    env = dict(os.environ)
    # stdout carries the machine-readable report; force UTF-8 so a Windows
    # console codepage can never turn it into an unparsable replacement string.
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


def _parse_child_report(stdout: str) -> dict | None:
    """Extract the child's single JSON report line, or None if it is absent."""
    for line in (stdout or "").splitlines():
        if not line.startswith(RESULT_MARKER):
            continue
        try:
            payload = json.loads(line[len(RESULT_MARKER):].strip())
        except ValueError:
            return None
        return payload if isinstance(payload, dict) else None
    return None


def _discard_quietly(path: Path) -> None:
    """Never leave a partial or zero-byte output behind (F4 runner precedent)."""
    try:
        path.unlink(missing_ok=True)
    except OSError:  # pragma: no cover - platform-specific file locking
        logger.warning("html-to-pdf could not discard a partial output file")


def _failure_from_child(returncode: int, report: dict | None) -> Exception:
    """Translate an exit code + child report into a typed honest error.

    The numeric exit code / signal number lands in ``detail`` (server-side log)
    only - never in the client-facing message.
    """
    status = str((report or {}).get("status", ""))
    reason = str((report or {}).get("detail", "none"))

    if status == "engine_missing":
        return RuntimeError("The HTML rendering engine is unavailable on this server.")

    summary = f"child exit={returncode} status={status or 'unknown'} reason={reason}"
    if returncode < 0:
        # POSIX signal death (SIGSEGV etc.).
        return HtmlRenderCrashed(f"{summary} signal={-returncode}")

    error_cls = _CHILD_STATUS_TO_ERROR.get(status)
    if error_cls is None:
        return HtmlRenderCrashed(f"{summary} (no result report)")
    return error_cls(summary)


def render_html_to_pdf(
    html_text: str,
    output_path: Path,
    *,
    timeout_seconds: int = RENDER_TIMEOUT_SECONDS,
    max_pages: int = MAX_RENDER_PAGES,
    page_size: str = "a4",
) -> HtmlRenderOutcome:
    """Render validated HTML to ``output_path`` in a killable child process.

    Blocking by design: an ``async def`` caller must wrap this in
    ``asyncio.to_thread`` (as app/plugins/document/html_to_pdf.py does) so the
    single-worker event loop keeps serving other requests while the child runs.

    The HTML crosses the process boundary on stdin instead of as a file
    argument because a temp source file would have to live inside the
    conversion working root, where ConversionService enumerates output
    candidates - an extra file there would be ambiguous.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        str(RENDER_WORKER_PATH),
        "--output", str(output_path),
        "--max-pages", str(max_pages),
        "--page-size", page_size,
        "--min-output-bytes", str(MIN_OUTPUT_BYTES),
    ]

    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            input=html_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout_seconds,
            cwd=str(REPO_ROOT),
            env=_child_environment(),
        )
    except subprocess.TimeoutExpired as exc:
        # subprocess.run terminates the child here; the partial PDF must not
        # survive it, and the exception text (which carries the command line
        # and therefore temp paths) is never forwarded to a client.
        _discard_quietly(output_path)
        logger.warning(
            "html-to-pdf render child exceeded %ss and was terminated", timeout_seconds
        )
        raise HtmlRenderTimeout(f"render child exceeded {timeout_seconds}s") from exc
    except OSError as exc:
        _discard_quietly(output_path)
        raise HtmlRenderCrashed(f"child launch failed: {type(exc).__name__}") from exc

    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
    report = _parse_child_report(completed.stdout)

    if completed.returncode != 0:
        _discard_quietly(output_path)
        failure = _failure_from_child(completed.returncode, report)
        logger.warning(
            "html-to-pdf render child failed detail=%s stderr_tail=%r",
            getattr(failure, "detail", ""),
            (completed.stderr or "")[-400:],
        )
        raise failure

    if report is None or report.get("status") != "ok":
        _discard_quietly(output_path)
        logger.warning("html-to-pdf render child exited 0 without a usable report")
        raise HtmlRenderCrashed("exit 0 with no result report")

    pages = int(report.get("pages") or 0)
    if pages < 1 or pages > max_pages:
        _discard_quietly(output_path)
        raise HtmlOutputInvalid(f"child reported {pages} pages")

    return HtmlRenderOutcome(
        pid=int(report.get("pid") or 0),
        pages=pages,
        output_bytes=int(report.get("bytes") or 0),
        elapsed_ms=elapsed_ms,
        unresolved_images=count_unresolved_image_tags(html_text),
    )


# ---------------------------------------------------------------------------
# Stage 3 - output validation (V1 structural, V2 meaningful content)
# ---------------------------------------------------------------------------


def _page_ink_pixels(page, *, dpi: int) -> int:
    """Count non-near-white samples on one page at ``dpi``.

    DeviceGray without alpha guarantees one sample per pixel, which lets the
    paper tones be counted with C-speed ``bytes.count`` instead of a Python
    loop over ~125k samples per page (audit: ~13 ms/page).
    """
    import fitz

    pixmap = page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY, alpha=False)
    samples = pixmap.samples

    if pixmap.n != 1:  # pragma: no cover - defensive: grayscale has 1 band
        return sum(1 for value in samples if value < INK_NEAR_WHITE_FLOOR)

    paper = sum(samples.count(value) for value in range(INK_NEAR_WHITE_FLOOR, 256))
    return len(samples) - paper


def validate_html_output_pdf(
    pdf_path: Path,
    *,
    ink_floor: int = MIN_TOTAL_INK_PIXELS,
    dpi: int = INK_SAMPLE_DPI,
    max_pages: int = MAX_RENDER_PAGES,
) -> HtmlOutputReport:
    """Prove the produced PDF is real (V1) and actually shows something (V2).

    V2 sums ink across the whole document but stops as soon as the floor is
    cleared: page 1 of a normal document settles the question in ~13 ms, and
    only the inconclusive cases pay for the remaining pages (design review 6b).
    """
    import fitz

    pdf_path = Path(pdf_path)

    if not pdf_path.is_file():
        raise HtmlOutputInvalid("renderer produced no file")
    if pdf_path.stat().st_size < max(1, MIN_OUTPUT_BYTES):
        raise HtmlOutputInvalid("renderer produced a zero-byte file")

    with pdf_path.open("rb") as handle:
        if handle.read(5) != b"%PDF-":
            raise HtmlOutputInvalid("output is not a PDF (header check)")
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        handle.seek(max(0, size - _TRAILER_SCAN_BYTES))
        if b"%%EOF" not in handle.read():
            raise HtmlOutputInvalid("output is a truncated PDF (no EOF marker)")

    try:
        document = fitz.open(str(pdf_path))
    except Exception as exc:
        # MuPDF raises bare Exception subclasses here; any of them means the
        # file is not a PDF we can serve.
        raise HtmlOutputInvalid(f"pdf re-open failed: {type(exc).__name__}") from exc

    pages_checked = 0
    ink_pixels = 0
    early_exit = False

    try:
        page_count = document.page_count
        if page_count < 1:
            raise HtmlOutputInvalid("pdf has no pages")
        if page_count > max_pages:
            raise HtmlOutputInvalid(f"pdf has {page_count} pages (cap {max_pages})")

        for index in range(page_count):
            ink_pixels += _page_ink_pixels(document[index], dpi=dpi)
            pages_checked += 1
            # ink_floor <= 0 means "measure the whole document" (used by the
            # calibration evidence in tests/fixtures/html_to_pdf/).
            if ink_floor > 0 and ink_pixels >= ink_floor:
                early_exit = True
                break
    finally:
        document.close()

    if ink_pixels < ink_floor:
        raise HtmlOutputVisuallyEmpty(
            f"total ink {ink_pixels} is below the {ink_floor}-pixel floor "
            f"({pages_checked}/{page_count} pages sampled)"
        )

    return HtmlOutputReport(
        pages=page_count,
        ink_pixels=ink_pixels,
        pages_checked=pages_checked,
        early_exit=early_exit,
    )


# ---------------------------------------------------------------------------
# Pipeline (the single entry point the plugin drives from a worker thread)
# ---------------------------------------------------------------------------


def render_html_document(
    source_path: Path,
    output_path: Path,
    *,
    timeout_seconds: int = RENDER_TIMEOUT_SECONDS,
    ink_floor: int = MIN_TOTAL_INK_PIXELS,
    page_size: str = "a4",
) -> tuple[HtmlRenderOutcome, HtmlOutputReport]:
    """Run all three stages for one conversion.

    Kept synchronous on purpose: the plugin offloads exactly this call with
    ``asyncio.to_thread``, which is what keeps the event loop free.
    """
    html_text = prepare_html_source(Path(source_path))

    try:
        outcome = render_html_to_pdf(
            html_text,
            Path(output_path),
            timeout_seconds=timeout_seconds,
            page_size=page_size,
        )
        report = validate_html_output_pdf(Path(output_path), ink_floor=ink_floor)
    except Exception:
        # A refused output must not linger as a servable file.
        _discard_quietly(Path(output_path))
        raise

    logger.info(
        "html-to-pdf rendered pid=%s pages=%s bytes=%s ink=%s sampled=%s "
        "unresolved_images=%s",
        outcome.pid,
        report.pages,
        outcome.output_bytes,
        report.ink_pixels,
        report.pages_checked,
        outcome.unresolved_images,
    )
    return outcome, report
