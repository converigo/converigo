"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

JPG -> PDF Plugin
"""

from pathlib import Path

from app.plugins.base import ConverterPlugin


class JPGToPDFPlugin(ConverterPlugin):
    slug = "jpg-to-pdf"
    name = "JPG to PDF"
    description = "Convert JPG images into PDF documents while preserving image quality."
    category = "document"
    engine = "document"
    icon = "📄"

    source_formats = ["jpg", "jpeg"]
    target_formats = ["pdf"]

    goal = "document"
    use_case = "Best for turning image files into portable PDF documents."
    priority = 80
    quality = 95
    compatibility = 90
    estimated_saving = 15
    badge = "Portable PDF"
    seo_title = "JPG to PDF Converter | Converigo"
    seo_description = "Convert JPG images into PDF documents with high quality."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("JPGToPDFPlugin only supports JPG -> PDF.")

        # Minimal, self-contained conversion: render the input image onto a single PDF page.
        output_dir = Path("outputs") / "document"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Use ReportLab if available; otherwise raise a clear error.
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
        except ImportError as exc:
            raise RuntimeError("reportlab is required for JPG to PDF conversion.") from exc

        try:
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError("Pillow is required for JPG to PDF conversion.") from exc

        output_path = output_dir / f"{source_path.stem}.pdf"

        img = Image.open(source_path)
        # Convert to RGB for consistent PDF embedding.
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        # Create a temporary PNG for ReportLab to embed.
        import tempfile

        with tempfile.TemporaryDirectory(prefix="jpg2pdf_") as temp_dir:
            tmp_png = Path(temp_dir) / "image.png"
            img.save(str(tmp_png), format="PNG")

            page_w, page_h = letter
            c = canvas.Canvas(str(output_path), pagesize=letter)
            # Draw image to fit page while preserving aspect ratio.
            img_w, img_h = img.size
            scale = min(page_w / img_w, page_h / img_h)
            draw_w = img_w * scale
            draw_h = img_h * scale
            x = (page_w - draw_w) / 2
            y = (page_h - draw_h) / 2
            c.drawImage(str(tmp_png), x, y, width=draw_w, height=draw_h)
            c.showPage()
            c.save()

        if not output_path.exists():
            raise RuntimeError("JPG to PDF conversion did not produce output.")

        return output_path

