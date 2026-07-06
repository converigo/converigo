from app.pipeline.base_pipeline import PipelineContext, PipelineStep


class MetadataStep(PipelineStep):
    name = "metadata_step"

    async def run(self, context: PipelineContext) -> PipelineContext:
        context.metadata.setdefault("requested_format", context.target_format)
        context.metadata.setdefault("pipeline_name", "conversion_pipeline")
        return context
