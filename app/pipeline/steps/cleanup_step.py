from app.pipeline.base_pipeline import PipelineContext, PipelineStep


class CleanupStep(PipelineStep):
    name = "cleanup_step"

    async def run(self, context: PipelineContext) -> PipelineContext:
        context.metadata["cleanup"] = True
        return context
