"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 1.0.0

CSV -> XLSX Plugin (SPR-02)

Convert CSV files to Excel XLSX spreadsheets using pandas + openpyxl.
"""
from __future__ import annotations

from app.plugins.spreadsheet.base import SpreadsheetConverterPlugin


class CSVToXLSXPlugin(SpreadsheetConverterPlugin):
    slug = "csv-to-xlsx"
    name = "CSV to XLSX"
    description = "Convert CSV files to Excel XLSX spreadsheets."
    engine = "spreadsheet"

    source_formats = ["csv"]
    target_formats = ["xlsx"]

    reader_kind = "csv"
    writer_kind = "excel"

    priority = 70
    quality = 90
    compatibility = 95
    estimated_saving = 5

    seo_title = "CSV to XLSX Converter | Converigo"
    seo_description = "Convert CSV data files to Excel XLSX spreadsheets quickly and easily."