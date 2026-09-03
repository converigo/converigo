"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 1.0.0

CSV -> JSON Plugin (SPR-05)

Convert CSV files to JSON (array of records) using pandas.
"""
from __future__ import annotations

from app.plugins.spreadsheet.base import SpreadsheetConverterPlugin


class CSVToJSONPlugin(SpreadsheetConverterPlugin):
    slug = "csv-to-json"
    name = "CSV to JSON"
    description = "Convert CSV data files to JSON format."
    engine = "spreadsheet"

    source_formats = ["csv"]
    target_formats = ["json"]

    reader_kind = "csv"
    writer_kind = "json"

    priority = 70
    quality = 90
    compatibility = 95
    estimated_saving = 5

    seo_title = "CSV to JSON Converter | Converigo"
    seo_description = "Convert CSV data files to JSON format quickly and easily."