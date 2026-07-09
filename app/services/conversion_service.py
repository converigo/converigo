"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 2.0.0
"""

from pathlib import Path

from app.plugins.registry import registry


class ConversionError(Exception):
    pass


class ConversionService:

    async def convert_file(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:

        source_format = source_path.suffix.replace(".", "")

        plugin = registry.get_plugin(
            source_format,
            target_format,
        )

        output_path = await plugin.convert(
            source_path,
            target_format,
        )

        if not output_path.exists():

            raise ConversionError(
                "Converted file was not saved."
            )

        return output_path