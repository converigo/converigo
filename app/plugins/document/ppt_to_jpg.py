"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

PPTX -> JPG Plugin

Converts PowerPoint presentations into JPG images (first slide only).
"""

from pathlib import Path

from app.engines.document_engine import DocumentEngine
from app.plugins.base import ConverterPlugin


class PPTToJPGPlugin(ConverterPlugin):
    slug = "ppt-to-jpg"
    name = "PPT to JPG"
    description = "Convert PowerPoint presentations into JPG images."
    category = "document"
    engine = "document"
    icon = "🖼️"

    source_formats = ["pptx", "ppt", "powerpoint"]
    target_formats = ["jpg", "jpeg"]

    goal = "document"
    use_case = "Best for turning PowerPoint slides into image files for previews and thumbnails."
    priority = 75
    quality = 85
    compatibility = 80
    estimated_saving = 8
    badge = "Office Conversion"
    seo_title = "PPT to JPG Converter | Converigo"
    seo_description = "Convert PowerPoint presentations into JPG images quickly and easily."

    # PPTX (OOXML) files are ZIP archives and start with the "PK" signature.
    _PPTX_PK_MAGIC = b"PK\x03\x04"
    # Legacy .ppt files are OLE2 / Compound File Binary containers.
    _PPT_OLE2_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"

    @classmethod
    def _detect_container(cls, source_path: Path) -> str:
        """Return the container type detected from file content.

        Returns "pptx" for ZIP/OOXML files, "ppt" for OLE2/CFB files, or
        "unknown" for anything else (empty file, plain text, ...).
        """
        try:
            with source_path.open("rb") as fh:
                header = fh.read(8)
        except OSError as exc:
            raise RuntimeError(f"Could not read the source file: {exc}") from exc

        if header.startswith(cls._PPTX_PK_MAGIC):
            return "pptx"
        if header.startswith(cls._PPT_OLE2_MAGIC):
            return "ppt"
        return "unknown"

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("PPTToJPGPlugin only supports PPTX -> JPG.")

        container = self._detect_container(source_path)

        if container == "ppt":
            raise RuntimeError(
                "Legacy .ppt format (OLE2 compound document) is not supported by "
                "this converter. Please save your presentation as .pptx and try again."
            )
        if container == "unknown":
            raise RuntimeError(
                "The uploaded file is not a valid PPTX presentation. Please save it "
                "as a valid .pptx file and try again."
            )

        engine = DocumentEngine()
        return await engine.convert(
            source_path=source_path,
            target_format=target_format,
            output_dir=output_dir,
            temp_dir=temp_dir,
        )