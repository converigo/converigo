"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / HTML-PDF)
Version : 1.0.0

Regenerates every html-to-pdf fixture in this directory.

Run from the repository root:

    python tests/fixtures/html_to_pdf/_generate.py

The fixtures exist so the ceilings in app/factory/html_pdf_runner.py and the
thresholds recorded in CALIBRATION.md stay reproducible and reviewable instead
of being asserted only in a chat log.  Pathological inputs are generated rather
than hand-written so their exact byte size (which the guards measure) is
obvious, and they are written without line breaks so git's text handling cannot
shift that size on checkout.
"""
from __future__ import annotations

import codecs
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

_CSS = (
    "<style>body{font-family:Helvetica,Arial,sans-serif;font-size:14px;"
    "color:#222}h1{font-size:26px}table{border-collapse:collapse}"
    "td,th{border:1px solid #999;padding:4px}</style>"
)

#: Ordinary 10-character words, used to hit byte-size ceilings exactly without
#: tripping the longest-token guard (a padded single word would be its own
#: pathological case).
_FILLER_WORD = "0123456789 "


def _sized_document(target_bytes: int) -> str:
    """An HTML document whose byte size is the largest that fits target_bytes."""
    prefix = "<html><body><p>"
    suffix = "</p></body></html>"
    repeats = max(1, (target_bytes - len(prefix) - len(suffix)) // len(_FILLER_WORD))
    return prefix + _FILLER_WORD * repeats + suffix



def _paragraphs(count: int) -> str:
    return "".join(
        f"<p>Section {i} carries measured report text with ordinary words "
        f"and a number {1000 + i}.</p>"
        for i in range(count)
    )


def write(name: str, content: str | bytes) -> int:
    """Write one fixture and return its byte size."""
    path = HERE / name
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8", newline="\n")
    return path.stat().st_size


def ordinary(sizes: dict[str, int]) -> None:
    """Documents a real user would expect to be served."""
    sizes["valid_report.html"] = write(
        "valid_report.html",
        "<!doctype html><html><head><meta charset='utf-8'>" + _CSS + "</head><body>"
        "<h1>Quarterly Report</h1>" + _paragraphs(12)
        + "<table><tr><th>Region</th><th>Revenue</th></tr>"
        + "".join(f"<tr><td>EMEA-{i}</td><td>{1000 + i}</td></tr>" for i in range(12))
        + "</table></body></html>",
    )

    sizes["minimal_word.html"] = write(
        "minimal_word.html", "<html><body><p>Hi</p></body></html>"
    )

    sizes["one_dot.html"] = write(
        "one_dot.html", "<html><body><p>.</p></body></html>"
    )

    sizes["multipage_report.html"] = write(
        "multipage_report.html",
        "<!doctype html><html><head><meta charset='utf-8'>" + _CSS + "</head><body>"
        + _paragraphs(400)
        + "</body></html>",
    )

    # Ordinary content on page 1, then forced page breaks that leave the last
    # pages blank: the per-page rule would wrongly reject this, the
    # document-total rule must accept it.
    sizes["page_break_blank_tail.html"] = write(
        "page_break_blank_tail.html",
        "<!doctype html><html><head><meta charset='utf-8'>" + _CSS + "</head><body>"
        + "<h1>Title page</h1>" + _paragraphs(8)
        + "<div style='page-break-before:always'></div>"
        + "<div style='page-break-before:always'></div>"
        + "<div style='page-break-before:always'></div>"
        + "</body></html>",
    )

    # Inline data-URI image: the only image form MuPDF can resolve without
    # network access, so it must produce ink on its own.
    sizes["data_uri_image.html"] = write(
        "data_uri_image.html",
        "<!doctype html><html><head><meta charset='utf-8'></head><body>"
        "<p>An inline data-URI image follows.</p>"
        "<img src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVU"
        "AAAAXklEQVR4Ae3OMQEAIAwAwPmftpIGxAnj2CVJkqQoSZIkSZIkSZIkSZIkSZIkSZIkSZIkS"
        "ZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIk+QqrNgLB6bUZ4QAAAABJRU5ErkJggg==' alt='box'>"
        "</body></html>",
    )

    # Layout CSS MuPDF does not implement: still has real text, so it renders
    # (differently from the browser) instead of failing.
    sizes["css_flexbox_layout.html"] = write(
        "css_flexbox_layout.html",
        "<!doctype html><html><head><meta charset='utf-8'><style>"
        ".a{display:flex;gap:20px}.b{display:grid;grid-template-columns:1fr 1fr}"
        ".c{float:left;width:50%}</style></head><body>"
        "<div class='a'><p>Flex child one</p><p>Flex child two</p></div>"
        "<div class='b'><p>Grid cell one</p><p>Grid cell two</p></div>"
        "<div class='c'><p>Float half</p></div></body></html>",
    )

    # Content that only exists if JavaScript runs: MuPDF executes no scripts,
    # so this page genuinely has nothing to show.
    sizes["script_generated_body.html"] = write(
        "script_generated_body.html",
        "<!doctype html><html><head><meta charset='utf-8'></head><body>"
        "<script>document.body.innerHTML='<h1>Injected by JavaScript</h1>';"
        "</script></body></html>",
    )


def visually_empty(sizes: dict[str, int]) -> None:
    """Documents that produce a structurally valid but blank-looking PDF."""
    sizes["blank.html"] = write("blank.html", "<html><body></body></html>")

    sizes["whitespace_only.html"] = write(
        "whitespace_only.html", "<html><body>   \n\t   \n   </body></html>"
    )

    sizes["nbsp_only.html"] = write(
        "nbsp_only.html", "<html><body>" + "&nbsp;" * 40 + "</body></html>"
    )

    # White text on a white page: extractable text, zero visible ink.
    # NOTE: the wrapper must be a <div>, not a <p> - a <p> inside a <p> is
    # auto-closed by the parser, so the style would land on an empty element
    # and the inner paragraphs would render at normal size (found while
    # calibrating; the first version of this fixture measured 13,510 ink).
    sizes["white_on_white.html"] = write(
        "white_on_white.html",
        "<html><body style='background:#ffffff'>"
        "<div style='color:#ffffff;font-size:40px'>Hello invisible world</div>"
        "<div style='color:white'>" + _paragraphs(20) + "</div></body></html>",
    )

    # Sub-pixel glyph: text is extractable, so text_chars-based checks pass,
    # but nothing is visible on paper.
    sizes["tiny_font.html"] = write(
        "tiny_font.html",
        "<html><body><div style='font-size:0.01px'>"
        + _paragraphs(20)
        + "</div></body></html>",
    )

    sizes["hidden_display_none.html"] = write(
        "hidden_display_none.html",
        "<html><head><style>.h{display:none}</style></head><body><div class='h'>"
        + _paragraphs(20)
        + "</div></body></html>",
    )

    # Only network images: no text, no resolvable image.  MuPDF writes its
    # "[image]" placeholder, which is exactly the ink floor's blind spot and
    # therefore documented on the landing page instead of being string-matched.
    sizes["external_image_only.html"] = write(
        "external_image_only.html",
        "<!doctype html><html><head><meta charset='utf-8'></head><body>"
        "<img src='https://example.invalid/network-only-logo.png' alt='logo'>"
        "<img src='//cdn.example.invalid/photo.jpg' alt='photo'></body></html>",
    )


def encodings(sizes: dict[str, int]) -> None:
    """Intake cases: strict UTF-8, narrow UTF-16 BOM, and honest refusals."""
    body = "<html><head><meta charset='utf-8'></head><body><p>Kilómetro 25 — naïve café</p></body></html>"

    sizes["valid_utf8.html"] = write("valid_utf8.html", body)

    sizes["utf8_bom.html"] = write(
        "utf8_bom.html", codecs.BOM_UTF8 + body.encode("utf-8")
    )

    sizes["utf16_le_bom.html"] = write(
        "utf16_le_bom.html",
        codecs.BOM_UTF16_LE + body.replace("utf-8", "utf-16").encode("utf-16-le"),
    )

    # Real cp1252 bytes: 0x92 is a typographic apostrophe there and an illegal
    # UTF-8 sequence, so this file is refused even though it declares its own
    # charset - the accepted trade-off of not honoring <meta charset>.
    sizes["cp1252_meta_charset.html"] = write(
        "cp1252_meta_charset.html",
        "<html><head><meta charset='windows-1252'></head><body><p>Don\u2019t convert"
        " this file \u2014 it holds cp1252 bytes behind an honest charset"
        " declaration.</p></body></html>".encode("cp1252"),
    )

    sizes["invalid_utf8.html"] = write(
        "invalid_utf8.html",
        b"<html><body><p>broken\xff\xfe\xfdbytes that are not utf-8</p></body></html>",
    )


def pathological(sizes: dict[str, int]) -> None:
    """Audit amplifiers: each one must be refused by a ceiling, not survived."""
    # MuPDF SIGSEGVs at ~11k nested inline tags (audit: "crash at 11k nested").
    sizes["deep_nesting_50k.html"] = write(
        "deep_nesting_50k.html", "<b>" * 50_000 + "payload" + "</b>" * 50_000
    )

    # 10k unclosed <div> elements: also a depth-shape attack, via never-closed
    # open tags instead of explicit nesting.
    sizes["unclosed_div_flood.html"] = write(
        "unclosed_div_flood.html", "<div>" * 10_000 + "content"
    )

    # One unsplittable 120k-character word.
    sizes["huge_single_word_120k.html"] = write(
        "huge_single_word_120k.html",
        "<html><body><p>" + "x" * 120_000 + "</p></body></html>",
    )

    # The audit's two amplification factors: many very long tokens.
    sizes["amplify_5k_tokens_100x.html"] = write(
        "amplify_5k_tokens_100x.html",
        "<html><body><p>" + ("y" * 5_000 + " ") * 100 + "</p></body></html>",
    )

    sizes["amplify_2k_tokens_1000x.html"] = write(
        "amplify_2k_tokens_1000x.html",
        "<html><body><p>" + ("z" * 2_000 + " ") * 1_000 + "</p></body></html>",
    )

    # Just above the 500 KiB intake ceiling (500 * 1024 = 512_000 bytes).
    sizes["oversize_513kb.html"] = write(
        "oversize_513kb.html", _sized_document(513_000)
    )

    # Just below the ceiling: must survive intake and reach the renderer.
    sizes["just_under_ceiling.html"] = write(
        "just_under_ceiling.html", _sized_document(511_000)
    )

    # Page-count amplifier: 5000 forced page breaks (over the 500-page cap).
    sizes["page_break_flood_5000.html"] = write(
        "page_break_flood_5000.html",
        "<html><body>" + "<div style='page-break-before:always'>x</div>" * 5_000
        + "</body></html>",
    )


def main() -> int:
    sizes: dict[str, int] = {}
    HERE.mkdir(parents=True, exist_ok=True)

    ordinary(sizes)
    visually_empty(sizes)
    encodings(sizes)
    pathological(sizes)

    for name in sorted(sizes):
        print(f"{name:34s} {sizes[name]:>9,} bytes")
    print(f"\n{len(sizes)} fixtures written to {HERE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


