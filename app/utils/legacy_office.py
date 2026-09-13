"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 1.0.0

PR-1 (OLE2 honest-disable) — single source of truth for legacy binary Office
containers (OLE2 / Compound File Binary, magic d0cf11e0a1b11ae1).

Scope
-----
openpyxl, python-docx and python-pptx can only read the ZIP-based OOXML
containers (.xlsx/.docx/.pptx). A genuine legacy .xls/.doc/.ppt file can never
be read by them, so every converter that advertises those inputs is a dead end
that surfaces as an HTTP 500 leaking the library's own error text (and
sometimes an absolute server path). This module gives every affected layer one
shared, content-based guard and one honest error type.

Honesty rule used throughout: the decision is made from the file's *bytes*,
never from its extension. A file named .xls that really contains a ZIP OOXML
workbook still works and must keep working; a file named .docx that contains
OLE2 never works and must be refused with guidance.

Why the conversion_service import is lazy
-----------------------------------------
app.services.conversion_service imports app.plugins.registry, and
app.plugins.registry instantiates PluginRegistry() at module scope, which
discovers and imports every plugin module. A plugin that imported this module
and resolved UnsupportedConversionError at module level would therefore re-enter
a partially initialised conversion_service and fail with a circular ImportError.
The base class is resolved inside the factory function instead — the same
precedent document_factory._unsupported() already follows for its honest-422
errors, and office_conversion_plugins.py:40-43 for its placeholder errors.
"""

from __future__ import annotations

from pathlib import Path

# ==========================================================
# Container facts
# ==========================================================

# OLE2 / Compound File Binary signature: legacy .xls, .doc and .ppt all live in
# this container. python-docx / openpyxl / python-pptx cannot read any of them.
OLE2_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"

# OOXML (.docx/.xlsx/.pptx) are ZIP archives.
ZIP_MAGIC = b"PK\x03\x04"

# legacy extension -> the modern format the user should re-save as.
LEGACY_OFFICE_REPLACEMENTS = {
    "xls": "xlsx",
    "doc": "docx",
    "ppt": "pptx",
}

# Extension used in user-facing copy when the uploaded suffix is not one of the
# three known legacy tokens (e.g. a .docx-named file holding OLE2 bytes).
_LEGACY_LABEL_BY_EXTENSION = {
    "xls": ".xls",
    "doc": ".doc",
    "ppt": ".ppt",
    "xlsx": ".xlsx",
    "docx": ".docx",
    "pptx": ".pptx",
}


def normalize_format(value: str) -> str:
    """Return a bare lowercase extension token from '.XLS', 'xls' or 'xlsx'."""
    return str(value or "").lower().lstrip(".").strip()


def detect_container(source_path: Path) -> str:
    """Classify a file by its leading bytes: 'ole2', 'zip' or 'other'.

    Reads only the 8-byte header and never raises for unreadable files, so the
    guard stays usable on any code path (a subsequent engine read will surface
    a genuine I/O problem on its own).
    """
    try:
        with Path(source_path).open("rb") as handle:
            header = handle.read(8)
    except OSError:
        return "other"

    if header.startswith(OLE2_MAGIC):
        return "ole2"
    if header.startswith(ZIP_MAGIC):
        return "zip"
    return "other"


def legacy_replacement_for(value: str) -> str:
    """The bare modern token to recommend for a (possibly mislabelled) input."""
    extension = normalize_format(value)
    if extension in LEGACY_OFFICE_REPLACEMENTS:
        return LEGACY_OFFICE_REPLACEMENTS[extension]
    # Already an OOXML token (a legacy file mislabelled as .docx/.xlsx/.pptx):
    # re-saving it in that same modern format is the fix. Anything else falls
    # back to .xlsx, the widest-compatible recommendation.
    if extension in {"xlsx", "docx", "pptx"}:
        return extension
    return "xlsx"


def legacy_guidance(source_format: str, target_format: str | None = None) -> str:
    """Build the user-facing copy: what failed, why, and what to do about it.

    Deliberately free of library names, exception class names and server paths —
    this string is returned to the client in the HTTP response body.
    """
    extension = normalize_format(source_format)
    replacement = legacy_replacement_for(extension)
    label = _LEGACY_LABEL_BY_EXTENSION.get(extension, f".{replacement}")

    if extension in LEGACY_OFFICE_REPLACEMENTS:
        problem = (
            f"Legacy {label} files (OLE2 compound document) are not supported "
            "by this converter."
        )
    else:
        # The extension claimed OOXML but the bytes are a legacy OLE2 container.
        problem = (
            f"That file is not a real {label} document: its contents are a "
            "legacy OLE2 compound document, which this converter cannot read."
        )

    advice = f"Please re-save it as .{replacement} and upload again"
    if target_format:
        advice += f" to convert it to {normalize_format(target_format).upper()}"
    return f"{problem} {advice}."


# ==========================================================
# Error type
# ==========================================================

_LEGACY_ERROR_CLASS: type[Exception] | None = None


def legacy_format_unsupported_error(
    source_format: str,
    target_format: str,
    message: str | None = None,
) -> Exception:
    """Build LegacyFormatUnsupportedError(source, target, guidance).

    The class subclasses conversion_service.UnsupportedConversionError, which is
    already mapped to HTTP 422 with a structured UNSUPPORTED_CONVERSION body
    (routers/convert.py), so no status mapping change is needed for the
    conversion layer. It is defined on first use and cached: subclassing at
    module import time would trigger the circular-import problem described in
    this module's docstring.
    """
    global _LEGACY_ERROR_CLASS

    from app.services.conversion_service import UnsupportedConversionError

    if _LEGACY_ERROR_CLASS is None:
        class LegacyFormatUnsupportedError(UnsupportedConversionError):
            """A legacy OLE2 .xls/.doc/.ppt input was refused honestly."""

        _LEGACY_ERROR_CLASS = LegacyFormatUnsupportedError

    extension = normalize_format(source_format)
    return _LEGACY_ERROR_CLASS(
        extension or "file",
        normalize_format(target_format),
        message or legacy_guidance(extension, target_format),
    )


def guard_legacy_container(
    source_path: Path,
    source_format: str,
    target_format: str,
) -> None:
    """Raise the honest-422 legacy error when bytes say OLE2, else pass.

    Content-driven by design: only files whose header carries the OLE2 magic are
    refused, because those are the only ones the OOXML libraries can never read.
    """
    if detect_container(source_path) != "ole2":
        return
    raise legacy_format_unsupported_error(source_format, target_format)

    return "other"
