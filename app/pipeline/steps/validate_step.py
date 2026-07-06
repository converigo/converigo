from app.pipeline.base_pipeline import PipelineContext, PipelineStep


class ValidateStep(PipelineStep):
    name = "validate_step"

    async def run(self, context: PipelineContext) -> PipelineContext:
        if not context.source_path.exists():
            context.errors.append("Source file does not exist.")
            return context

        if not context.target_format:
            context.errors.append("Target format is required.")
            return context

        context.validation_passed = True
        context.metadata["validated"] = True
        return context
