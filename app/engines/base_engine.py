from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional


class BaseEngine(ABC):
    ENGINE_NAME = "base"
    SUPPORTED_FORMATS: List[str] = []

    def __init__(
        self,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.metadata = metadata or {}

    @classmethod
    def supports_format(
        cls,
        file_format: str,
    ) -> bool:
        normalized = file_format.lower().lstrip(".")
        return normalized in cls.SUPPORTED_FORMATS

    @abstractmethod
    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        """
        Convert a source file into the requested format.

        In the staged transition, output_dir/temp_dir are optional so existing
        callers remain compatible while the migration proceeds. These will
        become required after the refactor is complete.
        """
        raise NotImplementedError

    def describe(self) -> str:
        return (
            f"{self.ENGINE_NAME.title()} engine "
            f"supporting: {', '.join(self.SUPPORTED_FORMATS)}"
        )