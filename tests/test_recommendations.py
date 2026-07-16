from __future__ import annotations

from typing import Any

import pytest

from app.services.recommendation_service import RecommendationService


class DummyConverterDataService:
    def __init__(self, converters: list[dict[str, Any]]):
        self._converters = converters

    def list_public_converters(self):
        return list(self._converters)

    def load_converter_by_slug(self, slug: str) -> dict[str, Any]:
        for c in self._converters:
            if str(c.get("slug", "")).lower() == str(slug or "").lower():
                return c
        raise FileNotFoundError


def test_recommendation_filters_unsupported(monkeypatch):
    # Two converters, one supported (a-to-b), one unsupported (x-to-y)
    converters = [
        {"slug": "a-to-b", "source": "a", "target": "b", "title": "A to B", "category": "general"},
        {"slug": "x-to-y", "source": "x", "target": "y", "title": "X to Y", "category": "general"},
    ]

    service = RecommendationService(DummyConverterDataService(converters))

    # plugin registry: only a->b exists
    def fake_get_plugin(src, tgt):
        if src == "a" and tgt == "b":
            return object()
        raise ValueError("not supported")

    monkeypatch.setattr("app.plugins.registry.registry.get_plugin", fake_get_plugin)

    recs = service.recommend_for_slug("a-to-b", limit=4)

    # Ensure unsupported converter not present in any group
    all_slugs = set()
    for group in recs.values():
        for item in group:
            all_slugs.add(item.get("slug"))

    assert "x-to-y" not in all_slugs
    assert "a-to-b" not in all_slugs  # shouldn't recommend itself


def test_recommendation_dedupes_target_formats(monkeypatch):
    # Two converters with same target 'pdf' but different slugs and ranks
    converters = [
        {"slug": "one-to-pdf", "source": "one", "target": "pdf", "title": "One PDF", "category": "general", "featured": True},
        {"slug": "two-to-pdf", "source": "two", "target": "pdf", "title": "Two PDF", "category": "general", "featured": False},
        {"slug": "other", "source": "other", "target": "txt", "title": "Other", "category": "general"},
    ]

    service = RecommendationService(DummyConverterDataService(converters))

    # plugin registry: all are supported
    def fake_get_plugin(src, tgt):
        return object()

    monkeypatch.setattr("app.plugins.registry.registry.get_plugin", fake_get_plugin)

    recs = service.recommend_for_slug("other", limit=10)

    # Count unique targets across all recommendation groups
    seen_targets = set()
    duplicates = []
    for group in recs.values():
        for item in group:
            tgt = str(item.get("target", "")).strip().lower()
            if tgt in seen_targets:
                duplicates.append(tgt)
            seen_targets.add(tgt)

    assert "pdf" in seen_targets
    assert duplicates == []
