import json
from pathlib import Path

from app.services.result_widget_service import ResultWidgetFlagService


def _service(tmp_path: Path, payload: dict) -> ResultWidgetFlagService:
    flags_path = tmp_path / "feature_flags.json"
    flags_path.write_text(json.dumps(payload), encoding="utf-8")
    return ResultWidgetFlagService(flags_path)


def test_shipped_flag_file_enables_tar_extract():
    # F5: the shipped flag file now enables the V2 tool-page widget for the
    # archive-extract slugs (tar-extract first; zip-extract/gz-extract added
    # incrementally during F5).
    service = ResultWidgetFlagService(Path("app/data/feature_flags.json"))

    flag = service.get_flag("result_widget_v2")
    assert flag["enabled"] is True
    assert service.is_enabled(slug="tar-extract", category="archive") is True
    # A different archive slug that is NOT in scope must stay on the legacy widget.
    assert service.is_enabled(slug="rar-extract", category="archive") is False


def test_enabled_flag_without_scope_stays_disabled(tmp_path):
    service = _service(tmp_path, {"result_widget_v2": {"enabled": True, "scope": []}})

    assert service.is_enabled(slug="tar-extract", category="archive") is False


def test_slug_scope_matches_only_that_slug(tmp_path):
    service = _service(tmp_path, {"result_widget_v2": {"enabled": True, "scope": ["slug:tar-extract"]}})

    assert service.is_enabled(slug="tar-extract", category="archive") is True
    assert service.is_enabled(slug="zip-extract", category="archive") is False


def test_category_scope_matches_every_slug_in_category(tmp_path):
    service = _service(tmp_path, {"result_widget_v2": {"enabled": True, "scope": ["category:archive"]}})

    assert service.is_enabled(slug="tar-extract", category="archive") is True
    assert service.is_enabled(slug="wav-to-mp3", category="audio") is False


def test_all_scope_matches_every_tool_page(tmp_path):
    service = _service(tmp_path, {"result_widget_v2": {"enabled": True, "scope": ["all"]}})

    assert service.is_enabled(slug="wav-to-mp3", category="audio") is True


def test_missing_flag_file_fails_safe_to_disabled(tmp_path):
    service = ResultWidgetFlagService(tmp_path / "does-not-exist.json")

    assert service.is_enabled(slug="tar-extract", category="archive") is False


def test_malformed_flag_file_fails_safe_to_disabled(tmp_path):
    flags_path = tmp_path / "feature_flags.json"
    flags_path.write_text("{ this is not json", encoding="utf-8")
    service = ResultWidgetFlagService(flags_path)

    assert service.is_enabled(slug="tar-extract", category="archive") is False


def test_unknown_scope_entries_are_ignored(tmp_path):
    service = _service(tmp_path, {"result_widget_v2": {"enabled": True, "scope": ["tar-extract", "  "]}})

    assert service.is_enabled(slug="tar-extract", category="archive") is False


def test_shipped_flag_file_keeps_gz_extract_disabled():
    # F5 governance decision: the shipped flag scope is TAR + ZIP only.
    # The GZ implementation and its wiring tests exist in the workstream, but the
    # gz-extract slug must NOT be enabled by the shipped flag — GZ release
    # enablement is deferred to its own gate. This is a governance choice, not a
    # GZ technical failure.
    service = ResultWidgetFlagService(Path("app/data/feature_flags.json"))

    assert service.is_enabled(slug="tar-extract", category="archive") is True
    assert service.is_enabled(slug="zip-extract", category="archive") is True
    assert service.is_enabled(slug="gz-extract", category="archive") is False
    # Slugs outside the flag scope must stay on the legacy widget.
    assert service.is_enabled(slug="rar-extract", category="archive") is False
    assert service.is_enabled(slug="7z-extract", category="archive") is False