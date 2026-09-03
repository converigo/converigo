"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 1.0.0

XLSX -> JSON Plugin (SPR-07)

Convert Excel XLSX files to JSON (array of records) using pandas.
"""
from __future__ import annotations

from app.plugins.spreadsheet.base import SpreadsheetConverterPlugin


class XLSXToJSONPlugin(SpreadsheetConverterPlugin):
    slug = "xlsx-to-json"
    name = "XLSX to JSON"
    description = "Convert Excel XLSX spreadsheets to JSON format."
    engine = "spreadsheet"

    source_formats = ["xlsx"]
    target_formats = ["json"]

    reader_kind = "excel"
    writer_kind = "json"

    priority = 70
    quality = 90
    compatibility = 95
    estimated_saving = 5

    seo_title = "XLSX to JSON Converter | Converigo"
    seo_description = "Convert Excel XLSX files to JSON format quickly and easily."