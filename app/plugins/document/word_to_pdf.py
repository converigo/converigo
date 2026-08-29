"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.1

DOCX -> PDF Plugin

Converts DOCX documents into PDF files. Source detection is content-based
(magic bytes) rather than extension-based:

- ZIP/OOXML magic (PK) -> treated as DOCX and real text is extracted,
  which also covers `.doc` files that are actually DOCX renamed.
- OLE2/CFB magic (d0cf11e0a1b11ae1) -> legacy binary `.doc`; not supported,
  raises an explicit error instead of emitting a content-less PDF.
- Anything else -> raises an explicit error (no silent fake pass).
"""

from pathlib import Path

from app.plugins.base import ConverterPlugin


class WordToPDFPlugin(ConverterPlugin):
    slug = "word-to-pdf"
    name = "Word to PDF"
    description = "Convert DOCX documents into PDF files."
    category = "document"
    engine = "document"
    icon = "📄"

    source_formats = ["docx", "doc"]
    target_formats = ["pdf"]

    goal = "document"
    use_case = "Best for turning Word documents into portable PDF files."
    priority = 85
    quality = 90
    compatibility = 85
    estimated_saving = 15
    badge = "Portable PDF"
    seo_title = "Word to PDF Converter | Converigo"
    seo_description = "Convert DOCX documents into PDF files quickly and easily."

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

    @staticmethod
    def _extract_docx_text(source_path: Path) -> str:
        from docx import Document as DocxDocument

        doc = DocxDocument(str(source_path))
        return "\n".join([p.text for p in doc.paragraphs if p.text])

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("WordToPDFPlugin only supports DOCX/DOC -> PDF.")

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

        try:
            extracted_text = self._extract_docx_text(source_path)
        except Exception as exc:
            raise RuntimeError(
                "The DOCX document could not be parsed. Please save it as a valid "
                ".docx file and try again."
            ) from exc

        from app.core.settings import settings

        working_dir = temp_dir or output_dir or (settings.OUTPUT_DIR / "document")
        working_dir.mkdir(parents=True, exist_ok=True)

        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
        except ImportError as exc:
            raise RuntimeError("reportlab is required for DOC/DOCX to PDF conversion.") from exc

        output_path = working_dir / f"{source_path.stem}.pdf"

        _ = temp_dir
        c = canvas.Canvas(str(output_path), pagesize=letter)
        text_obj = c.beginText(40, 750)
        text_obj.setFont("Helvetica", 11)
        if extracted_text:
            for line in extracted_text.splitlines()[:40]:
                text_obj.textLine(line[:95])

        c.drawText(text_obj)
        c.showPage()
        c.save()

        if not output_path.exists():
            raise RuntimeError("DOC/DOCX to PDF conversion did not produce output.")

        return output_path

