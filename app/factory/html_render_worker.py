"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / HTML-PDF)
Version : 1.0.0

Isolated MuPDF HTML -> PDF render worker (child-process entry point).

This module is NOT a converter plugin: it is a small standalone script that
``app/factory/html_pdf_runner.py`` executes as a *separate OS process*
(``sys.executable <path>``).  MuPDF's HTML engine is native code, and a native
hang or segfault inside it cannot be interrupted by the caller - so it has to
run in a process the caller can kill.  Keeping this file in app/factory/
(outside app/plugins/) also means plugin discovery rglob never mistakes it for
a converter plugin (same placement rule as ffmpeg_runner.py).

Protocol (deliberately narrow, so the parent never has to trust text):
  * input  : the HTML document arrives on stdin as UTF-8 bytes, already
             size-checked / decoded / structurally guarded by the parent.
  * output : one JSON line on stdout, prefixed with RESULT_MARKER, reporting
             pid, page count and output size.
  * exit   : one of the EXIT_* codes below.  The parent maps exit codes to
             typed honest errors; nothing on stderr ever reaches a client.

Rendering uses the documented Story -> DocumentWriter loop, the only HTML
entry point in this MuPDF build with defined pagination:

    while True:
        more, filled = story.place(rect)          # tuple, never falsy
        device = writer.begin_page(mediabox)
        story.draw(device)
        writer.end_page()
        if not more:
            break
    # a hard iteration cap sits on top of the loop as a second safety net

``insert_htmlbox`` (no pagination) and ``open(filetype="html")`` (broken
charset handling) are intentionally not used.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

#: Prefix of the single machine-readable stdout line the parent parses.
RESULT_MARKER = "CONVERIGO_HTML_RENDER_RESULT"

EXIT_OK = 0
EXIT_INPUT_REJECTED = 2
EXIT_RENDER_FAILED = 3
EXIT_PAGE_LIMIT = 4
EXIT_OUTPUT_REJECTED = 5
EXIT_ENGINE_MISSING = 6

#: Half-inch default margins, matching the repository's other PDF renderers.
DEFAULT_MARGIN_POINTS = 36.0

#: How many trailing bytes to scan for the %%EOF marker during self-check.
_TRAILER_SCAN_BYTES = 1024


class PageLimitExceeded(RuntimeError):
    """Raised when pagination would continue past the hard page cap."""

    def __init__(self, pages: int, limit: int) -> None:
        super().__init__(f"pagination exceeded the {limit}-page limit")
        self.pages = pages


class OutputRejected(RuntimeError):
    """Raised when the written file fails the byte-level self-check."""


def _emit(payload: dict) -> None:
    """Write the machine-readable result line (stdout is reserved for this)."""
    sys.stdout.write(f"{RESULT_MARKER} {json.dumps(payload)}\n")
    sys.stdout.flush()


def _fail(status: str, exc: BaseException, *, pages: int = -1, log: bool = False) -> tuple[int, dict]:
    """Build a (exit_code, payload) pair for one honest failure mode."""
    code = {
        "input_rejected": EXIT_INPUT_REJECTED,
        "engine_missing": EXIT_ENGINE_MISSING,
        "page_limit": EXIT_PAGE_LIMIT,
        "output_rejected": EXIT_OUTPUT_REJECTED,
    }.get(status, EXIT_RENDER_FAILED)
    if log:
        # Server-side only: stderr is captured by the parent and never
        # forwarded to a client, so the honest refusal stays debuggable.
        sys.stderr.write(f"{type(exc).__name__}: {exc}\n")
    return code, {"status": status, "detail": type(exc).__name__, "pages": pages}


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-pages", type=int, default=500)
    parser.add_argument("--page-size", default="a4")
    parser.add_argument("--margin", type=float, default=DEFAULT_MARGIN_POINTS)
    parser.add_argument("--min-output-bytes", type=int, default=1)
    return parser.parse_args(argv)


def _read_html_from_stdin() -> str:
    """Decode stdin as strict UTF-8 (the parent already validated it)."""
    raw = sys.stdin.buffer.read()
    if not raw.strip():
        raise ValueError("empty input")
    return raw.decode("utf-8")


def render(
    html_text: str,
    output_path: str,
    *,
    max_pages: int,
    page_size: str = "a4",
    margin: float = DEFAULT_MARGIN_POINTS,
) -> int:
    """Render HTML into a PDF file and return the page count written.

    ``max_pages`` is a hard cap on the pagination loop: it is enforced even
    though the loop is already driven by ``more``, because a future
    ``place()`` regression that always reports "more content" would otherwise
    turn one conversion into an endless page generator.
    """
    import fitz

    mediabox = fitz.paper_rect(page_size)
    body_rect = mediabox + (margin, margin, -margin, -margin)
    if body_rect.is_empty or body_rect.width <= 0 or body_rect.height <= 0:
        raise RuntimeError("degenerate page geometry")

    story = fitz.Story(html=html_text)
    pages = 0

    # Context manager: a failed write must never leave a locked or
    # half-written file that blocks the caller's cleanup.
    with fitz.DocumentWriter(output_path) as writer:
        while True:
            # place() returns the TUPLE (more, filled) and is therefore never
            # falsy: the loop is driven by `more`, never by the truthiness of
            # the call itself.
            more, _filled = story.place(body_rect)
            device = writer.begin_page(mediabox)
            story.draw(device)
            writer.end_page()
            pages += 1
            if not more:
                break
            if pages >= max_pages:
                raise PageLimitExceeded(pages, max_pages)

    return pages


def _self_check_output(output_path: str, min_bytes: int) -> int:
    """Cheap byte-level self-check; returns the file size.

    Only structural facts are checked here (existence, size, %PDF header,
    %%EOF trailer) - no native parsing of the file we just wrote.  Meaning
    (page count, visible content) is validated by the parent.
    """
    path = Path(output_path)
    if not path.is_file():
        raise OutputRejected("missing output")

    size = path.stat().st_size
    if size < max(1, min_bytes):
        raise OutputRejected("output too small")

    with path.open("rb") as handle:
        head = handle.read(5)
        handle.seek(max(0, size - _TRAILER_SCAN_BYTES))
        tail = handle.read()

    if head != b"%PDF-":
        raise OutputRejected("bad pdf header")
    if b"%%EOF" not in tail:
        raise OutputRejected("missing eof marker")
    return size


def main(argv: list[str] | None = None) -> int:
    """Child entry point: read HTML on stdin, write a PDF, report on stdout."""
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    started = time.perf_counter()

    try:
        html_text = _read_html_from_stdin()
    except Exception as exc:  # noqa: BLE001 - any undecodable stdin is refused
        code, payload = _fail("input_rejected", exc)
    else:
        try:
            import fitz  # noqa: F401  (engine availability is fatal, checked once)
        except Exception as exc:  # noqa: BLE001  # pragma: no cover - environment problem
            code, payload = _fail("engine_missing", exc)
        else:
            pages = 0
            try:
                pages = render(
                    html_text,
                    args.output,
                    max_pages=args.max_pages,
                    page_size=args.page_size,
                    margin=args.margin,
                )
            except PageLimitExceeded as exc:
                code, payload = _fail("page_limit", exc, pages=exc.pages)
            except Exception as exc:  # noqa: BLE001 - native failure surfaces here
                code, payload = _fail("render_failed", exc, pages=pages, log=True)
            else:
                try:
                    size = _self_check_output(args.output, args.min_output_bytes)
                except Exception as exc:  # noqa: BLE001
                    code, payload = _fail("output_rejected", exc, pages=pages, log=True)
                else:
                    _emit(
                        {
                            "status": "ok",
                            "pages": pages,
                            "bytes": size,
                            "pid": os.getpid(),
                            "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
                        }
                    )
                    return EXIT_OK

    _emit(payload)
    return code


if __name__ == "__main__":
    sys.exit(main())

