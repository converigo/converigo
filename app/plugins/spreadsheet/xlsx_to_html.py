"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 1.0.0

XLSX -> HTML Plugin (SPR-17)

Convert Excel XLSX files to an HTML table using pandas.
"""
from __future__ import annotations

from app.plugins.spreadsheet.base import SpreadsheetConverterPlugin


class XLSXToHTMLPlugin(SpreadsheetConverterPlugin):
    slug = "xlsx-to-html"
    name = "XLSX to HTML"
    description = "Convert Excel XLSX spreadsheets to HTML table format."
    engine = "spreadsheet"

    source_formats = ["xlsx"]
    target_formats = ["html"]

    reader_kind = "excel"
    writer_kind = "html"

    priority = 70
    quality = 85
    compatibility = 90
    estimated_saving = 5

    seo_title = "XLSX to HTML Converter | Converigo"
    seo_description = "Convert Excel XLSX files to HTML table format quickly and easily."