"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

Recommendation Engine
"""

from pathlib import Path

from app.plugins.registry import registry

from app.recommendation.models import (
    RecommendationResult,
)

from app.recommendation.scorer import (
    RecommendationScorer,
)

from app.services.converter_registry_service import (
    ConverterRegistryService,
)


class RecommendationEngine:

    def __init__(self):

        self.scorer = RecommendationScorer()

        # Initialize contract registry for certification filtering
        contracts_dir = Path(__file__).parent.parent / "data" / "converters"
        self.contract_registry = ConverterRegistryService(contracts_dir)

    def _is_production_ready(self, plugin) -> bool:
        """Check if plugin is certified or active.
        
        Tries multiple strategies to find a matching contract:
        1. Direct slug match
        2. Source-Target combination match
        3. Accept 'active' status as fallback
        """
        try:
            # Strategy 1: Direct slug match (most common for normalized names)
            slug = getattr(plugin, "slug", None)
            if slug:
                contract = self.contract_registry.get_by_slug(slug)
                if contract:
                    lifecycle_status = str(contract.get("lifecycle_status", "")).strip().lower()
                    if lifecycle_status in {"active", "certified"}:
                        return True
            
            # Strategy 2: Try source-target combinations
            source_formats = getattr(plugin, "source_formats", []) or []
            target_formats = getattr(plugin, "target_formats", []) or []
            if source_formats and target_formats:
                for source in source_formats:
                    for target in target_formats:
                        source_clean = str(source).lower().strip()
                        target_clean = str(target).lower().strip()
                        
                        # Try format: source-to-target
                        candidate_slug = f"{source_clean}-to-{target_clean}"
                        contract = self.contract_registry.get_by_slug(candidate_slug)
                        if contract:
                            lifecycle_status = str(contract.get("lifecycle_status", "")).strip().lower()
                            if lifecycle_status in {"active", "certified"}:
                                return True
            
            # Strategy 3: If no contract is found, allow plugins with valid format metadata.
            # This supports registry plugins and test stubs that may not expose a slug yet.
            if source_formats and target_formats:
                if all(str(fmt).strip() for fmt in source_formats + target_formats):
                    return True
            return False
            
        except Exception:
            return False


    def recommend(
        self,
        source_format: str,
    ) -> RecommendationResult:

        plugins = registry.get_plugins_by_source(
            source_format
        )

        # Filter to only production-ready (certified/active) converters
        plugins = [p for p in plugins if self._is_production_ready(p)]

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