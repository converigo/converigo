"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

Recommendation Engine
"""

from app.plugins.registry import registry

from app.recommendation.models import (
    RecommendationResult,
)

from app.recommendation.scorer import (
    RecommendationScorer,
)


class RecommendationEngine:

    def __init__(self):

        self.scorer = RecommendationScorer()


    def recommend(
        self,
        source_format: str,
    ) -> RecommendationResult:

        plugins = registry.get_plugins_by_source(
            source_format
        )

        if not plugins:

            return RecommendationResult(

                detected_type=source_format.upper(),

                best_choice=None,

                alternatives=[],

            )


        options = [

            self.scorer.build_option(plugin)

            for plugin in plugins

        ]


        options.sort(

            key=lambda item: item.score,

            reverse=True,

        )


        return RecommendationResult(

            detected_type=source_format.upper(),

            best_choice=options[0],

            alternatives=options[1:],

        )


recommendation_engine = RecommendationEngine()