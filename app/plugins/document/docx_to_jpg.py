"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

DOCX -> JPG Plugin

Converts DOCX documents into JPG images (first page only).
"""

from pathlib import Path

from app.engines.document_engine import DocumentEngine
from app.plugins.base import ConverterPlugin


class DOCXToJPGPlugin(ConverterPlugin):
    slug = "docx-to-jpg"
    name = "DOCX to JPG"
    description = "Convert DOCX documents into JPG images."
    category = "document"
    engine = "document"
    icon = "🖼️"

    source_formats = ["docx", "doc", "word"]
    target_formats = ["jpg", "jpeg"]

    goal = "document"
    use_case = "Best for turning Word documents into image files for previews and thumbnails."
    priority = 75
    quality = 85
    compatibility = 80
    estimated_saving = 8
    badge = "Office Conversion"
    seo_title = "DOCX to JPG Converter | Converigo"
    seo_description = "Convert DOCX documents into JPG images quickly and easily."

    # DOCX (OOXML) files are ZIP archives and start with the "PK" signature.
    _DOCX_PK_MAGIC = b"PK\x03\x04"
    # Legacy .doc files are OLE2 / Compound File Binary containers.
    _DOC_OLE2_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"

    @classmethod
    def _detect_container(cls, source_path: Path) -> str:
        """Return the container type detected from file content.

        Returns "docx" for ZIP/OOXML files, "doc" for OLE2/CFB files, or
        "unknown" for anything else (empty file, RTF, plain text, ...).
        """
        try:
            with source_path.open("rb") as fh:
                header = fh.read(8)
        except OSError as exc:
            raise RuntimeError(f"Could not read the source document: {exc}") from exc

        if header.startswith(cls._DOCX_PK_MAGIC):
            return "docx"
        if header.startswith(cls._DOC_OLE2_MAGIC):
            return "doc"
        return "unknown"

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("DOCXToJPGPlugin only supports DOCX -> JPG.")

        container = self._detect_container(source_path)

        if container == "doc":
            raise RuntimeError(
                "Legacy .doc format (OLE2 compound document) is not supported by "
                "this converter. Please save your document as .docx and try again."
            )
        if container == "unknown":
            raise RuntimeError(
                "The uploaded file is not a valid DOCX document. Please save it "
                "as a valid .docx file and try again."
            )

        engine = DocumentEngine()
        return await engine.convert(
            source_path=source_path,
            target_format=target_format,
            output_dir=output_dir,
            temp_dir=temp_dir,
        )