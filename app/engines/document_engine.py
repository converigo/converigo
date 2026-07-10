from pathlib import Path
import tempfile

from PIL import Image

from app.engines.base_engine import BaseEngine


class DocumentEngine(BaseEngine):
    ENGINE_NAME = "document"

    SUPPORTED_FORMATS = [
        "pdf",
        "docx",
        "txt",
        "md",
    ]

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:
        target = target_format.lower().lstrip(".")

        if target == "pdf":
            if source_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
                raise ValueError(
                    f"Unsupported source format for document engine: {source_path.suffix}"
                )

            output_dir = Path("outputs") / "document"
            output_dir.mkdir(parents=True, exist_ok=True)

            output_path = output_dir / f"{source_path.stem}.pdf"

            with Image.open(source_path) as image:
                if image.mode in ("RGBA", "LA", "P"):
                    image = image.convert("RGB")

                image.save(output_path, format="PDF", resolution=100.0)

            return output_path

        if target in {"jpg", "jpeg"}:
            if source_path.suffix.lower() != ".pdf":
                raise ValueError(
                    f"Unsupported source format for document engine: {source_path.suffix}"
                )

            output_dir = Path("outputs") / "document"
            output_dir.mkdir(parents=True, exist_ok=True)

            try:
                import fitz
            except ImportError as exc:
                raise RuntimeError("PyMuPDF is required for PDF to JPG conversion.") from exc

            with tempfile.TemporaryDirectory(prefix="pdf2jpg_", dir=str(output_dir)) as temp_dir:
                doc = fitz.open(str(source_path))
                try:
                    if doc.page_count == 0:
                        raise RuntimeError("No pages were extracted from the PDF.")

                    base_name = source_path.stem
                    output_paths = []

                    for index in range(doc.page_count):
                        page = doc.load_page(index)
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                        page_path = output_dir / f"{base_name}_page_{index + 1:02d}.jpg"
                        pix.pil_save(page_path, format="JPEG", quality=95)
                        output_paths.append(page_path)

                    if len(output_paths) == 1:
                        return output_paths[0]

                    return output_paths[0]
                finally:
                    doc.close()

        raise ValueError(
            f"Unsupported target format for document engine: {target}"
        )