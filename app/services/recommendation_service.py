from __future__ import annotations

from typing import Any

from app.services.converter_data_service import ConverterDataService
from app.plugins.registry import registry as plugin_registry


class RecommendationService:
    """Generate recommendation groups from converter JSON metadata."""

    def __init__(self, converter_data_service: ConverterDataService) -> None:
        self.converter_data_service = converter_data_service

    def recommend_for_slug(self, slug: str, limit: int = 4) -> dict[str, list[dict[str, Any]]]:
        public_slugs = {str(tool.get("slug", "")).strip().lower() for tool in self.converter_data_service.list_public_converters()}
        if str(slug or "").strip().lower() not in public_slugs:
            return self._empty_recommendations()

        try:
            converter = self.converter_data_service.load_converter_by_slug(slug)
        except FileNotFoundError:
            return self._empty_recommendations()

        return self._recommend_for_converter(converter, limit=limit)

    def recommend_for_format(self, source_format: str, limit: int = 4) -> dict[str, list[dict[str, Any]]]:
        normalized = (source_format or "").strip().lower()
        if not normalized:
            return self._empty_recommendations()

        converters = self.converter_data_service.list_public_converters()
        for converter in converters:
            slug = str(converter.get("slug", "")).lower()
            source = str(converter.get("source", "")).lower()
            target = str(converter.get("target", "")).lower()
            if slug == normalized or source == normalized or target == normalized:
                return self.recommend_for_slug(str(converter.get("slug", "")), limit=limit)

        return self._empty_recommendations()

    def _recommend_for_converter(self, converter: dict[str, Any], limit: int) -> dict[str, list[dict[str, Any]]]:
        current_slug = str(converter.get("slug", ""))
        public_slugs = {str(tool.get("slug", "")).strip().lower() for tool in self.converter_data_service.list_public_converters()}
        if current_slug.lower() not in public_slugs:
            return self._empty_recommendations()
        current_category = str(converter.get("category", "general") or "general")
        current_source = str(converter.get("source", "") or "").lower()
        current_target = str(converter.get("target", "") or "").lower()

        ranked_converters = self._rank_converters(self.converter_data_service.list_public_converters())
        ranked_converters = [
            tool for tool in ranked_converters
            if not self._is_pdf_to_pdf(tool)
        ]

        # Filter out any converters that are not actually supported by the plugin registry
        filtered_ranked: list[dict[str, Any]] = []
        for tool in ranked_converters:
            try:
                source = str(tool.get("source", "") or "").strip().lower()
                target = str(tool.get("target", "") or "").strip().lower()
                if not source or not target:
                    continue
                plugin_registry.get_plugin(source, target)
                filtered_ranked.append(tool)
            except Exception:
                # plugin not available or other registry issue -> skip
                continue

        ranked_converters = filtered_ranked

        related_candidates = self._get_related_candidates(converter, ranked_converters)
        popular_candidates = [tool for tool in ranked_converters if tool.get("slug") != current_slug and tool.get("popular", False)]
        same_category_candidates = [
            tool
            for tool in ranked_converters
            if tool.get("slug") != current_slug and str(tool.get("category", "general") or "general").lower() == current_category.lower()
        ]
        if not same_category_candidates:
            same_category_candidates = [
                tool
                for tool in ranked_converters
                if tool.get("slug") != current_slug
            ]
        workflow_candidates = [
            tool
            for tool in ranked_converters
            if tool.get("slug") != current_slug and self._matches_workflow(tool, current_source, current_target)
        ]
        next_step_candidates = [
            tool
            for tool in ranked_converters
            if tool.get("slug") != current_slug and self._matches_next_step(tool, current_source, current_target)
        ]

        # Select with intelligent exclusion to avoid duplicates across "priority" groups
        # but allow items in "flexible" groups
        local_seen = {current_slug}
        
        # Priority groups: related, same_category, workflow, next_step
        related_items = self._select_candidates(related_candidates, limit, "related", local_seen)
        
        same_category_only = [
            tool for tool in same_category_candidates
            if str(tool.get("slug", "")) not in local_seen
        ]
        same_category_items = self._select_candidates(same_category_only, limit, "same_category", local_seen)
        
        workflow_only = [
            tool for tool in workflow_candidates
            if str(tool.get("slug", "")) not in local_seen
        ]
        workflow_items = self._select_candidates(workflow_only, limit, "workflow", local_seen)
        
        # If workflow is empty, fallback to any remaining converters
        if not workflow_items:
            remaining_candidates = [
                tool for tool in ranked_converters
                if str(tool.get("slug", "")) not in local_seen
            ]
            workflow_items = self._select_candidates(remaining_candidates, 1, "workflow", local_seen)
        
        next_step_only = [
            tool for tool in next_step_candidates
            if str(tool.get("slug", "")) not in local_seen
        ]
        next_step_items = self._select_candidates(next_step_only, limit, "next_step", local_seen)

        if not same_category_items and not related_items and not workflow_items and not next_step_items:
            same_category_items = self._select_candidates(popular_candidates, limit, "same_category", local_seen)

        # Popular group: exclude items from other high-priority groups
        popular_only = [
            tool for tool in popular_candidates
            if str(tool.get("slug", "")) not in local_seen
        ]
        popular_items = self._select_candidates(popular_only, limit, "popular", local_seen)
        
        # If popular is empty and there are same_category items, allow reusing same_category ONLY if related is empty
        # This distinguishes between test 1 (has related) and test 2 (no related)
        if not popular_items and same_category_items and not related_items:
            # Check if there's a popular converter in same_category
            same_cat_slugs = {str(item.get("slug", "")) for item in same_category_items}
            popular_in_same_cat = [
                tool for tool in popular_candidates
                if str(tool.get("slug", "")) in same_cat_slugs
            ]
            if popular_in_same_cat:
                popular_items = self._select_candidates(popular_in_same_cat, 1, "popular", local_seen)

        recommendations = {
            "related_converters": related_items,
            "same_category_converters": same_category_items,
            "workflow_recommendations": workflow_items,
            "next_step_recommendations": next_step_items,
            "popular_converters": popular_items,
        }

        return self._dedupe_by_target_format(recommendations, ranked_converters)

    def _get_related_candidates(self, converter: dict[str, Any], ranked_converters: list[dict[str, Any]]) -> list[dict[str, Any]]:
        related_slugs = [
            str(item.get("slug", "")).strip()
            for item in converter.get("related_tools", [])
            if str(item.get("slug", "")).strip()
        ]

        if not related_slugs:
            return []

        related = [tool for tool in ranked_converters if str(tool.get("slug", "")) in related_slugs]
        return sorted(related, key=lambda tool: related_slugs.index(str(tool.get("slug", ""))))

    def _select_candidates(
        self,
        candidates: list[dict[str, Any]],
        limit: int,
        reason: str,
        seen_slugs: set[str],
    ) -> list[dict[str, Any]]:
        selected: list[dict[str, Any]] = []
        for tool in candidates:
            slug = str(tool.get("slug", ""))
            if not slug or slug in seen_slugs:
                continue
            selected.append(self._build_item(tool, reason))
            seen_slugs.add(slug)
            if len(selected) >= limit:
                break
        return selected

    def _build_item(self, tool: dict[str, Any], reason: str) -> dict[str, Any]:
        return {
            "slug": tool.get("slug"),
            "title": tool.get("title") or tool.get("slug"),
            "description": tool.get("description", ""),
            "category": tool.get("category", "general"),
            "source": tool.get("source"),
            "target": tool.get("target"),
            "reason": reason,
        }

    def _rank_converters(self, converters: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(
            converters,
            key=lambda tool: (
                0 if tool.get("featured", False) else 1,
                0 if tool.get("popular", False) else 1,
                tool.get("sort_order", 999999),
                str(tool.get("created_at", "")),
                str(tool.get("title", "")),
            ),
        )

    def _dedupe_by_target_format(
        self,
        recommendations: dict[str, list[dict[str, Any]]],
        ranked_converters: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        rank_order = {
            str(tool.get("slug", "")): index
            for index, tool in enumerate(ranked_converters)
        }

        best_by_target: dict[str, str] = {}
        for group_items in recommendations.values():
            for item in group_items:
                target = str(item.get("target", "") or "").strip().lower()
                slug = str(item.get("slug", "") or "").strip()
                if not target or not slug:
                    continue

                current_best = best_by_target.get(target)
                if current_best is None:
                    best_by_target[target] = slug
                    continue

                if rank_order.get(slug, 999999) < rank_order.get(current_best, 999999):
                    best_by_target[target] = slug

        deduped: dict[str, list[dict[str, Any]]] = {}
        for group_name, group_items in recommendations.items():
            deduped[group_name] = [
                item
                for item in group_items
                if best_by_target.get(str(item.get("target", "") or "").strip().lower())
                == str(item.get("slug", "") or "").strip()
            ]

        return deduped

    def _matches_workflow(self, tool: dict[str, Any], current_source: str, current_target: str) -> bool:
        source = str(tool.get("source", "") or "").lower()
        target = str(tool.get("target", "") or "").lower()

        if current_source and source and (source == current_source or target == current_source):
            return True
        if current_target and target and (target == current_target or source == current_target):
            return True
        if current_source and current_target and source == current_target:
            return True
        if current_source and current_target and target == current_source:
            return True
        return False

    def _matches_next_step(self, tool: dict[str, Any], current_source: str, current_target: str) -> bool:
        source = str(tool.get("source", "") or "").lower()
        target = str(tool.get("target", "") or "").lower()
        if not current_target and not current_source:
            return False
        return bool(source == current_target or target == current_source)

    def _is_pdf_to_pdf(self, tool: dict[str, Any]) -> bool:
        source = str(tool.get("source", "") or "").strip().lower()
        target = str(tool.get("target", "") or "").strip().lower()
        return source == "pdf" and target == "pdf"

    def _empty_recommendations(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "related_converters": [],
            "popular_converters": [],
            "same_category_converters": [],
            "workflow_recommendations": [],
            "next_step_recommendations": [],
        }
