"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / F5)
Version : 1.0.0

Excel/HTML Data Output Converters (SPR-16 xlsx-to-tsv, SPR-19 csv-to-html)
Factory Batch F5 - cluster G-E (Excel/HTML output), net-new pair.

Built on the F0 certified factory scaffolding: the conversion pipeline
(discovery -> supports() check -> working root -> single servable file ->
non-empty output -> honest error) is owned by FactoryConversionPlugin.
Each converter below is pure configuration plus a small hook, consistent
with the certified spreadsheet cluster engine (pandas BSD-3-Clause for
xlsx-to-tsv; stdlib csv + html modules for csv-to-html - zero new deps).

Semantics (fixed, D1-consistent):
- xlsx-to-tsv: the first worksheet is read with pandas (openpyxl engine)
  and written as standard tab-separated values (UTF-8, no index column).
- csv-to-html: the CSV is rendered as a clean, self-contained HTML table
  document (stdlib-only). D5b note: this is deliberately a minimal,
  semantic HTML table (escaped cells, thead/tbody, no styling) - the
  honest MVP scope is documented in the landing-page contract; content
  failures (empty CSV) raise UnsupportedConversionError -> honest 422,
  never a fabricated output.
"""
from __future__ import annotations

import csv as csv_mod
import html as html_mod
from pathlib import Path

import pandas as pd

from app.factory import make_plugin_class


def _unsupported(source: str, target: str, message: str) -> Exception:
    """Lazily build the honest-422 error (rar-extract/F4 lazy-import precedent)."""
    from app.services.conversion_service import UnsupportedConversionError

    return UnsupportedConversionError(source, target, message)


def _convert_xlsx_to_tsv(
    self, source_path: Path, target_format: str, working_root: Path
) -> Path:
    """Read the first XLSX worksheet and write standard tab-separated values."""
    try:
        frame = pd.read_excel(source_path)
    except Exception as exc:  # noqa: BLE001 - honest 422 for any parse failure
        raise _unsupported(
            "xlsx", "tsv", f"XLSX to TSV conversion failed: could not parse the workbook ({exc})."
        ) from exc
    if frame.empty:
        raise _unsupported("xlsx", "tsv", "XLSX to TSV conversion failed: the workbook has no data rows.")
    output_path = working_root / f"{source_path.stem}.{target_format}"
    frame.to_csv(output_path, index=False, sep="\t", encoding="utf-8")
    return output_path


def _convert_csv_to_html(
    self, source_path: Path, target_format: str, working_root: Path
) -> Path:
    """Render comma-separated CSV as a self-contained HTML table document."""
    try:
        with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = [row for row in csv_mod.reader(handle)]
    except UnicodeDecodeError as exc:
        raise _unsupported(
            "csv", "html", f"CSV to HTML conversion failed: file is not valid UTF-8 text ({exc})."
        ) from exc
    if not rows or all(not cell.strip() for cell in rows[0]):
        raise _unsupported("csv", "html", "CSV to HTML conversion failed: the file has no data rows.")
    header, body = rows[0], rows[1:]

    escape = html_mod.escape
    title = escape(source_path.stem)
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        f"<title>{title}</title>",
        "</head>",
        "<body>",
        f"<h1>{title}</h1>",
        "<table>",
        "<thead>",
        "<tr>" + "".join(f"<th>{escape(cell)}</th>" for cell in header) + "</tr>",
        "</thead>",
        "<tbody>",
    ]
    parts.extend(
        "<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in row) + "</tr>"
        for row in body
    )
    parts += ["</tbody>", "</table>", "</body>", "</html>", ""]

    output_path = working_root / f"{source_path.stem}.{target_format}"
    output_path.write_text("\n".join(parts), encoding="utf-8")
    return output_path


XlsxToTsvPlugin = make_plugin_class(
    slug="xlsx-to-tsv",
    source_formats=["xlsx"],
    target_formats=["tsv"],
    engine_hook=_convert_xlsx_to_tsv,
    name="XLSX to TSV",
    description="Convert Excel XLSX workbooks to TSV (tab-separated values) data files.",
    category="spreadsheet",
    engine="spreadsheet",
    priority=70,
    quality=90,
    compatibility=95,
    estimated_saving=5,
    seo_title="XLSX to TSV Converter | Converigo",
    seo_description="Convert XLSX spreadsheets to tab-separated TSV data files quickly and easily.",
)

CsvToHtmlPlugin = make_plugin_class(
    slug="csv-to-html",
    source_formats=["csv"],
    target_formats=["html"],
    engine_hook=_convert_csv_to_html,
    name="CSV to HTML",
    description="Convert CSV data files to a clean, self-contained HTML table document.",
    category="spreadsheet",
    engine="spreadsheet",
    priority=70,
    quality=90,
    compatibility=95,
    estimated_saving=5,
    seo_title="CSV to HTML Converter | Converigo",
    seo_description="Convert CSV data files to clean HTML table documents quickly and easily.",
)
