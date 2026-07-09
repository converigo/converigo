from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable


class ConverterPlugin(ABC):
    """
    Base class for every converter plugin.

    A plugin describes WHAT conversion is supported.
    The Engine describes HOW the conversion is executed.
    """

    # ---------- Identity ----------
    slug: str = ""
    name: str = ""
    description: str = ""

    # ---------- UI ----------
    icon: str = "📄"
    popular: bool = False
    featured: bool = False

    # ---------- Classification ----------
    category: str = "general"
    engine: str = ""

    # ---------- Supported Formats ----------
    source_formats: Iterable[str] = ()
    target_formats: Iterable[str] = ()

    @abstractmethod
    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:
        """
        Execute conversion.

        Returns
        -------
        Path
            Output file.
        """
        raise NotImplementedError

    @classmethod
    def supports(
        cls,
        source_format: str,
        target_format: str,
    ) -> bool:

        source = source_format.lower().lstrip(".")
        target = target_format.lower().lstrip(".")

        return (
            source in {
                fmt.lower().lstrip(".")
                for fmt in cls.source_formats
            }
            and target in {
                fmt.lower().lstrip(".")
                for fmt in cls.target_formats
            }
        )