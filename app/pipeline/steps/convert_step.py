from pathlib import Path

from app.pipeline.base_pipeline import PipelineContext, PipelineStep
from app.services.conversion_manager import ConversionManager


class ConvertStep(PipelineStep):
    name = "convert_step"

    def __init__(self) -> None:
        self.manager = ConversionManager()

    async def run(self, context: PipelineContext) -> PipelineContext:
        try:
            engine = self.manager.create_engine_for_format(context.source_path.suffix, metadata=context.metadata)
            output_path = await engine.convert(context.source_path, context.target_format)
            context.output_path = output_path
            context.metadata["converted"] = True
        except Exception as exc:
            context.errors.append(str(exc))
        return context
