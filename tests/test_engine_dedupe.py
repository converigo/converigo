from __future__ import annotations

from app.recommendation.engine import RecommendationEngine
from types import SimpleNamespace


class DummyPlugin:
    def __init__(self, source, target, name, priority=1, quality=1, compatibility=1):
        self.source_formats = [source]
        self.target_formats = [target]
        self.name = name
        self.description = ""
        self.category = "general"
        self.goal = ""
        self.priority = priority
        self.quality = quality
        self.compatibility = compatibility
        self.estimated_saving = 0
        self.badge = None
        self.icon = None

    def metadata(self):
        return {
            "slug": f"{self.source_formats[0]}-to-{self.target_formats[0]}",
            "source": self.source_formats[0],
            "target": self.target_formats[0],
            "name": self.name,
        }


def test_engine_dedupes_same_target(monkeypatch):
    engine = RecommendationEngine()

    # Create plugins that produce the same 'pdf' target
    p1 = DummyPlugin('pdf', 'pdf', 'PDF Compress', priority=10)
    p2 = DummyPlugin('pdf', 'pdf', 'PDF Split', priority=5)
    p3 = DummyPlugin('pdf', 'docx', 'PDF to DOCX', priority=8)

    # Monkeypatch registry.get_plugins_by_source to return plugin-like objects
    class FakePluginObj(SimpleNamespace):
        pass

    def to_plugin_obj(p):
        return FakePluginObj(
            source_formats=p.source_formats,
            target_formats=p.target_formats,
            name=p.name,
            description=p.description,
            category=p.category,
            goal=p.goal,
            priority=p.priority,
            quality=p.quality,
            compatibility=p.compatibility,
            estimated_saving=p.estimated_saving,
            badge=p.badge,
            icon=p.icon,
        )

    monkeypatch.setattr('app.plugins.registry.registry.get_plugins_by_source', lambda src: [to_plugin_obj(p1), to_plugin_obj(p2), to_plugin_obj(p3)])

    result = engine.recommend('pdf')

    # alternatives should not contain duplicate 'pdf' targets
    targets = [opt.target.lower() for opt in [result.best_choice] + list(result.alternatives)]
    assert targets.count('pdf') == 1
