"""
Project : Convertin
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
    ) -> RecommendationOption:

        return RecommendationOption(

            source=plugin.source_formats[0],

            target=plugin.target_formats[0],

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