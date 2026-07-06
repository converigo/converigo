from app.pipeline.base_pipeline import PipelineContext, PipelineStep


class SaveStep(PipelineStep):
    name = "save_step"

    async def run(self, context: PipelineContext) -> PipelineContext:
        if context.output_path is None:
            context.errors.append("No output path available to save.")
            return context

        if not context.output_path.exists():
            context.errors.append("Converted output file was not created.")
            return context

        context.metadata["saved"] = True
        return context
