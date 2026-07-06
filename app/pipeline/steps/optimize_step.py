from app.pipeline.base_pipeline import PipelineContext, PipelineStep


class OptimizeStep(PipelineStep):
    name = "optimize_step"

    async def run(self, context: PipelineContext) -> PipelineContext:
        context.metadata["optimized"] = True
        return context
