"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / F8)
Version : 1.0.0

Markdown -> HTML converter (F8-B: md-to-html, +Markdown>=3.10.3).
Factory Batch F8-B - document cluster (net-new, audit proposal).

Built on the F0 certified factory scaffolding: the conversion pipeline
(discovery -> supports() check -> working root -> single servable file ->
non-empty output -> honest error) is owned by FactoryConversionPlugin.

Semantics (fixed, deterministic, single-servable-file):
- md-to-html: python-markdown core (no extensions, MVP) renders the
  Markdown text, and the fragment is wrapped in a minimal deterministic
  HTML5 document (same wrapper shape as the certified docx-to-html).

D5b disclosure (explicit, MVP - NO sanitizer):
- python-markdown passes RAW HTML BLOCKS through UNCHANGED by default.
  An input .md may therefore contain arbitrary HTML that reappears
  VERBATIM in the rendered output.  This MVP intentionally ships
  disclosure-only (no bleach/nh3 in the venv; adding a sanitizer is a
  separate dependency decision).  The landing page documents this in
  FAQ + about-formats so users are not misled, and the certified test
  pins the passthrough behavior so it can never change silently.
"""
from __future__ import annotations

import html as _html
from pathlib import Path

import markdown as _markdown

from app.factory import make_plugin_class


def _unsupported(source: str, target: str, message: str) -> Exception:
    """Lazily build the honest-422 error (rar-extract/F4 lazy-import precedent)."""
    from app.services.conversion_service import UnsupportedConversionError

    return UnsupportedConversionError(source, target, message)


def _convert_md_to_html(
    plugin: object, source_path: Path, target_format: str, working_root: Path
) -> Path:
    """Markdown core -> HTML5 document (raw HTML blocks pass through, D5b)."""
    try:
        text = source_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise _unsupported(
            "md",
            "html",
            f"MD to HTML conversion failed: the file is not valid UTF-8 text ({exc}).",
        ) from exc

    body = _markdown.markdown(text)
    document = (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        f"<title>{_html.escape(source_path.stem)}</title>\n"
        "</head>\n"
        "<body>\n"
        f"{body}\n"
        "</body>\n"
        "</html>\n"
    )

    suffix = target_format.lower().lstrip(".")
    output_path = working_root / f"{source_path.stem}.{suffix}"
    output_path.write_text(document, encoding="utf-8")
    return output_path


MdToHtmlPlugin = make_plugin_class(
    slug="md-to-html",
    source_formats=["md"],
    target_formats=["html"],
    engine_hook=_convert_md_to_html,
    name="MD to HTML",
    description="Convert Markdown files to clean, standalone HTML5 documents.",
    category="document",
    engine="document",
    goal="document",
    use_case="Best for publishing Markdown notes and READMEs as web pages.",
    priority=60,
    quality=85,
    compatibility=80,
    estimated_saving=8,
    badge="Markup Conversion",
    icon="⬆️",
    seo_title="MD to HTML Converter | Converigo",
    seo_description="Convert Markdown files to HTML documents quickly and easily.",
)