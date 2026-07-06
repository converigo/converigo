from __future__ import annotations

from typing import Dict, List, Optional, Type

from app.pipeline.base_pipeline import Pipeline, PipelineStep
from app.pipeline.steps.convert_step import ConvertStep
from app.pipeline.steps.cleanup_step import CleanupStep
from app.pipeline.steps.metadata_step import MetadataStep
from app.pipeline.steps.optimize_step import OptimizeStep
from app.pipeline.steps.prepare_step import PrepareStep
from app.pipeline.steps.save_step import SaveStep
from app.pipeline.steps.validate_step import ValidateStep


class PipelineRegistry:
    def __init__(self) -> None:
        self._pipelines: Dict[str, List[Type[PipelineStep]]] = {}

    def register_pipeline(self, name: str, step_classes: List[Type[PipelineStep]]) -> None:
        if name in self._pipelines:
            raise ValueError(f"Pipeline '{name}' is already registered.")
        if not step_classes:
            raise ValueError("Pipeline must include at least one step.")
        self._pipelines[name] = step_classes

    def create_pipeline(self, name: str) -> Pipeline:
        try:
            step_classes = self._pipelines[name]
        except KeyError as exc:
            raise ValueError(f"Pipeline '{name}' is not registered.") from exc
        return Pipeline([step_class() for step_class in step_classes])

    def list_pipelines(self) -> List[str]:
        return sorted(self._pipelines.keys())


class PipelineManager:
    def __init__(self, registry: PipelineRegistry) -> None:
        self.registry = registry

    def create_pipeline(self, name: str) -> Pipeline:
        return self.registry.create_pipeline(name)

    def available_pipelines(self) -> List[str]:
        return self.registry.list_pipelines()


PIPELINE_REGISTRY = PipelineRegistry()
PIPELINE_MANAGER = PipelineManager(PIPELINE_REGISTRY)


def register_pipeline(name: str, step_classes: List[Type[PipelineStep]]) -> None:
    PIPELINE_REGISTRY.register_pipeline(name, step_classes)


DEFAULT_PIPELINE = "conversion_pipeline"


def _register_default_pipeline() -> None:
    register_pipeline(
        DEFAULT_PIPELINE,
        [
            ValidateStep,
            MetadataStep,
            PrepareStep,
            ConvertStep,
            OptimizeStep,
            SaveStep,
            CleanupStep,
        ],
    )


_register_default_pipeline()
