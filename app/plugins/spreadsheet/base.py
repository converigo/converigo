"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 1.0.0

Spreadsheet / Data Pipeline Plugin Base Class

Shared pandas-based conversion helpers for the XLSX / CSV / JSON / HTML
family of converters (pandas BSD-3-Clause, openpyxl MIT).

Every concrete plugin keeps its own slug, metadata and (source, target)
formats so the registry holds independent entries.  The base class only
owns the read/write DataFrame plumbing.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.core.settings import settings
from app.plugins.base import ConverterPlugin


class SpreadsheetConverterPlugin(ConverterPlugin):
    """Base class for pandas/openpyxl spreadsheet and data converters."""

    category = "spreadsheet"
    engine = "spreadsheet"
    icon = "📊"
    color = "green"

    # --------------------------------------------------
    # Subclass hooks
    # --------------------------------------------------
    # reader_kind: "excel" | "csv" | "json" | "auto"
    reader_kind = "auto"

    # writer_kind: "csv" | "excel" | "json" | "html"
    writer_kind = "csv"

    def _read_frame(self, source_path: Path) -> pd.DataFrame:
        suffix = source_path.suffix.lower().lstrip(".")
        reader = self.reader_kind

        if reader == "excel" or (reader == "auto" and suffix in {"xlsx", "xls"}):
            frame = pd.read_excel(source_path)
        elif reader == "json" or (reader == "auto" and suffix == "json"):
            frame = self._read_json_frame(source_path)
        else:
            # CSV is the default text format.
            frame = pd.read_csv(source_path)

        return frame

    @staticmethod
    def _read_json_frame(source_path: Path) -> pd.DataFrame:
        """Read a JSON file into a DataFrame.

        Handles the common shapes found in uploads:
        - a list of record objects
        - a single object (single row)
        - nested/ragged records (normalized via json_normalize)
        """
        import json

        raw = json.loads(source_path.read_text(encoding="utf-8"))

        if isinstance(raw, list):
            if not raw:
                return pd.DataFrame()
            return pd.json_normalize(raw)
        if isinstance(raw, dict):
            return pd.json_normalize(raw)
        raise ValueError("Unsupported JSON structure for conversion.")

    def _write_frame(self, frame: pd.DataFrame, output_path: Path) -> None:
        writer = self.writer_kind
        if writer == "csv":
            frame.to_csv(output_path, index=False, encoding="utf-8")
        elif writer == "excel":
            frame.to_excel(output_path, index=False, engine="openpyxl")
        elif writer == "json":
            frame.to_json(output_path, orient="records", force_ascii=False)
        elif writer == "html":
            html = frame.to_html(index=False, border=0, classes="converigo-table")
            output_path.write_text(html, encoding="utf-8")
        else:
            raise RuntimeError(f"Unsupported spreadsheet writer: {writer}")

    # --------------------------------------------------
    # Conversion
    # --------------------------------------------------
    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError(f"{type(self).__name__} does not support {source_path.suffix} -> {target_format}.")

        working_root = (temp_dir or output_dir or (settings.OUTPUT_DIR / "spreadsheet"))
        working_root.mkdir(parents=True, exist_ok=True)

        frame = self._read_frame(source_path)
        output_path = working_root / f"{source_path.stem}.{target_format}"
        self._write_frame(frame, output_path)

        if not output_path.exists():
            raise RuntimeError(f"Spreadsheet conversion did not produce output: {output_path}")
        return output_path
