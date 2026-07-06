from pathlib import Path

from app.pipeline.base_pipeline import PipelineContext
from app.pipeline.pipeline_manager import PIPELINE_MANAGER


class ConversionError(Exception):
    pass


class ConversionService:
    async def convert_file(self, source_path: Path, target_format: str) -> Path:
        if source_path.suffix.lower() != ".mp4":
            raise ValueError("Only MP4 source files are supported.")

        normalized_target = target_format.lower()
        if normalized_target != "mp3":
            raise ValueError("Only MP3 target format is supported.")

        pipeline = PIPELINE_MANAGER.create_pipeline("conversion_pipeline")
        context = PipelineContext(source_path=source_path, target_format=normalized_target)
        result = await pipeline.run(context)

        if result.errors:
            raise ConversionError("; ".join(result.errors))

        if result.output_path is None:
            raise ConversionError("Conversion pipeline did not produce an output file.")

        if not result.output_path.exists():
            raise ConversionError("Converted file was not saved to disk.")

        return result.output_path
