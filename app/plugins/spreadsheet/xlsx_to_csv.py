"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 1.0.0

XLSX -> CSV Plugin (SPR-01)

Convert Excel spreadsheets to CSV format using pandas.
"""
from __future__ import annotations

from app.plugins.spreadsheet.base import SpreadsheetConverterPlugin


class XLSXToCSVPlugin(SpreadsheetConverterPlugin):
    slug = "xlsx-to-csv"
    name = "XLSX to CSV"
    description = "Convert Excel XLSX files to CSV format."
    engine = "spreadsheet"

    source_formats = ["xlsx"]
    target_formats = ["csv"]

    reader_kind = "excel"
    writer_kind = "csv"

    priority = 70
    quality = 90
    compatibility = 95
    estimated_saving = 5

    seo_title = "XLSX to CSV Converter | Converigo"
    seo_description = "Convert Excel XLSX spreadsheets to CSV files quickly and easily."