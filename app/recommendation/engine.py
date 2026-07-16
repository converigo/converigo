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

        # Deduplicate by normalized target format while preserving ranking.
        deduped: list[object] = []
        seen_targets: set[str] = set()
        for opt in options:
            target = (opt.target or "").strip().lower()
            if not target:
                # keep items with no explicit target
                deduped.append(opt)
                continue
            if target in seen_targets:
                continue
            seen_targets.add(target)
            deduped.append(opt)

        if not deduped:
            return RecommendationResult(
                detected_type=source_format.upper(),
                best_choice=None,
                alternatives=[],
            )

        return RecommendationResult(
            detected_type=source_format.upper(),
            best_choice=deduped[0],
            alternatives=deduped[1:],
        )


recommendation_engine = RecommendationEngine()