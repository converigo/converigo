"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 1.0.0

JSON -> CSV Plugin (SPR-06)

Convert JSON (array of records) files to CSV using pandas.
"""
from __future__ import annotations

from app.plugins.spreadsheet.base import SpreadsheetConverterPlugin


class JSONToCSVPlugin(SpreadsheetConverterPlugin):
    slug = "json-to-csv"
    name = "JSON to CSV"
    description = "Convert JSON data files to CSV format."
    engine = "spreadsheet"

    source_formats = ["json"]
    target_formats = ["csv"]

    reader_kind = "json"
    writer_kind = "csv"

    priority = 70
    quality = 90
    compatibility = 95
    estimated_saving = 5

    seo_title = "JSON to CSV Converter | Converigo"
    seo_description = "Convert JSON data files to CSV format quickly and easily."