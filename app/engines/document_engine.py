from pathlib import Path

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

        if target != "pdf":
            raise ValueError(
                f"Unsupported target format for document engine: {target}"
            )

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