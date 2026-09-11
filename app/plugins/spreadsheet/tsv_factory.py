"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / F1)
Version : 1.0.0

TSV <-> CSV Data Converters (SPR-14 tsv-to-csv, SPR-15 csv-to-tsv)
Factory Batch F1 - cluster G-A (Data/Spreadsheet text), net-new pair.

Built on the F0 certified factory scaffolding: the conversion pipeline
(discovery -> supports() check -> working root -> single servable file ->
non-empty output -> honest RuntimeError -> API 422 UNSUPPORTED_CONVERSION)
is owned by FactoryConversionPlugin.  Each converter below is pure
configuration plus a small pandas hook, consistent with the certified
spreadsheet cluster engine (pandas BSD-3-Clause).

Governance note (F1 audit): of the six G-A candidates in the Factory Batch
Plan, four (SPR-01 xlsx-to-csv, SPR-02 csv-to-xlsx, SPR-05 csv-to-json,
SPR-06 json-to-csv) were already installed and certified before F1; only
this TSV pair was missing from the registry.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.factory import make_plugin_class


def _convert_tsv_to_csv(
    self, source_path: Path, target_format: str, working_root: Path
) -> Path:
    """Read tab-separated values and write standard comma-separated CSV."""
    frame = pd.read_csv(source_path, sep="\t")
    output_path = working_root / f"{source_path.stem}.{target_format}"
    frame.to_csv(output_path, index=False, encoding="utf-8")
    return output_path


def _convert_csv_to_tsv(
    self, source_path: Path, target_format: str, working_root: Path
) -> Path:
    """Read comma-separated CSV and write tab-separated values."""
    frame = pd.read_csv(source_path)
    output_path = working_root / f"{source_path.stem}.{target_format}"
    frame.to_csv(output_path, index=False, sep="\t", encoding="utf-8")
    return output_path


TsvToCsvPlugin = make_plugin_class(
    slug="tsv-to-csv",
    source_formats=["tsv"],
    target_formats=["csv"],
    engine_hook=_convert_tsv_to_csv,
    name="TSV to CSV",
    description="Convert TSV (tab-separated values) data files to CSV format.",
    category="spreadsheet",
    engine="spreadsheet",
    priority=70,
    quality=90,
    compatibility=95,
    estimated_saving=5,
    seo_title="TSV to CSV Converter | Converigo",
    seo_description="Convert TSV data files to CSV format quickly and easily.",
)

CsvToTsvPlugin = make_plugin_class(
    slug="csv-to-tsv",
    source_formats=["csv"],
    target_formats=["tsv"],
    engine_hook=_convert_csv_to_tsv,
    name="CSV to TSV",
    description="Convert CSV data files to TSV (tab-separated values) format.",
    category="spreadsheet",
    engine="spreadsheet",
    priority=70,
    quality=90,
    compatibility=95,
    estimated_saving=5,
    seo_title="CSV to TSV Converter | Converigo",
    seo_description="Convert CSV data files to TSV format quickly and easily.",
)