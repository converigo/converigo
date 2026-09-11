"""F3/F5 wiring evidence: /tools/<slug> switches between the legacy widget and the
V2 tool-page widget ("tv2-") based on the result_widget_v2 feature flag."""

from fastapi.testclient import TestClient

import app.routers.tools as tools_router
from app.main import app

LEGACY_MARKERS = [
    'id="uploadSection"',
    'id="dropZone"',
    'id="chooseFile"',
    'id="smartRecommendation"',
]

# The extracted V2 tool-page widget ("Hasil Konversi" panel) is namespaced "tv2-"
# (see components/tool_result_widget_v2.html) and is selected per-slug by the
# result_widget_v2 feature flag.
V2_MARKERS = [
    'id="tv2-panelZone"',
    'id="tv2-rows"',
    'id="tv2-goBtn"',
    'id="tv2-dlAllBtn"',
]


def test_tool_page_renders_legacy_widget_when_flag_is_off(monkeypatch):
    monkeypatch.setattr(tools_router, "is_result_widget_v2_enabled", lambda **kwargs: False)

    client = TestClient(app)
    response = client.get("/tools/tar-extract")

    assert response.status_code == 200
    for marker in LEGACY_MARKERS:
        assert marker in response.text
    for marker in V2_MARKERS:
        assert marker not in response.text


def test_tool_page_renders_v2_widget_when_flag_is_forced_on(monkeypatch):
    monkeypatch.setattr(tools_router, "is_result_widget_v2_enabled", lambda **kwargs: True)

    client = TestClient(app)
    response = client.get("/tools/tar-extract")

    assert response.status_code == 200
    for marker in V2_MARKERS:
        assert marker in response.text
    assert 'id="uploadSection"' not in response.text
    assert 'widgets/result_widget_v2.js' not in response.text


# ---------------------------------------------------------------------------
# F5: per-slug parameterization of the V2 tool-page widget for archive-extract.
# ---------------------------------------------------------------------------

ARCHIVE_EXTRACT_CONFIG = {
    "tar-extract": {"operation": "tar-extract", "target": "tar"},
    "zip-extract": {"operation": "zip-extract", "target": "zip"},
    "gz-extract": {"operation": "gz-extract", "target": "gz"},
}


def test_v2_widget_is_parameterized_per_slug_when_flag_forced_on(monkeypatch):
    monkeypatch.setattr(tools_router, "is_result_widget_v2_enabled", lambda **kwargs: True)

    client = TestClient(app)
    for slug, expected in ARCHIVE_EXTRACT_CONFIG.items():
        response = client.get(f"/tools/{slug}")
        assert response.status_code == 200, slug
        for marker in V2_MARKERS:
            assert marker in response.text, f"{slug}: missing {marker}"
        assert f'data-operation="{expected["operation"]}"' in response.text, slug
        assert f'data-target-format="{expected["target"]}"' in response.text, slug


def test_zip_extract_renders_v2_when_flag_forced_on(monkeypatch):
    monkeypatch.setattr(tools_router, "is_result_widget_v2_enabled", lambda **kwargs: True)

    client = TestClient(app)
    response = client.get("/tools/zip-extract")

    assert response.status_code == 200
    assert 'data-operation="zip-extract"' in response.text
    assert 'data-target-format="zip"' in response.text
    assert 'accept=".zip,application/zip"' in response.text
    assert 'id="tv2-fileInput"' in response.text


def test_zip_extract_legacy_widget_when_flag_off(monkeypatch):
    monkeypatch.setattr(tools_router, "is_result_widget_v2_enabled", lambda **kwargs: False)

    client = TestClient(app)
    response = client.get("/tools/zip-extract")

    assert response.status_code == 200
    for marker in LEGACY_MARKERS:
        assert marker in response.text
    for marker in V2_MARKERS:
        assert marker not in response.text


def test_gz_extract_renders_v2_when_flag_forced_on(monkeypatch):
    monkeypatch.setattr(tools_router, "is_result_widget_v2_enabled", lambda **kwargs: True)

    client = TestClient(app)
    response = client.get("/tools/gz-extract")

    assert response.status_code == 200
    assert 'data-operation="gz-extract"' in response.text
    assert 'data-target-format="gz"' in response.text
    assert 'accept=".gz,.gzip,application/gzip"' in response.text
    assert 'id="tv2-fileInput"' in response.text


def test_gz_extract_legacy_widget_when_flag_off(monkeypatch):
    monkeypatch.setattr(tools_router, "is_result_widget_v2_enabled", lambda **kwargs: False)

    client = TestClient(app)
    response = client.get("/tools/gz-extract")

    assert response.status_code == 200
    for marker in LEGACY_MARKERS:
        assert marker in response.text
    for marker in V2_MARKERS:
        assert marker not in response.text