from pathlib import Path

from app.pipeline.base_pipeline import PipelineContext, PipelineStep


class PrepareStep(PipelineStep):
    name = "prepare_step"

    async def run(self, context: PipelineContext) -> PipelineContext:
        context.temp_path = Path(str(context.source_path) + ".tmp")
        context.metadata["prepared"] = True
        return context
