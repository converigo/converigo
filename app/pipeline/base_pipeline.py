from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PipelineContext:
    source_path: Path
    target_format: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    temp_path: Optional[Path] = None
    output_path: Optional[Path] = None
    validation_passed: bool = False
    errors: List[str] = field(default_factory=list)


class PipelineStep(ABC):
    name = "base_step"

    async def execute(self, context: PipelineContext) -> PipelineContext:
        return await self.run(context)

    @abstractmethod
    async def run(self, context: PipelineContext) -> PipelineContext:
        raise NotImplementedError


class Pipeline:
    def __init__(self, steps: List[PipelineStep]) -> None:
        if not steps:
            raise ValueError("A pipeline must contain at least one step.")
        self.steps = steps

    async def run(self, context: PipelineContext) -> PipelineContext:
        for step in self.steps:
            context = await step.execute(context)
            if context.errors:
                break
        return context
