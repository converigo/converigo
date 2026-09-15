"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

Recommendation Scorer
"""

from app.recommendation.models import RecommendationOption


class RecommendationScorer:
    """
    Calculate recommendation score.
    """

    def calculate(
        self,
        plugin,
    ) -> float:

        score = (

            plugin.priority * 0.40

            +

            plugin.quality * 0.25

            +

            plugin.compatibility * 0.25

            +

            plugin.estimated_saving * 0.10

        )

        return round(
            score,
            2,
        )


    def build_option(
        self,
        plugin,
        *,
        source: str | None = None,
        target: str | None = None,
    ) -> RecommendationOption:
        """Build one recommendation chip from the plugin that will run it.

        ``source``/``target`` are optional overrides. The caller passes the values
        the request actually carries, so a chip never describes a pair the plugin
        declared only incidentally (a plugin whose ``target_formats[0]`` is the
        legacy alias ``ppt`` delivers a ``.pptx``; the chip must say ``pptx``).
        """

        return RecommendationOption(

            source=plugin.source_formats[0] if source is None else source,

            target=plugin.target_formats[0] if target is None else target,

            title=plugin.name,

            description=plugin.description,

            category=plugin.category,

            goal=plugin.goal,

            priority=plugin.priority,

            quality=plugin.quality,

            compatibility=plugin.compatibility,

            estimated_saving=plugin.estimated_saving,

            score=self.calculate(plugin),

            badge=plugin.badge,

            icon=plugin.icon,

        )