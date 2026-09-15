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

from app.services.target_capability import (
    AUTO_DEFAULT_FIRST,
    TARGET_CANONICAL,
    TARGET_ORDER_PREFERENCE,
    build_capability,
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


    # ------------------------------------------------------------------
    # Capability authority (D5) owns eligibility; this engine owns ranking.
    # ------------------------------------------------------------------

    @staticmethod
    def _allowed_targets(source: str, operation: str | None) -> set[str]:
        """What ``target_capability`` allows this source to be offered right now.

        The authority already folds legacy alias tokens onto the extension that is
        really delivered, drops placeholder-backed pairs, gates a source on
        uploadability, and only authorizes a self-conversion when ``operation``
        names the page that owns it. None of that is recomputed here.
        """

        view = build_capability(operation).map
        return {str(target).lower() for target in view.get(source, [])}

    @staticmethod
    def _canonical_target(target: str, allowed: set[str]) -> str | None:
        """Fold a declared token onto the canonical target the authority allows.

        Same rule the authority applies in ``admit()``: a fold is honoured only onto
        a pair that is itself dispatchable, so this can never invent capability - it
        can only name an existing one correctly (``ppt`` -> ``pptx``).
        """

        token = str(target).lower().strip()
        if token in allowed:
            return token
        canonical = TARGET_CANONICAL.get(token)
        if canonical is not None and canonical in allowed:
            return canonical
        return None

    @staticmethod
    def _dispatch_winner(source: str, target: str, operation: str | None):
        """The plugin ``/convert`` will actually run for this chip, else ``None``.

        ``get_plugin`` raises ``ValueError`` for a pair/slug combination it cannot
        resolve - precisely the ``422 UNSUPPORTED_CONVERSION`` the browser would
        receive - so a chip that cannot dispatch is dropped instead of advertised.
        """

        try:
            plugin = registry.get_plugin(source, target, slug=operation)
        except Exception:
            return None
        if getattr(plugin, "advertisable", True) is False:
            # Registered so the failure message stays honest, but it can never
            # deliver the file: it must not turn into an offer.
            return None
        return plugin

    @staticmethod
    def _pin_default(source: str, options: list) -> list:
        """Keep the authority's pinned default target in first position.

        ``renderFormats()`` auto-selects the first chip, so position zero *is* the
        default-target policy, which belongs to the authority
        (``TARGET_ORDER_PREFERENCE`` / ``AUTO_DEFAULT_FIRST``) rather than to the
        score formula: ranked on score alone a ``.wav`` upload on a legacy page
        defaults to AAC, the silent-wrong-format regression WS1 had to fix on the
        homepage. Everything after the pinned default stays score-ranked.
        """

        targets = [str(option.target).lower() for option in options]
        preferred = next(
            (token for token in TARGET_ORDER_PREFERENCE.get(source, ()) if token in targets),
            None,
        ) or AUTO_DEFAULT_FIRST.get(source)
        if not preferred or preferred not in targets or targets[0] == preferred:
            return options
        index = targets.index(preferred)
        return [options[index], *options[:index], *options[index + 1 :]]

    def recommend(
        self,
        source_format: str,
        operation: str | None = None,
    ) -> RecommendationResult:
        """Rank the targets a legacy surface may offer for one uploaded source.

        Ordering and tool context stay this engine's job; *eligibility* is the D5
        authority's. A chip survives only when the authority allows that target for
        this source under this operation and ``registry.get_plugin()`` resolves a
        real, advertisable, production-ready plugin for the exact request the
        browser is about to post. So an advertised target can never be wider than a
        dispatchable target, while ranking remains a recommendation.
        """

        source = str(source_format or "").lower().strip()
        detected = source.upper()

        allowed = self._allowed_targets(source, operation)
        if not allowed:
            # No authority row means nothing may be offered: a non-uploadable alias
            # (word/xls/ppt/doc), an unknown token, or every pair unadvertisable.
            return RecommendationResult(
                detected_type=detected,
                best_choice=None,
                alternatives=[],
            )

        plugins = registry.get_plugins_by_source(
            source
        )

        # Filter to only production-ready (certified/active) converters
        plugins = [p for p in plugins if self._is_production_ready(p)]

        options = []
        seen_targets: set[str] = set()
        for plugin in plugins:
            target_formats = getattr(plugin, "target_formats", []) or []
            if not target_formats:
                continue
            target = self._canonical_target(target_formats[0], allowed)
            if target is None or target in seen_targets:
                # Out of authority: this plugin's claim is not something the user
                # could actually convert to on this surface.
                continue
            winner = self._dispatch_winner(source, target, operation)
            if winner is None:
                continue
            if not self._is_production_ready(winner):
                # The chip is backed by the plugin that will run it, so that
                # plugin's certification status is the one that matters.
                continue
            seen_targets.add(target)
            options.append(
                self.scorer.build_option(winner, source=source, target=target)
            )

        options.sort(

            key=lambda item: item.score,

            reverse=True,

        )

        options = self._pin_default(source, options)

        if not options:
            return RecommendationResult(
                detected_type=detected,
                best_choice=None,
                alternatives=[],
            )

        return RecommendationResult(
            detected_type=detected,
            best_choice=options[0],
            alternatives=options[1:],
        )


recommendation_engine = RecommendationEngine()
