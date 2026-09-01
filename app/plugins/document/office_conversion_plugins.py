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

        # PR-0 (Opsi B — honest-message stopgap): this converter is still a
        # placeholder and the real conversion has NOT been implemented yet.
        # Never fabricate a fake .txt file disguised as the target format.
        # Instead raise an honest UnsupportedConversionError so the existing
        # error pipeline (convert.py -> HTTP 422 + code UNSUPPORTED_CONVERSION)
        # surfaces a clear "not available yet" message to the user.
        # Local import keeps the module safe during plugin discovery (no
        # circular import with app.services.conversion_service).
        # Real conversion implementation lands in PR-1 / PR-2.
        from app.services.conversion_service import UnsupportedConversionError

        raise UnsupportedConversionError(
            source_path.suffix.lstrip(".").lower(),
            target_format,
            message=(
                f"{self.slug} conversion is not available yet. "
                "This converter is coming soon — please check back later."
            ),
        )

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


class PDFToWordPlugin(_OfficePlaceholderPlugin):
    slug = "pdf-to-word"
    name = "PDF to Word"
    description = "Convert PDF documents into editable Word files."
    source_formats = ["pdf"]
    target_formats = ["docx", "doc", "word"]
    seo_title = "PDF to Word Converter | Converigo"
    seo_description = "Convert PDF documents into editable Word files quickly and easily."


class WordToPDFPlugin(_OfficePlaceholderPlugin):
    slug = "word-to-pdf"
    name = "Word to PDF"
    description = "Convert Word documents into PDF files."
    source_formats = ["docx", "doc", "word"]
    target_formats = ["pdf"]
    seo_title = "Word to PDF Converter | Converigo"
    seo_description = "Convert Word documents into PDF files quickly and easily."
