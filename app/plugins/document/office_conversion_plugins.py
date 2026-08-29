"""Office document converter plugins for deployment-validation coverage."""

from __future__ import annotations

from pathlib import Path

from app.plugins.base import ConverterPlugin


class _OfficePlaceholderPlugin(ConverterPlugin):
    """Minimal placeholder implementation for office-format converters."""

    category = "document"
    engine = "document"
    icon = "📄"
    goal = "document"
    use_case = "Placeholder office-document conversion for deployment validation."
    priority = 75
    quality = 80
    compatibility = 80
    estimated_saving = 5
    badge = "Office Conversion"

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError(f"{self.slug} only supports {self.source_formats} -> {self.target_formats}.")

        from app.core.settings import settings

        working_dir = temp_dir or output_dir or (settings.OUTPUT_DIR / "document")
        working_dir.mkdir(parents=True, exist_ok=True)

        normalized_target = self._resolve_output_extension(target_format)
        output_path = working_dir / f"{source_path.stem}.{normalized_target}"
        output_path.write_text(
            f"Placeholder conversion for {self.slug}: {source_path.name} -> {normalized_target}\n",
            encoding="utf-8",
        )
        return output_path

    @staticmethod
    def _resolve_output_extension(target_format: str) -> str:
        normalized = target_format.lower().lstrip(".")
        if normalized in {"word", "doc", "docx"}:
            return "docx"
        if normalized in {"ppt", "pptx", "powerpoint"}:
            return "pptx"
        if normalized in {"xlsx", "xls", "spreadsheet"}:
            return "xlsx"
        return normalized


class DOCXToJPGPlugin(_OfficePlaceholderPlugin):
    slug = "docx-to-jpg"
    name = "DOCX to JPG"
    description = "Convert DOCX documents into JPG images."
    source_formats = ["docx", "doc", "word"]
    target_formats = ["jpg", "jpeg"]
    seo_title = "DOCX to JPG Converter | Converigo"
    seo_description = "Convert DOCX documents into JPG images quickly and easily."


class DOCXToPPTPlugin(_OfficePlaceholderPlugin):
    slug = "docx-to-ppt"
    name = "DOCX to PPT"
    description = "Convert DOCX documents into PowerPoint presentations."
    source_formats = ["docx", "doc", "word"]
    target_formats = ["ppt", "pptx", "powerpoint"]
    seo_title = "DOCX to PPT Converter | Converigo"
    seo_description = "Convert DOCX documents into PowerPoint files quickly and easily."


class DOCXToXLSXPlugin(_OfficePlaceholderPlugin):
    slug = "docx-to-xlsx"
    name = "DOCX to XLSX"
    description = "Convert DOCX documents into Excel spreadsheets."
    source_formats = ["docx", "doc", "word"]
    target_formats = ["xlsx", "xls", "spreadsheet"]
    seo_title = "DOCX to XLSX Converter | Converigo"
    seo_description = "Convert DOCX documents into Excel spreadsheets quickly and easily."


class PDFToWordPlugin(_OfficePlaceholderPlugin):
    slug = "pdf-to-word"
    name = "PDF to Word"
    description = "Convert PDF documents into editable Word files."
    source_formats = ["pdf"]
    target_formats = ["docx", "doc", "word"]
    seo_title = "PDF to Word Converter | Converigo"
    seo_description = "Convert PDF documents into editable Word files quickly and easily."


class PPTToDOCXPlugin(_OfficePlaceholderPlugin):
    slug = "ppt-to-docx"
    name = "PPT to DOCX"
    description = "Convert PowerPoint presentations into editable Word documents."
    source_formats = ["ppt", "pptx", "powerpoint"]
    target_formats = ["docx", "doc", "word"]
    seo_title = "PPT to DOCX Converter | Converigo"
    seo_description = "Convert PowerPoint presentations into editable Word documents quickly and easily."


class PPTToJPGPlugin(_OfficePlaceholderPlugin):
    slug = "ppt-to-jpg"
    name = "PPT to JPG"
    description = "Convert PowerPoint presentations into JPG images."
    source_formats = ["ppt", "pptx", "powerpoint"]
    target_formats = ["jpg", "jpeg"]
    seo_title = "PPT to JPG Converter | Converigo"
    seo_description = "Convert PowerPoint presentations into JPG images quickly and easily."


class PPTToXLSXPlugin(_OfficePlaceholderPlugin):
    slug = "ppt-to-xlsx"
    name = "PPT to XLSX"
    description = "Convert PowerPoint presentations into Excel spreadsheets."
    source_formats = ["ppt", "pptx", "powerpoint"]
    target_formats = ["xlsx", "xls", "spreadsheet"]
    seo_title = "PPT to XLSX Converter | Converigo"
    seo_description = "Convert PowerPoint presentations into Excel spreadsheets quickly and easily."


class WordToPDFPlugin(_OfficePlaceholderPlugin):
    slug = "word-to-pdf"
    name = "Word to PDF"
    description = "Convert Word documents into PDF files."
    source_formats = ["docx", "doc", "word"]
    target_formats = ["pdf"]
    seo_title = "Word to PDF Converter | Converigo"
    seo_description = "Convert Word documents into PDF files quickly and easily."


class XLSXToDOCXPlugin(_OfficePlaceholderPlugin):
    slug = "xlsx-to-docx"
    name = "XLSX to DOCX"
    description = "Convert Excel spreadsheets into Word documents."
    source_formats = ["xlsx", "xls", "spreadsheet"]
    target_formats = ["docx", "doc", "word"]
    seo_title = "XLSX to DOCX Converter | Converigo"
    seo_description = "Convert Excel spreadsheets into Word documents quickly and easily."


class XLSXToPPTPlugin(_OfficePlaceholderPlugin):
    slug = "xlsx-to-ppt"
    name = "XLSX to PPT"
    description = "Convert Excel spreadsheets into PowerPoint presentations."
    source_formats = ["xlsx", "xls", "spreadsheet"]
    target_formats = ["ppt", "pptx", "powerpoint"]
    seo_title = "XLSX to PPT Converter | Converigo"
    seo_description = "Convert Excel spreadsheets into PowerPoint presentations quickly and easily."
