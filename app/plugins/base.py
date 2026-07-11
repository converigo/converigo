"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

Plugin Base Class

Converigo Core Architecture
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class ConverterPlugin(ABC):
    """
    Base class for every converter plugin.

    Every plugin must inherit this class.
    """

    # --------------------------------------------------
    # Identity
    # --------------------------------------------------

    slug = ""

    name = ""

    description = ""

    category = ""

    engine = ""

    # --------------------------------------------------
    # Formats
    # --------------------------------------------------

    source_formats = []

    target_formats = []

    # --------------------------------------------------
    # Recommendation Metadata
    # --------------------------------------------------

    goal = ""

    use_case = ""

    priority = 50

    quality = 50

    compatibility = 50

    estimated_saving = 0

    badge = ""

    icon = "📄"

    color = "blue"

    # --------------------------------------------------
    # SEO
    # --------------------------------------------------

    seo_title = ""

    seo_description = ""

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def supports(
        self,
        source_format: str,
        target_format: str,
    ) -> bool:

        source = source_format.lower().replace(".", "")
        target = target_format.lower().replace(".", "")

        return (
            source in self.source_formats
            and
            target in self.target_formats
        )

    def metadata(self) -> dict:

        return {

            "slug": self.slug,

            "name": self.name,

            "description": self.description,

            "category": self.category,

            "engine": self.engine,

            "source_formats": self.source_formats,

            "target_formats": self.target_formats,

            "goal": self.goal,

            "use_case": self.use_case,

            "priority": self.priority,

            "quality": self.quality,

            "compatibility": self.compatibility,

            "estimated_saving": self.estimated_saving,

            "badge": self.badge,

            "icon": self.icon,

            "color": self.color,

            "seo_title": self.seo_title,

            "seo_description": self.seo_description,

        }

    @abstractmethod
    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:
        """
        Convert file.

        Must return converted file path.
        """
        raise NotImplementedError