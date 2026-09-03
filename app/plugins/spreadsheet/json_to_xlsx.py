"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 1.0.0

JSON -> XLSX Plugin (SPR-08)

Convert JSON (array of records) files to Excel XLSX using pandas + openpyxl.
"""
from __future__ import annotations

from app.plugins.spreadsheet.base import SpreadsheetConverterPlugin


class JSONToXLSXPlugin(SpreadsheetConverterPlugin):
    slug = "json-to-xlsx"
    name = "JSON to XLSX"
    description = "Convert JSON data files to Excel XLSX spreadsheets."
    engine = "spreadsheet"

    source_formats = ["json"]
    target_formats = ["xlsx"]

    reader_kind = "json"
    writer_kind = "excel"

    priority = 70
    quality = 90
    compatibility = 95
    estimated_saving = 5

    seo_title = "JSON to XLSX Converter | Converigo"
    seo_description = "Convert JSON files to Excel XLSX format quickly and easily."