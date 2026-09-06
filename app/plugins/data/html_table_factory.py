"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / F8)
Version : 1.0.0

HTML -> CSV converter (F8-C: html-to-csv via pandas.read_html).
Factory Batch F8-C - data cluster (net-new, audit proposal).

Built on the F0 certified factory scaffolding: the conversion pipeline
(discovery -> supports() check -> working root -> single servable file ->
non-empty output -> honest error) is owned by FactoryConversionPlugin.

Semantics (fixed, deterministic, single-servable-file):
- html-to-csv: pandas.read_html (lxml flavor) extracts ALL tables; the
  FIRST table in document order is serialized to CSV (index=False).
  Documents without any <table> raise the honest 422.  The first-table
  scope is disclosed on the landing page (FAQ + about-formats).

Dependency hygiene (audit Bagian 4.5 / Gate 0): pandas.read_html needs
lxml (and bs4 as the alternate flavor); both were used at runtime but
undeclared in requirements.txt.  Gate 0 pins lxml>=6.0.0 and
beautifulsoup4>=4.12.0 as part of the F8 commit series.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as _pandas

from app.factory import make_plugin_class


def _unsupported(source: str, target: str, message: str) -> Exception:
    """Lazily build the honest-422 error (rar-extract/F4 lazy-import precedent)."""
    from app.services.conversion_service import UnsupportedConversionError

    return UnsupportedConversionError(source, target, message)


def _convert_html_to_csv(
    plugin: object, source_path: Path, target_format: str, working_root: Path
) -> Path:
    """First <table> in document order -> deterministic CSV (index=False)."""
    try:
        tables = _pandas.read_html(BytesIO(source_path.read_bytes()), flavor="lxml")
    except ValueError as exc:
        # pandas raises ValueError("No tables found") for table-less HTML.
        raise _unsupported(
            "html",
            "csv",
            f"HTML to CSV conversion failed: no readable table found ({exc}).",
        ) from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise _unsupported(
            "html",
            "csv",
            f"HTML to CSV conversion failed: the file is not readable HTML ({exc}).",
        ) from exc

    if not tables:
        raise _unsupported(
            "html",
            "csv",
            "HTML to CSV conversion failed: the document contains no table.",
        )

    frame = tables[0]
    if frame.empty:
        raise _unsupported(
            "html",
            "csv",
            "HTML to CSV conversion failed: the first table is empty.",
        )

    suffix = target_format.lower().lstrip(".")
    output_path = working_root / f"{source_path.stem}.{suffix}"
    frame.to_csv(output_path, index=False)
    return output_path


HtmlToCsvPlugin = make_plugin_class(
    slug="html-to-csv",
    source_formats=["html"],
    target_formats=["csv"],
    engine_hook=_convert_html_to_csv,
    name="HTML to CSV",
    description="Extract the first HTML table into a CSV data file.",
    category="data",
    engine="data",
    goal="conversion",
    use_case="Best for pulling tabular data out of saved web pages into spreadsheets.",
    priority=60,
    quality=90,
    compatibility=95,
    estimated_saving=5,
    badge="Table Extractor",
    icon="📊",
    seo_title="HTML to CSV Converter | Converigo",
    seo_description="Convert HTML tables to CSV data files quickly and easily.",
)