from pathlib import Path

from app.services.conversion_manager import ConversionManager


class ConversionError(Exception):
    pass


class ConversionService:
    async def convert_file(self, source_path: Path, target_format: str) -> Path:
        converter = ConversionManager().create_converter(source_path.suffix, target_format)
        output_path = await converter.convert(source_path, target_format)

        if not output_path.exists():
            raise ConversionError("Converted file was not saved to disk.")

        return output_path
