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

    # The engine no longer trusts a source-keyed claim on its own: before a chip is
    # advertised it asks the dispatch registry which plugin will really serve the
    # exact request the browser posts, so the fake has to answer that too. Highest
    # priority wins, mirroring PluginRegistry resolution order.
    candidates = [to_plugin_obj(p1), to_plugin_obj(p2), to_plugin_obj(p3)]

    def fake_get_plugin(source, target, slug=None):
        matches = [
            p
            for p in candidates
            if source in p.source_formats and target in p.target_formats
        ]
        if not matches:
            raise ValueError(f"no plugin for {source}->{target}")
        return max(matches, key=lambda p: p.priority)

    monkeypatch.setattr('app.plugins.registry.registry.get_plugin', fake_get_plugin)

    # A pdf -> pdf chip is only offerable on a page whose operation owns that
    # self-conversion; that is exactly the legacy tool-page case (/tools/pdf-compress).
    result = engine.recommend('pdf', operation='pdf-compress')

    # alternatives should not contain duplicate 'pdf' targets
    targets = [opt.target.lower() for opt in [result.best_choice] + list(result.alternatives)]
    assert targets.count('pdf') == 1
